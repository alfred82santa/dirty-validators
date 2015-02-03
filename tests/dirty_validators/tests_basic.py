from unittest import TestCase
from dirty_validators.basic import (BaseValidator, EqualTo, NotEqualTo, StringNotContaining, Length, NumberRange,
                                    Regexp, Email, IPAddress, MacAddress, URL, UUID, AnyOf, NoneOf,
                                    IsEmpty, NotEmpty, IsNone, NotNone)
import re


class TestBaseValidator(TestCase):

    def setUp(self):
        self.validator = BaseValidator()

    def tearDown(self):
        pass

    def test_validate_any(self):
        self.assertTrue(self.validator.is_valid(None))
        self.assertDictEqual(self.validator.messages, {})
        self.assertTrue(self.validator.is_valid(3))
        self.assertDictEqual(self.validator.messages, {})
        self.assertTrue(self.validator.is_valid('aaa'))
        self.assertDictEqual(self.validator.messages, {})
        self.assertTrue(self.validator.is_valid({}))
        self.assertDictEqual(self.validator.messages, {})

    def test_error_not_hidden_behaviour(self):
        error_key = 'Test key'
        error_message = "'$value' is the value error to test hidden feature"
        self.validator.error_messages = {error_key: error_message}
        self.validator.error(error_key, 'Not hidden')
        self.assertEqual(self.validator.messages,
                         {error_key: "'Not hidden' is the value error to test hidden feature"})

    def test_error_hidden_behaviour(self):
        hidden_validator = BaseValidator(hidden=True)
        error_key = 'Test key'
        error_message = "'$value' is the value error to test hidden feature"
        hidden_validator.error_messages = {error_key: error_message}
        hidden_validator.error(error_key, 'Will it be hidden?')
        self.assertEqual(hidden_validator.messages,
                         {error_key: "'**Hidden**' is the value error to test hidden feature"})


class TestEqualTo(TestCase):

    def setUp(self):
        self.validator = EqualTo(comp_value="aaa")

    def tearDown(self):
        pass

    def test_validate_str_success(self):
        self.assertTrue(self.validator.is_valid("aaa"))
        self.assertDictEqual(self.validator.messages, {})

    def test_validate_str_fail(self):
        self.assertFalse(self.validator.is_valid("aqaa"))
        self.assertDictEqual(self.validator.messages, {EqualTo.NOT_EQUAL: "'aqaa' is not equal to 'aaa'"})

    def test_validate_int_success(self):
        self.validator = EqualTo(comp_value=3)
        self.assertTrue(self.validator.is_valid(3))
        self.assertDictEqual(self.validator.messages, {})

    def test_validate_int_fail(self):
        self.validator = EqualTo(comp_value=3)
        self.assertFalse(self.validator.is_valid(4))
        self.assertDictEqual(self.validator.messages, {EqualTo.NOT_EQUAL: "'4' is not equal to '3'"})

    def test_validate_int_fail_custom_error_message(self):
        self.validator = EqualTo(comp_value=3, error_messages={EqualTo.NOT_EQUAL: "$value $value aaa $comp_value"})
        self.assertFalse(self.validator.is_valid(4))
        self.assertDictEqual(self.validator.messages, {EqualTo.NOT_EQUAL: "4 4 aaa 3"})

    def test_validate_int_fail_custom_error_code(self):
        self.validator = EqualTo(comp_value=3, error_code_map={EqualTo.NOT_EQUAL: "newError"})
        self.assertFalse(self.validator.is_valid(4))
        self.assertDictEqual(self.validator.messages, {"newError": "'4' is not equal to '3'"})

    def test_validate_int_fail_custom_error_code_and_error_message(self):
        self.validator = EqualTo(comp_value=3,
                                 error_code_map={EqualTo.NOT_EQUAL: "newError"},
                                 error_messages={EqualTo.NOT_EQUAL: "$value $value aaa $comp_value"})
        self.assertFalse(self.validator.is_valid(4))
        self.assertDictEqual(self.validator.messages, {"newError": "4 4 aaa 3"})

    def test_validate_int_fail_custom_error_code_error_message_and_custom_value(self):
        self.validator = EqualTo(comp_value=3,
                                 error_code_map={EqualTo.NOT_EQUAL: "newError"},
                                 error_messages={EqualTo.NOT_EQUAL: "$value $value aaa $comp_value $value1 $value2"},
                                 message_values={"value1": "aaaaaa1", "value2": "eeeeee1"})
        self.assertFalse(self.validator.is_valid(4))
        self.assertDictEqual(self.validator.messages, {"newError": "4 4 aaa 3 aaaaaa1 eeeeee1"})


