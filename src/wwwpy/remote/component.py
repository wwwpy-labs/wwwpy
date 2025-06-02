from __future__ import annotations

import asyncio
import logging
from typing import Dict, TypeVar

import js
from js import Element, HTMLElement, console
from pyodide.ffi import create_proxy

logger = logging.getLogger(__name__)
namespace = "window.python_custom_elements"


class Metadata:
    def __init__(self, clazz, tag_name: str | None = None):
        if not issubclass(clazz, Component):
            raise Exception(f'clazz must be a subclass of {Component.__name__}')
        if tag_name is None:
            # get the full class name
            fully_qualified_class_name = clazz.__qualname__
            tag_name = ('wwwpy-auto-' + fully_qualified_class_name.lower()
                        .replace('<', '-')
                        .replace('>', '-')
                        .replace('.', '-')
                        )

        self.tag_name = tag_name
        self.observed_attributes = set()
        self.registered = False
        self.clazz: type[Component] = clazz
        self._custom_element_class_template = None

    @property
    def class_full_name(self) -> str:
        return f'{self.clazz.__module__}.{self.clazz.__qualname__}'

    def __set_name__(self, owner, name):
        if not issubclass(owner, Component):
            raise Exception(f'attribute {name} must be in a subclass of {Component.__name__}')
        self.clazz = owner
        # if self.auto_define:
        #     self.define_element()

    def define_element(self):
        if self.registered:
            return
        if js.eval(f'typeof {namespace}') == 'undefined':
            js.eval(namespace + ' = {}')

        js_class_name = self.tag_name.replace('-', '_').replace('.', '_')
        self._js_class_name = js_class_name

        pc = js.eval(namespace)
        already_defined = hasattr(pc, js_class_name)

        def create_instance(js_element=None):
            self.clazz(js_element)
            # when passing the instance back to javascript it seems it will not be garbage collected
            # doing this we track the JsProxy and we can manually call the JsProxy.destroy()
            return None

        setattr(pc, js_class_name, create_instance)  # set the python constructor, in any case
        if not already_defined:
            obs_attr = ', '.join(f'"{attr}"' for attr in self.observed_attributes)
            code = (_custom_element_class_template
                    .replace('$ClassName', js_class_name)
                    .replace('$tagName', self.tag_name)
                    .replace('$observedAttributes', obs_attr)
                    .replace('$namespace', namespace)
                    )
            self._custom_element_class_template = code
            # raise Exception(code)
            js.eval(code)

        self.registered = True

    @property
    def html_snippet(self):
        """Returns the complete HTML markup for this custom element."""
        return self.build_snippet()

    def build_snippet(self, attributes: Dict[str, str | None] = None, inner_html: str = '') -> str:
        """Returns a snippet of HTML for this custom element."""
        if attributes is None:
            attributes = {}
        attr_str = ' '.join(f'{k}="{v}"' for k, v in attributes.items())
        return f'<{self.tag_name} {attr_str}>{inner_html}</{self.tag_name}>'


