"""
Validators library

Complex validators
"""
from abc import abstractmethod
from collections import OrderedDict
from typing import Any, Callable, Iterable

from .basic import BaseValidator, NotNone, ValidatorMetaclass
from .ctx import Context

try:
    from dirty_models.model_types import ListModel

    ListLike = (list, tuple, set, ListModel)
except ImportError:  # pragma: no cover
    ListLike = (list, tuple, set)


class DeferredMixin:
    def __init__(self,
                 validator: Callable[['Context'], 'BaseValidator'] = None,
                 *args, **kwargs):
        assert validator is not None, 'Validator builder function is required'

        super(DeferredMixin, self).__init__(*args, **kwargs)

        self.validator = validator

    def build_validator(self, ctx: 'Context') -> BaseValidator:
        return self.validator(ctx)


class Deferred(DeferredMixin, BaseValidator):
    """
    Use a deferred validator to build a validator on runtime.
    """

    def _internal_is_valid(self, value, *args, ctx: 'Context', **kwargs) -> 'Context':
        child_ctx = self.build_validator(ctx).is_valid(value, *args, parent_ctx=ctx, **kwargs)
        ctx.import_errors(child_ctx)
        return ctx


class ChainMixin:
    def __init__(self, validators=None, stop_on_fail=True, *args, **kwargs):
        super(ChainMixin, self).__init__(*args, **kwargs)

        self.stop_on_fail = stop_on_fail
        self.validators = validators.copy() if validators is not None else []


class Chain(ChainMixin, BaseValidator):
    """
    Use a chain of validators for one value
    """

    def _internal_is_valid(self, value, *args, ctx: 'Context', **kwargs) -> 'Context':
        for validator in self.validators:
            child_ctx = validator.is_valid(value, *args, parent_ctx=ctx, **kwargs)
            ctx.import_errors(child_ctx)
            if not child_ctx and self.stop_on_fail:
                break
        return ctx


class SomeMixin(metaclass=ValidatorMetaclass):
    def __init__(self, validators=None, *args, **kwargs):
        super(SomeMixin, self).__init__(*args, **kwargs)

        self.validators = validators.copy() if validators is not None else []


class Some(SomeMixin, BaseValidator):
    """
    Pass some validators for one value
    """

    def _internal_is_valid(self, value, *args, ctx: 'Context', **kwargs) -> 'Context':
        child_ctxs = []
        for validator in self.validators:
            child_ctx = validator.is_valid(value, *args, parent_ctx=ctx, **kwargs)
            if child_ctx:
                return ctx
            child_ctxs.append(child_ctx)

        [ctx.import_errors(c) for c in child_ctxs]
        return ctx


class ComplexValidatorMixin(metaclass=ValidatorMetaclass):
    def _build_context(self: BaseValidator, value, *args, parent_ctx: 'Context' = None, **kwargs):
        return Context(value=value,
                       parent=parent_ctx,
                       hidden_value=self.hidden_value,
                       hide_value=self.hide_value,
                       is_step=True,
                       **self.message_values)


class ComplexValidator(ComplexValidatorMixin, BaseValidator):
    """
    Base for validator which inject step context
    """
    pass


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

    def _internal_is_valid(self, value, *args, ctx: 'Context', **kwargs) -> 'Context':
        for idx, val in self._iter_values(value):
            child_ctx = self.validator.is_valid(val, *args, parent_ctx=ctx, **kwargs)
            if not child_ctx:
                ctx.import_errors(child_ctx, field_path=str(idx))
                if self.stop_on_fail:
                    break

        return ctx


class SomeItemsMixin(metaclass=ValidatorMetaclass):
    TOO_MANY_VALID_ITEMS = 'tooManyValidItems'
    TOO_FEW_VALID_ITEMS = 'tooFewValidItems'

    error_messages = {
        TOO_MANY_VALID_ITEMS: "Too many items pass validation",
        TOO_FEW_VALID_ITEMS: "Too few items pass validation"
    }

    def __init__(self, min=1, max=-1, *args, **kwargs):
        assert min != -1 or max != -1, 'At least one of `min` or `max` must be specified.'
        assert max == -1 or min <= max, '`min` cannot be more than `max`.'

        super(SomeItemsMixin, self).__init__(*args, **kwargs)
        self.min = min
        self.max = max

        self.message_values.update({"min": self.min, "max": self.max})