class TestNotEqualTo(TestCase):

    def setUp(self):
        self.validator = NotEqualTo(comp_value="aaa")

    def tearDown(self):
        pass

    def test_validate_str_success(self):
        self.assertTrue(self.validator.is_valid("aqaa"))
        self.assertDictEqual(self.validator.messages, {})

    def test_validate_str_fail(self):
        self.assertFalse(self.validator.is_valid("aaa"))
        self.assertDictEqual(self.validator.messages, {NotEqualTo.IS_EQUAL: "'aaa' is equal to 'aaa'"})

    def test_validate_int_success(self):
        self.validator = NotEqualTo(comp_value=3)
        self.assertTrue(self.validator.is_valid(4))
        self.assertDictEqual(self.validator.messages, {})

    def test_validate_int_fail(self):
        self.validator = NotEqualTo(comp_value=3)
        self.assertFalse(self.validator.is_valid(3))
        self.assertDictEqual(self.validator.messages, {NotEqualTo.IS_EQUAL: "'3' is equal to '3'"})


class TestStringNotContaining(TestCase):

    def setUp(self):
        self.validator = StringNotContaining(token='Test_TOKEN')

    def test_validate_string_contains(self):
        self.assertFalse(self.validator.is_valid('This string contains Test_TOKEN for sure'))
        self.assertDictEqual(self.validator.messages,
                             {StringNotContaining.NOT_CONTAINS:
                              "'This string contains Test_TOKEN for sure' contains 'Test_TOKEN'"})

    def test_validate_string_not_contains(self):
        self.assertTrue(self.validator.is_valid('This string does not contain TESt_TOKEN for sensitive cases'))

    def test_validate_string_contains_not_sensitive(self):
        self.validator.case_sensitive = False
        self.assertFalse(self.validator.is_valid('This string contains TESt_TOKEN for sensitive cases'))


class TestLength(TestCase):

    def setUp(self):
        self.validator = Length(min=3, max=6)

    def tearDown(self):
        pass

    def test_validate_str_success(self):
        self.assertTrue(self.validator.is_valid("aqaa"))
        self.assertDictEqual(self.validator.messages, {})

    def test_validate_str_fail_short(self):
        self.assertFalse(self.validator.is_valid("aa"))
        self.assertDictEqual(self.validator.messages, {Length.TOO_SHORT: "'aa' is less than 3 unit length"})

    def test_validate_str_fail_long(self):
        self.assertFalse(self.validator.is_valid("aabbnnmm"))
        self.assertDictEqual(self.validator.messages, {Length.TOO_LONG: "'aabbnnmm' is more than 6 unit length"})

    def test_validate_int_fail(self):
        self.assertFalse(self.validator.is_valid(5))
        self.assertDictEqual(self.validator.messages, {Length.INVALID_TYPE: "'5' has no length"})

    def test_validate_list_success(self):
        self.assertTrue(self.validator.is_valid(["1a", "32d", "tr", "wq"]))
        self.assertDictEqual(self.validator.messages, {})

    def test_validate_list_fail_short(self):
        self.assertFalse(self.validator.is_valid(["1a"]))
        self.assertDictEqual(self.validator.messages, {Length.TOO_SHORT: "'['1a']' is less than 3 unit length"})

    def test_validate_list_fail_long(self):
        self.assertFalse(self.validator.is_valid(["1a", "32d", "tr", "wq", "qwqw", "dd", "as", "er"]))
        self.assertDictEqual(self.validator.messages,
                             {Length.TOO_LONG:
                              "'['1a', '32d', 'tr', 'wq', 'qwqw', 'dd', 'as', 'er']' is more than 6 unit length"})


