from __future__ import annotations

import logging
import time

import js
from pyodide.ffi import create_proxy

import wwwpy.remote.component as wpc
from wwwpy.remote import dict_to_js, hotkeylib
from wwwpy.remote._elementlib import ensure_tag_instance
from wwwpy.remote.designer.ui.design_aware import DesignAware
from wwwpy.remote.designer.ui.intent import IntentEvent
from wwwpy.remote.designer.ui.locator_event import LocatorEvent
from wwwpy.remote.jslib import is_instance_of, is_contained

logger = logging.getLogger(__name__)


class _SidebarDesignAware(DesignAware):

    def is_selectable_le(self, locator_event: LocatorEvent) -> bool | None:
        def is_container(element: js.Element) -> bool:
            return element.tagName.lower() == PushableSidebar.component_metadata.tag_name.lower()

        is_cont = is_contained(locator_event.main_element, is_container)
        logger.debug(f'is_selectable_le is_contained inside :{is_cont} ')
        if is_cont:
            return False
        return None

    def is_selectable_old(self, hover_event: IntentEvent) -> bool | None:
        # return None
        target = hover_event.deep_target
        if target is None:
            return None

        sidebar = is_inside_sidebar(target)
        if sidebar:
            logger.debug(f'inside sidebar')
            return False
        else:
            logger.debug('outside sidebar')
            return None


_sidebar_design_aware = _SidebarDesignAware()


def register_extension_point():
    DesignAware.EP_REGISTRY.register(_sidebar_design_aware)


_BODY_PADDING_STYLE_ID = '_wwwpy_body_padding_style'


def is_inside_sidebar(element: js.Element) -> bool:
    tag = PushableSidebar.component_metadata.tag_name

    def _check(el: js.Element) -> bool:
        # light DOM
        if el.closest(tag):
            return True
        # shadow DOM: climb to host if present
        root = el.getRootNode()
        host = getattr(root, 'host', None)
        if host:
            return _check(host)
        return False

    return _check(element)


