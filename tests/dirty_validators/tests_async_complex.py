from collections import OrderedDict

from aiounittest import AsyncTestCase as TestCase
from dirty_models import IntegerField
from dirty_models.fields import ModelField, StringField
from dirty_models.models import BaseModel, FastDynamicModel, HashMapModel

from dirty_validators.async_complex import (AllItems, Chain, Deferred,
                                            DictValidate, IfField,
                                            ModelValidate, Optional, Required,
                                            Some, SomeItems)
from dirty_validators.basic import (Email, Length, NotEmpty, NotNone,
                                    NumberRange, Regexp)
from dirty_validators.ctx import Context


class TestChainStopOnFail(TestCase):
    def setUp(self):
        self.validator = Chain(validators=[Length(min=14, max=16), Regexp(regex='^abc'), Email()])

    async def test_validate_str_success(self):
        self.assertTrue(await self.validator.is_valid('abcdefg@test.com'))

    async def test_validate_str_message_first_validator_fail_1(self):
        result = await self.validator.is_valid('abcdefghijk@test.com')
        self.assertFalse(result)
        self.assertEqual(len(result.error_messages), 1)
        self.assertEqual(result.error_messages[0].code, Length.TOO_LONG)
        self.assertEqual(result.error_messages[0].msg,
                         "'abcdefghijk@test.com' is more than 16 unit length")

    async def test_validate_str_message_first_validator_fail_2(self):
        result = await self.validator.is_valid('abc@test.com')
        self.assertFalse(result)
        self.assertEqual(len(result.error_messages), 1)
        self.assertEqual(result.error_messages[0].code, Length.TOO_SHORT)
        self.assertEqual(result.error_messages[0].msg,
                         "'abc@test.com' is less than 14 unit length")

    async def test_validate_str_message_second_validator_fail(self):
        result = await self.validator.is_valid('abfghi@test.com')
        self.assertFalse(result)
        self.assertEqual(len(result.error_messages), 1)
        self.assertEqual(result.error_messages[0].code, Regexp.NOT_MATCH)
        self.assertEqual(result.error_messages[0].msg,
                         "'abfghi@test.com' does not match against pattern '^abc'")

    async def test_validate_str_message_third_validator_fail(self):
        result = await self.validator.is_valid('abcdefg+test.com')
        self.assertFalse(result)
        self.assertEqual(len(result.error_messages), 1)
        self.assertEqual(result.error_messages[0].code, Email.NOT_MAIL)
        self.assertEqual(result.error_messages[0].msg,
                         "'abcdefg+test.com' is not a valid email address.")


class TestChainDontStopOnFail(TestCase):
    def setUp(self):
        self.validator = Chain(validators=[Length(min=14, max=16), Regexp(regex='^abc'), Email()], stop_on_fail=False)

    def tearDown(self):
        pass

    async def test_validate_str_success(self):
        self.assertTrue(await self.validator.is_valid('abcdefg@test.com'))

    async def test_validate_str_fail_all(self):
        result = await self.validator.is_valid('abadefghijk+test.com')
        self.assertFalse(result)
        self.assertEqual(len(result.error_messages), 3)
        self.assertEqual(result.error_messages[0].code, Length.TOO_LONG)
        self.assertEqual(result.error_messages[0].msg,
                         "'abadefghijk+test.com' is more than 16 unit length")
        self.assertEqual(result.error_messages[1].code, Regexp.NOT_MATCH)
        self.assertEqual(result.error_messages[1].msg,
                         "'abadefghijk+test.com' does not match against pattern '^abc'")
        self.assertEqual(result.error_messages[2].code, Email.NOT_MAIL)
        self.assertEqual(result.error_messages[2].msg,
                         "'abadefghijk+test.com' is not a valid email address.")


class TestSome(TestCase):
    def setUp(self):
        self.validator = Some(validators=[Regexp(regex='^cba'),
                                          Regexp(regex='^abc', error_code_map={Regexp.NOT_MATCH: 'ouch'}),
                                          Email()])

    def tearDown(self):
        pass

    async def test_validate_str_first_success(self):
        self.assertTrue(await self.validator.is_valid('cbaaaa'))

    async def test_validate_str_second_success(self):
        self.assertTrue(await self.validator.is_valid('abcdefg'))

    async def test_validate_str_third_success(self):
        self.assertTrue(await self.validator.is_valid('bcdefg@test.com'))

    async def test_validate_str_fail_all(self):
        result = await self.validator.is_valid('abadefghijk+test.com')
        self.assertFalse(result)
        self.assertEqual(len(result.error_messages), 3)
        self.assertEqual(result.error_messages[0].code, Regexp.NOT_MATCH)
        self.assertEqual(result.error_messages[0].msg,
                         "'abadefghijk+test.com' does not match against pattern '^cba'")
        self.assertEqual(result.error_messages[1].code, 'ouch')
        self.assertEqual(result.error_messages[1].msg,
                         "'abadefghijk+test.com' does not match against pattern '^abc'")
        self.assertEqual(result.error_messages[2].code, Email.NOT_MAIL)
        self.assertEqual(result.error_messages[2].msg,
                         "'abadefghijk+test.com' is not a valid email address.")