class TestNumberRange(TestCase):

    def setUp(self):
        self.validator = NumberRange(min=3, max=4)

    def tearDown(self):
        pass

    def test_validate_int_success(self):
        self.assertTrue(self.validator.is_valid(4))
        self.assertDictEqual(self.validator.messages, {})

    def test_validate_int_fail(self):
        self.assertFalse(self.validator.is_valid(5))
        self.assertDictEqual(self.validator.messages, {NumberRange.OUT_OF_RANGE: "'5' is out of range (3, 4)"})

    def test_validate_int_no_min_success(self):
        self.validator = NumberRange(max=4)
        self.assertTrue(self.validator.is_valid(1))
        self.assertDictEqual(self.validator.messages, {})

    def test_validate_int_no_min_fail(self):
        self.validator = NumberRange(max=4)
        self.assertFalse(self.validator.is_valid(5))
        self.assertDictEqual(self.validator.messages, {NumberRange.OUT_OF_RANGE: "'5' is out of range (None, 4)"})

    def test_validate_int_no_max_success(self):
        self.validator = NumberRange(min=4)
        self.assertTrue(self.validator.is_valid(5))
        self.assertDictEqual(self.validator.messages, {})

    def test_validate_int_no_max_fail(self):
        self.validator = NumberRange(min=4)
        self.assertFalse(self.validator.is_valid(1))
        self.assertDictEqual(self.validator.messages, {NumberRange.OUT_OF_RANGE: "'1' is out of range (4, None)"})


class TestRegexp(TestCase):

    def setUp(self):
        self.validator = Regexp(regex="^aa.+bb$")

    def tearDown(self):
        pass

    def test_validate_str_success(self):
        self.assertTrue(self.validator.is_valid("aarrbb"))
        self.assertDictEqual(self.validator.messages, {})

    def test_validate_str_fail(self):
        self.assertFalse(self.validator.is_valid("aarrbbcc"))
        self.assertDictEqual(self.validator.messages,
                             {Regexp.NOT_MATCH: "'aarrbbcc' does not match against pattern '^aa.+bb$'"})

    def test_validate_str_case_sensitive_fail(self):
        self.assertFalse(self.validator.is_valid("Aarrbb"))
        self.assertDictEqual(self.validator.messages,
                             {Regexp.NOT_MATCH: "'Aarrbb' does not match against pattern '^aa.+bb$'"})

    def test_validate_str_case_insensitive_success(self):
        self.validator = Regexp(regex="^aa.+bb$", flags=re.IGNORECASE)
        self.assertTrue(self.validator.is_valid("Aarrbb"))
        self.assertDictEqual(self.validator.messages, {})

    def test_validate_int_fail(self):
        self.assertFalse(self.validator.is_valid(6))
        self.assertDictEqual(self.validator.messages,
                             {Regexp.NOT_MATCH: "'6' does not match against pattern '^aa.+bb$'"})


class TestEmail(TestCase):

    def setUp(self):
        self.validator = Email()

    def tearDown(self):
        pass

    def test_validate_str_success(self):
        self.assertTrue(self.validator.is_valid("aarrbb@aaaa.com"))
        self.assertDictEqual(self.validator.messages, {})

    def test_validate_str_fail(self):
        self.assertFalse(self.validator.is_valid("aarrbbaaaa@sas.c"))
        self.assertDictEqual(self.validator.messages,
                             {Email.NOT_MAIL: "'aarrbbaaaa@sas.c' is not a valid email address."})

    def test_validate_int_fail(self):
        self.assertFalse(self.validator.is_valid(4))
        self.assertDictEqual(self.validator.messages, {Email.NOT_MAIL: "'4' is not a valid email address."})


