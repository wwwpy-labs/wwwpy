from wwwpy.remote.designer.ui import intent_aware, palette


def register_bindings():
    intent_aware.register_bindings()
    palette.register_extension_point()