class TestAllItemsStopOnFail(TestCase):
    def setUp(self):
        self.validator = AllItems(validator=Length(min=14, max=16))

    def tearDown(self):
        pass

    async def test_validate_success(self):
        self.assertTrue(await self.validator.is_valid(['abcdefg@test.com', '12345678901234', 'abcdefghijklmno']))

    async def test_validate_first_fail(self):
        result = await self.validator.is_valid(['test', '12345678901234', 'abcdefghijklmno'])
        self.assertFalse(result)
        self.assertEqual(len(result.error_messages), 1)
        self.assertEqual(result.error_messages[0].code, Length.TOO_SHORT)
        self.assertEqual(result.error_messages[0].field_path, '0')
        self.assertEqual(result.error_messages[0].msg,
                         "'test' is less than 14 unit length")

    async def test_validate_second_fail(self):
        result = await self.validator.is_valid(['abcdefg@test.com', '12345678901234567', 'abcdefghijklmno'])
        self.assertFalse(result)
        self.assertEqual(len(result.error_messages), 1)
        self.assertEqual(result.error_messages[0].code, Length.TOO_LONG)
        self.assertEqual(result.error_messages[0].field_path, '1')
        self.assertEqual(result.error_messages[0].msg,
                         "'12345678901234567' is more than 16 unit length")

    async def test_validate_first_and_last_fail(self):
        result = await self.validator.is_valid(['test', '12345678901234', 'abcdefghijklmnsssssssso'])
        self.assertFalse(result)
        self.assertEqual(len(result.error_messages), 1)
        self.assertEqual(result.error_messages[0].code, Length.TOO_SHORT)
        self.assertEqual(result.error_messages[0].field_path, '0')
        self.assertEqual(result.error_messages[0].msg,
                         "'test' is less than 14 unit length")

    async def test_validate_embeded_fail(self):
        validator = AllItems(validator=AllItems(validator=Length(min=5, max=16)))
        result = await validator.is_valid([['testaaa', 'assa'], ['auds', 'aass']])
        self.assertFalse(result)
        self.assertEqual(len(result.error_messages), 1)
        self.assertEqual(result.error_messages[0].code, Length.TOO_SHORT)
        self.assertEqual(result.error_messages[0].field_path, '0.1')
        self.assertEqual(result.error_messages[0].msg,
                         "'assa' is less than 5 unit length")


class TestAllItemsForModelsStopOnFail(TestCase):
    def setUp(self):
        self.validator = AllItems(validator=Length(min=14, max=16))

    async def test_validate_success(self):
        self.assertTrue(await self.validator.is_valid(HashMapModel(data={'field1': 'abcdefg@test.com',
                                                                         'field2': '12345678901234',
                                                                         'field3': 'abcdefghijklmno'})))

    async def test_validate_first_fail(self):
        result = await self.validator.is_valid(HashMapModel(data={'field1': 'test',
                                                                  'field2': '12345678901234',
                                                                  'field3': 'abcdefghijklmno'}))
        self.assertFalse(result)
        self.assertEqual(len(result.error_messages), 1)
        self.assertEqual(result.error_messages[0].code, Length.TOO_SHORT)
        self.assertEqual(result.error_messages[0].field_path, 'field1')
        self.assertEqual(result.error_messages[0].msg,
                         "'test' is less than 14 unit length")


class TestAllItemsDontStopOnFail(TestCase):
    def setUp(self):
        self.validator = AllItems(validator=Length(min=14, max=16), stop_on_fail=False)

    async def test_validate_all_fail(self):
        result = await self.validator.is_valid(['test', '12345678901234567', 'abcdefghijklmnsssssssso'])
        self.assertFalse(result)
        self.assertEqual(len(result.error_messages), 3)
        self.assertEqual(result.error_messages[0].code, Length.TOO_SHORT)
        self.assertEqual(result.error_messages[0].field_path, '0')
        self.assertEqual(result.error_messages[0].msg,
                         "'test' is less than 14 unit length")
        self.assertEqual(result.error_messages[1].code, Length.TOO_LONG)
        self.assertEqual(result.error_messages[1].field_path, '1')
        self.assertEqual(result.error_messages[1].msg,
                         "'12345678901234567' is more than 16 unit length")
        self.assertEqual(result.error_messages[2].code, Length.TOO_LONG)
        self.assertEqual(result.error_messages[2].field_path, '2')
        self.assertEqual(result.error_messages[2].msg,
                         "'abcdefghijklmnsssssssso' is more than 16 unit length")


class TestSomeItems(TestCase):
    def setUp(self):
        self.validator = SomeItems(min=2, max=3, validator=Length(min=4, max=6))

    async def test_validate_success(self):
        self.assertTrue(await self.validator.is_valid(['abcde', '12345678901234', 'abcd', 'qawsw']))

    async def test_validate_too_few_items_fail(self):
        result = await self.validator.is_valid(['tes', '1234', 'abcdefghijklmno'])
        self.assertFalse(result)
        self.assertEqual(len(result.error_messages), 3)
        self.assertEqual(result.error_messages[0].code, SomeItems.TOO_FEW_VALID_ITEMS)
        self.assertIsNone(result.error_messages[0].field_path)
        self.assertEqual(result.error_messages[0].msg,
                         "Too few items pass validation")
        self.assertEqual(result.error_messages[1].code, Length.TOO_SHORT)
        self.assertEqual(result.error_messages[1].field_path, '0')
        self.assertEqual(result.error_messages[1].msg,
                         "'tes' is less than 4 unit length")
        self.assertEqual(result.error_messages[2].code, Length.TOO_LONG)
        self.assertEqual(result.error_messages[2].field_path, '2')
        self.assertEqual(result.error_messages[2].msg,
                         "'abcdefghijklmno' is more than 6 unit length")

    async def test_validate_too_many_items_stop_on_fail(self):
        result = await self.validator.is_valid(['test', '12345', 'asaa', 'abcde', 'wewwwwww', 'sd'])
        self.assertFalse(result)
        self.assertEqual(len(result.error_messages), 1)
        self.assertEqual(result.error_messages[0].code, SomeItems.TOO_MANY_VALID_ITEMS)
        self.assertIsNone(result.error_messages[0].field_path)
        self.assertEqual(result.error_messages[0].msg,
                         "Too many items pass validation")

    async def test_validate_too_many_items_dont_stop_on_fail(self):
        validator = SomeItems(min=1, max=2, stop_on_fail=False, validator=Length(min=4, max=6))

        result = await validator.is_valid(['test', '12345', 'asaa', 'abcde', 'wewwwwww', 'sd'])
        self.assertFalse(result)
        self.assertEqual(len(result.error_messages), 3, result)
        self.assertEqual(result.error_messages[0].code, SomeItems.TOO_MANY_VALID_ITEMS)
        self.assertIsNone(result.error_messages[0].field_path)
        self.assertEqual(result.error_messages[0].msg,
                         "Too many items pass validation")
        self.assertEqual(result.error_messages[1].code, Length.TOO_LONG)
        self.assertEqual(result.error_messages[1].field_path, '4')
        self.assertEqual(result.error_messages[1].msg,
                         "'wewwwwww' is more than 6 unit length")
        self.assertEqual(result.error_messages[2].code, Length.TOO_SHORT)
        self.assertEqual(result.error_messages[2].field_path, '5')
        self.assertEqual(result.error_messages[2].msg,
                         "'sd' is less than 4 unit length")