class SomeItems(SomeItemsMixin, ListValidator):
    """
    Validate some items on list
    """

    def _internal_is_valid(self, value, *args, ctx: 'Context', **kwargs) -> 'Context':
        tmp_ctx = Context(parent=ctx)
        item_pass = 0
        already_too_many = False
        for idx, val in self._iter_values(value):
            child_ctx = self.validator.is_valid(val, *args, parent_ctx=tmp_ctx, **kwargs)
            if not child_ctx:
                tmp_ctx.import_errors(child_ctx, field_path=str(idx))
            else:
                item_pass += 1

            if not already_too_many and self.max != -1 and item_pass > self.max:
                self.error(self.TOO_MANY_VALID_ITEMS, value, ctx=ctx)
                already_too_many = True

                if self.stop_on_fail:
                    break

        if self.min != -1 and item_pass < self.min:
            self.error(self.TOO_FEW_VALID_ITEMS, value, ctx=ctx)

        if not ctx:
            ctx.import_errors(tmp_ctx)

        return ctx


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

    def _get_checking_value(self, value, *, ctx: 'Context'):
        """
        It must be override on descendant validators
        """
        return value

    def _internal_is_valid(self, value, *args, ctx: 'Context', **kwargs) -> 'Context':

        def add_occurrence(val, counter):
            if val not in counter:
                counter[val] = 0

            counter[val] += 1

        counter = {}

        for _, val in self._iter_values(value):
            val = self._get_checking_value(val, ctx=ctx)
            add_occurrence(val, counter)

            if counter[val] > self.max_occ:
                child_ctx = ctx.build_child(value=val)
                self.error(self.TOO_MANY_ITEM_OCCURRENCES, val, ctx=child_ctx)
                ctx.import_errors(child_ctx)
                return ctx

        for val, occ in counter.items():
            if occ < self.min_occ:
                child_ctx = ctx.build_child(value=val)
                self.error(self.TOO_FEW_ITEM_OCCURRENCES, val, ctx=child_ctx)
                ctx.import_errors(child_ctx)
                return ctx

        return ctx


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

    def _internal_is_valid(self, value, *args, ctx: 'Context', **kwargs) -> 'Context':
        field_value = ctx.get_field_value(self.field_name)

        if not self.run_if_none and field_value is None:
            return ctx

        if self.field_validator is not None:
            field_valid_ctx = self.field_validator.is_valid(field_value, *args, parent_ctx=ctx, **kwargs)

            if not field_valid_ctx:
                return ctx

        child_ctx = self.validator.is_valid(value, *args, parent_ctx=ctx, **kwargs)

        if not child_ctx:
            ctx.import_errors(child_ctx)
            if self.add_check_info:
                self.error(self.NEEDS_VALIDATE, value, field_value=field_value, ctx=ctx)

        return ctx


class BaseSpecMixin(metaclass=ValidatorMetaclass):
    INVALID_KEY = 'invalidKey'

    error_messages = {
        INVALID_KEY: "'$value' is not a valid key",
    }

    __key_validator__ = None
    __value_validators__ = None

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
            self.__key_validator__ = key_validator

        if value_validators:
            self.__value_validators__ = value_validators

    @abstractmethod
    def get_field_value(self, field_name, value, ctx: 'Context', kwargs):
        raise NotImplementedError()

    @abstractmethod
    def _get_keys(self, value, ctx: 'Context', **kwargs):
        raise NotImplementedError()


class BaseSpec(BaseSpecMixin, ComplexValidator):
    """
    Base class to use spec
    """

    def _internal_field_validate(self, validator, field_name, field_value, *args, ctx: 'Context', **kwargs):
        child_ctx = validator.is_valid(field_value, *args, parent_ctx=ctx, **kwargs)
        ctx.import_errors(child_ctx, field_name)

        return ctx

    def _internal_validate_keys(self, keys, *args, ctx: 'Context', **kwargs):
        for k in keys:
            if k in self.spec:
                continue

            key_ctx = self.__key_validator__.is_valid(k, *args, parent_ctx=ctx, **kwargs)
            if key_ctx:
                continue
            child_ctx = ctx.build_child(value=k)
            self.error(self.INVALID_KEY, k, ctx=child_ctx)
            ctx.import_errors(child_ctx)
            ctx.import_errors(key_ctx, field_path=k)
            if self.stop_on_fail:
                break
        return ctx

    def _internal_validate_values(self, value, keys, *args, ctx: 'Context', **kwargs):
        temp = {}

        for k in keys:
            if k in self.spec:
                continue

            temp[k] = self.get_field_value(k, value, ctx=ctx, kwargs=kwargs)

        child_ctx = self.__value_validators__.is_valid(temp, *args, parent_ctx=ctx, **kwargs)
        ctx.import_errors(child_ctx)

        return ctx

    def _internal_is_valid(self, value, *args, ctx: 'Context', **kwargs) -> 'Context':
        if self.__key_validator__ and not self._internal_validate_keys(self._get_keys(value, ctx=ctx),
                                                                       *args,
                                                                       ctx=ctx,
                                                                       **kwargs):
            if self.stop_on_fail:
                return ctx

        for field_name, validator in self.spec.items():
            field_value = self.get_field_value(field_name, value, ctx=ctx, kwargs=kwargs)

            if not self._internal_field_validate(validator, field_name, field_value, *args, ctx=ctx, **kwargs):
                if self.stop_on_fail:
                    return ctx

        if self.__value_validators__:
            if not self._internal_validate_values(value, self._get_keys(value, ctx=ctx), *args, ctx=ctx, **kwargs):
                if self.stop_on_fail:
                    return ctx

        return ctx


