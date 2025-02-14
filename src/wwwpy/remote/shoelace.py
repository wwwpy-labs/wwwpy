from js import document
import js

from wwwpy.common.asynclib import create_task_safe
from wwwpy.remote.jslib import script_load_once

_version = '2.20.0'
_css_url = f'https://cdn.jsdelivr.net/npm/@shoelace-style/shoelace@{_version}/cdn/themes/dark.css'
_js_url = f'https://cdn.jsdelivr.net/npm/@shoelace-style/shoelace@{_version}/cdn/shoelace.js'

_task = []


def setup_shoelace():
    async def _setup_shoelace():
        needed = await script_load_once(_js_url, type='module')
        if needed:
            document.documentElement.className = 'sl-theme-dark'
            document.head.append(document.createRange().createContextualFragment(_head_style))

    return create_task_safe(_setup_shoelace())


# <script type="module" src="https://cdn.jsdelivr.net/npm/@shoelace-style/shoelace@2.20.0/cdn/shoelace.js" ></script>

# language=html
_head_style = f"""
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=0">
<style>@import '{_css_url}';</style>
<style>
    body {{
        font: 16px sans-serif;
        background-color: var(--sl-color-neutral-0);
        color: var(--sl-color-neutral-900);
        padding: 1rem;
    }}
</style>
"""
_head_script = f"""<script type="module" src="{_js_url}"></script>"""


# alternative
# language=html
_head_style_dark_palin ="""
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=0">
<style>
    body {
        background: #121212;
        color: #e0e0e0;
        margin: 1rem;
        font: 16px sans-serif;
    }

    a {
        color: #bb86fc
    }
</style>
"""