class TestIfField(TestCase):
    def setUp(self):
        self.validator = IfField(validator=Length(min=4, max=6),
                                 field_name='fieldname1',
                                 field_validator=Length(min=1, max=2))

    async def test_validate_success(self):
        result = await self.validator.is_valid('abcd',
                                               parent_ctx=Context(value={'fieldname1': 'a'}))
        self.assertTrue(result,
                        result)

    async def test_no_validate_success(self):
        self.assertTrue(await self.validator.is_valid('a',
                                                      parent_ctx=Context(value={'fieldname1': 'abcd'})))

    async def test_no_context_success(self):
        self.assertTrue(await self.validator.is_valid('a'))

    async def test_validate_fail(self):
        result = await self.validator.is_valid('abcdefg', parent_ctx=Context(value={'fieldname1': 'a'}))
        self.assertFalse(result)
        self.assertEqual(len(result.error_messages), 2)
        self.assertEqual(result.error_messages[0].code, Length.TOO_LONG)
        self.assertIsNone(result.error_messages[0].field_path)
        self.assertEqual(result.error_messages[0].msg,
                         "'abcdefg' is more than 6 unit length")
        self.assertEqual(result.error_messages[1].code, IfField.NEEDS_VALIDATE)
        self.assertIsNone(result.error_messages[1].field_path)
        self.assertEqual(result.error_messages[1].msg,
                         "Some validate error due to field 'fieldname1' has value 'a'.")

    async def test_no_field_validator_fail(self):
        self.validator = IfField(validator=Length(min=4, max=6),
                                 field_name='fieldname1')
        self.assertTrue(await self.validator.is_valid('abcdefg'))

    async def test_no_context_fail(self):
        validator = IfField(validator=Length(min=4, max=6),
                            field_name='fieldname1',
                            run_if_none=True)

        result = await validator.is_valid('abcdefg')
        self.assertFalse(result)
        self.assertEqual(len(result.error_messages), 2)
        self.assertEqual(result.error_messages[0].code, Length.TOO_LONG)
        self.assertIsNone(result.error_messages[0].field_path)
        self.assertEqual(result.error_messages[0].msg,
                         "'abcdefg' is more than 6 unit length")
        self.assertEqual(result.error_messages[1].code, IfField.NEEDS_VALIDATE)
        self.assertIsNone(result.error_messages[1].field_path)
        self.assertEqual(result.error_messages[1].msg,
                         "Some validate error due to field 'fieldname1' has value 'None'.")

    async def test_no_context_no_check_info_fail(self):
        validator = IfField(validator=Length(min=4, max=6),
                            field_name='fieldname1',
                            run_if_none=True,
                            add_check_info=False)
        result = await validator.is_valid('abcdefg')
        self.assertFalse(result)
        self.assertEqual(len(result.error_messages), 1)
        self.assertEqual(result.error_messages[0].code, Length.TOO_LONG)
        self.assertIsNone(result.error_messages[0].field_path)
        self.assertEqual(result.error_messages[0].msg,
                         "'abcdefg' is more than 6 unit length")


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

    async def test_validate_only_required_success(self):
        self.assertTrue(await self.validator.is_valid({"fieldName3": "abcedef"}))

    async def test_validate_only_required_fail(self):
        result = await self.validator.is_valid({})
        self.assertFalse(result)
        self.assertEqual(len(result.error_messages), 1)
        self.assertEqual(result.error_messages[0].code, NotNone.NOT_NONE)
        self.assertEqual(result.error_messages[0].field_path, 'fieldName3')
        self.assertEqual(result.error_messages[0].msg,
                         'Value must not be None')

    async def test_validate_first_optional_success(self):
        self.assertTrue(await self.validator.is_valid({"fieldName1": "abdef",
                                                       "fieldName3": "abcedef"}))

    async def test_validate_first_optional_fail(self):
        result = await self.validator.is_valid({"fieldName1": "af",
                                                "fieldName3": "abcedef"})
        self.assertFalse(result)
        self.assertEqual(len(result.error_messages), 2)
        self.assertEqual(result.error_messages[0].code, Length.TOO_SHORT)
        self.assertEqual(result.error_messages[0].field_path, 'fieldName1')
        self.assertEqual(result.error_messages[0].msg,
                         "'af' is less than 4 unit length")
        self.assertEqual(result.error_messages[1].code, IfField.NEEDS_VALIDATE)
        self.assertEqual(result.error_messages[1].field_path, 'fieldName1')
        self.assertEqual(result.error_messages[1].msg,
                         "Some validate error due to field 'fieldName1' has value 'af'.")

    async def test_validate_second_optional_success(self):
        self.assertTrue(await self.validator.is_valid({"fieldName2": "ab",
                                                       "fieldName3": "abcedef"}))

    async def test_validate_second_optional_fail(self):
        result = await self.validator.is_valid({"fieldName2": "afaas",
                                                "fieldName3": "abcedef"})
        self.assertFalse(result)
        self.assertEqual(len(result.error_messages), 1)
        self.assertEqual(result.error_messages[0].code, Length.TOO_LONG)
        self.assertEqual(result.error_messages[0].field_path, 'fieldName2')
        self.assertEqual(result.error_messages[0].msg,
                         "'afaas' is more than 2 unit length")

    async def test_validate_no_dict_fail(self):
        result = await self.validator.is_valid("asasa")
        self.assertFalse(result)
        self.assertEqual(len(result.error_messages), 1)
        self.assertEqual(result.error_messages[0].code, DictValidate.INVALID_TYPE)
        self.assertIsNone(result.error_messages[0].field_path)
        self.assertEqual(result.error_messages[0].msg,
                         "'asasa' is not a dictionary")

    async def test_validate_no_spec(self):
        validator = DictValidate()
        self.assertIsInstance(validator.spec, OrderedDict)

    async def test_validate_all_stop_on_fail_fail(self):
        validator = DictValidate(spec=OrderedDict([("fieldName1", Length(min=4, max=6)),
                                                   ("fieldName2", IfField(field_name="fieldName2",
                                                                          field_validator=NotNone(),
                                                                          run_if_none=True,
                                                                          add_check_info=False,
                                                                          validator=Length(min=1, max=2))),
                                                   ("fieldName3", Chain(validators=[NotNone(),
                                                                                    Length(min=7, max=8)]))]), )
        result = await validator.is_valid({"fieldName1": "af",
                                           "fieldName2": "asasasasas",
                                           "fieldName3": "abcedddddef"})
        self.assertFalse(result)
        self.assertEqual(len(result.error_messages), 1)
        self.assertEqual(result.error_messages[0].code, Length.TOO_SHORT)
        self.assertEqual(result.error_messages[0].field_path, 'fieldName1')
        self.assertEqual(result.error_messages[0].msg,
                         "'af' is less than 4 unit length")

    async def test_validate_all_dont_stop_on_fail_fail(self):
        validator = DictValidate(spec=OrderedDict([("fieldName1", Length(min=4, max=6)),
                                                   ("fieldName2", IfField(field_name="fieldName1",
                                                                          field_validator=NotNone(),
                                                                          run_if_none=True,
                                                                          add_check_info=False,
                                                                          validator=Length(min=1, max=2))),
                                                   ("fieldName3", Chain(validators=[NotNone(),
                                                                                    Length(min=7, max=8)]))]),
                                 stop_on_fail=False)

        result = await validator.is_valid({"fieldName1": "af",
                                           "fieldName2": "asasasasas",
                                           "fieldName3": "abcedddddef"})
        self.assertFalse(result)
        self.assertEqual(len(result.error_messages), 3, result)
        self.assertEqual(result.error_messages[0].code, Length.TOO_SHORT)
        self.assertEqual(result.error_messages[0].field_path, 'fieldName1')
        self.assertEqual(result.error_messages[0].msg,
                         "'af' is less than 4 unit length")
        self.assertEqual(result.error_messages[1].code, Length.TOO_LONG)
        self.assertEqual(result.error_messages[1].field_path, 'fieldName2')
        self.assertEqual(result.error_messages[1].msg,
                         "'asasasasas' is more than 2 unit length")
        self.assertEqual(result.error_messages[2].code, Length.TOO_LONG)
        self.assertEqual(result.error_messages[2].field_path, 'fieldName3')
        self.assertEqual(result.error_messages[2].msg,
                         "'abcedddddef' is more than 8 unit length")