class TestIPAddress(TestCase):

    def setUp(self):
        self.validator = IPAddress()

    def tearDown(self):
        pass

    def test_validate_str_ipv4_success(self):
        self.assertTrue(self.validator.is_valid("192.168.2.2"))
        self.assertDictEqual(self.validator.messages, {})

    def test_validate_str_ipv4_fail(self):
        self.assertFalse(self.validator.is_valid("192.168.2.277"))
        self.assertDictEqual(self.validator.messages,
                             {IPAddress.NOT_IP_ADDRESS:
                              "'192.168.2.277' does not appear to be a valid IP address. Allowed ipv4"})

    def test_validate_str_ipv6_not_allowed_fail(self):
        self.assertFalse(self.validator.is_valid("2001:0db8:85a3:08d3:1319:8a2e:0370:7334"))
        self.assertDictEqual(self.validator.messages,
                             {IPAddress.IPV6_NOT_ALLOWED:
                              "'2001:0db8:85a3:08d3:1319:8a2e:0370:7334' is " +
                              "an ipv6 address that is not allowed. Allowed ipv4"})

    def test_validate_str_ipv6_success(self):
        self.validator = IPAddress(ipv4=False, ipv6=True)
        self.assertTrue(self.validator.is_valid("2001:0db8:85a3:08d3:1319:8a2e:0370:7334"))
        self.assertDictEqual(self.validator.messages, {})

    def test_validate_str_ipv6_reduced_success(self):
        self.validator = IPAddress(ipv4=False, ipv6=True)
        self.assertTrue(self.validator.is_valid("2001:0db8:85a3::8a2e:0370:7334"))
        self.assertDictEqual(self.validator.messages, {})

    def test_validate_str_ipv6_reduced_localhost_success(self):
        self.validator = IPAddress(ipv4=False, ipv6=True)
        self.assertTrue(self.validator.is_valid("::1"))
        self.assertDictEqual(self.validator.messages, {})

    def test_validate_str_ipv6_fail(self):
        self.validator = IPAddress(ipv4=False, ipv6=True)
        self.assertFalse(self.validator.is_valid("2001:0db8:85a3:08d3:1319:8a2e:0370:733T"))
        self.assertDictEqual(self.validator.messages,
                             {IPAddress.NOT_IP_ADDRESS:
                              "'2001:0db8:85a3:08d3:1319:8a2e:0370:733T' does " +
                              "not appear to be a valid IP address. Allowed ipv6"})

    def test_validate_str_ipv6_too_large_fail(self):
        self.validator = IPAddress(ipv4=False, ipv6=True)
        self.assertFalse(self.validator.is_valid("2001:0db8:85a3:08d3:1319:8a2e:0370:7333:3333:3333"))
        self.assertDictEqual(self.validator.messages,
                             {IPAddress.NOT_IP_ADDRESS:
                              "'2001:0db8:85a3:08d3:1319:8a2e:0370:7333:3333:3333' does " +
                              "not appear to be a valid IP address. Allowed ipv6"})

    def test_validate_str_ipv6_too_big_fail(self):
        self.validator = IPAddress(ipv4=False, ipv6=True)
        self.assertFalse(self.validator.is_valid("2001:0db8:85a3:08d3:1319:8a2e:0370:7333FFF"))
        self.assertDictEqual(self.validator.messages,
                             {IPAddress.NOT_IP_ADDRESS:
                              "'2001:0db8:85a3:08d3:1319:8a2e:0370:7333FFF' does " +
                              "not appear to be a valid IP address. Allowed ipv6"})

    def test_validate_str_ipv6_bad_white_spaces_fail(self):
        self.validator = IPAddress(ipv4=False, ipv6=True)
        self.assertFalse(self.validator.is_valid(":0db8:"))
        self.assertDictEqual(self.validator.messages,
                             {IPAddress.NOT_IP_ADDRESS:
                              "':0db8:' does " +
                              "not appear to be a valid IP address. Allowed ipv6"})

    def test_validate_str_ipv4_not_allowed_fail(self):
        self.validator = IPAddress(ipv4=False, ipv6=True)
        self.assertFalse(self.validator.is_valid("192.168.2.233"))
        self.assertDictEqual(self.validator.messages,
                             {IPAddress.IPV4_NOT_ALLOWED:
                              "'192.168.2.233' is an ipv4 address that is not allowed. Allowed ipv6"})

    def test_validate_str_ipv4_ipv6_using_ipv4_success(self):
        self.validator = IPAddress(ipv4=True, ipv6=True)
        self.assertTrue(self.validator.is_valid("192.168.2.2"))
        self.assertDictEqual(self.validator.messages, {})

    def test_validate_str_ipv4_ipv6_using_ipv6_success(self):
        self.validator = IPAddress(ipv4=True, ipv6=True)
        self.assertTrue(self.validator.is_valid("2001:0db8:85a3:08d3:1319:8a2e:0370:7334"))
        self.assertDictEqual(self.validator.messages, {})

    def test_validate_str_ipv4_ipv6_using_ipv6_reduced_success(self):
        self.validator = IPAddress(ipv4=True, ipv6=True)
        self.assertTrue(self.validator.is_valid("2001:0db8:85a3::8a2e:0370:7334"))
        self.assertDictEqual(self.validator.messages, {})

    def test_validate_str_ipv4_ipv6_using_wrong_ipv4_fail(self):
        self.validator = IPAddress(ipv4=True, ipv6=True)
        self.assertFalse(self.validator.is_valid("192.168.2.277"))
        self.assertDictEqual(self.validator.messages,
                             {IPAddress.NOT_IP_ADDRESS:
                              "'192.168.2.277' does not appear to be a valid IP address. Allowed ipv4 and ipv6"})

    def test_validate_str_ipv4_ipv6_using_wrong_ipv6_fail(self):
        self.validator = IPAddress(ipv4=True, ipv6=True)
        self.assertFalse(self.validator.is_valid("2001:0db8:85a3:08d3:1319:8a2e:0370:733T"))
        self.assertDictEqual(self.validator.messages,
                             {IPAddress.NOT_IP_ADDRESS:
                              "'2001:0db8:85a3:08d3:1319:8a2e:0370:733T' does not " +
                              "appear to be a valid IP address. Allowed ipv4 and ipv6"})

    def test_validate_int_fail(self):
        self.validator = IPAddress(ipv4=True, ipv6=True)
        self.assertFalse(self.validator.is_valid(2323))
        self.assertDictEqual(self.validator.messages,
                             {IPAddress.NOT_IP_ADDRESS:
                              "'2323' does not appear to be a valid IP address. Allowed ipv4 and ipv6"})

    def test_bad_definition(self):
        with self.assertRaises(ValueError):
            self.validator = IPAddress(ipv4=False, ipv6=False)


