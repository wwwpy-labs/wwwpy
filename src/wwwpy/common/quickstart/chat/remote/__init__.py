from js import document


async def main():
    from wwwpy.remote import simple_dark_theme
    simple_dark_theme.setup()

    from . import component1  # for component registration
    document.body.innerHTML = '<component-1></component-1>'
