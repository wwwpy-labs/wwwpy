import base64
import builtins
import dataclasses
import enum
import importlib
import json
import re
import sys
import types
import typing
from dataclasses import is_dataclass
from datetime import datetime
from typing import Any, Type, get_origin, get_args, TypeVar, List, Optional

from wwwpy.common import result

T = TypeVar('T')

class SerializationError(Exception):
    """Custom exception for serialization errors with path tracking."""
    def __init__(self, message: str, path: List[str]):
        self.path = path
        path_str = ".".join(str(p) for p in path) if path else "root"
        super().__init__(f"At {path_str}: {message}")


def serialize(obj: T, cls: Type[T], path: Optional[List[str]] = None) -> Any:
    """
    Serialize an object based on its type annotation.

    Args:
        obj: The object to serialize
        cls: The expected type of the object
        path: The current path in the object tree for error reporting

    Returns:
        The serialized representation of the object

    Raises:
        SerializationError: If serialization fails with detailed path information
    """
    path = path or [f"{cls}"]

    try:
        optional_type = _get_optional_type(cls)
        if optional_type:
            if obj is None:
                return None
            return serialize(obj, optional_type, path)

        origin = typing.get_origin(cls)

        # Handle union types
        if _is_union_type(origin):
            return _serialize_union(obj, cls, path)

        # Handle Result types
        if origin is result.Result:
            return _serialize_result(obj, cls, path)

        # Type checking
        if origin is not None:
            if not isinstance(obj, origin):
                raise SerializationError(
                    f"Expected object of type {origin}, got {type(obj).__name__}", path
                )
        elif not isinstance(obj, cls):
            raise SerializationError(
                f"Expected object of type {cls.__name__}, got {type(obj).__name__}", path
            )

        # Handle different types
        if is_dataclass(obj):
            return _serialize_dataclass(obj, cls, path)
        elif isinstance(obj, list):
            return _serialize_list(obj, cls, path)
        elif isinstance(obj, tuple):
            return _serialize_tuple(obj, cls, path)
        elif isinstance(obj, dict):
            return _serialize_dict(obj, cls, path)
        elif isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, bytes):
            return base64.b64encode(obj).decode('utf-8')
        elif isinstance(obj, (int, float, str, bool)):
            return obj
        elif isinstance(obj, enum.Enum):
            return serialize(obj.value, type(obj.value), path)
        elif obj is None:
            return None
        else:
            raise SerializationError(f"Unsupported type: {type(obj).__name__}", path)

    except SerializationError:
        # Just re-raise SerializationError as it already has path information
        raise
    except Exception as e:
        # Wrap other exceptions with context
        raise SerializationError(
            f"Serialization failed: {str(e)}", path
        ) from e


def _serialize_union(obj: Any, cls: Type, path: List[str]) -> Any:
    """Handle serialization of Union types."""
    args = set(get_args(cls))
    obj_type = type(obj)

    if obj_type not in args:
        valid_types = ", ".join(t.__name__ for t in args)
        raise SerializationError(
            f"Expected object of type {valid_types}, got {obj_type.__name__}", path
        )

    try:
        obj_ser = serialize(obj, obj_type, path)
        return [str(obj_type), obj_ser]
    except Exception as e:
        raise SerializationError(
            f"Failed to serialize union type {obj_type.__name__}", path
        ) from e


def _serialize_result(obj: Any, cls: Type, path: List[str]) -> Any:
    """Handle serialization of Result types."""
    args = set(get_args(cls))

    try:
        _assert_valid_result_type(type(obj))
    except ValueError as e:
        raise SerializationError(str(e), path) from e

    obj_type = type(obj._value)
    if obj_type not in args:
        valid_types = ", ".join(t.__name__ for t in args)
        raise SerializationError(
            f"Expected object of type Result {valid_types}, got {obj_type.__name__}", path
        )

    value_path = path + ["value"]
    try:
        obj_ser = serialize(obj._value, obj_type, value_path)
        return [str(type(obj)), obj_ser]
    except Exception as e:
        raise SerializationError(
            f"Failed to serialize Result value of type {obj_type.__name__}", path
        ) from e


def _serialize_dataclass(obj: Any, cls: Type, path: List[str]) -> dict:
    """Handle serialization of dataclass objects."""
    result = {}
    field_types = typing.get_type_hints(cls)

    for field_name, field_type in field_types.items():
        field_path = path + [field_name]
        try:
            field_value = getattr(obj, field_name)
            result[field_name] = serialize(field_value, field_type, field_path)
        except Exception as e:
            if not isinstance(e, SerializationError):
                raise SerializationError(
                    f"Failed to serialize field '{field_name}' of type {field_type.__name__}",
                    field_path
                ) from e
            raise

    return result


