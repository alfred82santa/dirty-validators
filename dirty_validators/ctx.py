from collections.abc import Mapping, Sequence
from string import Template
from typing import Any, Dict, Iterator, List, Optional

sequence_classes = (list, tuple, Sequence)
mapping_classes = (dict, Mapping)

try:
    from dirty_models.model_types import ListModel
except BaseException:  # pragma: no cover
    pass
else:
    sequence_classes = (*sequence_classes, ListModel)

try:
    from dirty_models import BaseModel
except BaseException:  # pragma: no cover
    pass
else:
    mapping_classes = (*mapping_classes, BaseModel)


class ValidationErrorMessage:

    def __init__(self, code: str, msg_tpl: str, ctx_values: Dict = None, field_path: str = None):
        self.code = code
        self.msg_tpl = msg_tpl
        self.field_path = field_path
        self.ctx_values = ctx_values or {}

        self._msg: Optional[str] = None

    @property
    def msg(self):
        if not self._msg:
            error_message_tpl = Template(self.msg_tpl)
            self._msg = error_message_tpl.safe_substitute(self.ctx_values)
        return self._msg

    def copy_as_child(self, field_path: str = None) -> 'ValidationErrorMessage':
        if field_path is None:
            field_path = self.field_path
        else:
            if self.field_path is not None:
                field_path = '.'.join([field_path, self.field_path])

        return self.__class__(code=self.code,
                              msg_tpl=self.msg_tpl,
                              ctx_values=self.ctx_values.copy(),
                              field_path=field_path)

    def __str__(self) -> str:  # pragma: no cover
        return self.msg

    def __repr__(self) -> str:  # pragma: no cover
        prefix = f'{self.field_path} -> ' if self.field_path else ''
        return f'{self.__class__.__name__}<{prefix}{self.code}: {self.msg}>'


class Context:

    def __init__(self,
                 value: Any = None,
                 parent: 'Context' = None,
                 is_step: bool = False,
                 hide_value: bool = False,
                 hidden_value: str = '***hidden***',
                 **message_values: Dict[str, Any]):
        self._parent = parent
        self._value = value
        self._is_step = is_step or parent is None
        self._message_values = message_values

        self._hide_value = hide_value
        self._hidden_value = hidden_value

        self._error_messages: List['ValidationErrorMessage'] = []

    @property
    def parent(self) -> Optional['Context']:
        return self._parent

    @property
    def parent_step(self) -> Optional['Context']:
        if self.parent is None:
            return None

        if self.parent.is_step:
            return self.parent
        return self.parent.parent_step

    @property
    def value(self) -> Any:
        return self._value

    @property
    def message_values(self) -> Dict[str, Any]:
        return self._message_values.copy()

    @property
    def error_messages(self) -> List['ValidationErrorMessage']:
        return self._error_messages.copy()

    @property
    def is_step(self) -> bool:
        return self._is_step

    def error(self, error_code: str, error_message_tpl: str, **kwargs):
        placeholders = {}
        placeholders.update(self._message_values)
        placeholders.update(kwargs)
        placeholders.update({"value": self._hidden_value if self._hide_value else self.value})

        self.add_error(ValidationErrorMessage(
            code=error_code,
            msg_tpl=error_message_tpl,
            ctx_values=placeholders
        ))

    def add_error(self, validation_error: 'ValidationErrorMessage'):
        self._error_messages.append(validation_error)

    def import_errors(self, ctx: 'Context', field_path: str = None):
        for ev in ctx:
            self.add_error(ev.copy_as_child(field_path=field_path))

    def get_field_value(self, field_path: str) -> Any:
        return get_field_value_from_context(field_path=field_path, ctx=self)

    def build_child(self,
                    value: Any,
                    *,
                    is_step: bool = False,
                    **message_values: Dict[str, Any]) -> 'Context':
        msg_vals = self.message_values
        msg_vals.update(message_values)

        return Context(value=value,
                       parent=self,
                       is_step=is_step,
                       hide_value=self._hide_value,
                       hidden_value=self._hidden_value,
                       **msg_vals)

    def __bool__(self) -> bool:
        return len(self._error_messages) == 0

    def __iter__(self) -> Iterator['ValidationErrorMessage']:
        return iter(self._error_messages)

    def __repr__(self) -> str:  # pragma: no cover
        if self:
            return f'{self.__class__.__name__}<True>'
        el = '\n'.join([repr(m) for m in self.error_messages])
        return f'{self.__class__.__name__}<False>:\n{el}'


def get_field_value_from_context(field_path, ctx: 'Context') -> Any:
    """
    Helper to get field value from string path.
    String '<context>' is used to go up on context stack. It just
    can be used at the beginning of path: <context>.<context>.field_name_1
    On the other hand, '<root>' is used to start lookup from first item on context.
    """
    if not ctx.is_step:
        if ctx.parent_step is not None:
            return get_field_value_from_context(field_path=field_path,
                                                ctx=ctx.parent_step)
        else:
            return None

    if field_path.startswith('<root>.'):
        if ctx.parent_step is not None:
            return get_field_value_from_context(field_path=field_path,
                                                ctx=ctx.parent_step)
        else:
            _, field_path = field_path.split('.', 1)
    try:
        field_path, next_field_path = field_path.split('.', 1)
    except ValueError:
        next_field_path = ''

    if field_path == '<context>':
        if ctx.parent_step is not None:
            return get_field_value_from_context(field_path=next_field_path,
                                                ctx=ctx.parent_step)
        else:
            return None

    try:
        field_value = ctx.value

        if field_value is None:
            return None

        field_path = [field_path, *(next_field_path.split('.') if len(next_field_path) else [])]

        while len(field_path):
            field = field_path.pop(0)
            if isinstance(field_value, sequence_classes):
                if field.isdigit():
                    field = int(field)
                field_value = field_value[field]
            elif isinstance(field_value, mapping_classes):
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