class TestDictTreeValidate(TestCase):
    def setUp(self):
        dicttree1 = DictValidate(spec={"fieldName1": Optional(validators=[Length(min=4, max=6)]),
                                       "fieldName2": IfField(field_name="<context>.fieldName2",
                                                             field_validator=NotNone(),
                                                             run_if_none=True,
                                                             add_check_info=False,
                                                             validator=NotNone()),
                                       "fieldName3": Chain(validators=[NotNone(),
                                                                       Length(min=7, max=8)])})

        self.validator = DictValidate(spec={"fieldName1": Optional(validators=[Length(min=4, max=6)]),
                                            "fieldName2": IfField(field_name="fieldName1",
                                                                  field_validator=NotNone(),
                                                                  run_if_none=True,
                                                                  add_check_info=False,
                                                                  validator=Length(min=1, max=2)),
                                            "fieldName3": Chain(validators=[NotNone(),
                                                                            Length(min=7, max=8)]),
                                            "fieldTree1": Chain(validators=[NotEmpty(), dicttree1])},
                                      key_validator=Regexp(regex='^field'),
                                      value_validators=SomeItems(validator=NumberRange(min=1)))

    async def test_validate_only_required_success(self):
        data = {
            "fieldName3": "123456qw",
            "fieldTree1": {
                "fieldName3": "123456qw"
            },
            'fieldNumber': 2
        }
        self.assertTrue(await self.validator.is_valid(data))

    async def test_validate_dependent_fields_success(self):
        data = {
            "fieldName1": 'asas',
            "fieldName2": "13",
            "fieldName3": "123456qw",
            "fieldTree1": {
                "fieldName1": 'asas',
                "fieldName2": "12",
                "fieldName3": "123456qw",
            },
            'fieldNumber': 2
        }
        self.assertTrue(await self.validator.is_valid(data))

    async def test_validate_dependent_fields_fail(self):
        data = {
            "fieldName1": 'asas',
            "fieldName2": "1322",
            "fieldName3": "123456qw",
            "fieldTree1": {
                "fieldName3": "123456qw",
            },
            'fieldNumber': 2
        }

        result = await self.validator.is_valid(data)
        self.assertFalse(result)
        self.assertEqual(len(result.error_messages), 1)
        self.assertEqual(result.error_messages[0].code, Length.TOO_LONG, result.error_messages[0])
        self.assertEqual(result.error_messages[0].field_path, 'fieldName2', result.error_messages[0])
        self.assertEqual(result.error_messages[0].msg,
                         "'1322' is more than 2 unit length",
                         result.error_messages[0])

    async def test_validate_keys_fail(self):
        data = {
            "fieldName1": 'asas',
            "fieldName2": "12",
            "fakeField": "123456qw",
            "fieldName3": "123456qw",
            "fieldTree1": {
                "fieldName1": 'asas',
                "fieldName2": "12",
                "fieldName3": "123456qw",
            },
            'fieldNumber': 2
        }

        result = await self.validator.is_valid(data)
        self.assertFalse(result)
        self.assertEqual(len(result.error_messages), 2)
        self.assertEqual(result.error_messages[0].code, DictValidate.INVALID_KEY)
        self.assertIsNone(result.error_messages[0].field_path)
        self.assertEqual(result.error_messages[0].msg,
                         "'fakeField' is not a valid key")
        self.assertEqual(result.error_messages[1].code, Regexp.NOT_MATCH)
        self.assertEqual(result.error_messages[1].field_path, 'fakeField')
        self.assertEqual(result.error_messages[1].msg,
                         "'fakeField' does not match against pattern '^field'")

    async def test_validate_extra_fields_fail(self):
        data = {
            "fieldName1": 'asas',
            "fieldName2": "12",
            "fieldName3": "123456qw",
            "fieldTree1": {
                "fieldName1": 'asas',
                "fieldName2": "12",
                "fieldName3": "123456qw",
            }
        }
        result = await self.validator.is_valid(data)
        self.assertFalse(result)
        self.assertEqual(len(result.error_messages), 1)
        self.assertEqual(result.error_messages[0].code, SomeItems.TOO_FEW_VALID_ITEMS, result)
        self.assertIsNone(result.error_messages[0].field_path)
        self.assertEqual(result.error_messages[0].msg,
                         'Too few items pass validation')