def _serialize_list(obj: list, cls: Type, path: List[str]) -> list:
    """Handle serialization of list objects."""
    item_type = typing.get_args(cls)[0]
    result = []

    for i, item in enumerate(obj):
        item_path = path + [str(i)]
        try:
            result.append(serialize(item, item_type, item_path))
        except Exception as e:
            if not isinstance(e, SerializationError):
                raise SerializationError(
                    f"Failed to serialize list item at index {i}", item_path
                ) from e
            raise

    return result


def _serialize_tuple(obj: tuple, cls: Type, path: List[str]) -> list:
    """Handle serialization of tuple objects."""
    result = []
    item_types = get_args(cls)

    for i, (item, item_type) in enumerate(zip(obj, item_types)):
        item_path = path + [str(i)]
        try:
            result.append(serialize(item, item_type, item_path))
        except Exception as e:
            if not isinstance(e, SerializationError):
                raise SerializationError(
                    f"Failed to serialize tuple item at index {i}", item_path
                ) from e
            raise

    return result


def _serialize_dict(obj: dict, cls: Type, path: List[str]) -> dict:
    """Handle serialization of dictionary objects."""
    key_type, value_type = typing.get_args(cls)
    result = {}

    for key, value in obj.items():
        key_path = path + ["key"]
        value_path = path + [str(key)]

        try:
            serialized_key = serialize(key, key_type, key_path)
            serialized_value = serialize(value, value_type, value_path)
            result[serialized_key] = serialized_value
        except Exception as e:
            if not isinstance(e, SerializationError):
                raise SerializationError(
                    f"Failed to serialize dictionary entry with key '{key}'",
                    value_path
                ) from e
            raise

    return result


def _get_optional_type(cls):
    """Extract the type from Optional[Type]."""
    origin = typing.get_origin(cls)
    args = typing.get_args(cls)

    if origin is typing.Union:
        if type(None) in args and len(args) == 2:
            return next(arg for arg in args if arg is not type(None))
    return None


class DeserializationError(Exception):
    """Custom exception for deserialization errors with path tracking."""
    def __init__(self, message: str, path: List[str]):
        self.path = path
        path_str = ".".join(str(p) for p in path) if path else "root"
        super().__init__(f"At {path_str}: {message}")


def deserialize(data: Any, cls: Type[T], path: Optional[List[str]] = None) -> T:
    """
    Deserialize data into an object of the specified type.

    Args:
        data: The serialized data
        cls: The target type to deserialize into
        path: The current path in the object tree for error reporting

    Returns:
        The deserialized object

    Raises:
        DeserializationError: If deserialization fails with detailed path information
    """
    path = path or [f"{cls}"]

    try:
        optional_type = _get_optional_type(cls)
        if optional_type:
            if data is None:
                return None
            return deserialize(data, optional_type, path)

        origin = get_origin(cls)

        # Handle union types
        if _is_union_type(origin):
            return _deserialize_union(data, cls, path)

        # Handle Result types
        if origin is result.Result:
            return _deserialize_result(data, cls, path)

        # Handle different types
        if is_dataclass(cls):
            return _deserialize_dataclass(data, cls, path)
        elif origin == list or cls == list:
            return _deserialize_list(data, cls, path)
        elif origin == tuple or cls == tuple:
            return _deserialize_tuple(data, cls, path)
        elif origin == dict or cls == dict:
            return _deserialize_dict(data, cls, path)
        elif isinstance(data, list):
            return _deserialize_subclass_list(data, cls, origin, path)
        elif cls == datetime:
            try:
                return datetime.fromisoformat(data)
            except ValueError as e:
                raise DeserializationError(
                    f"Invalid datetime format: {data}", path
                ) from e
        elif cls == bytes:
            try:
                return base64.b64decode(data.encode('utf-8'))
            except Exception as e:
                raise DeserializationError(
                    f"Invalid base64 data", path
                ) from e
        elif cls in (int, float, str, bool):
            try:
                return cls(data)
            except (ValueError, TypeError) as e:
                raise DeserializationError(
                    f"Cannot convert {data} to {cls.__name__}", path
                ) from e
        elif issubclass(cls, enum.Enum):
            try:
                first_member = next(iter(cls))
                value = deserialize(data, type(first_member.value), path)
                return cls(value)
            except (ValueError, KeyError) as e:
                valid_values = [m.value for m in cls]
                raise DeserializationError(
                    f"Invalid enum value for {cls.__name__}. Expected one of {valid_values}", path
                ) from e
        elif cls is type(None):
            if data is not None:
                raise DeserializationError(
                    f"Expected None, got {type(data).__name__}", path
                )
            return None
        else:
            raise DeserializationError(f"Unsupported type: {cls.__name__}", path)

    except DeserializationError:
        # Just re-raise DeserializationError as it already has path information
        raise
    except Exception as e:
        # Wrap other exceptions with context
        raise DeserializationError(
            f"Deserialization failed: {str(e)}", path
        ) from e


