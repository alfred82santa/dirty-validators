"""
Validators library

Async complex validators
"""
from typing import Any

from .basic import BaseValidator
from .complex import (BaseSpecMixin, ChainMixin, ComplexValidatorMixin,
                      DeferredMixin, DictValidateMixin, IfFieldMixin,
                      ListValidatorMixin, OptionalMixin, RequiredMixin,
                      SomeItemsMixin, SomeMixin)
from .ctx import Context


async def is_valid_helper(validator, value, *args, parent_ctx: 'Context', **kwargs):
    if isinstance(validator, AsyncBaseValidator):
        return await validator.is_valid(value, *args, parent_ctx=parent_ctx, **kwargs)
    else:
        return validator.is_valid(value, *args, parent_ctx=parent_ctx, **kwargs)


class AsyncBaseValidator(BaseValidator):

    async def is_valid(self, value, *args, parent_ctx: 'Context' = None, **kwargs) -> 'Context':
        ctx = self._build_context(value, *args, parent_ctx=parent_ctx, **kwargs)

        await self._internal_is_valid(value, *args, ctx=ctx, **kwargs)

        return ctx

    async def _internal_is_valid(self, value, *args, ctx: 'Context', **kwargs) -> 'Context':  # pragma: no cover
        return ctx


class Deferred(DeferredMixin, AsyncBaseValidator):
    """
    Use a deferred validator to build it on run time.
    """

    async def _internal_is_valid(self, value, *args, ctx: 'Context', **kwargs) -> 'Context':
        child_ctx = await is_valid_helper(self.build_validator(ctx), value, *args, parent_ctx=ctx, **kwargs)
        ctx.import_errors(child_ctx)
        return ctx


class Chain(ChainMixin, AsyncBaseValidator):
    """
    Use a ChainMixin of validators for one value
    """

    async def _internal_is_valid(self, value, *args, ctx: 'Context', **kwargs) -> 'Context':
        for validator in self.validators:
            child_ctx = await is_valid_helper(validator, value, *args, parent_ctx=ctx, **kwargs)
            ctx.import_errors(child_ctx)
            if not child_ctx and self.stop_on_fail:
                break
        return ctx


class Some(SomeMixin, AsyncBaseValidator):
    """
    Pass SomeMixin validators for one value
    """

    async def _internal_is_valid(self, value, *args, ctx: 'Context', **kwargs) -> 'Context':
        child_ctxs = []
        for validator in self.validators:
            child_ctx = await is_valid_helper(validator, value, *args, parent_ctx=ctx, **kwargs)
            if child_ctx:
                return ctx
            child_ctxs.append(child_ctx)

        [ctx.import_errors(c) for c in child_ctxs]
        return ctx


class ComplexValidator(ComplexValidatorMixin, AsyncBaseValidator):
    """
    Base for validator which inject context
    """
    pass


class ListValidator(ListValidatorMixin, ComplexValidator):
    """
    Validate items on list
    """
    pass


class AllItems(ListValidator):
    """
    Validate all items on list
    """

    async def _internal_is_valid(self, value, *args, ctx: 'Context', **kwargs) -> 'Context':
        for idx, val in self._iter_values(value):
            child_ctx = await is_valid_helper(self.validator, val, *args, parent_ctx=ctx, **kwargs)
            if not child_ctx:
                ctx.import_errors(child_ctx, field_path=str(idx))
                if self.stop_on_fail:
                    break

        return ctx


class SomeItems(SomeItemsMixin, ListValidator):
    """
    Validate SomeMixin items on list
    """

    async def _internal_is_valid(self, value, *args, ctx: 'Context', **kwargs) -> 'Context':
        tmp_ctx = Context(parent=ctx)
        item_pass = 0
        already_too_many = False
        for idx, val in self._iter_values(value):
            child_ctx = await is_valid_helper(self.validator, val, *args, parent_ctx=tmp_ctx, **kwargs)
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


class IfField(IfFieldMixin, AsyncBaseValidator):
    """
    Conditional validator. It runs validators if a specific field value pass validations.
    """

    async def _internal_is_valid(self, value, *args, ctx: 'Context', **kwargs) -> 'Context':
        field_value = ctx.get_field_value(self.field_name)

        if not self.run_if_none and field_value is None:
            return ctx

        if self.field_validator is not None:
            field_valid_ctx = await is_valid_helper(self.field_validator, field_value, *args, parent_ctx=ctx, **kwargs)

            if not field_valid_ctx:
                return ctx

        child_ctx = await is_valid_helper(self.validator, value, *args, parent_ctx=ctx, **kwargs)

        if not child_ctx:
            ctx.import_errors(child_ctx)
            if self.add_check_info:
                self.error(self.NEEDS_VALIDATE, value, field_value=field_value, ctx=ctx)

        return ctx