class TestRequiredValidate(TestCase):
    def setUp(self):
        self.validator = Required(validators=[Length(min=7, max=8)])

    async def test_success(self):
        data = 'asdfghw'
        self.assertTrue(await self.validator.is_valid(data))

    async def test_fail(self):
        data = None
        result = await self.validator.is_valid(data)
        self.assertFalse(result)
        self.assertEqual(len(result.error_messages), 1)
        self.assertEqual(result.error_messages[0].code, Required.REQUIRED, result)
        self.assertIsNone(result.error_messages[0].field_path)
        self.assertEqual(result.error_messages[0].msg,
                         'Value is required and can not be empty')

    async def test_chain_fail(self):
        data = ''
        result = await self.validator.is_valid(data)
        self.assertFalse(result)
        self.assertEqual(len(result.error_messages), 1)
        self.assertEqual(result.error_messages[0].code, Length.TOO_SHORT, result)
        self.assertIsNone(result.error_messages[0].field_path)
        self.assertEqual(result.error_messages[0].msg,
                         "'' is less than 7 unit length")

    async def test_empty_fail(self):
        self.validator = Required(empty_validator=NotEmpty(), validators=[Length(min=7, max=8)])
        data = ''
        result = await self.validator.is_valid(data)
        self.assertFalse(result)
        self.assertEqual(len(result.error_messages), 1)
        self.assertEqual(result.error_messages[0].code, Required.REQUIRED, result)
        self.assertIsNone(result.error_messages[0].field_path)
        self.assertEqual(result.error_messages[0].msg,
                         'Value is required and can not be empty')


class TestOptionalValidate(TestCase):
    def setUp(self):
        self.validator = Optional(validators=[Length(min=7, max=8)])

    async def test_success(self):
        data = None
        self.assertTrue(await self.validator.is_valid(data))

    async def test_chain_success(self):
        data = 'asdfghw'
        self.assertTrue(await self.validator.is_valid(data))

    async def test_chain_fail(self):
        data = ''
        result = await self.validator.is_valid(data)
        self.assertFalse(result)
        self.assertEqual(len(result.error_messages), 1)
        self.assertEqual(result.error_messages[0].code, Length.TOO_SHORT, result)
        self.assertIsNone(result.error_messages[0].field_path)
        self.assertEqual(result.error_messages[0].msg,
                         "'' is less than 7 unit length")

    async def test_empty_fail(self):
        self.validator = Optional(empty_validator=NotEmpty(), validators=[Length(min=7, max=8)])
        data = ''
        self.assertTrue(await self.validator.is_valid(data))


class FakeModelInner(BaseModel):
    fieldName1 = StringField()
    fieldName2 = StringField()
    fieldName3 = StringField()


