class TargetAdapter:

    def __init__(self):
        self.listeners = []
        super().__init__()

    def set_target_value(self, value):
        pass

    def get_target_value(self):
        pass


class Binding:

    def __init__(self, instance, attr_name, target_adapter: TargetAdapter):
        super().__init__()
        self.instance = instance
        self.attr_name = attr_name
        self.target_adapter = target_adapter
        target_adapter.listeners.append(self._set_attr)

    def apply_binding(self):
        self.target_adapter.set_target_value(getattr(self.instance, self.attr_name))

    def _set_attr(self, event):
        setattr(self.instance, self.attr_name, self.target_adapter.get_target_value())