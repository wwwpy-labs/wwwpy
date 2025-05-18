from wwwpy.remote.designer.ui import palette, pushable_sidebar, floater_action_band


def register_bindings():
    palette.extension_point_register()
    pushable_sidebar.register_extension_point()
    floater_action_band.extension_point_register()
