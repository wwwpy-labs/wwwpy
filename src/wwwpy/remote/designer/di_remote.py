from wwwpy.remote.designer.ui import palette, pushable_sidebar


def register_bindings():
    palette.register_extension_point()
    pushable_sidebar.register_extension_point()