# PUBLIC-API
class Component:
    component_metadata: Metadata = None
    element: HTMLElement = None
    element_not_found_raises = False

    def __init_subclass__(cls, tag_name: str | None = None, auto_define=True, **kwargs):
        super().__init_subclass__(**kwargs)
        metadata = Metadata(clazz=cls, tag_name=tag_name)
        cls.component_metadata = metadata
        if metadata.clazz is None:
            metadata.clazz = cls

        for name, value in cls.__dict__.items():
            if isinstance(value, attribute):
                cls.component_metadata.observed_attributes.add(value.name)

        if auto_define:
            cls.component_metadata.define_element()

    def __init__(self, element_from_js=None):
        self._proxy = create_proxy(self)
        if element_from_js is None:
            self.element = js.eval(f'window.{self.component_metadata._js_class_name}').new('init_from_python_yes')
        else:
            self.element = element_from_js

        self.element._python_component = self._proxy

        try:
            self.init_component()
        except Exception as e:
            logger.exception(f'Error in init_component: {e}')

        self._bind_events()

        if hasattr(self, 'after_init_component'):
            if asyncio.iscoroutinefunction(self.after_init_component):
                asyncio.create_task(self.after_init_component())
            else:
                self.after_init_component()

    def dispose(self):
        """
        After calling this method, the component will be unusable.
        This method is needed to break the circular reference between the element and the component.

        Sadly, the garbage collecting of the Component/Element instance is not automatic: I hope in
        some WASM unified garbage collecting.
        """
        if self.element:
            self.element._python_component = None
            self.element = None
        if self._proxy:
            self._proxy.destroy()
            self._proxy = None

    async def after_init_component(self):
        """This is called after init_component, it can be async or called synchronously if it is a normal method.
        It is called after the event binding is completed"""
        pass

    def init_component(self):
        pass

    def connectedCallback(self):
        pass

    def disconnectedCallback(self):
        pass

    def adoptedCallback(self):
        pass

    def attributeChangedCallback(self, name: str, oldValue: str | None, newValue: str | None):
        """
        This is called when an attribute is changed. The name is the name of the attribute, oldValue is the old value
        and newValue is the new value. The default implementation does nothing.
        """

    def root_element(self):
        """This is used to locate the child elements"""
        e = self.element
        return e if e.shadowRoot is None else e.shadowRoot

    def _find_element(self, name: str):
        root = self.root_element()
        selector = root.querySelector(f'[data-name="{name}"]')
        if selector is None:
            html_hint = root.outerHTML if hasattr(root, 'outerHTML') else (
                root.innerHTML if hasattr(root, 'innerHTML') else '--no-html-av--')
            msg = f'Not found data-name: [{name}] html: [{html_hint}]'
            if self.element_not_found_raises:
                raise ElementNotFound(msg)
            else:
                console.warn(msg)

        return selector

    def _find_python_attribute(self, name: str):
        selector = self._find_element(name)

        if selector:
            comp = get_component(selector)
            if comp:
                selector = comp

        self._check_type(name, selector)
        return selector

    def _check_type(self, name, selector):
        import inspect
        try:
            annotations = inspect.get_annotations(self.__class__, eval_str=True)
        except Exception as e:
            fqn = f'{self.__module__}.{self.__class__.__name__}'
            import sys
            state_unloaded = self.__module__ not in sys.modules
            att_ds = (f'Class {fqn} was unloaded but an instance is still referenced (with e.g., through DOM events)'
                      f'\nAttribute accessed `{name}` Instance id={id(self)}'
                      f'\nTo fix this error, remove the listeners that are firing (usually in a `disconnectedCallback` method)'
                      f'\nBeware that the stack trace could point to the wrong line because the instance in memory'
                      f'\nwas generated by a previous source.'
                      f'\nStack trace:\n{_get_stack_trace_string(-4)}') if state_unloaded else ''
            if not att_ds:
                logger.error(f'Error {fqn} getting annotations name=`{name}` selector=`{selector}`: {e}')
            else:
                try:
                    from wwwpy.server.designer import rpc
                    asyncio.create_task(rpc.on_exception_string(att_ds))
                except:
                    logger.error(att_ds)

            if logger.isEnabledFor(logging.DEBUG):
                logger.exception(e)
            return

        expected_type = annotations.get(name, None)
        if expected_type is None:
            # raise Exception(f'No type defined for field: {name}')
            return
        # raise Exception(f'type of expected_type: {type(expected_type)}')
        # test if expected_type is a class
        if not inspect.isclass(expected_type):
            return
        if not issubclass(expected_type, Component):
            return
        # raise Exception(f'Expected type: {expected_type} for field: {name} but found: {type(selector)}')
        isinst = not isinstance(selector, expected_type)
        # raise Exception(f'isinst: {isinst}')
        if isinst:
            raise WrongTypeDefinition(f'Expected type: {expected_type} for field: {name} but found: {type(selector)}')

    def _bind_events(self):

        members = dir(self)

        for name in members:
            if name.startswith('__'):
                continue
            if name.startswith('_js_'):  # fixme # this is a hack to be compatible with eventlib.py
                continue
            parts = name.split('__')
            if len(parts) != 2:
                continue

            element_name = parts[0]
            event_name = parts[1].replace('_', '-')
            if element_name == '' or event_name == '':
                continue

            element = self._find_element(element_name)
            if element is None:
                console.warn(f'Event bind failed, element `{element_name}` was not found for method `{name}`')
                continue

            m = getattr(self, name)
            element.addEventListener(event_name, create_proxy(m))