class PushableSidebar(wpc.Component, tag_name='pushable-sidebar'):
    position: str = wpc.attribute()
    width: str = wpc.attribute()
    min_width: str = wpc.attribute()
    max_width: str = wpc.attribute()
    collapsed_width: str = wpc.attribute()
    z_index: str = wpc.attribute()
    state: str = wpc.attribute()

    _toggle_button: js.HTMLButtonElement = wpc.element()
    _close_button: js.HTMLButtonElement = wpc.element()
    _resize_handle: js.HTMLDivElement = wpc.element()
    _container: js.HTMLDivElement = wpc.element()
    _sidebar_content: js.HTMLDivElement = wpc.element()
    _style: js.HTMLStyleElement = wpc.element()
    _sb_buttons: js.HTMLDivElement = wpc.element()

    def init_component(self):
        """

        # Update the style
        self._update_style()Initialize the sidebar component"""
        # Create shadow DOM with HTML template
        self.element.attachShadow(dict_to_js({'mode': 'open'}))

        # language=html
        self.element.shadowRoot.innerHTML = """
        <style data-name="_style"></style>
        
        <div class="sidebar-container" data-name="_container">
            <div class="sidebar-header">
                <div class="sidebar-header-buttons" data-name="_sb_buttons">
                    <button class="toggle-button" 
                            data-name="_toggle_button" 
                            title="Toggle sidebar">
                    </button>
                    <button class="close-button" 
                            data-name="_close_button" 
                            title="Hide sidebar">
                        &times;
                    </button>
                </div>
            </div>
            <div class="sidebar-content" data-name="_sidebar_content">
                <slot></slot>
            </div>
            <div class="resize-handle" data-name="_resize_handle"></div>
        </div>
        """

        self._config = {
            'width': '300px',
            'minWidth': '50px',
            'maxWidth': '5000px',
            'collapsedWidth': '30px',
            'zIndex': 9999,
            'enable_animation': True,
        }

        # Initial state
        self._state = 'expanded'

        # Resize state variables
        self._is_resizing = False
        self._start_width = 0
        self._start_x = 0

        # Apply attribute values if provided
        if self.width:
            self._config['width'] = self.width
        if self.min_width:
            self._config['minWidth'] = self.min_width
        if self.max_width:
            self._config['maxWidth'] = self.max_width
        if self.collapsed_width:
            self._config['collapsedWidth'] = self.collapsed_width
        if self.z_index:
            self._config['zIndex'] = self.z_index
        if self.state:
            self._state = self.state

        self._hotkeys = hotkeylib.Hotkey(js.window)
        self._last_ctrl_time = None
        self._hotkeys.add('CTRL-Control', self._double_ctrl_detector)

    @property
    def _body_padding(self) -> js.HTMLStyleElement:
        instance = ensure_tag_instance('style', _BODY_PADDING_STYLE_ID, js.document.head)
        assert is_instance_of(instance, js.HTMLStyleElement)
        return instance

    def _double_ctrl_detector(self, event):
        if not self._last_ctrl_time:
            self._last_ctrl_time = time.perf_counter()
            return
        _current_time = time.perf_counter()
        delta = _current_time - self._last_ctrl_time
        self._last_ctrl_time = _current_time
        if delta < 0.3:
            self._last_ctrl_time = None
            self.toggle()
            return

    @property
    def _position(self) -> str:
        return self.position or 'left'

    def _update_style(self):
        """Update the style element based on current configuration"""
        position = self._position
        animation_speed = 300 if self._config['enable_animation'] else 0

        # Generate CSS content
        # language=css
        css = f"""
         :host {{
            display: {'none' if self._state == 'hidden' else 'block'};
            position: fixed;
            top: 0;
            {position}: 0;
            height: 100%;
            box-sizing: border-box;
            z-index: {self._config['zIndex']};
            transition: width {animation_speed}ms ease;
            width: {self._config['collapsedWidth'] if self._state == 'collapsed' else self._config['width']};
            overflow: hidden;
        }}
        
        .sidebar-container {{
            display: flex;
            flex-direction: column;
            height: 100%;
            width: 100%;
            background-color: #333;
            color: #fff;
            box-shadow: {('2px' if position == 'left' else '-2px')} 0 5px rgba(0, 0, 0, 0.1);
            box-sizing: border-box;
            transition: transform {animation_speed}ms ease;
        }}
        
        .sidebar-header {{
            display: flex;
            justify-content: {('flex-end' if position == 'left' else 'flex-start')};
            align-items: center;
            padding: 5px;
            border-bottom: 1px solid #444;
        }}
        
        .sidebar-header-buttons {{
            display: flex;
            flex-direction: column;
            align-items: center;
        }}
        
        .toggle-button, .close-button {{
            background: none;
            border: none;
            cursor: pointer;
            color: #fff;
            font-size: 14px;
            padding: 3px;
            margin: 2px 0;
            width: 20px;
            height: 20px;
            display: flex;
            align-items: center;
            justify-content: center;
            border-radius: 2px;
        }}
        
        .toggle-button:hover, .close-button:hover {{
            background-color: rgba(255, 255, 255, 0.1);
        }}
        
        .close-button {{
            font-size: 16px;
        }}
        
        .sidebar-content {{
            flex: 1;
            overflow-y: auto;
            padding: 10px;
        }}
        
        .resize-handle {{
            position: absolute;
            top: 0;
            {('right' if position == 'left' else 'left')}: 0;
            width: 8px;
            height: 100%;
            cursor: {('e-resize' if position == 'left' else 'w-resize')};
            background-color: transparent;
            transition: background-color 0.2s;
            z-index: 2;
            touch-action: none;
        }}
        
        .resize-handle:hover,
        .resize-handle.active {{
            background-color: rgba(255, 255, 255, 0.2);
        }}
        
        :host([state="collapsed"]) .sidebar-content,
        :host([state="collapsed"]) .resize-handle {{
            opacity: 0;
        }}
        
        :host([state="collapsed"]) .sidebar-header {{
            border-bottom: none;
        }}
        """

        # Update the style element
        self._style.textContent = css

    def _update_sidebar(self):
        """Update sidebar appearance and behavior based on configuration"""
        # Set attribute to match internal state
        self.element.setAttribute('state', self._state)

        # Handle display based on state
        if self._state == 'hidden':
            self.element.style.display = 'none'
            self._remove_padding()
            return
        else:
            self.element.style.display = 'block'

        # Update the width based on state
        self.element.style.width = self._config['collapsedWidth'] if self._state == 'collapsed' else self._config[
            'width']

        # Update toggle button icon and title
        position = self._position
        toggle_icon = '&#9658;' if (position == 'left' and self._state == 'collapsed') or \
                                   (position == 'right' and self._state != 'collapsed') else '&#9668;'
        self._toggle_button.innerHTML = toggle_icon
        self._toggle_button.title = 'Expand sidebar' if self._state == 'collapsed' else 'Collapse sidebar'

        # Update style
        self._update_style()

        # Update document body padding
        self._adjust_content_padding()

    def _adjust_content_padding(self):
        """Adjust body padding to accommodate the sidebar"""
        # Remove existing padding first
        self._remove_padding()

        # Skip adding padding if sidebar is hidden
        if self._state == 'hidden':
            return

        # Add padding based on current sidebar state
        current_width = self._config['collapsedWidth'] if self._state == 'collapsed' else \
            self.element.style.width or self._config['width']

        # Calculate padding with the px suffix if needed
        padding_value = current_width if current_width.endswith('px') else f"{current_width}px"

        # Apply padding to body to push content
        self._set_padding(padding_value)

        # Dispatch event for external components to react
        self.element.dispatchEvent(
            js.CustomEvent.new('sidebar-resize', dict_to_js({
                'detail': {'width': current_width}
            }))
        )

    def _remove_padding(self):
        """Remove body padding"""
        self._set_padding('')

    async def _resize_handle__mousedown(self, event):
        """Start resize operation (using wwwpy's naming convention for event handlers)"""
        # If sidebar is in collapsed state, expand it first but keep the current width
        if self._state == 'collapsed':
            current_width = self.element.style.width
            self._config.update({'width': current_width})
            self.set_state('expanded')
            self.element.style.width = current_width  # Prevent jumping to stored width

        self._is_resizing = True
        self._start_width = int(js.getComputedStyle(self.element).width.replace('px', ''))
        self._start_x = event.clientX

        # Add active class to handle
        self._resize_handle.classList.add('active')

        # Set up mousemove and mouseup handlers directly on document
        self._mousemove_handler = create_proxy(self._handle_resize)
        self._mouseup_handler = create_proxy(self._stop_resize)

        js.document.addEventListener('mousemove', self._mousemove_handler)
        js.document.addEventListener('mouseup', self._mouseup_handler)
        js.document.addEventListener('mouseleave', self._mouseup_handler)

        # Prevent text selection during resize
        js.document.body.style.userSelect = 'none'

        # Add a resize class to the body to optimize rendering
        # self._config['animation_speed'] = 0  # Disable animation during resize
        # self._config['enable_animation'] = False
        self._config.update({'enable_animation': False})
        self._update_style()

        event.preventDefault()

    def _handle_resize(self, event):
        """Handle resize during mouse move"""
        if not self._is_resizing:
            return

        # Calculate new width
        if self.position == 'left':
            new_width = self._start_width + (event.clientX - self._start_x)
        else:
            new_width = self._start_width - (event.clientX - self._start_x)

        # Apply min/max constraints
        min_width = int(self._config['minWidth'].replace('px', ''))
        max_width = int(self._config['maxWidth'].replace('px', ''))

        if new_width < min_width:
            new_width = min_width
        if new_width > max_width:
            new_width = max_width

        # Update the sidebar width
        self.element.style.width = f"{new_width}px"

        # Update body padding
        self._set_padding(f"{new_width}px")

    def _set_padding(self, padding):
        # if self._config['position'] == 'left':
        #     js.document.body.style.paddingLeft = padding
        # else:
        #     js.document.body.style.paddingRight = padding
        # use a style tag to set the padding to body; use important
        if padding == '':
            style = ''
        else:
            style = (
                """body {\n padding-WHERE: PADDING !important; \n} """
                .replace('WHERE', self.position)
                .replace('PADDING', padding))

        self._body_padding.innerHTML = style

    def _stop_resize(self, event):
        """End resize operation"""
        if not self._is_resizing:
            return

        self._is_resizing = False
        self._resize_handle.classList.remove('active')

        # Clean up event listeners
        js.document.removeEventListener('mousemove', self._mousemove_handler)
        js.document.removeEventListener('mouseup', self._mouseup_handler)
        js.document.removeEventListener('mouseleave', self._mouseup_handler)

        # Restore text selection
        js.document.body.style.userSelect = ''

        # Remove resize class
        # self._config['animation_speed'] = 300  # Restore animation speed
        self._config.update({'enable_animation': True})
        self._update_style()

        # Store the final width in the config
        width_val = self.element.style.width
        if width_val.endswith('px'):
            width_px = int(width_val.replace('px', ''))
            self._config['width'] = f"{width_px}px"
        else:
            self._config['width'] = width_val

        # Save the current width to localStorage if desired
        try:
            js.localStorage.setItem('pushable-sidebar-width', self._config['width'])
        except:
            pass

        # Fire an event for the resize completion
        self.element.dispatchEvent(
            js.CustomEvent.new('sidebar-resize-end', dict_to_js({
                'detail': {'width': self._config['width']}
            }))
        )

    async def _toggle_button__click(self, event):
        """Handle toggle button click - uses wwwpy's automatic event binding"""
        self.toggle()

    async def _close_button__click(self, event):
        """Handle close button click - uses wwwpy's automatic event binding"""
        self.set_state('hidden')

    # Public API methods
    def set_state(self, state):
        """Set sidebar state ('hidden', 'collapsed', 'expanded')"""
        logger.debug(f'set_state called with state: {state}, current state: {self._state}')
        if state not in ['hidden', 'collapsed', 'expanded']:
            logger.warning('Invalid state. Valid states are: hidden, collapsed, expanded')
            return self

        old_state = self._state
        self._state = state
        self._update_sidebar()

        # Dispatch event
        self.element.dispatchEvent(
            js.CustomEvent.new('sidebar-state-change', dict_to_js({
                'detail': {
                    'oldState': old_state,
                    'newState': state
                }
            }))
        )

        return self

    def get_state(self):
        """Get current state"""
        return self._state

    def toggle(self):
        logger.debug(f'toggle called, current state: {self._state}')
        """Toggle sidebar state: expanded <-> collapsed, or hidden -> expanded"""
        if self._state == 'hidden':
            self.set_state('expanded')
        elif self._state == 'expanded':
            self.set_state('collapsed')
        else:  # collapsed
            self.set_state('expanded')
        return self

    def set_width(self, width):
        """Set sidebar width programmatically"""
        self._config['width'] = width
        if self._state == 'expanded':
            self.element.style.width = width
            self._adjust_content_padding()
        return self

    def set_position(self, position):
        """Set sidebar position"""
        if position not in ['left', 'right']:
            logger.warning('Sidebar position must be "left" or "right"')
            return self

        # Remove current positioning
        self._remove_padding()

        # Update position
        self.position = position
        # self.element.setAttribute('position', position)

        # Re-initialize the component
        # self._update_sidebar()

        return self

    # Lifecycle callbacks from the web components spec
    def connectedCallback(self):
        """Called when the element is added to the DOM"""
        # logger.warning(f'connectedCallback {self._state}')
        self._hotkeys.install()
        # Update the sidebar when connected
        self._update_sidebar()

        # Add resize event listener for responsive behavior
        self._window_resize_handler = create_proxy(lambda event: self._adjust_content_padding())
        js.window.addEventListener('resize', self._window_resize_handler)

    def disconnectedCallback(self):
        """Called when the element is removed from the DOM"""
        # logger.warning(f'disconnectedCallback {self._state}')
        self._hotkeys.uninstall()
        # Remove the padding from body when sidebar is removed
        self._remove_padding()

        # Clean up event listeners
        if hasattr(self, '_window_resize_handler'):
            js.window.removeEventListener('resize', self._window_resize_handler)

    def attributeChangedCallback(self, name, old_value, new_value):
        """Called when an observed attribute changes"""
        if old_value == new_value:
            return

        # Convert kebab-case to camelCase for some attribute names
        elif name == 'width':
            self._config['width'] = new_value
        elif name == 'min-width':
            self._config['minWidth'] = new_value
        elif name == 'max-width':
            self._config['maxWidth'] = new_value
        elif name == 'collapsed-width':
            self._config['collapsedWidth'] = new_value
        elif name == 'z-index':
            self._config['zIndex'] = new_value
        elif name == 'state':
            if new_value in ['hidden', 'collapsed', 'expanded']:
                self._state = new_value
            else:
                logger.warning('Invalid state. Valid values are: hidden, collapsed, expanded')

        # Update the sidebar if it's already connected
        if self.element.isConnected:
            self._update_sidebar()
