"""
Validators library

Complex validators
"""
from .basic import BaseValidator


class Chain(BaseValidator):
    """
    Use a chain of validators for one value
    """
    def __init__(self, validators=None, stop_on_fail=True, *args, **kwargs):
        super(Chain, self).__init__(*args, **kwargs)
        
        self.stop_on_fail = stop_on_fail
        self.validators = validators
      
    def is_valid(self, value, *args, **kwargs):
        self.messages = {}
        return self._internal_is_valid(value, *args, **kwargs)

    def _internal_is_valid(self, value, *args, **kwargs):
        return True

