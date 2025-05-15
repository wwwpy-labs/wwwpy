from wwwpy.remote.designer.ui import palette, pushable_sidebar


def register_bindings():
    palette.extension_point_register()
    pushable_sidebar.register_extension_point()