class TestMacAddress(TestCase):

    def setUp(self):
        self.validator = MacAddress()

    def tearDown(self):
        pass

    def test_validate_str_success(self):
        self.assertTrue(self.validator.is_valid("01:23:45:67:89:ab"))
        self.assertDictEqual(self.validator.messages, {})

    def test_validate_str_fail(self):
        self.assertFalse(self.validator.is_valid("aarrbba@sas.c"))
        self.assertDictEqual(self.validator.messages,
                             {MacAddress.INVALID_MAC_ADDRESS: "'aarrbba@sas.c' is not a valid mac address."})

    def test_validate_int_fail(self):
        self.assertFalse(self.validator.is_valid(4))
        self.assertDictEqual(self.validator.messages,
                             {MacAddress.INVALID_MAC_ADDRESS: "'4' is not a valid mac address."})


class TestURL(TestCase):

    def setUp(self):
        self.validator = URL()

    def tearDown(self):
        pass

    def test_validate_str_required_tld_http_success(self):
        self.assertTrue(self.validator.is_valid("http://www.google.com"))
        self.assertDictEqual(self.validator.messages, {})

    def test_validate_str_required_tld_git_success(self):
        self.assertTrue(self.validator.is_valid("git://github.com"))
        self.assertDictEqual(self.validator.messages, {})

    def test_validate_str_no_protocol_fail(self):
        self.assertFalse(self.validator.is_valid("google.com"))
        self.assertDictEqual(self.validator.messages, {URL.INVALID_URL: "'google.com' is not a valid url."})

    def test_validate_int_fail(self):
        self.assertFalse(self.validator.is_valid(4))
        self.assertDictEqual(self.validator.messages, {URL.INVALID_URL: "'4' is not a valid url."})

    def test_validate_str_not_required_tld_http_success(self):
        self.validator = URL(require_tld=False)
        self.assertTrue(self.validator.is_valid("http://google"))
        self.assertDictEqual(self.validator.messages, {})

    def test_validate_str_not_required_tld_git_success(self):
        self.validator = URL(require_tld=False)
        self.assertTrue(self.validator.is_valid("git://github"))
        self.assertDictEqual(self.validator.messages, {})


class TestUUID(TestCase):

    def setUp(self):
        self.validator = UUID()

    def tearDown(self):
        pass

    def test_validate_str_success(self):
        self.assertTrue(self.validator.is_valid("550e8400-e29b-41d4-a716-446655440000"))
        self.assertDictEqual(self.validator.messages, {})

    def test_validate_str_fail(self):
        self.assertFalse(self.validator.is_valid("aarrbbaaaa@sas.c"))
        self.assertDictEqual(self.validator.messages, {UUID.INVALID_UUID: "'aarrbbaaaa@sas.c' is not a valid UUID."})

    def test_validate_int_fail(self):
        self.assertFalse(self.validator.is_valid(4))
        self.assertDictEqual(self.validator.messages, {UUID.INVALID_UUID: "'4' is not a valid UUID."})


class TestAnyOf(TestCase):

    def setUp(self):
        self.validator = AnyOf(values=[1, "2", "aaas", "ouch"])

    def tearDown(self):
        pass

    def test_validate_str_success(self):
        self.assertTrue(self.validator.is_valid("aaas"))
        self.assertDictEqual(self.validator.messages, {})

    def test_validate_int_success(self):
        self.assertTrue(self.validator.is_valid(1))
        self.assertDictEqual(self.validator.messages, {})

    def test_validate_str_fail(self):
        self.assertFalse(self.validator.is_valid("lass"))
        self.assertDictEqual(self.validator.messages, {AnyOf.NOT_IN_LIST: "'lass' is none of 1, '2', 'aaas', 'ouch'."})

    def test_validate_int_as_str_fail(self):
        self.assertFalse(self.validator.is_valid(2))
        self.assertDictEqual(self.validator.messages, {AnyOf.NOT_IN_LIST: "'2' is none of 1, '2', 'aaas', 'ouch'."})