class FakeModel(BaseModel):
    fieldName1 = StringField()
    fieldName2 = StringField()
    fieldName3 = StringField()
    fieldTree1 = ModelField(model_class=FakeModelInner)


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

    async def test_validate_only_required_success(self):
        data = {
            "fieldName3": "123456qw",
            "fieldTree1": {
                "fieldName3": "123456qw",
                "fieldName2": "343434"
            }
        }
        self.assertTrue(await self.validator.is_valid(FakeModel(data)))

    async def test_validate_dependent_fields_success(self):
        data = {
            "fieldName2": "12",
            "fieldName3": "123456qw",
            "fieldTree1": {
                "fieldName2": "12",
                "fieldName3": "123456qw",
            }
        }
        self.assertTrue(await self.validator.is_valid(FakeModel(data)))

    async def test_validate_first_level_fail(self):
        data = {
            "fieldTree1": {
                "fieldName2": "12",
                "fieldName3": "123456qw",
            }
        }

        result = await self.validator.is_valid(FakeModel(data))
        self.assertFalse(result)
        self.assertEqual(len(result.error_messages), 1)
        self.assertEqual(result.error_messages[0].code, Required.REQUIRED, result)
        self.assertEqual(result.error_messages[0].field_path, 'fieldName3')
        self.assertEqual(result.error_messages[0].msg,
                         'Value is required and can not be empty')

    async def test_validate_change_spec_success(self):
        self.validator = FakeModelValidate(spec={'fieldName3': Optional()})

        data = {
            "fieldTree1": {
                "fieldName2": "12",
                "fieldName3": "123456qw",
            }
        }
        self.assertTrue(await self.validator.is_valid(FakeModel(data)))

    async def test_validate_change_spec_fail(self):
        validator = FakeModelValidate(spec={'fieldName3': Optional()})

        data = {
            "fieldTree1": {
                "fieldName3": "123456qw",
            }
        }

        result = await validator.is_valid(FakeModel(data))
        self.assertFalse(result)
        self.assertEqual(len(result.error_messages), 1)
        self.assertEqual(result.error_messages[0].code, Required.REQUIRED, result)
        self.assertEqual(result.error_messages[0].field_path, 'fieldTree1.fieldName2')
        self.assertEqual(result.error_messages[0].msg,
                         'Value is required and can not be empty')

    async def test_validate_dependent_fields_fail(self):
        data = {
            "fieldName3": "123456qw",
            "fieldTree1": {
                "fieldName3": "123456qw",
            }
        }

        result = await self.validator.is_valid(FakeModel(data))
        self.assertFalse(result)
        self.assertEqual(len(result.error_messages), 1)
        self.assertEqual(result.error_messages[0].code, Required.REQUIRED, result)
        self.assertEqual(result.error_messages[0].field_path, 'fieldTree1.fieldName2')
        self.assertEqual(result.error_messages[0].msg,
                         'Value is required and can not be empty')

    async def test_validate_wrong_model_fail(self):
        result = await self.validator.is_valid(FakeModelInner())
        self.assertFalse(result)
        self.assertEqual(len(result.error_messages), 1)
        self.assertEqual(result.error_messages[0].code, FakeModelValidate.INVALID_MODEL, result)
        self.assertIsNone(result.error_messages[0].field_path)
        self.assertEqual(result.error_messages[0].msg,
                         "'FakeModelInner()' is not an instance of FakeModel")

    async def test_validate_wrong_field_fail(self):
        class FakeModel(BaseModel):
            pass

        class FakeModelValidate(ModelValidate):
            __modelclass__ = FakeModel

            fieldName1 = Optional(validators=[Length(min=4, max=6)])
            fieldName2 = Optional(validators=[Length(min=1, max=2)])
            fieldName3 = Required(validators=[Length(min=7, max=8)])
            fieldTree1 = Required(validators=[FakeModelInnerValidate()])

        validator = FakeModelValidate()

        result = await validator.is_valid(FakeModel())
        self.assertFalse(result)
        self.assertEqual(len(result.error_messages), 1)
        self.assertEqual(result.error_messages[0].code, Required.REQUIRED, result)
        self.assertEqual(result.error_messages[0].field_path, 'fieldName3')
        self.assertEqual(result.error_messages[0].msg,
                         'Value is required and can not be empty')


