from unittest import TestCase

from dirty_validators.basic import Length, Regexp
from dirty_validators.complex import AllItems, Chain, DictValidate, Required
from dirty_validators.legacy import from_context_to_legacy_message


class TestFromContextToLegacyMessages(TestCase):
    def test_specific_model_key_fail_2(self):
        class Validator(DictValidate):
            __key_validator__ = Regexp(regex='^field')
            __value_validators__ = AllItems(validator=Chain(validators=[Regexp(regex='^value'),
                                                                        Length(min=10)],
                                                            stop_on_fail=False))

            hard_field = Required()

        validator = Validator(stop_on_fail=False)

        data = {
            'field_1': 'v',
            'my_field_2': 'v'
        }

        result = validator.is_valid(data)
        self.assertEqual(
            from_context_to_legacy_message(result),
            {
                'field_1': {'notMatch': "'v' does not match against pattern '^value'",
                            'tooShort': "'v' is less than 10 unit length"},
                'invalidKey': "'my_field_2' is not a valid key",
                'my_field_2': {'notMatch': "'my_field_2' does not match against pattern '^field'"}
            }
        )
