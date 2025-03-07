import base64
import builtins
import enum
import importlib
import json
import re
import typing
from dataclasses import is_dataclass
from datetime import datetime
from typing import Any, Type, get_origin, get_args, TypeVar

from wwwpy.common import result

T = TypeVar('T')


# todo this should also receive the expected cls Type.
# this way we can check that the instance is of the expected type
def serialize(obj: T, cls: Type[T]) -> Any:
    optional_type = _get_optional_type(cls)
    if optional_type:
        if obj is None:
            return None
        return serialize(obj, optional_type)
    origin = typing.get_origin(cls)
    if origin is typing.Union:
        args = set(get_args(cls))
        obj_type = type(obj)
        if obj_type not in args:
            raise ValueError(f"Expected object of type {args}, got {obj_type}")
        obj_ser = serialize(obj, obj_type)
        return [str(obj_type), obj_ser]
    if origin is result.Result:
        args = set(get_args(cls))
        _assert_valid_result_type(type(obj))
        obj_type = type(obj._value)
        if obj_type not in args:
            raise ValueError(f"Expected object of type Result {args}, got {obj._value}")
        obj_ser = serialize(obj._value, obj_type)
        return [str(type(obj)), obj_ser]

    if origin is not None:
        if not isinstance(obj, origin):
            raise ValueError(f"Expected object of type {origin}, got {type(obj)}")
    elif not isinstance(obj, cls):
        raise ValueError(f"Expected object of type {cls}, got {type(obj)}")
    if is_dataclass(obj):
        field_types = typing.get_type_hints(cls)
        return {
            field_name: serialize(getattr(obj, field_name), field_type)
            for field_name, field_type in field_types.items()
        }
    elif isinstance(obj, list):
        item_type = typing.get_args(cls)[0]
        return [serialize(item, item_type) for item in obj]
    elif isinstance(obj, tuple):
        return [serialize(item, get_args(cls)[i]) for i, item in enumerate(obj)]
    elif isinstance(obj, dict):
        key_type, value_type = typing.get_args(cls)
        return {
            serialize(key, key_type): serialize(value, value_type)
            for key, value in obj.items()
        }
    elif isinstance(obj, datetime):
        return obj.isoformat()
    elif isinstance(obj, bytes):
        return base64.b64encode(obj).decode('utf-8')
    elif isinstance(obj, (int, float, str, bool)):
        return obj
    elif isinstance(obj, enum.Enum):
        return serialize(obj.value, type(obj.value))
    elif obj is None:
        return None
    else:
        raise ValueError(f"Unsupported type: {type(obj)}")


def _get_optional_type(cls):
    origin = typing.get_origin(cls)
    args = typing.get_args(cls)

    if origin is typing.Union:
        if type(None) in args and len(args) == 2:
            return args[0]
    # if origin is types.UnionType:
    #     return type(None) in args
    return None


def deserialize(data: Any, cls: Type[T]) -> T:
    optional_type = _get_optional_type(cls)
    if optional_type:
        if data is None:
            return None
        return deserialize(data, optional_type)
    origin = get_origin(cls)
    if origin is typing.Union:
        args = set(get_args(cls))
        obj_type = _get_type_from_string(data[0])
        if obj_type not in args:
            raise ValueError(f"Expected object of type {args}, got {obj_type}")
        return deserialize(data[1], obj_type)
    if origin is result.Result:
        args = list(get_args(cls))
        obj_type = _get_type_from_string(data[0])
        _assert_valid_result_type(obj_type)
        if obj_type is result.Success:
            des = deserialize(data[1], args[0])
            return result.Success(des)
        elif obj_type is result.Failure:
            des = deserialize(data[1], args[1])
            return result.Failure(des)
        else:
            raise ValueError(f"Expected object of type Result {args}, got {obj_type}")
    if is_dataclass(cls):
        args = {}
        field_types = typing.get_type_hints(cls)
        for name, value in data.items():
            args[name] = deserialize(value, field_types[name])
        instance = cls(**args)
        return instance
    elif origin == list or cls == list:
        item_type = get_args(cls)[0]
        return [deserialize(item, item_type) for item in data]
    elif origin == tuple or cls == tuple:
        item_types = get_args(cls)
        return tuple(deserialize(data[i], item_types[i]) for i in range(len(data)))
    elif origin == dict or cls == dict:
        key_type, value_type = get_args(cls)
        return {
            deserialize(key, key_type): deserialize(value, value_type)
            for key, value in data.items()
        }
    elif isinstance(data, list):  # for subclasses of list
        item_type = get_args(cls)[0]
        return cls([deserialize(item, item_type) for item in data])
    elif cls == datetime:
        return datetime.fromisoformat(data)
    elif cls == bytes:
        return base64.b64decode(data.encode('utf-8'))
    elif cls in (int, float, str, bool):
        return cls(data)
    elif issubclass(cls, enum.Enum):
        first_member = next(iter(cls))
        return cls(deserialize(data, type(first_member.value)))
    elif cls is type(None):
        return None
    else:
        raise ValueError(f"Unsupported type: {cls}")


def to_json(obj: Any, cls: Type[T]) -> str:
    return json.dumps(serialize(obj, cls))


def from_json(json_str: str, cls: Type[T]) -> T:
    data = json.loads(json_str)
    return deserialize(data, cls)


def _get_type_from_string(type_str):
    # Use regex to extract the full type path
    match = re.search(r"<class '(.+)'>|(.+)", type_str)
    if not match:
        raise ValueError(f"Invalid type string format: {type_str}")

    full_path = match.group(1) or match.group(2)

    if full_path == 'NoneType':
        return type(None)

    # Check if it's a builtin type
    if hasattr(builtins, full_path):
        return getattr(builtins, full_path)

    # Split the path into parts
    parts = full_path.split('.')

    # The class name is the last part
    class_name = parts.pop()

    # The module name is everything else
    module_name = '.'.join(parts)

    # Import the module dynamically
    module = importlib.import_module(module_name)

    # Get the class from the module
    return getattr(module, class_name)


def _assert_valid_result_type(typ):
    success = typ is result.Success
    failure = typ is result.Failure
    ok = success or failure
    if not ok:
        raise ValueError(f"Expected object of type Result got {typ}")