class TestNoneOf(TestCase):

    def setUp(self):
        self.validator = NoneOf(values=[1, "2", "aaas", "ouch"])

    def tearDown(self):
        pass

    def test_validate_str_success(self):
        self.assertTrue(self.validator.is_valid("aaaaaas"))
        self.assertDictEqual(self.validator.messages, {})

    def test_validate_int_success(self):
        self.assertTrue(self.validator.is_valid(9))
        self.assertDictEqual(self.validator.messages, {})

    def test_validate_int_as_str_success(self):
        self.assertTrue(self.validator.is_valid(2))
        self.assertDictEqual(self.validator.messages, {})

    def test_validate_str_fail(self):
        self.assertFalse(self.validator.is_valid("ouch"))
        self.assertDictEqual(self.validator.messages, {NoneOf.IN_LIST: "'ouch' is one of 1, '2', 'aaas', 'ouch'."})


class TestEmpty(TestCase):

    def setUp(self):
        self.validator = IsEmpty()

    def test_validate_str_empty(self):
        self.assertTrue(self.validator.is_valid(""))
        self.assertDictEqual(self.validator.messages, {})

    def test_validate_class_empty(self):

        class EmptyClass:

            def __len__(self):
                return 0

        self.assertTrue(self.validator.is_valid(EmptyClass()))
        self.assertDictEqual(self.validator.messages, {})

    def test_validate_not_empty_class(self):

        class NotEmptyClass:

            def __repr__(self):
                return "NotEmptyClass"

        self.assertFalse(self.validator.is_valid(NotEmptyClass()))
        self.assertDictEqual(self.validator.messages, {IsEmpty.EMPTY: "'NotEmptyClass' must be empty"})

    def test_validate_none_ok(self):
        self.assertTrue(self.validator.is_valid(None))
        self.assertDictEqual(self.validator.messages, {})

    def test_float_ok(self):
        self.assertTrue(self.validator.is_valid(0.0))


class TestNotEmpty(TestCase):

    def setUp(self):
        self.validator = NotEmpty()

    def test_validate_str_empty(self):
        self.assertFalse(self.validator.is_valid(""))
        self.assertDictEqual(self.validator.messages,
                             {NotEmpty.NOT_EMPTY: "Value can not be empty"})

    def test_validate_class_empty(self):

        class EmptyClass:

            def __len__(self):
                return 0

        self.assertFalse(self.validator.is_valid(EmptyClass()))

    def test_validate_not_empty_class(self):

        class NotEmptyClass:
            pass

        self.assertTrue(self.validator.is_valid(NotEmptyClass()))
        self.assertDictEqual(self.validator.messages, {})

    def test_validate_none_raises(self):
        self.assertFalse(self.validator.is_valid(None))

    def test_float_raises(self):
        self.assertFalse(self.validator.is_valid(0.0))


class TestIsNone(TestCase):

    def setUp(self):
        self.validator = IsNone()

    def test_validate_str_empty(self):
        self.assertFalse(self.validator.is_valid(""))
        self.assertDictEqual(self.validator.messages,
                             {IsNone.NONE: "'' must be None"})

    def test_validate_class_empty(self):

        class EmptyClass:

            def __len__(self):
                return 0

        self.assertFalse(self.validator.is_valid(EmptyClass()))

    def test_validate_none(self):
        self.assertTrue(self.validator.is_valid(None))

    def test_float_raises(self):
        self.assertFalse(self.validator.is_valid(0.0))


class TestIsNotNone(TestCase):

    def setUp(self):
        self.validator = NotNone()

    def test_validate_none_raises(self):
        self.assertFalse(self.validator.is_valid(None))
        self.assertDictEqual(self.validator.messages,
                             {NotNone.NOT_NONE: NotNone.error_messages[NotNone.NOT_NONE]})

    def test_empty_class_ok(self):

        class EmptyClass:

            def __len__(self):
                return 0

        self.assertTrue(self.validator.is_valid(EmptyClass()))
        self.assertDictEqual(self.validator.messages, {})