# this is a convenience to detect if the method is overridden or not and avoid creating void async task
del Component.after_init_component


class ElementNotFound(AttributeError): pass


class WrongTypeDefinition(TypeError): pass


# language=javascript
_custom_element_class_template = """
class $ClassName extends HTMLElement {
    static observedAttributes = [ $observedAttributes ];
    constructor(init_from_python) {
        super();
        if (!init_from_python)
            $namespace.$ClassName(this);
    }

    connectedCallback()    { this._python_component.connectedCallback(); }
    disconnectedCallback() { this._python_component.disconnectedCallback(); }
    adoptedCallback()      { this._python_component.adoptedCallback(); }
    attributeChangedCallback(name, oldValue, newValue) { this._python_component.attributeChangedCallback(name, oldValue, newValue); }
}

customElements.define('$tagName', $ClassName);
window.$ClassName = $ClassName;
"""

_C = TypeVar('_C', bound=Component)


def from_element(js_element: Element, component_class: type[_C] | None = None) -> _C | None:
    # verify that component_class is a subclass of Component
    if component_class is not None and not issubclass(component_class, Component):
        raise TypeError(f'component_class must be a subclass of {Component.__name__} but got {component_class}')
    if not hasattr(js_element, '_python_component'):
        return None
    component = js_element._python_component
    if hasattr(component, "unwrap"):
        component = component.unwrap()

    if component_class is not None:
        if not isinstance(component, component_class):
            raise TypeError(f'Expected {component_class.__name__}, but got {type(component).__name__}')

    return component


def get_component(js_element: Element, component_class: type[_C] | None = None) -> _C | None:
    return from_element(js_element, component_class)


# class Attribute(str):
#     _attr: attribute
#     present: bool
#
#     def toggle(self):
#         pass

# PUBLIC-API
class attribute:

    def __init__(self, name: str | None = None):
        self.name = name

    def __set_name__(self, owner, name):
        if not issubclass(owner, Component):
            raise Exception(f'attribute {name} must be in a subclass of {Component.__qualname__}')
        if self.name is None:
            self.name = name

    def __get__(self, obj: Component, objtype=None) -> str | None:
        return obj.element.getAttribute(self.name)

    def __set__(self, obj: Component, value: str | None):
        if value is None:
            obj.element.removeAttribute(self.name)
        else:
            obj.element.setAttribute(self.name, value)


# PUBLIC-API
class element:

    def __init__(self, cached=False):
        """ If cached is True, the element will be cached after the first access.
        Default is False.
        The practical use of this is when removing the element from the parent, the element is still available.
        Without cache, if it is detached from the parent, the element will be unreachable.
        """
        self.name = None
        self.cached = cached
        self.cache = None

    def __set_name__(self, owner, name):
        if not issubclass(owner, Component):
            raise Exception(f'attribute {name} must be in a subclass of {Component.__qualname__}')
        self.name = name

    def __get__(self, obj: Component, objtype=None):
        value = obj._find_python_attribute(self.name) if self.cache is None else self.cache
        if self.cached and self.cache is None:
            self.cache = value
        return value


def _get_stack_trace_string(skip_frames):
    import traceback
    stack = traceback.extract_stack()[:skip_frames]
    formatted_stack = traceback.format_list(stack)
    return ''.join(formatted_stack)
