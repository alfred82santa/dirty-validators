"""
Validators library

Complex validators
"""
from .basic import BaseValidator
from dirty_validators.basic import NotNone
from collections import OrderedDict
from dirty_models.models import BaseModel


class Chain(BaseValidator):

    """
    Use a chain of validators for one value
    """

    def __init__(self, validators=None, stop_on_fail=True, *args, **kwargs):
        super(Chain, self).__init__(*args, **kwargs)

        self.stop_on_fail = stop_on_fail
        self.validators = validators.copy() if validators is not None else []

    def _internal_is_valid(self, value, *args, **kwargs):
        result = True
        for validator in self.validators:
            if not validator.is_valid(value, *args, **kwargs):
                self.messages.update(validator.messages)
                result = False
                if self.stop_on_fail:
                    return False
        return result


class Some(BaseValidator):

    """
    Pass some validators for one value
    """

    def __init__(self, validators=None, *args, **kwargs):
        super(Some, self).__init__(*args, **kwargs)

        self.validators = validators.copy() if validators is not None else []

    def _internal_is_valid(self, value, *args, **kwargs):
        messages = {}
        for validator in self.validators:
            if validator.is_valid(value, *args, **kwargs):
                return True
            messages.update(validator.messages)

        self.messages.update(messages)
        return False


class ComplexValidator(BaseValidator):

    """
    Base for validator which inject context
    """

    def is_valid(self, value, *args, **kwargs):
        context = kwargs.get('context', [])
        context.append(value)
        kwargs['context'] = context

        result = super(ComplexValidator, self).is_valid(value, *args, **kwargs)

        context.pop()
        return result

    def import_messages(self, prefix, messages):
        base_messages = {}
        for key, message in messages.items():
            if isinstance(message, dict):
                self.messages[str(prefix) + "." + str(key)] = message
            else:
                base_messages[key] = message

        if len(base_messages):
            self.messages[prefix] = base_messages


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
                self.import_messages(item_index, self.validator.messages)
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
        for item_index in range(len(value)):
            if not self.validator.is_valid(value[item_index], *args, **kwargs):
                self.import_messages(item_index, self.validator.messages)
            else:
                item_pass += 1
                if self.stop_on_fail and max != -1 and item_pass > self.max:
                    self.error(self.TOO_MANY_VALID_ITEMS, value)
                    return False

        if max != -1 and item_pass > self.max:
            self.error(self.TOO_MANY_VALID_ITEMS, value)
            return False

        if min != -1 and item_pass < self.min:
            self.error(self.TOO_FEW_VALID_ITEMS, value)
            return False

        self.messages = {}
        return True


class ItemLimitedOccuerrences(BaseValidator):

    """
    Validate whether item in list are distincts
    """

    TOO_MANY_ITEM_OCCURRENCES = 'tooManyItemOccurrences'
    TOO_FEW_ITEM_OCCURRENCES = 'tooFewItemOccurrences'

    error_messages = {
        TOO_MANY_ITEM_OCCURRENCES: "Item '$value' is repeated to many times. Limit to $max_occ.",
        TOO_FEW_ITEM_OCCURRENCES: "Item '$value' is not enough repeated. Limit to $min_occ.",
    }

    def __init__(self, min_occ=0, max_occ=1, *args, **kwargs):
        super(ItemLimitedOccuerrences, self).__init__(*args, **kwargs)
        self.min_occ = min_occ
        self.max_occ = max_occ

        self.message_values['min_occ'] = self.min_occ
        self.message_values['max_occ'] = self.max_occ

    def _get_checking_value(self, value):
        """
        It must be override on descendant validators
        """
        return value

    def _internal_is_valid(self, value, *args, **kwargs):

        def add_occurrence(val, counter):
            if val not in counter:
                counter[val] = 0

            counter[val] += 1

        counter = {}

        for item in value:
            val = self._get_checking_value(item)
            add_occurrence(val, counter)

            if counter[val] > self.max_occ:
                self.error(self.TOO_MANY_ITEM_OCCURRENCES, val)
                return False

        for val, occ in counter.items():
            if occ < self.min_occ:
                self.error(self.TOO_FEW_ITEM_OCCURRENCES, val)
                return False

        return True


def get_field_value_from_context(field_name, context_list):
    """
    Helper to get field value from string path.
    String '<context>' is used to go up on context stack. It just
    can be used at the beginning of path: <context>.<context>.field_name_1
    """
    field_path = field_name.split('.')
    context_index = -1
    while field_path[0] == '<context>':
        context_index -= 1
        field_path.pop(0)

    try:
        field_value = context_list[context_index]

        while len(field_path):
            field = field_path.pop(0)
            if isinstance(field_value, (list, tuple)):
                if field.isdigit():
                    field = int(field)
                field_value = field_value[field]
            elif isinstance(field_value, dict):
                try:
                    field_value = field_value[field]
                except KeyError:
                    if field.isdigit():
                        field = int(field)
                        field_value = field_value[field]
                    else:
                        field_value = None

            else:
                field_value = getattr(field_value, field)

        return field_value
    except (IndexError, AttributeError, KeyError):
        return None


