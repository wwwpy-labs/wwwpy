class Binding:

    def __init__(self, instance, attr_name, ui_element):
        self.instance = instance
        self.attr_name = attr_name
        self.ui_element = ui_element
        super().__init__()

    def apply_binding(self):
        self.ui_element.value = getattr(self.instance, self.attr_name)


def new_dataclass_binding(instance, attr_name, ui_element) -> Binding:
    return Binding(instance, attr_name, ui_element)
