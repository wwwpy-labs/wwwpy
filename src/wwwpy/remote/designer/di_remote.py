from wwwpy.remote.designer.ui import intent_aware, palette, design_aware, pushable_sidebar


def register_bindings():
    intent_aware.register_bindings()
    design_aware.register_bindings()
    palette.register_extension_point()
    pushable_sidebar.register_extension_point()