def _deserialize_union(data: list, cls: Type, path: List[str]) -> Any:
    """Handle deserialization of Union types."""
    if not isinstance(data, list) or len(data) != 2:
        raise DeserializationError(
            f"Invalid union data format: expected [type_str, value], got {data}", path
        )

    args = set(get_args(cls))
    try:
        obj_type = _get_type_from_string(data[0])
    except ValueError as e:
        raise DeserializationError(
            f"Invalid type string: {data[0]}", path
        ) from e

    if obj_type not in args:
        valid_types = ", ".join(t.__name__ for t in args)
        raise DeserializationError(
            f"Type {obj_type.__name__} not in union {valid_types}", path
        )

    try:
        return deserialize(data[1], obj_type, path)
    except Exception as e:
        if not isinstance(e, DeserializationError):
            raise DeserializationError(
                f"Failed to deserialize union value of type {obj_type.__name__}", path
            ) from e
        raise


def _deserialize_result(data: list, cls: Type, path: List[str]) -> Any:
    """Handle deserialization of Result types."""
    if not isinstance(data, list) or len(data) != 2:
        raise DeserializationError(
            f"Invalid Result data format: expected [type_str, value], got {data}", path
        )

    args = list(get_args(cls))
    try:
        obj_type = _get_type_from_string(data[0])
        _assert_valid_result_type(obj_type)
    except ValueError as e:
        raise DeserializationError(str(e), path) from e

    value_path = path + ["value"]
    if obj_type is result.Success:
        try:
            des = deserialize(data[1], args[0], value_path)
            return result.Success(des)
        except Exception as e:
            if not isinstance(e, DeserializationError):
                raise DeserializationError(
                    f"Failed to deserialize Success value", value_path
                ) from e
            raise
    elif obj_type is result.Failure:
        try:
            des = deserialize(data[1], args[1], value_path)
            return result.Failure(des)
        except Exception as e:
            if not isinstance(e, DeserializationError):
                raise DeserializationError(
                    f"Failed to deserialize Failure value", value_path
                ) from e
            raise
    else:
        raise DeserializationError(
            f"Expected Result type (Success or Failure), got {obj_type.__name__}", path
        )


def _deserialize_dataclass(data: dict, cls: Type, path: List[str]) -> Any:
    """Handle deserialization of dataclass objects."""
    if not isinstance(data, dict):
        raise DeserializationError(
            f"Expected dict for dataclass, got {type(data).__name__}", path
        )

    args = {}
    field_types = typing.get_type_hints(cls)

    # Get dataclass fields to check for default values
    dc_fields = {field.name: field for field in dataclasses.fields(cls)}

    # Check for missing required fields (those without default values)
    missing_fields = [
        field for field in field_types
        if field not in data and field in dc_fields and
           not dc_fields[field].default is dataclasses.MISSING and
           not dc_fields[field].default_factory is dataclasses.MISSING
    ]

    if missing_fields:
        raise DeserializationError(
            f"Missing required fields: {', '.join(missing_fields)}", path
        )

    # Process available fields
    for field_name, field_type in field_types.items():
        if field_name in data:
            field_path = path + [field_name]
            args[field_name] = deserialize(data[field_name], field_type, field_path)

    # Create the dataclass instance
    try:
        return cls(**args)
    except TypeError as e:
        raise DeserializationError(f"Failed to create dataclass: {str(e)}", path) from e

def _deserialize_list(data: list, cls: Type, path: List[str]) -> list:
    """Handle deserialization of list objects."""
    if not isinstance(data, list):
        raise DeserializationError(
            f"Expected list, got {type(data).__name__}", path
        )

    item_type = get_args(cls)[0]
    result = []

    for i, item in enumerate(data):
        item_path = path + [str(i)]
        try:
            result.append(deserialize(item, item_type, item_path))
        except Exception as e:
            if not isinstance(e, DeserializationError):
                raise DeserializationError(
                    f"Failed to deserialize list item at index {i}", item_path
                ) from e
            raise

    return result


