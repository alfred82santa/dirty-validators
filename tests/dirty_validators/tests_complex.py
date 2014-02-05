from unittest import TestCase
from dirty_validators.complex import Chain, AllItems, SomeItems, get_field_value_from_context, IfField
from dirty_validators.basic import Length, Regexp, Email


class TestChainStopOnFail(TestCase):

    def setUp(self):
        self.validator = Chain(validators=[Length(min=14, max=16), Regexp(regex='^abc'), Email()])

    def tearDown(self):
        pass

    def test_validate_str_success(self):
        self.assertTrue(self.validator.is_valid('abcdefg@test.com'))
        self.assertDictEqual(self.validator.messages, {})

    def test_validate_str_message_first_validator_fail_1(self):
        self.assertFalse(self.validator.is_valid('abcdefghijk@test.com'))
        self.assertDictEqual(self.validator.messages,
                             {Length.TOO_LONG: "'abcdefghijk@test.com' is more than 16 unit length"})

    def test_validate_str_message_first_validator_fail_2(self):
        self.assertFalse(self.validator.is_valid('abc@test.com'))
        self.assertDictEqual(self.validator.messages,
                             {Length.TOO_SHORT: "'abc@test.com' is less than 14 unit length"})

    def test_validate_str_message_second_validator_fail(self):
        self.assertFalse(self.validator.is_valid('abfghi@test.com'))
        self.assertDictEqual(self.validator.messages,
                             {Regexp.NOT_MATCH: "'abfghi@test.com' does not match against pattern '^abc'"})

    def test_validate_str_message_third_validator_fail(self):
        self.assertFalse(self.validator.is_valid('abcdefg+test.com'))
        self.assertDictEqual(self.validator.messages,
                             {Email.NOT_MAIL: "'abcdefg+test.com' is not a valid email address."})


class TestChainDontStopOnFail(TestCase):

    def setUp(self):
        self.validator = Chain(validators=[Length(min=14, max=16), Regexp(regex='^abc'), Email()], stop_on_fail=False)

    def tearDown(self):
        pass

    def test_validate_str_success(self):
        self.assertTrue(self.validator.is_valid('abcdefg@test.com'))
        self.assertDictEqual(self.validator.messages, {})

    def test_validate_str_fail_all(self):
        self.assertFalse(self.validator.is_valid('abadefghijk+test.com'))
        self.assertDictEqual(self.validator.messages,
                             {Length.TOO_LONG: "'abadefghijk+test.com' is more than 16 unit length",
                              Regexp.NOT_MATCH: "'abadefghijk+test.com' does not match against pattern '^abc'",
                              Email.NOT_MAIL: "'abadefghijk+test.com' is not a valid email address."})


class TestAllItemsStopOnFail(TestCase):

    def setUp(self):
        self.validator = AllItems(validator=Length(min=14, max=16))

    def tearDown(self):
        pass

    def test_validate_success(self):
        self.assertTrue(self.validator.is_valid(['abcdefg@test.com', '12345678901234', 'abcdefghijklmno']))
        self.assertDictEqual(self.validator.messages, {})

    def test_validate_first_fail(self):
        self.assertFalse(self.validator.is_valid(['test', '12345678901234', 'abcdefghijklmno']))
        self.assertDictEqual(self.validator.messages,
                             {0: {Length.TOO_SHORT: "'test' is less than 14 unit length"}})

    def test_validate_second_fail(self):
        self.assertFalse(self.validator.is_valid(['abcdefg@test.com', '12345678901234567', 'abcdefghijklmno']))
        self.assertDictEqual(self.validator.messages,
                             {1: {Length.TOO_LONG: "'12345678901234567' is more than 16 unit length"}})

    def test_validate_first_and_last_fail(self):
        self.assertFalse(self.validator.is_valid(['test', '12345678901234', 'abcdefghijklmnsssssssso']))
        self.assertDictEqual(self.validator.messages,
                             {0: {Length.TOO_SHORT: "'test' is less than 14 unit length"}})


class TestAllItemsDontStopOnFail(TestCase):

    def setUp(self):
        self.validator = AllItems(validator=Length(min=14, max=16), stop_on_fail=False)

    def tearDown(self):
        pass

    def test_validate_all_fail(self):
        self.assertFalse(self.validator.is_valid(['test', '12345678901234567', 'abcdefghijklmnsssssssso']))
        self.assertDictEqual(self.validator.messages,
                             {0: {Length.TOO_SHORT: "'test' is less than 14 unit length"},
                              1: {Length.TOO_LONG: "'12345678901234567' is more than 16 unit length"},
                              2: {Length.TOO_LONG: "'abcdefghijklmnsssssssso' is more than 16 unit length"}})


class TestSomeItems(TestCase):

    def setUp(self):
        self.validator = SomeItems(min=2, max=3, validator=Length(min=4, max=6))

    def tearDown(self):
        pass

    def test_validate_success(self):
        self.assertTrue(self.validator.is_valid(['abcde', '12345678901234', 'abcd', 'qawsw']), self.validator.messages)
        self.assertDictEqual(self.validator.messages, {})

    def test_validate_too_few_items_fail(self):
        self.assertFalse(self.validator.is_valid(['tes', '1234', 'abcdefghijklmno']))
        self.assertDictEqual(self.validator.messages,
                             {0: {Length.TOO_SHORT: "'tes' is less than 4 unit length"},
                              2: {Length.TOO_LONG: "'abcdefghijklmno' is more than 6 unit length"},
                              SomeItems.TOO_FEW_VALID_ITEMS: "Too few items pass validation"})

    def test_validate_too_many_items_stop_on_fail(self):
        self.assertFalse(self.validator.is_valid(['test', '12345', 'asaa', 'abcde', 'wewwwwww', 'sd']))
        self.assertDictEqual(self.validator.messages,
                             {SomeItems.TOO_MANY_VALID_ITEMS: "Too many items pass validation"})

    def test_validate_too_many_items_dont_stop_on_fail(self):
        self.validator = SomeItems(min=1, max=2, stop_on_fail=False, validator=Length(min=4, max=6))
        self.assertFalse(self.validator.is_valid(['test', '12345', 'abcde', 'wewwwwww', 'sd', '1qaz', '2wsx']))
        self.assertDictEqual(self.validator.messages,
                             {SomeItems.TOO_MANY_VALID_ITEMS: "Too many items pass validation",
                              4: {Length.TOO_SHORT: "'sd' is less than 4 unit length"},
                              3: {Length.TOO_LONG: "'wewwwwww' is more than 6 unit length"}})


