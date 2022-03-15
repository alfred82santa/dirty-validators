from unittest import TestCase

from dirty_models import ArrayField, BaseModel, ModelField, StringField

from dirty_validators.ctx import Context

from .tests_complex import FakeModelInner


class FakeListModel(BaseModel):
    fieldName1 = StringField()
    fieldList1 = ArrayField(field_type=ModelField(model_class=FakeModelInner))


class TestContext(TestCase):

    def test_get_first_context_field(self):
        ctx = Context(value={"fieldname1": "bbb"}, is_step=True, parent=Context(value={"fieldname1": "asa"}))
        self.assertEqual(ctx.get_field_value('fieldname1'), "bbb")

    def test_get_second_context_field(self):
        ctx = Context(value={"fieldname1": "bbb"}, is_step=True, parent=Context(value={"fieldname1": "asa"}))
        self.assertEqual(ctx.get_field_value('<context>.fieldname1'), "asa")

    def test_get_second_context_field_no_step(self):
        ctx = Context(value={"fieldname1": "bbb"}, is_step=False, parent=Context(value={"fieldname1": "asa"}))
        self.assertEqual(ctx.get_field_value('fieldname1'), "asa")

    def test_get_third_context_no_existing_field(self):
        ctx = Context(value={"fieldname1": "bbb"}, is_step=True, parent=Context(value={"fieldname1": "asa"}))
        self.assertIsNone(ctx.get_field_value('<context>.<context>.fieldname1'))

    def test_get_third_context_no_existing_field_no_step(self):
        ctx = Context(value={"fieldname1": "bbb"}, is_step=False, parent=Context(value={"fieldname1": "asa"}))
        self.assertIsNone(ctx.get_field_value('<context>.fieldname1'))

    def test_get_first_context_embeded_field(self):
        ctx = Context(value={"fieldname1": "bbb", "fieldname2": {"fieldname3": "oouch"}},
                      is_step=True,
                      parent=Context(value={"fieldname1": "asa", "fieldname2": {"fieldname3": "fuii"}}))
        self.assertEqual(ctx.get_field_value('fieldname2.fieldname3'), "oouch")

    def test_get_second_context_embeded_field(self):
        ctx = Context(value={"fieldname1": "bbb", "fieldname2": {"fieldname3": "oouch"}},
                      is_step=True,
                      parent=Context(value={"fieldname1": "asa", "fieldname2": {"fieldname3": "fuii"}}))

        self.assertEqual(ctx.get_field_value('<context>.fieldname2.fieldname3'), "fuii")

    def test_get_embeded_field_fail(self):
        ctx = Context(value={"fieldname1": "bbb"}, is_step=False, parent=Context(value={"fieldname1": "asa"}))

        self.assertIsNone(ctx.get_field_value('fieldname2.fieldname3'))

    def test_get_first_context_list_field(self):
        ctx = Context(value={"fieldname1": "bbb", "fieldname2": ["asase11", "fuii11"]},
                      is_step=True,
                      parent=Context(value={"fieldname1": "asa", "fieldname2": ["asase", "fuii"]}))
        self.assertEqual(ctx.get_field_value('fieldname2.1'), "fuii11")

    def test_get_second_context_list_field(self):
        ctx = Context(value={"fieldname1": "bbb", "fieldname2": ["asase11", "fuii11"]},
                      is_step=True,
                      parent=Context(value={"fieldname1": "asa", "fieldname2": ["asase", "fuii"]}))

        self.assertEqual(ctx.get_field_value('<context>.fieldname2.1'), "fuii")

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
        ctx = Context(value=FakeListModel(data_b),
                      is_step=True,
                      parent=Context(value=FakeListModel(data_a)))
        self.assertEqual(ctx.get_field_value('fieldList1.1.fieldName2'), 'value_B_1_2')

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
        ctx = Context(value=FakeListModel(data_b),
                      is_step=True,
                      parent=Context(value=FakeListModel(data_a)))
        self.assertEqual(ctx.get_field_value('<context>.fieldList1.1.fieldName2'), 'value_A_1_2')

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
        ctx = Context(value=FakeListModel(data_b),
                      is_step=True,
                      parent=Context(value=FakeListModel(data_a)))
        self.assertIsNone(ctx.get_field_value('<context>.fieldList1.3.fieldName2'))

    def test_get_list_field_fail(self):
        ctx = Context(value={"fieldname1": "bbb", "fieldname2": ["asase11", "fuii11"]},
                      is_step=True,
                      parent=Context(value={"fieldname1": "asa", "fieldname2": ["asase", "fuii"]}))

        self.assertIsNone(ctx.get_field_value('fieldname2.3'))

    def test_get_immutable_field_fail(self):
        ctx = Context(value={"fieldname1": "bbb", "fieldname2": ["asase11", "fuii11"]},
                      is_step=True,
                      parent=Context(value={"fieldname1": "asa", "fieldname2": ["asase", "fuii"]}))

        self.assertIsNone(ctx.get_field_value('fieldname2.3.qwq'))

    def test_get_first_context_dict_field(self):
        ctx = Context(value={"fieldname1": "bbb", "fieldname2": {1: "asase11", 2: "fuii11"}},
                      is_step=True,
                      parent=Context(value={"fieldname1": "asa", "fieldname2": {1: "asase", 2: "fuii"}}))

        self.assertEqual(ctx.get_field_value('fieldname2.1'), "asase11")

    def test_get_second_context_dict_field(self):
        ctx = Context(value={"fieldname1": "bbb", "fieldname2": {1: "asase11", 2: "fuii11"}},
                      is_step=True,
                      parent=Context(value={"fieldname1": "asa", "fieldname2": {1: "asase", 2: "fuii"}}))

        self.assertEqual(ctx.get_field_value('<context>.fieldname2.1'), "asase")

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
        ctx = Context(value=FakeListModel(data_b),
                      is_step=True,
                      parent=Context(value=FakeListModel(data_a)))
        self.assertEqual(ctx.get_field_value('<root>.fieldList1.1.fieldName2'), 'value_A_1_2')

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
        ctx = Context(value=FakeListModel(data_b),
                      is_step=True,
                      parent=Context(value=FakeListModel(data_a)))
        self.assertIsNone(ctx.get_field_value('<root>.fieldList1.3.fieldName2'))

    def test_multi_steps(self):
        ctx = None
        for i in range(10):
            ctx = Context(value={'fieldName': i}, is_step=True, parent=ctx)
            ctx = Context(value={'fieldName': 'a'}, parent=ctx)

        self.assertEqual(ctx.get_field_value('<root>.fieldName'), 0)
        self.assertEqual(ctx.get_field_value('fieldName'), 9)
        self.assertEqual(ctx.get_field_value('<context>.fieldName'), 8)
        self.assertEqual(ctx.get_field_value('<context>.<context>.fieldName'), 7)

    def test_no_parent_step(self):
        ctx = Context(value=None, is_step=False)
        ctx = Context(value={'fieldName': 'a'}, parent=ctx)

        self.assertIsNone(ctx.get_field_value('fieldName'))

    def test_no_parent_step_single(self):
        ctx = Context(value=None, is_step=False)
        ctx._is_step = False

        self.assertIsNone(ctx.get_field_value('fieldName'))

    def test_no_parent_step_up(self):
        ctx = Context(value=None, is_step=False)
        ctx._is_step = False

        self.assertIsNone(ctx.get_field_value('<context>.fieldName'))
