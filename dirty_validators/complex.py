"""
Validators library

Complex validators
"""
from collections import OrderedDict

from .basic import BaseValidator, NotNone, ValidatorMetaclass

try:
    from dirty_models.model_types import ListModel

    ListLike = (list, tuple, set, ListModel)
except ImportError:  # pragma: no cover
    ListLike = (list, tuple, set)


class ChainMixin:
    def __init__(self, validators=None, stop_on_fail=True, *args, **kwargs):
        super(ChainMixin, self).__init__(*args, **kwargs)

        self.stop_on_fail = stop_on_fail
        self.validators = validators.copy() if validators is not None else []


class Chain(ChainMixin, BaseValidator):
    """
    Use a chain of validators for one value
    """

    def _internal_is_valid(self, value, *args, **kwargs):
        result = True
        for validator in self.validators:
            if not validator.is_valid(value, *args, **kwargs):
                self.messages.update(validator.messages)
                result = False
                if self.stop_on_fail:
                    return False
        return result


class SomeMixin(metaclass=ValidatorMetaclass):
    def __init__(self, validators=None, *args, **kwargs):
        super(SomeMixin, self).__init__(*args, **kwargs)

        self.validators = validators.copy() if validators is not None else []


class Some(SomeMixin, BaseValidator):
    """
    Pass some validators for one value
    """

    def _internal_is_valid(self, value, *args, **kwargs):
        messages = {}
        for validator in self.validators:
            if validator.is_valid(value, *args, **kwargs):
                return True
            messages.update(validator.messages)

        self.messages.update(messages)
        return False


class ComplexValidatorMixin(metaclass=ValidatorMetaclass):
    def import_messages(self, prefix, messages):
        base_messages = {}
        for key, message in messages.items():
            if isinstance(message, dict):
                self.messages[str(prefix) + "." + str(key)] = message
            else:
                base_messages[key] = message

        if len(base_messages):
            self.messages[prefix] = base_messages


class ComplexValidator(ComplexValidatorMixin, BaseValidator):
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


class BaseValueIterableMixin:

    def _iter_values(self, value):
        if isinstance(value, ListLike):
            return enumerate(value)
        elif isinstance(value, dict):
            return value.items()
        else:
            return value


class ListValidatorMixin(BaseValueIterableMixin, metaclass=ValidatorMetaclass):

    def __init__(self, validator, stop_on_fail=True, *args, **kwargs):
        super(ListValidatorMixin, self).__init__(*args, **kwargs)

        self.validator = validator
        self.stop_on_fail = stop_on_fail


class ListValidator(ListValidatorMixin, ComplexValidator):
    """
    Validate items on list
    """
    pass


class AllItems(ListValidator):
    """
    Validate all items on list
    """

    def _internal_is_valid(self, value, *args, **kwargs):
        result = True

        for idx, val in self._iter_values(value):

            if not self.validator.is_valid(val, *args, **kwargs):
                self.import_messages(idx, self.validator.messages)
                result = False
                if self.stop_on_fail:
                    return False
        return result


class SomeItemsMixin(metaclass=ValidatorMetaclass):
    TOO_MANY_VALID_ITEMS = 'tooManyValidItems'
    TOO_FEW_VALID_ITEMS = 'tooFewValidItems'

    error_messages = {
        TOO_MANY_VALID_ITEMS: "Too many items pass validation",
        TOO_FEW_VALID_ITEMS: "Too few items pass validation"
    }

    def __init__(self, min=1, max=-1, *args, **kwargs):
        super(SomeItemsMixin, self).__init__(*args, **kwargs)
        assert min != -1 or max != -1, 'At least one of `min` or `max` must be specified.'
        assert max == -1 or min <= max, '`min` cannot be more than `max`.'
        self.min = min
        self.max = max

        self.message_values.update({"min": self.min, "max": self.max})