class BaseSpec(BaseSpecMixin, ComplexValidator):
    """
    Base class to use spec
    """

    async def _internal_field_validate(self,
                                       validator: BaseValidator,
                                       field_name: str,
                                       field_value: Any,
                                       *args,
                                       ctx: 'Context',
                                       **kwargs) -> 'Context':
        child_ctx = await is_valid_helper(validator, field_value, *args, parent_ctx=ctx, **kwargs)
        ctx.import_errors(child_ctx, field_name)

        return ctx

    async def _internal_validate_keys(self,
                                      keys,
                                      *args,
                                      ctx: 'Context',
                                      **kwargs) -> 'Context':
        for k in keys:
            if k in self.spec:
                continue

            key_ctx = await is_valid_helper(self.__key_validator__, k, *args, parent_ctx=ctx, **kwargs)
            if key_ctx:
                continue
            child_ctx = ctx.build_child(value=k)
            self.error(self.INVALID_KEY, k, ctx=child_ctx)
            ctx.import_errors(child_ctx)
            ctx.import_errors(key_ctx, field_path=k)
            if self.stop_on_fail:
                break
        return ctx

    async def _internal_validate_values(self, value, keys, *args, ctx: 'Context', **kwargs) -> 'Context':
        temp = {}

        for k in keys:
            if k in self.spec:
                continue

            temp[k] = self.get_field_value(k, value, ctx=ctx, kwargs=kwargs)

        child_ctx = await is_valid_helper(self.__value_validators__, temp, *args, parent_ctx=ctx, **kwargs)
        ctx.import_errors(child_ctx)

        return ctx

    async def _internal_is_valid(self, value, *args, ctx: 'Context', **kwargs) -> 'Context':
        if self.__key_validator__ and not await self._internal_validate_keys(self._get_keys(value, ctx=ctx),
                                                                             *args,
                                                                             ctx=ctx,
                                                                             **kwargs):
            if self.stop_on_fail:
                return ctx

        for field_name, validator in self.spec.items():
            field_value = self.get_field_value(field_name, value, ctx=ctx, kwargs=kwargs)

            if not await self._internal_field_validate(validator,
                                                       field_name,
                                                       field_value,
                                                       *args,
                                                       ctx=ctx,
                                                       **kwargs):
                if self.stop_on_fail:
                    return ctx

        if self.__value_validators__:
            if not await self._internal_validate_values(value,
                                                        self._get_keys(value, ctx=ctx),
                                                        *args,
                                                        ctx=ctx,
                                                        **kwargs):
                if self.stop_on_fail:
                    return ctx

        return ctx


class DictValidate(DictValidateMixin, BaseSpec):

    async def _internal_is_valid(self, value, *args, ctx: 'Context', **kwargs) -> 'Context':
        if not isinstance(value, dict):
            self.error(self.INVALID_TYPE, value, ctx=ctx)
            return ctx

        return await super(DictValidate, self)._internal_is_valid(value, *args, ctx=ctx, **kwargs)


class Required(RequiredMixin, Chain):

    async def _internal_is_valid(self, value, *args, ctx: 'Context', **kwargs) -> 'Context':
        if not await is_valid_helper(self.empty_validator, value, parent_ctx=ctx):
            self.error(self.REQUIRED, value, ctx=ctx)
            return ctx

        return await Chain._internal_is_valid(self, value, *args, ctx=ctx, **kwargs)


class Optional(OptionalMixin, Chain):

    async def _internal_is_valid(self, value, *args, ctx: 'Context', **kwargs) -> 'Context':
        if not await is_valid_helper(self.empty_validator, value, parent_ctx=ctx):
            return ctx

        return await Chain._internal_is_valid(self, value, *args, ctx=ctx, **kwargs)


try:
    from .complex import ModelValidateMixin
except ImportError:  # pragma: no cover
    pass
else:
    class ModelValidate(ModelValidateMixin, BaseSpec):

        async def _internal_is_valid(self, value, *args, ctx: 'Context', **kwargs) -> 'Context':
            if not isinstance(value, self.__modelclass__):
                self.error(self.INVALID_MODEL, value, model=self.__modelclass__.__name__, ctx=ctx)
                return ctx

            return await super(ModelValidate, self)._internal_is_valid(value, *args, ctx=ctx, **kwargs)