class TestHashMapModelValidate(TestCase):

    async def test_key_validate(self):
        model = HashMapModel(data={'fieldName1': 1,
                                   'fieldName2': 2})

        validator = ModelValidate(key_validator=Regexp(regex='^field'))
        self.assertTrue(await validator.is_valid(model))

    async def test_key_validate_ignore_def(self):
        model = HashMapModel(data={'fakeName1': 1,
                                   'fieldName2': 2})

        class Validator(ModelValidate):
            fakeName1 = Required()

        validator = Validator(key_validator=Regexp(regex='^field'))
        self.assertTrue(await validator.is_valid(model))

    async def test_key_validate_fail(self):
        model = HashMapModel(data={'fakeName1': 1,
                                   'fieldName2': 2})

        validator = ModelValidate(key_validator=Regexp(regex='^field'))
        result = await validator.is_valid(model)
        self.assertFalse(result)
        self.assertEqual(len(result.error_messages), 2)
        self.assertEqual(result.error_messages[0].code, ModelValidate.INVALID_KEY, result)
        self.assertIsNone(result.error_messages[0].field_path)
        self.assertEqual(result.error_messages[0].msg,
                         "'fakeName1' is not a valid key")
        self.assertEqual(result.error_messages[1].code, Regexp.NOT_MATCH, result)
        self.assertEqual(result.error_messages[1].field_path, 'fakeName1')
        self.assertEqual(result.error_messages[1].msg,
                         "'fakeName1' does not match against pattern '^field'")

    async def test_values_validate(self):
        model = HashMapModel(data={'fieldName1': 1,
                                   'fieldName2': 2})

        validator = ModelValidate(value_validators=AllItems(validator=NumberRange(max=2)))
        self.assertTrue(await validator.is_valid(model))

    async def test_value_validate_ignore_def(self):
        model = HashMapModel(data={'fakeName1': 12,
                                   'fieldName2': 2})

        class Validator(ModelValidate):
            fakeName1 = Required()

        validator = Validator(value_validators=AllItems(validator=NumberRange(max=2)))
        self.assertTrue(await validator.is_valid(model))

    async def test_values_validate_fail(self):
        model = HashMapModel(data={'fakeName1': 1,
                                   'fieldName2': 3})

        validator = ModelValidate(value_validators=AllItems(validator=NumberRange(max=2)))
        result = await validator.is_valid(model)
        self.assertFalse(result)
        self.assertEqual(len(result.error_messages), 1)
        self.assertEqual(result.error_messages[0].code, NumberRange.OUT_OF_RANGE, result)
        self.assertEqual(result.error_messages[0].field_path, 'fieldName2')
        self.assertEqual(result.error_messages[0].msg,
                         "'3' is out of range (None, 2)")

    async def test_hard_field_fail(self):
        model = HashMapModel(data={'fieldName2': 2})

        class Validator(ModelValidate):
            fakeName1 = Required()

        validator = Validator(key_validator=Regexp(regex='^field'))
        result = await validator.is_valid(model)
        self.assertFalse(result)
        self.assertEqual(len(result.error_messages), 1)
        self.assertEqual(result.error_messages[0].code, Required.REQUIRED, result)
        self.assertEqual(result.error_messages[0].field_path, 'fakeName1')
        self.assertEqual(result.error_messages[0].msg,
                         'Value is required and can not be empty')

    async def test_specific_model_ok(self):
        class Model(HashMapModel):
            hard_field = IntegerField(name='hardField')

        model = Model(data={'fieldName2': 2, 'hard_field': 1})

        class Validator(ModelValidate):
            __modelclass__ = Model

            hard_field = Required()

        validator = Validator(key_validator=Regexp(regex='^field'))
        self.assertTrue(await validator.is_valid(model))

    async def test_specific_model_hard_field_fail(self):
        class Model(HashMapModel):
            hard_field = IntegerField(name='hardField')

        model = Model(data={'fieldName2': 2})

        class Validator(ModelValidate):
            __modelclass__ = Model

            hard_field = Required()

        validator = Validator(key_validator=Regexp(regex='^field'))

        result = await validator.is_valid(model)
        self.assertFalse(result)
        self.assertEqual(len(result.error_messages), 1)
        self.assertEqual(result.error_messages[0].code, Required.REQUIRED, result)
        self.assertEqual(result.error_messages[0].field_path, 'hardField')
        self.assertEqual(result.error_messages[0].msg,
                         'Value is required and can not be empty')

    async def test_specific_model_key_fail(self):
        class Model(HashMapModel):
            hard_field = IntegerField(name='hardField')

        model = Model(data={'fakeName': 2})

        class Validator(ModelValidate):
            __modelclass__ = Model

            hard_field = Required()

        validator = Validator(key_validator=Regexp(regex='^field'))

        result = await validator.is_valid(model)
        self.assertFalse(result)
        self.assertEqual(len(result.error_messages), 2)
        self.assertEqual(result.error_messages[0].code, ModelValidate.INVALID_KEY, result)
        self.assertIsNone(result.error_messages[0].field_path)
        self.assertEqual(result.error_messages[0].msg,
                         "'fakeName' is not a valid key")
        self.assertEqual(result.error_messages[1].code, Regexp.NOT_MATCH, result)
        self.assertEqual(result.error_messages[1].field_path, 'fakeName')
        self.assertEqual(result.error_messages[1].msg,
                         "'fakeName' does not match against pattern '^field'")

    async def test_specific_model_key_fail_2(self):
        class Model(HashMapModel):
            hard_field = IntegerField(name='hardField')

        model = Model(data={'fakeName': 2})

        class Validator(ModelValidate):
            __modelclass__ = Model
            __key_validator__ = Regexp(regex='^field')

            hard_field = Required()

        validator = Validator(stop_on_fail=False)

        result = await validator.is_valid(model)
        self.assertFalse(result)
        self.assertEqual(len(result.error_messages), 3, result)
        self.assertEqual(result.error_messages[0].code, ModelValidate.INVALID_KEY, result)
        self.assertIsNone(result.error_messages[0].field_path)
        self.assertEqual(result.error_messages[0].msg,
                         "'fakeName' is not a valid key")
        self.assertEqual(result.error_messages[1].code, Regexp.NOT_MATCH, result)
        self.assertEqual(result.error_messages[1].field_path, 'fakeName')
        self.assertEqual(result.error_messages[1].msg,
                         "'fakeName' does not match against pattern '^field'")
        self.assertEqual(result.error_messages[2].code, Required.REQUIRED, result)
        self.assertEqual(result.error_messages[2].field_path, 'hardField')
        self.assertEqual(result.error_messages[2].msg,
                         'Value is required and can not be empty')


