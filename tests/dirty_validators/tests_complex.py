from unittest import TestCase

from collections import OrderedDict
from dirty_models.fields import StringField, ModelField, ArrayField
from dirty_models.models import BaseModel, HashMapModel

from dirty_validators.basic import Length, Regexp, Email, NotNone, NotEmpty
from dirty_validators.complex import (Chain, Some, AllItems, SomeItems,
                                      get_field_value_from_context, IfField,
                                      DictValidate, Required, Optional, ModelValidate, ItemLimitedOccurrences)


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


class TestSome(TestCase):
    def setUp(self):
        self.validator = Some(validators=[Regexp(regex='^cba'),
                                          Regexp(regex='^abc', error_code_map={Regexp.NOT_MATCH: 'ouch'}),
                                          Email()])

    def tearDown(self):
        pass

    def test_validate_str_first_success(self):
        self.assertTrue(self.validator.is_valid('cbaaaa'))
        self.assertDictEqual(self.validator.messages, {})

    def test_validate_str_second_success(self):
        self.assertTrue(self.validator.is_valid('abcdefg'))
        self.assertDictEqual(self.validator.messages, {})

    def test_validate_str_third_success(self):
        self.assertTrue(self.validator.is_valid('bcdefg@test.com'))
        self.assertDictEqual(self.validator.messages, {})

    def test_validate_str_fail_all(self):
        self.assertFalse(self.validator.is_valid('abadefghijk+test.com'))
        self.assertDictEqual(self.validator.messages,
                             {Regexp.NOT_MATCH: "'abadefghijk+test.com' does not match against pattern '^cba'",
                              'ouch': "'abadefghijk+test.com' does not match against pattern '^abc'",
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

    def test_validate_embeded_fail(self):
        self.validator = AllItems(validator=AllItems(validator=Length(min=5, max=16)))
        self.assertFalse(self.validator.is_valid([['testaaa', 'assa'], ['auds', 'aass']]))
        self.assertDictEqual(self.validator.messages,
                             {"0.1": {Length.TOO_SHORT: "'assa' is less than 5 unit length"}})


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


class TestItemLimitedOccuerrencesDefault(TestCase):
    def setUp(self):
        self.validator = ItemLimitedOccurrences()

    def test_validate_success(self):
        self.assertTrue(self.validator.is_valid([]), 'Zero elements')
        self.assertTrue(self.validator.is_valid(['aaa']), 'One element')
        self.assertTrue(self.validator.is_valid(['aaa', 'bbb']), 'Two elements')

    def test_validate_fail(self):
        self.assertFalse(self.validator.is_valid(['aaa', 'aaa', 'bbb', 'ccc', 'ccc']))
        self.assertDictEqual(self.validator.messages, {'tooManyItemOccurrences':
                                                       "Item 'aaa' is repeated to many times. Limit is 1."})

    def test_validate_fail_2(self):
        self.assertFalse(self.validator.is_valid(['aaa', 'bbb', 'ccc', 'ccc']))
        self.assertDictEqual(self.validator.messages, {'tooManyItemOccurrences':
                                                       "Item 'ccc' is repeated to many times. Limit is 1."})


class TestItemLimitedOccuerrencesCustomLimits(TestCase):
    def setUp(self):
        self.validator = ItemLimitedOccurrences(min_occ=2, max_occ=3)

    def test_validate_success(self):
        self.assertTrue(self.validator.is_valid([]), 'Zero elements')
        self.assertTrue(self.validator.is_valid(['aaa', 'aaa']), 'One element')
        self.assertTrue(self.validator.is_valid(['aaa', 'aaa', 'bbb', 'bbb', 'bbb']), 'Two elements')

    def test_validate_too_few_fail(self):
        self.assertFalse(self.validator.is_valid(['aaa', 'bbb', 'bbb', 'ccc', 'ccc', 'ccc']))
        self.assertDictEqual(self.validator.messages, {'tooFewItemOccurrences':
                                                       "Item 'aaa' is not enough repeated. Limit is 2."})

    def test_validate_too_many_fail(self):
        self.assertFalse(self.validator.is_valid(['aaa', 'bbb', 'bbb', 'ccc', 'ccc', 'ccc', 'ccc']))
        self.assertDictEqual(self.validator.messages, {'tooManyItemOccurrences':
                                                       "Item 'ccc' is repeated to many times. Limit is 3."})


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

    def test_get_first_context_list_model_field(self):
        data_a = {
            'fieldName1': 'aaa',
            'fieldList1': [
                {
                    'fieldName1': 'value_A_0_1',
                    'fieldName2': 'value_A_0_2',
                    'fieldName3': 'value_A_0_3'
                },
                {
                    'fieldName1': 'value_A_1_1',
                    'fieldName2': 'value_A_1_2',
                    'fieldName3': 'value_A_1_3'
                }
            ]
        }
        data_b = {
            'fieldName1': 'bbb',
            'fieldList1': [
                {
                    'fieldName1': 'value_B_0_1',
                    'fieldName2': 'value_B_0_2',
                    'fieldName3': 'value_B_0_3'
                },
                {
                    'fieldName1': 'value_B_1_1',
                    'fieldName2': 'value_B_1_2',
                    'fieldName3': 'value_B_1_3'
                }
            ]
        }
        contexts = [FakeListModel(data_a), FakeListModel(data_b)]
        self.assertEqual(get_field_value_from_context('fieldList1.1.fieldName2', contexts), 'value_B_1_2')

    def test_get_second_context_list_model_field(self):
        data_a = {
            'fieldName1': 'aaa',
            'fieldList1': [
                {
                    'fieldName1': 'value_A_0_1',
                    'fieldName2': 'value_A_0_2',
                    'fieldName3': 'value_A_0_3'
                },
                {
                    'fieldName1': 'value_A_1_1',
                    'fieldName2': 'value_A_1_2',
                    'fieldName3': 'value_A_1_3'
                }
            ]
        }
        data_b = {
            'fieldName1': 'bbb',
            'fieldList1': [
                {
                    'fieldName1': 'value_B_0_1',
                    'fieldName2': 'value_B_0_2',
                    'fieldName3': 'value_B_0_3'
                },
                {
                    'fieldName1': 'value_B_1_1',
                    'fieldName2': 'value_B_1_2',
                    'fieldName3': 'value_B_1_3'
                }
            ]
        }
        contexts = [FakeListModel(data_a), FakeListModel(data_b)]
        self.assertEqual(get_field_value_from_context('<context>.fieldList1.1.fieldName2', contexts), 'value_A_1_2')

    def test_get_context_list_model_field_fail(self):
        data_a = {
            'fieldName1': 'aaa',
            'fieldList1': [
                {
                    'fieldName1': 'value_A_0_1',
                    'fieldName2': 'value_A_0_2',
                    'fieldName3': 'value_A_0_3'
                },
                {
                    'fieldName1': 'value_A_1_1',
                    'fieldName2': 'value_A_1_2',
                    'fieldName3': 'value_A_1_3'
                }
            ]
        }
        data_b = {
            'fieldName1': 'bbb',
            'fieldList1': [
                {
                    'fieldName1': 'value_B_0_1',
                    'fieldName2': 'value_B_0_2',
                    'fieldName3': 'value_B_0_3'
                },
                {
                    'fieldName1': 'value_B_1_1',
                    'fieldName2': 'value_B_1_2',
                    'fieldName3': 'value_B_1_3'
                }
            ]
        }
        contexts = [FakeListModel(data_a), FakeListModel(data_b)]
        self.assertIsNone(get_field_value_from_context('<context>.fieldList1.3.fieldName2', contexts))

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

    def test_get_root_context_list_model_field(self):
        data_a = {
            'fieldName1': 'aaa',
            'fieldList1': [
                {
                    'fieldName1': 'value_A_0_1',
                    'fieldName2': 'value_A_0_2',
                    'fieldName3': 'value_A_0_3'
                },
                {
                    'fieldName1': 'value_A_1_1',
                    'fieldName2': 'value_A_1_2',
                    'fieldName3': 'value_A_1_3'
                }
            ]
        }
        data_b = {
            'fieldName1': 'bbb',
            'fieldList1': [
                {
                    'fieldName1': 'value_B_0_1',
                    'fieldName2': 'value_B_0_2',
                    'fieldName3': 'value_B_0_3'
                },
                {
                    'fieldName1': 'value_B_1_1',
                    'fieldName2': 'value_B_1_2',
                    'fieldName3': 'value_B_1_3'
                }
            ]
        }
        contexts = [FakeListModel(data_a), FakeListModel(data_b)]
        self.assertEqual(get_field_value_from_context('<root>.fieldList1.1.fieldName2', contexts), 'value_A_1_2')

    def test_get_root_context_list_model_field_fail(self):
        data_a = {
            'fieldName1': 'aaa',
            'fieldList1': [
                {
                    'fieldName1': 'value_A_0_1',
                    'fieldName2': 'value_A_0_2',
                    'fieldName3': 'value_A_0_3'
                },
                {
                    'fieldName1': 'value_A_1_1',
                    'fieldName2': 'value_A_1_2',
                    'fieldName3': 'value_A_1_3'
                }
            ]
        }
        data_b = {
            'fieldName1': 'bbb',
            'fieldList1': [
                {
                    'fieldName1': 'value_B_0_1',
                    'fieldName2': 'value_B_0_2',
                    'fieldName3': 'value_B_0_3'
                },
                {
                    'fieldName1': 'value_B_1_1',
                    'fieldName2': 'value_B_1_2',
                    'fieldName3': 'value_B_1_3'
                }
            ]
        }
        contexts = [FakeListModel(data_a), FakeListModel(data_b)]
        self.assertIsNone(get_field_value_from_context('<root>.fieldList1.3.fieldName2', contexts))


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

    def test_no_context_success(self):
        self.assertTrue(self.validator.is_valid('a', context=[]), self.validator.messages)
        self.assertDictEqual(self.validator.messages, {})

    def test_validate_fail(self):
        self.assertFalse(self.validator.is_valid('abcdefg', context=[{'fieldname1': 'a'}]), self.validator.messages)
        self.assertDictEqual(self.validator.messages,
                             {IfField.NEEDS_VALIDATE: "Some validate error due to field 'fieldname1' has value 'a'.",
                              Length.TOO_LONG: "'abcdefg' is more than 6 unit length"})

    def test_no_field_validator_fail(self):
        self.validator = IfField(validator=Length(min=4, max=6),
                                 field_name='fieldname1')
        self.assertTrue(self.validator.is_valid('abcdefg', context=[]), self.validator.messages)
        self.assertDictEqual(self.validator.messages, {})

    def test_no_context_fail(self):
        self.validator = IfField(validator=Length(min=4, max=6),
                                 field_name='fieldname1',
                                 run_if_none=True)
        self.assertFalse(self.validator.is_valid('abcdefg', context=[]), self.validator.messages)
        self.assertDictEqual(self.validator.messages,
                             {IfField.NEEDS_VALIDATE: "Some validate error due to field 'fieldname1' has value 'None'.",
                              Length.TOO_LONG: "'abcdefg' is more than 6 unit length"})

    def test_no_context_no_check_info_fail(self):
        self.validator = IfField(validator=Length(min=4, max=6),
                                 field_name='fieldname1',
                                 run_if_none=True,
                                 add_check_info=False)
        self.assertFalse(self.validator.is_valid('abcdefg', context=[]), self.validator.messages)
        self.assertDictEqual(self.validator.messages,
                             {Length.TOO_LONG: "'abcdefg' is more than 6 unit length"})


class TestDictValidate(TestCase):
    def setUp(self):
        self.validator = DictValidate(spec={"fieldName1": IfField(field_name="fieldName1",
                                                                  field_validator=NotNone(),
                                                                  run_if_none=True,
                                                                  validator=Length(min=4, max=6)),
                                            "fieldName2": IfField(field_name="fieldName2",
                                                                  field_validator=NotNone(),
                                                                  run_if_none=True,
                                                                  add_check_info=False,
                                                                  validator=Length(min=1, max=2)),
                                            "fieldName3": Chain(validators=[NotNone(),
                                                                            Length(min=7, max=8)])})

    def test_validate_only_required_success(self):
        self.assertTrue(self.validator.is_valid({"fieldName3": "abcedef"}), self.validator.messages)
        self.assertDictEqual(self.validator.messages, {})

    def test_validate_only_required_fail(self):
        self.assertFalse(self.validator.is_valid({}))
        self.assertDictEqual(self.validator.messages, {'fieldName3': {NotNone.NOT_NONE: 'Value must not be None'}})

    def test_validate_first_optional_success(self):
        self.assertTrue(self.validator.is_valid({"fieldName1": "abdef",
                                                 "fieldName3": "abcedef"}),
                        self.validator.messages)
        self.assertDictEqual(self.validator.messages, {})

    def test_validate_first_optional_fail(self):
        self.assertFalse(self.validator.is_valid({"fieldName1": "af",
                                                  "fieldName3": "abcedef"}))
        self.assertDictEqual(self.validator.messages,
                             {'fieldName1': {Length.TOO_SHORT:
                                             "'af' is less than 4 unit length",
                                             IfField.NEEDS_VALIDATE:
                                                 "Some validate error due to field 'fieldName1' has value 'af'."}})

    def test_validate_second_optional_success(self):
        self.assertTrue(self.validator.is_valid({"fieldName2": "ab",
                                                 "fieldName3": "abcedef"}),
                        self.validator.messages)
        self.assertDictEqual(self.validator.messages, {})

    def test_validate_second_optional_fail(self):
        self.assertFalse(self.validator.is_valid({"fieldName2": "afaas",
                                                  "fieldName3": "abcedef"}))
        self.assertDictEqual(self.validator.messages,
                             {'fieldName2': {Length.TOO_LONG: "'afaas' is more than 2 unit length"}})

    def test_validate_no_dict_fail(self):
        self.assertFalse(self.validator.is_valid("asasa"))
        self.assertDictEqual(self.validator.messages,
                             {DictValidate.INVALID_TYPE: "'asasa' is not a dictionary"})

    def test_validate_no_spec(self):
        validator = DictValidate()
        self.assertIsInstance(validator.spec, OrderedDict)

    def test_validate_all_stop_on_fail_fail(self):
        self.validator = DictValidate(spec=OrderedDict([("fieldName1", IfField(field_name="fieldName1",
                                                                               field_validator=NotNone(),
                                                                               run_if_none=True,
                                                                               validator=Length(min=4, max=6))),
                                                        ("fieldName2", IfField(field_name="fieldName2",
                                                                               field_validator=NotNone(),
                                                                               run_if_none=True,
                                                                               add_check_info=False,
                                                                               validator=Length(min=1, max=2))),
                                                        ("fieldName3", Chain(validators=[NotNone(),
                                                                                         Length(min=7, max=8)]))]))
        self.assertFalse(self.validator.is_valid({"fieldName1": "af",
                                                  "fieldName2": "asasasasas",
                                                  "fieldName3": "abcedddddef"}))
        self.assertDictEqual(self.validator.messages,
                             {'fieldName1': {Length.TOO_SHORT:
                                             "'af' is less than 4 unit length",
                                             IfField.NEEDS_VALIDATE:
                                                 "Some validate error due to field 'fieldName1' has value 'af'."}})

    def test_validate_all_dont_stop_on_fail_fail(self):
        self.validator = DictValidate(spec=OrderedDict([("fieldName1", IfField(field_name="fieldName1",
                                                                               field_validator=NotNone(),
                                                                               run_if_none=True,
                                                                               validator=Length(min=4, max=6))),
                                                        ("fieldName2", IfField(field_name="fieldName2",
                                                                               field_validator=NotNone(),
                                                                               run_if_none=True,
                                                                               add_check_info=False,
                                                                               validator=Length(min=1, max=2))),
                                                        ("fieldName3", Chain(validators=[NotNone(),
                                                                                         Length(min=7, max=8)]))]),
                                      stop_on_fail=False)
        self.assertFalse(self.validator.is_valid({"fieldName1": "af",
                                                  "fieldName2": "asasasasas",
                                                  "fieldName3": "abcedddddef"}))
        self.assertDictEqual(self.validator.messages,
                             {'fieldName1': {Length.TOO_SHORT:
                                             "'af' is less than 4 unit length",
                                             IfField.NEEDS_VALIDATE:
                                                 "Some validate error due to field 'fieldName1' has value 'af'."},
                              'fieldName2': {Length.TOO_LONG: "'asasasasas' is more than 2 unit length"},
                              'fieldName3': {Length.TOO_LONG: "'abcedddddef' is more than 8 unit length"}})


class TestDictTreeValidate(TestCase):
    def setUp(self):
        dicttree1 = DictValidate(spec={"fieldName1": IfField(field_name="fieldName1",
                                                             field_validator=NotNone(),
                                                             run_if_none=True,
                                                             validator=Length(min=4, max=6)),
                                       "fieldName2": IfField(field_name="<context>.fieldName2",
                                                             field_validator=NotNone(),
                                                             run_if_none=True,
                                                             add_check_info=False,
                                                             validator=NotNone()),
                                       "fieldName3": Chain(validators=[NotNone(),
                                                                       Length(min=7, max=8)])})

        self.validator = DictValidate(spec={"fieldName1": IfField(field_name="fieldName1",
                                                                  field_validator=NotNone(),
                                                                  run_if_none=True,
                                                                  validator=Length(min=4, max=6)),
                                            "fieldName2": IfField(field_name="fieldName2",
                                                                  field_validator=NotNone(),
                                                                  run_if_none=True,
                                                                  add_check_info=False,
                                                                  validator=Length(min=1, max=2)),
                                            "fieldName3": Chain(validators=[NotNone(),
                                                                            Length(min=7, max=8)]),
                                            "fieldTree1": Chain(validators=[NotEmpty(), dicttree1])},
                                      key_validator=Regexp(regex='^field'))

    def test_validate_only_required_success(self):
        data = {
            "fieldName3": "123456qw",
            "fieldTree1": {
                "fieldName3": "123456qw"
            }
        }
        self.assertTrue(self.validator.is_valid(data), self.validator.messages)
        self.assertDictEqual(self.validator.messages, {})

    def test_validate_dependent_fields_success(self):
        data = {
            "fieldName2": "12",
            "fieldName3": "123456qw",
            "fieldTree1": {
                "fieldName2": "12",
                "fieldName3": "123456qw",
            }
        }
        self.assertTrue(self.validator.is_valid(data), self.validator.messages)
        self.assertDictEqual(self.validator.messages, {})

    def test_validate_dependent_fields_fail(self):
        data = {
            "fieldName2": "12",
            "fieldName3": "123456qw",
            "fieldTree1": {
                "fieldName3": "123456qw",
            }
        }
        self.assertFalse(self.validator.is_valid(data), self.validator.messages)
        self.assertDictEqual(self.validator.messages, {'fieldTree1.fieldName2': {'notNone': 'Value must not be None'}})

    def test_validate_keys_fail(self):
        data = {
            "fieldName2": "12",
            "fakeField": "123456qw",
            "fieldName3": "123456qw",
            "fieldTree1": {
                "fieldName2": "12",
                "fieldName3": "123456qw",
            }
        }
        self.assertFalse(self.validator.is_valid(data), self.validator.messages)
        self.assertDictEqual(self.validator.messages,
                             {'invalidKey': "'fakeField' is not a valid key",
                              'fakeField': {'notMatch': "'fakeField' does not match against pattern '^field'"}},
                             self.validator.messages)


class TestRequiredValidate(TestCase):
    def setUp(self):
        self.validator = Required(validators=[Length(min=7, max=8)])

    def test_success(self):
        data = 'asdfghw'
        self.assertTrue(self.validator.is_valid(data), self.validator.messages)
        self.assertDictEqual(self.validator.messages, {})

    def test_fail(self):
        data = None
        self.assertFalse(self.validator.is_valid(data), self.validator.messages)
        self.assertDictEqual(self.validator.messages, {'required': 'Value is required and can not be empty'})

    def test_chain_fail(self):
        data = ''
        self.assertFalse(self.validator.is_valid(data), self.validator.messages)
        self.assertDictEqual(self.validator.messages, {'tooShort': "'' is less than 7 unit length"})

    def test_empty_fail(self):
        self.validator = Required(empty_validator=NotEmpty(), validators=[Length(min=7, max=8)])
        data = ''
        self.assertFalse(self.validator.is_valid(data), self.validator.messages)
        self.assertDictEqual(self.validator.messages, {'required': 'Value is required and can not be empty'})


class TestOptionalValidate(TestCase):
    def setUp(self):
        self.validator = Optional(validators=[Length(min=7, max=8)])

    def test_success(self):
        data = None
        self.assertTrue(self.validator.is_valid(data), self.validator.messages)
        self.assertDictEqual(self.validator.messages, {})

    def test_chain_success(self):
        data = 'asdfghw'
        self.assertTrue(self.validator.is_valid(data), self.validator.messages)
        self.assertDictEqual(self.validator.messages, {})

    def test_chain_fail(self):
        data = ''
        self.assertFalse(self.validator.is_valid(data), self.validator.messages)
        self.assertDictEqual(self.validator.messages, {'tooShort': "'' is less than 7 unit length"})

    def test_empty_fail(self):
        self.validator = Optional(empty_validator=NotEmpty(), validators=[Length(min=7, max=8)])
        data = ''
        self.assertTrue(self.validator.is_valid(data), self.validator.messages)
        self.assertDictEqual(self.validator.messages, {})


class FakeModelInner(BaseModel):
    fieldName1 = StringField()
    fieldName2 = StringField()
    fieldName3 = StringField()


class FakeModel(BaseModel):
    fieldName1 = StringField()
    fieldName2 = StringField()
    fieldName3 = StringField()
    fieldTree1 = ModelField(model_class=FakeModelInner)


class FakeListModel(BaseModel):
    fieldName1 = StringField()
    fieldList1 = ArrayField(field_type=ModelField(model_class=FakeModelInner))


class FakeModelInnerValidate(ModelValidate):
    __modelclass__ = FakeModelInner

    fieldName1 = Optional(validators=[Length(min=4, max=6)])
    fieldName2 = Required()
    fieldName3 = Required(validators=[Length(min=7, max=8)])


class FakeModelValidate(ModelValidate):
    __modelclass__ = FakeModel

    fieldName1 = Optional(validators=[Length(min=4, max=6)])
    fieldName2 = Optional(validators=[Length(min=1, max=2)])
    fieldName3 = Required(validators=[Length(min=7, max=8)])
    fieldTree1 = Required(validators=[FakeModelInnerValidate()])


class TestModelValidate(TestCase):
    def setUp(self):
        self.validator = FakeModelValidate()

    def test_validate_only_required_success(self):
        data = {
            "fieldName3": "123456qw",
            "fieldTree1": {
                "fieldName3": "123456qw",
                "fieldName2": "343434"
            }
        }
        self.assertTrue(self.validator.is_valid(FakeModel(data)), self.validator.messages)
        self.assertDictEqual(self.validator.messages, {})

    def test_validate_dependent_fields_success(self):
        data = {
            "fieldName2": "12",
            "fieldName3": "123456qw",
            "fieldTree1": {
                "fieldName2": "12",
                "fieldName3": "123456qw",
            }
        }
        self.assertTrue(self.validator.is_valid(FakeModel(data)), self.validator.messages)
        self.assertDictEqual(self.validator.messages, {})

    def test_validate_first_level_fail(self):
        data = {
            "fieldTree1": {
                "fieldName2": "12",
                "fieldName3": "123456qw",
            }
        }
        self.assertFalse(self.validator.is_valid(FakeModel(data)), self.validator.messages)
        self.assertDictEqual(self.validator.messages,
                             {'fieldName3': {'required': 'Value is required and can not be empty'}})

    def test_validate_change_spec_success(self):
        self.validator = FakeModelValidate(spec={'fieldName3': Optional()})

        data = {
            "fieldTree1": {
                "fieldName2": "12",
                "fieldName3": "123456qw",
            }
        }
        self.assertTrue(self.validator.is_valid(FakeModel(data)), self.validator.messages)
        self.assertDictEqual(self.validator.messages, {})

    def test_validate_change_spec_fail(self):
        self.validator = FakeModelValidate(spec={'fieldName3': Optional()})

        data = {
            "fieldTree1": {
                "fieldName3": "123456qw",
            }
        }
        self.assertFalse(self.validator.is_valid(FakeModel(data)), self.validator.messages)
        self.assertDictEqual(self.validator.messages,
                             {'fieldTree1.fieldName2': {'required': 'Value is required and can not be empty'}})

    def test_validate_dependent_fields_fail(self):
        data = {
            "fieldName3": "123456qw",
            "fieldTree1": {
                "fieldName3": "123456qw",
            }
        }
        self.assertFalse(self.validator.is_valid(FakeModel(data)), self.validator.messages)
        self.assertDictEqual(self.validator.messages,
                             {'fieldTree1.fieldName2': {'required': 'Value is required and can not be empty'}})

    def test_validate_wrong_model_fail(self):
        self.assertFalse(self.validator.is_valid(FakeModelInner()), self.validator.messages)
        self.assertDictEqual(self.validator.messages,
                             {'notModel': "'FakeModelInner()' is not an instance of FakeModel"})

    def test_validate_wrong_field_fail(self):
        class FakeModel(BaseModel):
            pass

        class FakeModelValidate(ModelValidate):
            __modelclass__ = FakeModel

            fieldName1 = Optional(validators=[Length(min=4, max=6)])
            fieldName2 = Optional(validators=[Length(min=1, max=2)])
            fieldName3 = Required(validators=[Length(min=7, max=8)])
            fieldTree1 = Required(validators=[FakeModelInnerValidate()])

        validator = FakeModelValidate()
        self.assertFalse(validator.is_valid(FakeModel()), validator.messages)

        self.assertDictEqual(validator.messages,
                             {'fieldName3': {'required': 'Value is required and can not be empty'}})


class TestHashMapModelValidate(TestCase):

    def test_key_validate(self):

        model = HashMapModel(data={'fieldName1': 1,
                                   'fieldName2': 2})

        validator = ModelValidate(key_validator=Regexp(regex='^field'))
        self.assertTrue(validator.is_valid(model), validator.messages)

    def test_key_validate_fail(self):

        model = HashMapModel(data={'fakeName1': 1,
                                   'fieldName2': 2})

        validator = ModelValidate(key_validator=Regexp(regex='^field'))
        self.assertFalse(validator.is_valid(model), validator.messages)
        self.assertDictEqual(validator.messages,
                             {'fakeName1': {'notMatch': "'fakeName1' does not match against pattern '^field'"},
                              'invalidKey': "'fakeName1' is not a valid key"})
