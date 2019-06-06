"""
Validators library

Async complex validators
"""

from .basic import BaseValidator
from .complex import BaseSpecMixin, ChainMixin, ComplexValidatorMixin, DictValidateMixin, \
    IfFieldMixin, ListValidatorMixin, ModelValidateMixin, OptionalMixin, RequiredMixin, SomeItemsMixin, SomeMixin, \
    get_field_value_from_context


async def is_valid_helper(validator, value, *args, **kwargs):
    if isinstance(validator, AsyncBaseValidator):
        return await validator.is_valid(value, *args, **kwargs)
    else:
        return validator.is_valid(value, *args, **kwargs)


class AsyncBaseValidator(BaseValidator):

    async def is_valid(self, value, *args, **kwargs):
        self.messages = {}
        return await self._internal_is_valid(value, *args, **kwargs)

    async def _internal_is_valid(self, value, *args, **kwargs):  # pragma: no cover
        return True


class Chain(ChainMixin, AsyncBaseValidator):
    """
    Use a ChainMixin of validators for one value
    """

    async def _internal_is_valid(self, value, *args, **kwargs):
        result = True
        for validator in self.validators:
            if not (await is_valid_helper(validator, value, *args, **kwargs)):
                self.messages.update(validator.messages)
                result = False
                if self.stop_on_fail:
                    return False
        return result


class Some(SomeMixin, AsyncBaseValidator):
    """
    Pass SomeMixin validators for one value
    """

    async def _internal_is_valid(self, value, *args, **kwargs):
        messages = {}
        for validator in self.validators:
            if (await is_valid_helper(validator, value, *args, **kwargs)):
                return True
            messages.update(validator.messages)

        self.messages.update(messages)
        return False


class ComplexValidator(ComplexValidatorMixin, AsyncBaseValidator):
    """
    Base for validator which inject context
    """

    async def is_valid(self, value, *args, **kwargs):
        context = kwargs.get('context', [])
        context.append(value)
        kwargs['context'] = context

        result = await super(ComplexValidator, self).is_valid(value, *args, **kwargs)

        context.pop()
        return result


class ListValidator(ListValidatorMixin, ComplexValidator):
    """
    Validate items on list
    """
    pass


class AllItems(ListValidator):
    """
    Validate all items on list
    """

    async def _internal_is_valid(self, value, *args, **kwargs):
        result = True
        for idx, val in self._iter_values(value):
            if not (await is_valid_helper(self.validator, val, *args, **kwargs)):
                self.import_messages(idx, self.validator.messages)
                result = False
                if self.stop_on_fail:
                    return False
        return result


class SomeItems(SomeItemsMixin, ListValidator):
    """
    Validate SomeMixin items on list
    """

    async def _internal_is_valid(self, value, *args, **kwargs):
        item_pass = 0
        for idx, val in self._iter_values(value):
            if not (await is_valid_helper(self.validator, val, *args, **kwargs)):
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


class IfField(IfFieldMixin, AsyncBaseValidator):
    """
    Conditional validator. It runs validators if a specific field value pass validations.
    """

    async def _internal_is_valid(self, value, *args, **kwargs):
        field_value = get_field_value_from_context(self.field_name, kwargs.get('context', []))

        if (self.run_if_none or field_value is not None) and \
                (self.field_validator is None or
                 (await is_valid_helper(self.field_validator, field_value, *args, **kwargs))) and \
                not (await is_valid_helper(self.validator, value, *args, **kwargs)):
            self.messages.update(self.validator.messages)
            if self.add_check_info:
                self.error(self.NEEDS_VALIDATE, value, field_value=field_value)
            return False

        return True


class BaseSpec(BaseSpecMixin, ComplexValidator):
    """
    Base class to use spec
    """

    async def _internal_field_validate(self, validator, field_name, field_value, *args, **kwargs):

        if not (await is_valid_helper(validator, field_value, *args, **kwargs)):
            self.import_messages(field_name, validator.messages)
            return False
        return True

    async def _internal_validate_keys(self, keys, *args, **kwargs):
        result = True
        for k in keys:
            if k in self.spec:
                continue

            if (await is_valid_helper(self.key_validator, k, *args, **kwargs)):
                continue

            self.error(self.INVALID_KEY, k)
            self.import_messages(k, self.key_validator.messages)
            result = False
            if self.stop_on_fail:
                return False
        return result

    async def _internal_validate_values(self, value, keys, *args, **kwargs):
        temp = {}

        for k in keys:
            if k in self.spec:
                continue

            temp[k] = self.get_field_value(k, value, kwargs)

        if not (await is_valid_helper(self.value_validators, temp, *args, **kwargs)):
            self.messages.update(self.value_validators.messages)
            return False
        return True

    async def _internal_is_valid(self, value, *args, **kwargs):
        result = True
        if self.key_validator and not await self._internal_validate_keys(self._get_keys(value), *args, **kwargs):
            result = False
            if self.stop_on_fail:
                return False

        for field_name, validator in self.spec.items():
            field_value = self.get_field_value(field_name, value, kwargs)

            if not (await self._internal_field_validate(validator, field_name, field_value, *args, **kwargs)):
                result = False
                if self.stop_on_fail:
                    return False

        if self.value_validators:
            if not (await self._internal_validate_values(value, self._get_keys(value), *args, **kwargs)):
                result = False
                if self.stop_on_fail:
                    return False

        return result


class DictValidate(DictValidateMixin, BaseSpec):

    async def _internal_is_valid(self, value, *args, **kwargs):
        if not isinstance(value, dict):
            self.error(self.INVALID_TYPE, value)
            return False

        return await super(DictValidate, self)._internal_is_valid(value, *args, **kwargs)


class Required(RequiredMixin, Chain):

    async def _internal_is_valid(self, value, *args, **kwargs):
        if not (await is_valid_helper(self.empty_validator, value)):
            self.error(self.REQUIRED, value)
            return False

        return await super(Required, self)._internal_is_valid(value, *args, **kwargs)


class Optional(OptionalMixin, Chain):

    async def _internal_is_valid(self, value, *args, **kwargs):
        if not (await is_valid_helper(self.empty_validator, value)):
            return True

        return await super(Optional, self)._internal_is_valid(value, *args, **kwargs)


class ModelValidate(ModelValidateMixin, BaseSpec):

    async def _internal_is_valid(self, value, *args, **kwargs):
        if not isinstance(value, self.__modelclass__):
            self.error(self.INVALID_MODEL, value, model=self.__modelclass__.__name__)
            return False

        return await super(ModelValidate, self)._internal_is_valid(value, *args, **kwargs)