def _deserialize_tuple(data: list, cls: Type, path: List[str]) -> tuple:
    """Handle deserialization of tuple objects."""
    if not isinstance(data, list):
        raise DeserializationError(
            f"Expected list for tuple, got {type(data).__name__}", path
        )

    item_types = get_args(cls)
    if len(data) != len(item_types):
        raise DeserializationError(
            f"Expected tuple of length {len(item_types)}, got {len(data)}", path
        )

    result = []
    for i, (item, item_type) in enumerate(zip(data, item_types)):
        item_path = path + [str(i)]
        try:
            result.append(deserialize(item, item_type, item_path))
        except Exception as e:
            if not isinstance(e, DeserializationError):
                raise DeserializationError(
                    f"Failed to deserialize tuple item at index {i}", item_path
                ) from e
            raise

    return tuple(result)


def _deserialize_dict(data: dict, cls: Type, path: List[str]) -> dict:
    """Handle deserialization of dictionary objects."""
    if not isinstance(data, dict):
        raise DeserializationError(
            f"Expected dict, got {type(data).__name__}", path
        )

    key_type, value_type = get_args(cls)
    result = {}

    for key, value in data.items():
        key_path = path + ["key"]

        try:
            deserialized_key = deserialize(key, key_type, key_path)
            value_path = path + [str(key)]
            deserialized_value = deserialize(value, value_type, value_path)
            result[deserialized_key] = deserialized_value
        except Exception as e:
            if not isinstance(e, DeserializationError):
                raise DeserializationError(
                    f"Failed to deserialize dictionary entry with key '{key}'",
                    path + [str(key)]
                ) from e
            raise

    return result


def _deserialize_subclass_list(data: list, cls: Type, origin, path: List[str]) -> Any:
    """Handle deserialization of list subclasses."""
    # Check if cls is a subclass of list or has origin that is a subclass of list
    ok = (origin is not None and issubclass(origin, list)) or (origin is None and issubclass(cls, list))
    if ok:
        # For subclasses of list
        item_type = get_args(cls)[0] if get_args(cls) else Any
        items = [deserialize(item, item_type, path + [str(i)]) for i, item in enumerate(data)]
        # If origin is None, use cls directly
        list_class = origin if origin is not None else cls
        return list_class(items)
    else:
        # If cls is not a subclass of list, raise an error
        raise DeserializationError(
            f"Expected a subclass of list, got {cls.__name__}", path
        )

def _get_type_from_string(type_str):
    """Convert a string representation of a type to the actual type object."""
    try:
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
    except (ImportError, AttributeError) as e:
        raise ValueError(f"Failed to resolve type '{type_str}': {str(e)}")


def _assert_valid_result_type(typ):
    """Ensure the type is a valid Result type (Success or Failure)."""
    success = typ is result.Success
    failure = typ is result.Failure
    ok = success or failure
    if not ok:
        raise ValueError(f"Expected object of type Result (Success or Failure), got {typ.__name__}")


def _is_union_type_3_10(origin):
    """Check if a type origin is a Union type in Python 3.10+."""
    return origin is typing.Union or origin is types.UnionType


def _is_union_type_3_9(origin):
    """Check if a type origin is a Union type in Python 3.9."""
    return origin is typing.Union


# Select the appropriate Union check based on Python version
_is_union_type = _is_union_type_3_10 if sys.version_info >= (3, 10) else _is_union_type_3_9


def to_json(obj: Any, cls: Type[T]) -> str:
    """
    Serialize an object to a JSON string.

    Args:
        obj: The object to serialize
        cls: The expected type of the object

    Returns:
        A JSON string representation of the object
    """
    try:
        return json.dumps(serialize(obj, cls))
    except SerializationError as e:
        # Re-raise with a more descriptive message
        raise SerializationError(
            f"JSON serialization failed: {str(e)}", e.path
        ) from e


def from_json(json_str: str, cls: Type[T]) -> T:
    """
    Deserialize a JSON string into an object of the specified type.

    Args:
        json_str: The JSON string to deserialize
        cls: The target type to deserialize into

    Returns:
        The deserialized object
    """
    try:
        data = json.loads(json_str)
    except json.JSONDecodeError as e:
        raise DeserializationError(
            f"Invalid JSON format: {str(e)}", []
        ) from e

    try:
        return deserialize(data, cls)
    except DeserializationError as e:
        # Re-raise with a more descriptive message
        raise DeserializationError(
            f"JSON deserialization failed: {str(e)}", e.path
        ) from e