class TestContextField(TestCase):

    def test_get_first_context_root_field(self):
        contexts = [{"fieldname1": "asa"}, {"fieldname1": "bbb"}]
        self.assertEqual(get_field_value_from_context('fieldname1', contexts), "bbb")

    def test_get_second_context_root_field(self):
        contexts = [{"fieldname1": "asa"}, {"fieldname1": "bbb"}]
        self.assertEqual(get_field_value_from_context('<context>.fieldname1', contexts), "asa")

    def test_get_third_context_root_field(self):
        contexts = [{"fieldname1": "asa"}, {"fieldname1": "bbb"}]
        self.assertIsNone(get_field_value_from_context('<context>.<context>.fieldname1', contexts))

    def test_get_first_context_embeded_field(self):
        contexts = [{"fieldname1": "asa", "fieldname2": {"fieldname3": "fuii"}},
                    {"fieldname1": "bbb", "fieldname2": {"fieldname3": "oouch"}}]
        self.assertEqual(get_field_value_from_context('fieldname2.fieldname3', contexts), "oouch")

    def test_get_second_context_embeded_field(self):
        contexts = [{"fieldname1": "asa", "fieldname2": {"fieldname3": "fuii"}},
                    {"fieldname1": "bbb", "fieldname2": {"fieldname3": "oouch"}}]
        self.assertEqual(get_field_value_from_context('<context>.fieldname2.fieldname3', contexts), "fuii")

    def test_get_embeded_field_fail(self):
        contexts = [{"fieldname1": "asa"}, {"fieldname1": "bbb"}]
        self.assertIsNone(get_field_value_from_context('fieldname2.fieldname3', contexts))

    def test_get_first_context_list_field(self):
        contexts = [{"fieldname1": "asa", "fieldname2": ["asase", "fuii"]},
                    {"fieldname1": "bbb", "fieldname2": ["asase11", "fuii11"]}]
        self.assertEqual(get_field_value_from_context('fieldname2.1', contexts), "fuii11")

    def test_get_second_context_list_field(self):
        contexts = [{"fieldname1": "asa", "fieldname2": ["asase", "fuii"]},
                    {"fieldname1": "bbb", "fieldname2": ["asase11", "fuii11"]}]
        self.assertEqual(get_field_value_from_context('<context>.fieldname2.1', contexts), "fuii")

    def test_get_list_field_fail(self):
        contexts = [{"fieldname1": "asa", "fieldname2": ["asase", "fuii"]},
                    {"fieldname1": "bbb", "fieldname2": ["asase11", "fuii11"]}]
        self.assertIsNone(get_field_value_from_context('fieldname2.3', contexts))

    def test_get_immutable_field_fail(self):
        contexts = [{"fieldname1": "asa", "fieldname2": ["asase", "fuii"]},
                    {"fieldname1": "bbb", "fieldname2": ["asase11", "fuii11"]}]
        self.assertIsNone(get_field_value_from_context('fieldname2.3.qwq', contexts))

    def test_get_first_context_dict_field(self):
        contexts = [{"fieldname1": "asa", "fieldname2": {1: "asase", 2: "fuii"}},
                    {"fieldname1": "bbb", "fieldname2": {1: "asase11", 2: "fuii11"}}]
        self.assertEqual(get_field_value_from_context('fieldname2.1', contexts), "asase11")

    def test_get_second_context_dict_field(self):
        contexts = [{"fieldname1": "asa", "fieldname2": {1: "asase", 2: "fuii"}},
                    {"fieldname1": "bbb", "fieldname2": {1: "asase11", 2: "fuii11"}}]
        self.assertEqual(get_field_value_from_context('<context>.fieldname2.1', contexts), "asase")


class TestIfField(TestCase):

    def setUp(self):
        self.validator = IfField(validator=Length(min=4, max=6),
                                 field_name='fieldname1',
                                 field_validator=Length(min=1, max=2))

    def tearDown(self):
        pass

    def test_validate_success(self):
        self.assertTrue(self.validator.is_valid('abcd', context=[{'fieldname1': 'a'}]), self.validator.messages)
        self.assertDictEqual(self.validator.messages, {})

    def test_no_validate_success(self):
        self.assertTrue(self.validator.is_valid('a', context=[{'fieldname1': 'abcd'}]), self.validator.messages)
        self.assertDictEqual(self.validator.messages, {})

    def test_validate_fail(self):
        self.assertFalse(self.validator.is_valid('abcdefg', context=[{'fieldname1': 'a'}]), self.validator.messages)
        self.assertDictEqual(self.validator.messages,
                             {IfField.NEEDS_VALIDATE: "Some validate error due to field 'fieldname1' has value 'a'.",
                              Length.TOO_LONG: "'abcdefg' is more than 6 unit length"})