class TestFastDynamicModelValidate(TestCase):

    async def test_key_validate(self):
        model = FastDynamicModel(data={'fieldName1': 1,
                                       'fieldName2': 2})

        validator = ModelValidate(key_validator=Regexp(regex='^field'))
        self.assertTrue(await validator.is_valid(model))

    async def test_key_validate_ignore_def(self):
        model = FastDynamicModel(data={'fakeName1': 1,
                                       'fieldName2': 2})

        class Validator(ModelValidate):
            fakeName1 = Required()

        validator = Validator(key_validator=Regexp(regex='^field'))
        self.assertTrue(await validator.is_valid(model))

    async def test_key_validate_fail(self):
        model = FastDynamicModel(data={'fakeName1': 1,
                                       'fieldName2': 2})

        validator = ModelValidate(key_validator=Regexp(regex='^field'))

        result = await validator.is_valid(model)
        self.assertFalse(result)
        self.assertEqual(len(result.error_messages), 2)
        self.assertEqual(result.error_messages[0].code, ModelValidate.INVALID_KEY, result)
        self.assertIsNone(result.error_messages[0].field_path)
        self.assertEqual(result.error_messages[0].msg,
                         "'fakeName1' is not a valid key")
        self.assertEqual(result.error_messages[1].code, Regexp.NOT_MATCH, result)
        self.assertEqual(result.error_messages[1].field_path, 'fakeName1')
        self.assertEqual(result.error_messages[1].msg,
                         "'fakeName1' does not match against pattern '^field'")

    async def test_values_validate(self):
        model = FastDynamicModel(data={'fieldName1': 1,
                                       'fieldName2': 2})

        validator = ModelValidate(value_validators=AllItems(validator=NumberRange(max=2)))
        self.assertTrue(await validator.is_valid(model))

    async def test_value_validate_ignore_def(self):
        model = FastDynamicModel(data={'fakeName1': 12,
                                       'fieldName2': 2})

        class Validator(ModelValidate):
            fakeName1 = Required()

        validator = Validator(value_validators=AllItems(validator=NumberRange(max=2)))
        self.assertTrue(await validator.is_valid(model))

    async def test_values_validate_fail(self):
        model = FastDynamicModel(data={'fakeName1': 1,
                                       'fieldName2': 3})

        validator = ModelValidate(value_validators=AllItems(validator=NumberRange(max=2)))

        result = await validator.is_valid(model)
        self.assertFalse(result)
        self.assertEqual(len(result.error_messages), 1)
        self.assertEqual(result.error_messages[0].code, NumberRange.OUT_OF_RANGE, result)
        self.assertEqual(result.error_messages[0].field_path, 'fieldName2')
        self.assertEqual(result.error_messages[0].msg,
                         "'3' is out of range (None, 2)")

    async def test_hard_field_fail(self):
        model = FastDynamicModel(data={'fieldName2': 2})

        class Validator(ModelValidate):
            fakeName1 = Required()

        validator = Validator(key_validator=Regexp(regex='^field'))
        result = await validator.is_valid(model)
        self.assertFalse(result)
        self.assertEqual(len(result.error_messages), 1)
        self.assertEqual(result.error_messages[0].code, Required.REQUIRED, result)
        self.assertEqual(result.error_messages[0].field_path, 'fakeName1')
        self.assertEqual(result.error_messages[0].msg,
                         'Value is required and can not be empty')

    async def test_specific_model_ok(self):
        class Model(FastDynamicModel):
            hard_field = IntegerField(name='hardField')

        model = Model(data={'fieldName2': 2, 'hard_field': 1})

        class Validator(ModelValidate):
            __modelclass__ = Model

            hard_field = Required()

        validator = Validator(key_validator=Regexp(regex='^field'))
        self.assertTrue(await validator.is_valid(model))

    async def test_specific_model_hard_field_fail(self):
        class Model(FastDynamicModel):
            hard_field = IntegerField(name='hardField')

        model = Model(data={'fieldName2': 2})

        class Validator(ModelValidate):
            __modelclass__ = Model

            hard_field = Required()

        validator = Validator(key_validator=Regexp(regex='^field'))

        result = await validator.is_valid(model)
        self.assertFalse(result)
        self.assertEqual(len(result.error_messages), 1)
        self.assertEqual(result.error_messages[0].code, Required.REQUIRED, result)
        self.assertEqual(result.error_messages[0].field_path, 'hardField')
        self.assertEqual(result.error_messages[0].msg,
                         'Value is required and can not be empty')

    async def test_specific_model_key_fail(self):
        class Model(FastDynamicModel):
            hard_field = IntegerField(name='hardField')

        model = Model(data={'fakeName': 2})

        class Validator(ModelValidate):
            __modelclass__ = Model

            hard_field = Required()

        validator = Validator(key_validator=Regexp(regex='^field'))

        result = await validator.is_valid(model)
        self.assertFalse(result)
        self.assertEqual(len(result.error_messages), 2)
        self.assertEqual(result.error_messages[0].code, ModelValidate.INVALID_KEY, result)
        self.assertIsNone(result.error_messages[0].field_path)
        self.assertEqual(result.error_messages[0].msg,
                         "'fakeName' is not a valid key")
        self.assertEqual(result.error_messages[1].code, Regexp.NOT_MATCH, result)
        self.assertEqual(result.error_messages[1].field_path, 'fakeName')
        self.assertEqual(result.error_messages[1].msg,
                         "'fakeName' does not match against pattern '^field'")

    async def test_model_validator_inheritance_ok(self):
        class Model(BaseModel):
            hard_field = IntegerField()
            soft_field = IntegerField()

        model = Model(data={'hard_field': 2, 'soft_field': 2})

        class BaseValidator(ModelValidate):
            __modelclass__ = Model

            soft_field = Required()

        class Validator(BaseValidator):
            hard_field = Required()

        validator = Validator()
        self.assertTrue(await validator.is_valid(model))

    async def test_model_validator_inheritance_fail(self):
        class Model(BaseModel):
            hard_field = IntegerField()
            soft_field = IntegerField()

        model = Model(data={'hard_field': 2})

        class BaseValidator(ModelValidate):
            __modelclass__ = Model

            soft_field = Required()

        class Validator(BaseValidator):
            hard_field = Required()

        validator = Validator()

        result = await validator.is_valid(model)
        self.assertFalse(result)
        self.assertEqual(len(result.error_messages), 1)
        self.assertEqual(result.error_messages[0].code, Required.REQUIRED, result)
        self.assertEqual(result.error_messages[0].field_path, 'soft_field')
        self.assertEqual(result.error_messages[0].msg,
                         'Value is required and can not be empty')


class TestsDeferred(TestCase):

    def setUp(self) -> None:
        class Model(BaseModel):
            int_field = IntegerField()
            model_field = ModelField()

        self.Model = Model

        class Validator(ModelValidate):
            __modelclass__ = Model

            int_field = Required(validators=[NumberRange(min=1, max=4)])
            model_field = Optional(validators=[Deferred(validator=lambda ctx: Validator())])

        self.validator = Validator()

    async def test_deferred_success(self):
        data = {
            'int_field': 1,
            'model_field': {
                'int_field': 2,
                'model_field': {
                    'int_field': 3,
                    'model_field': {
                        'int_field': 4,
                    }
                }
            }
        }

        self.assertTrue(await self.validator.is_valid(self.Model(data=data)))

    async def test_deferred_fail(self):
        data = {
            'int_field': 1,
            'model_field': {
                'int_field': 2,
                'model_field': {
                    'int_field': 3,
                    'model_field': {
                        'int_field': 5,
                    }
                }
            }
        }

        result = await self.validator.is_valid(self.Model(data=data))
        self.assertEqual(len(result.error_messages), 1)
        self.assertEqual(result.error_messages[0].code, NumberRange.OUT_OF_RANGE, result)
        self.assertEqual(result.error_messages[0].field_path, 'model_field.model_field.model_field.int_field')
        self.assertEqual(result.error_messages[0].msg,
                         "'5' is out of range (1, 4)")
