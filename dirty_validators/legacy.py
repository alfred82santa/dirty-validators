from typing import Dict, List, Optional

from .ctx import Context, ValidationErrorMessage


def from_context_to_legacy_message(ctx: 'Context') -> Dict:
    msgs: Dict[Optional[str], List[ValidationErrorMessage]] = {}

    for msg in ctx:
        msgs.setdefault(msg.field_path, [])
        msgs[msg.field_path].append(msg)

    return {
        **{m.code: m.msg for m in msgs.get(None, [])},
        **{f: {m.code: m.msg for m in ms} for f, ms in msgs.items() if f is not None},
    }