class DictValidateMixin(metaclass=ValidatorMetaclass):
    INVALID_TYPE = 'notDict'

    error_messages = {
        INVALID_TYPE: "'$value' is not a dictionary",
    }

    def get_field_value(self, field_name, value, ctx: 'Context', kwargs) -> Any:
        return value.get(field_name, None)

    def _get_keys(self, value, ctx: 'Context', **kwargs) -> Iterable[Any]:
        return value.keys()


class DictValidate(DictValidateMixin, BaseSpec):

    def _internal_is_valid(self, value, *args, ctx: 'Context', **kwargs) -> 'Context':
        if not isinstance(value, dict):
            self.error(self.INVALID_TYPE, value, ctx=ctx)
            return ctx

        return super(DictValidate, self)._internal_is_valid(value, *args, ctx=ctx, **kwargs)


class RequiredMixin(metaclass=ValidatorMetaclass):
    REQUIRED = 'required'

    error_messages = {
        REQUIRED: "Value is required and can not be empty",
    }

    def __init__(self, empty_validator=None, *args, **kwargs):
        self.empty_validator = empty_validator or NotNone()
        super(RequiredMixin, self).__init__(*args, **kwargs)


class Required(RequiredMixin, Chain):
    def _internal_is_valid(self, value, *args, ctx: 'Context', **kwargs) -> 'Context':
        if not self.empty_validator.is_valid(value, parent_ctx=ctx):
            self.error(self.REQUIRED, value, ctx=ctx)
            return ctx

        return Chain._internal_is_valid(self, value, *args, ctx=ctx, **kwargs)


class OptionalMixin(metaclass=ValidatorMetaclass):

    def __init__(self, empty_validator=None, *args, **kwargs):
        self.empty_validator = empty_validator or NotNone()
        super(OptionalMixin, self).__init__(*args, **kwargs)


class Optional(OptionalMixin, Chain):

    def _internal_is_valid(self, value, *args, ctx: 'Context', **kwargs) -> 'Context':
        if not self.empty_validator.is_valid(value, parent_ctx=ctx):
            return ctx

        return Chain._internal_is_valid(self, value, *args, ctx=ctx, **kwargs)


try:
    from dirty_models.models import BaseDynamicModel, BaseModel, HashMapModel
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

            spec = getattr(result, 'spec', OrderedDict()).copy()

            new_spec = OrderedDict([(field, validator) for field, validator in classdict.items()
                                    if hasattr(validator, 'is_valid') and not field.startswith('_')])

            spec.update(new_spec)

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
                if issubclass(self.__modelclass__, (HashMapModel, BaseDynamicModel)):
                    return self.__modelclass__().get_field_obj(fieldname).name
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

        def get_field_value(self, field_name, value, ctx: 'Context', kwargs):
            kwargs['is_modified'] = value.is_modified_field(field_name)

            try:
                return getattr(value, field_name)
            except AttributeError:
                return None

        def _get_keys(self, value, ctx: 'Context', **kwargs):
            return value.get_fields()

    class ModelValidate(ModelValidateMixin, BaseSpec):

        def _internal_is_valid(self, value, *args, ctx: 'Context', **kwargs) -> 'Context':
            if not isinstance(value, self.__modelclass__):
                self.error(self.INVALID_MODEL, value, model=self.__modelclass__.__name__, ctx=ctx)
                return ctx

            return super(ModelValidate, self)._internal_is_valid(value, *args, ctx=ctx, **kwargs)