class SomeItems(SomeItemsMixin, ListValidator):
    """
    Validate some items on list
    """

    def _internal_is_valid(self, value, *args, **kwargs):
        item_pass = 0
        for idx, val in self._iter_values(value):
            if not self.validator.is_valid(val, *args, **kwargs):
                self.import_messages(idx, self.validator.messages)
            else:
                item_pass += 1
                if self.stop_on_fail and self.max != -1 and item_pass > self.max:
                    self.error(self.TOO_MANY_VALID_ITEMS, value)
                    return False

        if self.max != -1 and item_pass > self.max:
            self.error(self.TOO_MANY_VALID_ITEMS, value)
            return False

        if self.min != -1 and item_pass < self.min:
            self.error(self.TOO_FEW_VALID_ITEMS, value)
            return False

        self.messages = {}
        return True


class ItemLimitedOccurrences(BaseValueIterableMixin, BaseValidator):
    """
    Validate whether item in list are distincts
    """

    TOO_MANY_ITEM_OCCURRENCES = 'tooManyItemOccurrences'
    TOO_FEW_ITEM_OCCURRENCES = 'tooFewItemOccurrences'

    error_messages = {
        TOO_MANY_ITEM_OCCURRENCES: "Item '$value' is repeated to many times. Limit is $max_occ.",
        TOO_FEW_ITEM_OCCURRENCES: "Item '$value' is not enough repeated. Limit is $min_occ.",
    }

    def __init__(self, min_occ=0, max_occ=1, *args, **kwargs):
        super(ItemLimitedOccurrences, self).__init__(*args, **kwargs)
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

        for _, val in self._iter_values(value):
            val = self._get_checking_value(val)
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
    On the other hand, '<root>' is used to start lookup from first item on context.
    """
    field_path = field_name.split('.')

    if field_path[0] == '<root>':
        context_index = 0
        field_path.pop(0)
    else:
        context_index = -1
        while field_path[0] == '<context>':
            context_index -= 1
            field_path.pop(0)

    try:
        field_value = context_list[context_index]

        while len(field_path):
            field = field_path.pop(0)
            if isinstance(field_value, (list, tuple, ListModel)):
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
    except (IndexError, AttributeError, KeyError, TypeError):
        return None


class IfFieldMixin(metaclass=ValidatorMetaclass):
    NEEDS_VALIDATE = 'needsValidate'

    error_messages = {
        NEEDS_VALIDATE: "Some validate error due to field '$field_name' has value '$field_value'.",
    }

    def __init__(self, validator, field_name, field_validator=None,
                 run_if_none=False, add_check_info=True, *args, **kwargs):
        super(IfFieldMixin, self).__init__(*args, **kwargs)

        self.validator = validator
        self.field_name = field_name
        self.field_validator = field_validator
        self.run_if_none = run_if_none
        self.add_check_info = add_check_info

        self.message_values['field_name'] = field_name


class IfField(IfFieldMixin, BaseValidator):
    """
    Conditional validator. It runs validators if a specific field value pass validations.
    """

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


class BaseSpecMixin(metaclass=ValidatorMetaclass):
    INVALID_KEY = 'invalidKey'

    error_messages = {
        INVALID_KEY: "'$value' is not a valid key",
    }

    key_validator = None
    value_validators = None

    def __init__(self, spec=None, stop_on_fail=True, key_validator=None, value_validators=None, *args, **kwargs):
        super(BaseSpecMixin, self).__init__(*args, **kwargs)

        if spec is not None:
            self.spec = spec.copy()

        try:
            self.spec
        except AttributeError:
            self.spec = OrderedDict()

        self.stop_on_fail = stop_on_fail

        if key_validator:
            self.key_validator = key_validator

        if value_validators:
            self.value_validators = value_validators


class BaseSpec(BaseSpecMixin, ComplexValidator):
    """
    Base class to use spec
    """

    def _internal_field_validate(self, validator, field_name, field_value, *args, **kwargs):

        if not validator.is_valid(field_value, *args, **kwargs):
            self.import_messages(field_name, validator.messages)
            return False
        return True

    def _internal_validate_keys(self, keys, *args, **kwargs):
        result = True
        for k in keys:
            if k in self.spec:
                continue

            if self.key_validator.is_valid(k, *args, **kwargs):
                continue
            self.error(self.INVALID_KEY, k)
            self.import_messages(k, self.key_validator.messages)
            result = False
            if self.stop_on_fail:
                return False
        return result

    def _internal_validate_values(self, value, keys, *args, **kwargs):
        temp = {}

        for k in keys:
            if k in self.spec:
                continue

            temp[k] = self.get_field_value(k, value, kwargs)

        if not self.value_validators.is_valid(temp, *args, **kwargs):
            self.messages.update(self.value_validators.messages)
            return False
        return True

    def _internal_is_valid(self, value, *args, **kwargs):
        result = True
        if self.key_validator and not self._internal_validate_keys(self._get_keys(value), *args, **kwargs):
            result = False
            if self.stop_on_fail:
                return False

        for field_name, validator in self.spec.items():
            field_value = self.get_field_value(field_name, value, kwargs)

            if not self._internal_field_validate(validator, field_name, field_value, *args, **kwargs):
                result = False
                if self.stop_on_fail:
                    return False

        if self.value_validators:
            if not self._internal_validate_values(value, self._get_keys(value), *args, **kwargs):
                result = False
                if self.stop_on_fail:
                    return False

        return result


class DictValidateMixin(metaclass=ValidatorMetaclass):
    INVALID_TYPE = 'notDict'

    error_messages = {
        INVALID_TYPE: "'$value' is not a dictionary",
    }

    def get_field_value(self, field_name, value, kwargs):
        return value.get(field_name, None)

    def _get_keys(self, value):
        return value.keys()


class DictValidate(DictValidateMixin, BaseSpec):

    def _internal_is_valid(self, value, *args, **kwargs):
        if not isinstance(value, dict):
            self.error(self.INVALID_TYPE, value)
            return False

        return super(DictValidate, self)._internal_is_valid(value, *args, **kwargs)


class RequiredMixin(metaclass=ValidatorMetaclass):
    REQUIRED = 'required'

    error_messages = {
        REQUIRED: "Value is required and can not be empty",
    }

    def __init__(self, empty_validator=None, *args, **kwargs):
        self.empty_validator = empty_validator or NotNone()
        super(RequiredMixin, self).__init__(*args, **kwargs)


class Required(RequiredMixin, Chain):
    def _internal_is_valid(self, value, *args, **kwargs):
        if not self.empty_validator.is_valid(value):
            self.error(self.REQUIRED, value)
            return False

        return super(Required, self)._internal_is_valid(value, *args, **kwargs)


class OptionalMixin(metaclass=ValidatorMetaclass):

    def __init__(self, empty_validator=None, *args, **kwargs):
        self.empty_validator = empty_validator or NotNone()
        super(OptionalMixin, self).__init__(*args, **kwargs)


class Optional(OptionalMixin, Chain):

    def _internal_is_valid(self, value, *args, **kwargs):
        if not self.empty_validator.is_valid(value):
            return True

        return Chain._internal_is_valid(self, value, *args, **kwargs)


try:
    from dirty_models.models import BaseModel
except ImportError:  # pragma: no cover
    pass
else:

    class ModelValidateMetaclass(ValidatorMetaclass):

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

    class ModelValidateMixin(metaclass=ModelValidateMetaclass):
        __modelclass__ = BaseModel

        INVALID_MODEL = 'notModel'

        error_messages = {
            INVALID_MODEL: "'$value' is not an instance of $model",
        }

        def _get_real_fieldname(self, fieldname):
            try:
                return self.__modelclass__.get_field_obj(fieldname).name
            except AttributeError:
                return fieldname

        def __init__(self, spec=None, *args, **kwargs):
            self.spec = self.spec.copy()
            if spec is not None:
                self.spec.update(spec)

            self.spec = OrderedDict((self._get_real_fieldname(fieldname), validator)
                                    for fieldname, validator in self.spec.items())
            super(ModelValidateMixin, self).__init__(*args, **kwargs)

        def get_field_value(self, field_name, value, kwargs):
            kwargs['is_modified'] = value.is_modified_field(field_name)

            try:
                return getattr(value, field_name)
            except AttributeError:
                return None

        def _get_keys(self, value):
            return value.get_fields()

    class ModelValidate(ModelValidateMixin, BaseSpec):

        def _internal_is_valid(self, value, *args, **kwargs):
            if not isinstance(value, self.__modelclass__):
                self.error(self.INVALID_MODEL, value, model=self.__modelclass__.__name__)
                return False

            return super(ModelValidate, self)._internal_is_valid(value, *args, **kwargs)
