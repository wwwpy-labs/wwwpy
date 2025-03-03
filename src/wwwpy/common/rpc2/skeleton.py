from __future__ import annotations


class Skeleton:
    def invoke(self, module_name: str, name: str, *args):
        """name can be
        - a function name
        - a method name in the form of 'class_name.method'

        In the case this is a method invocation the first element of args can be None or any value
        that can be used by the implementation to link a Called object to the Caller object
        """
