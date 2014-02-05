"""
Validators library

Complex validators
"""
from .basic import BaseValidator


class Chain(BaseValidator):

    """
    Use a chain of validators for one value
    """

    def __init__(self, validators=[], stop_on_fail=True, *args, **kwargs):
        super(Chain, self).__init__(*args, **kwargs)

        self.stop_on_fail = stop_on_fail
        self.validators = validators[:]

    def _internal_is_valid(self, value, *args, **kwargs):
        result = True
        for validator in self.validators:
            if not validator.is_valid(value, *args, **kwargs):
                self.messages.update(validator.messages)
                result = False
                if self.stop_on_fail:
                    return False
        return result


class ComplexValidator(BaseValidator):

    def is_valid(self, value, *args, **kwargs):
        context = kwargs.get('context', [])
        context.append(value)
        kwargs['context'] = context

        result = super(ComplexValidator, self).is_valid(value, *args, **kwargs)

        context.pop()
        return result


class ListValidator(ComplexValidator):

    """
    Validate items on list
    """

    def __init__(self, validator, stop_on_fail=True, *args, **kwargs):
        super(ListValidator, self).__init__(*args, **kwargs)

        self.validator = validator
        self.stop_on_fail = stop_on_fail


class AllItems(ListValidator):

    """
    Validate all items on list
    """

    def _internal_is_valid(self, value, *args, **kwargs):
        result = True
        for item_index in range(len(value)):
            if not self.validator.is_valid(value[item_index], *args, **kwargs):
                self.messages[item_index] = self.validator.messages
                result = False
                if self.stop_on_fail:
                    return False
        return result


class SomeItems(ListValidator):

    """
    Validate some items on list
    """

    TOO_MANY_VALID_ITEMS = 'tooManyValidItems'
    TOO_FEW_VALID_ITEMS = 'tooFewValidItems'

    error_messages = {
        TOO_MANY_VALID_ITEMS: "Too many items pass validation",
        TOO_FEW_VALID_ITEMS: "Too few items pass validation"
    }

    def __init__(self, min=1, max=-1, *args, **kwargs):
        super(SomeItems, self).__init__(*args, **kwargs)
        assert min != -1 or max != -1, 'At least one of `min` or `max` must be specified.'
        assert max == -1 or min <= max, '`min` cannot be more than `max`.'
        self.min = min
        self.max = max

        self.message_values.update({"min": self.min, "max": self.max})

    def _internal_is_valid(self, value, *args, **kwargs):
        item_pass = 0
        messages = {}
        for item_index in range(len(value)):
            if not self.validator.is_valid(value[item_index], *args, **kwargs):
                messages[item_index] = self.validator.messages
            else:
                item_pass += 1
                if self.stop_on_fail and max != -1 and item_pass > self.max:
                    self.error(self.TOO_MANY_VALID_ITEMS, value)
                    self.messages.update(messages)
                    return False

        if max != -1 and item_pass > self.max:
            self.error(self.TOO_MANY_VALID_ITEMS, value)
            self.messages.update(messages)
            return False

        if min != -1 and item_pass < self.min:
            self.error(self.TOO_FEW_VALID_ITEMS, value)
            self.messages.update(messages)
            return False

        return True


# class DependsOnFields(BaseValidator):
#    def is_valid(self, value, *args, **kwargs):
#        context = kwargs.get('context', [])
#        context.append(value)
#        kwargs['context'] = context
#
#        result = super(ComplexValidator, self).is_valid(value, *args, **kwargs)
#
#        context.pop()
#        return result