class IfField(BaseValidator):

    """
    Conditional validator. It run validators if a specific field value pass validations.
    """

    NEEDS_VALIDATE = 'needsValidate'

    error_messages = {
        NEEDS_VALIDATE: "Some validate error due to field '$field_name' has value '$field_value'.",
    }

    def __init__(self, validator, field_name, field_validator=None,
                 run_if_none=False, add_check_info=True, *args, **kwargs):
        super(IfField, self).__init__(*args, **kwargs)

        self.validator = validator
        self.field_name = field_name
        self.field_validator = field_validator
        self.run_if_none = run_if_none
        self.add_check_info = add_check_info

        self.message_values['field_name'] = field_name

    def _internal_is_valid(self, value, *args, **kwargs):
        field_value = get_field_value_from_context(self.field_name, kwargs.get('context', []))

        if (self.run_if_none or field_value is not None) and \
                (self.field_validator is None or self.field_validator.is_valid(field_value, *args, **kwargs)) and \
                not self.validator.is_valid(value, *args, **kwargs):
            self.messages.update(self.validator.messages)
            if self.add_check_info:
                self.error(self.NEEDS_VALIDATE, value, field_value=field_value)
            return False

        return True


class BaseSpec(ComplexValidator):

    """
    Base class to use spec
    """

    def __init__(self, spec=None, stop_on_fail=True, *args, **kwargs):
        super(BaseSpec, self).__init__(*args, **kwargs)

        if spec is not None:
            self.spec = spec.copy()

        try:
            self.spec
        except AttributeError:
            self.spec = OrderedDict()

        self.stop_on_fail = stop_on_fail

    def _internal_is_valid(self, value, *args, **kwargs):
        result = True
        for field_name, validator in self.spec.items():
            field_value = self.get_field_value(field_name, value, kwargs)

            if not validator.is_valid(field_value, *args, **kwargs):
                self.import_messages(field_name, validator.messages)
                result = False
                if self.stop_on_fail:
                    return False

        return result


class DictValidate(BaseSpec):

    INVALID_TYPE = 'notDict'

    error_messages = {
        INVALID_TYPE: "'$value' is not a dictionary",
    }

    def get_field_value(self, field_name, value, kwargs):
        return value.get(field_name, None)

    def _internal_is_valid(self, value, *args, **kwargs):
        if not isinstance(value, dict):
            self.error(self.INVALID_TYPE, value)
            return False
        return super(DictValidate, self)._internal_is_valid(value, *args, **kwargs)


class Required(Chain):

    REQUIRED = 'required'

    error_messages = {
        REQUIRED: "Value is required and can not be empty",
    }

    def __init__(self, empty_validator=None, *args, **kwargs):
        self.empty_validator = empty_validator or NotNone()
        super(Required, self).__init__(*args, **kwargs)

    def _internal_is_valid(self, value, *args, **kwargs):
        if not self.empty_validator.is_valid(value):
            self.error(self.REQUIRED, value)
            return False

        return super(Required, self)._internal_is_valid(value, *args, **kwargs)


class Optional(Chain):

    def __init__(self, empty_validator=None, *args, **kwargs):
        self.empty_validator = empty_validator or NotNone()
        super(Optional, self).__init__(*args, **kwargs)

    def _internal_is_valid(self, value, *args, **kwargs):
        if not self.empty_validator.is_valid(value):
            return True

        return Chain._internal_is_valid(self, value, *args, **kwargs)


class ModelValidateMetaclass(type):

    @classmethod
    def __prepare__(metacls, name, bases):  # No keywords in this case
        return OrderedDict()

    def __new__(cls, name, bases, classdict):

        result = super(ModelValidateMetaclass, cls).__new__(
            cls, name, bases, classdict)

        spec = OrderedDict([(field, validator) for field, validator in classdict.items()
                            if hasattr(validator, 'is_valid')])

        setattr(result, 'spec', spec)
        return result


class ModelValidate(BaseSpec, metaclass=ModelValidateMetaclass):

    __modelclass__ = BaseModel

    INVALID_MODEL = 'notModel'

    error_messages = {
        INVALID_MODEL: "'$value' is not an instance of $model",
    }

    def __init__(self, spec=None, *args, **kwargs):
        self.spec = self.spec.copy()
        if spec is not None:
            self.spec.update(spec)

        super(ModelValidate, self).__init__(*args, **kwargs)

    def get_field_value(self, field_name, value, kwargs):
        kwargs['is_modified'] = value.is_modified_field(field_name)

        try:
            return getattr(value, field_name)
        except AttributeError:
            return None

    def _internal_is_valid(self, value, *args, **kwargs):
        if not isinstance(value, self.__modelclass__):
            self.error(self.INVALID_MODEL, value, model=self.__modelclass__.__name__)
            return False

        return super(ModelValidate, self)._internal_is_valid(value, *args, **kwargs)
