import re
from unittest import TestCase

from dirty_validators.basic import (URI, URL, UUID, AnyOf, BaseValidator,
                                    Email, EqualTo, IPAddress, IsEmpty, IsNone,
                                    Length, MacAddress, NoneOf, NotEmpty,
                                    NotEmptyString, NotEqualTo, NotNone,
                                    NumberRange, Regexp, StringNotContaining)


class TestBaseValidator(TestCase):

    def setUp(self):
        self.validator = BaseValidator()

    def tearDown(self):
        pass

    def test_validate_none(self):
        result = self.validator.is_valid(None)
        self.assertTrue(result)
        self.assertEqual(result.error_messages, [])

    def test_validate_int(self):
        result = self.validator.is_valid(3)
        self.assertTrue(result)
        self.assertEqual(result.error_messages, [])

    def test_validate_str(self):
        result = self.validator.is_valid('aaa')
        self.assertTrue(result)
        self.assertEqual(result.error_messages, [])

    def test_validate_dict(self):
        result = self.validator.is_valid({})
        self.assertTrue(result)
        self.assertEqual(result.error_messages, [])

    def test_error_not_hidden_behaviour(self):
        error_key = 'Test key'
        error_message = "'$value' is the value error to test hidden feature"
        self.validator.error_messages = {error_key: error_message}

        ctx = self.validator._build_context('Not hidden')
        self.validator.error(error_code=error_key, ctx=ctx)

        self.assertFalse(ctx)
        self.assertEqual(len(ctx.error_messages), 1)
        self.assertEqual(ctx.error_messages[0].code, error_key)
        self.assertEqual(ctx.error_messages[0].msg,
                         "'Not hidden' is the value error to test hidden feature")

    def test_error_hidden_behaviour(self):
        hidden_validator = BaseValidator(hide_value=True)
        error_key = 'Test key'
        error_message = "'$value' is the value error to test hidden feature"
        hidden_validator.error_messages = {error_key: error_message}

        ctx = hidden_validator._build_context('Not hidden')
        hidden_validator.error(error_code=error_key, ctx=ctx)

        self.assertFalse(ctx)
        self.assertEqual(len(ctx.error_messages), 1)
        self.assertEqual(ctx.error_messages[0].code, error_key)
        self.assertEqual(ctx.error_messages[0].msg,
                         "'**hidden**' is the value error to test hidden feature")


class TestEqualTo(TestCase):

    def test_validate_str_success(self):
        validator = EqualTo(comp_value="aaa")
        result = validator.is_valid("aaa")

        self.assertTrue(result)
        self.assertEqual(result.error_messages, [])

    def test_validate_str_fail(self):
        validator = EqualTo(comp_value="aaa")
        result = validator.is_valid("aqaa")

        self.assertFalse(result)
        self.assertEqual(len(result.error_messages), 1)
        self.assertEqual(result.error_messages[0].code, EqualTo.NOT_EQUAL)
        self.assertEqual(result.error_messages[0].msg,
                         "'aqaa' is not equal to 'aaa'")

    def test_validate_int_success(self):
        validator = EqualTo(comp_value=3)
        result = validator.is_valid(3)

        self.assertTrue(result)
        self.assertEqual(result.error_messages, [])

    def test_validate_int_fail(self):
        validator = EqualTo(comp_value=3)
        result = validator.is_valid(1)

        self.assertFalse(result)
        self.assertEqual(len(result.error_messages), 1)
        self.assertEqual(result.error_messages[0].code, EqualTo.NOT_EQUAL)
        self.assertEqual(result.error_messages[0].msg,
                         "'1' is not equal to '3'")

    def test_validate_int_fail_custom_error_message(self):
        validator = EqualTo(comp_value=3, error_messages={EqualTo.NOT_EQUAL: "$value $value aaa $comp_value"})
        result = validator.is_valid(4)

        self.assertFalse(result)
        self.assertEqual(len(result.error_messages), 1)
        self.assertEqual(result.error_messages[0].code, EqualTo.NOT_EQUAL)
        self.assertEqual(result.error_messages[0].msg,
                         "4 4 aaa 3")

    def test_validate_int_fail_custom_error_code(self):
        validator = EqualTo(comp_value=3, error_code_map={EqualTo.NOT_EQUAL: "newError"})
        result = validator.is_valid(4)

        self.assertFalse(result)
        self.assertEqual(len(result.error_messages), 1)
        self.assertEqual(result.error_messages[0].code, 'newError')
        self.assertEqual(result.error_messages[0].msg,
                         "'4' is not equal to '3'")

    def test_validate_int_fail_custom_error_code_and_error_message(self):
        validator = EqualTo(comp_value=3,
                            error_code_map={EqualTo.NOT_EQUAL: "newError"},
                            error_messages={EqualTo.NOT_EQUAL: "$value $value aaa $comp_value"})
        result = validator.is_valid(4)

        self.assertFalse(result)
        self.assertEqual(len(result.error_messages), 1)
        self.assertEqual(result.error_messages[0].code, 'newError')
        self.assertEqual(result.error_messages[0].msg,
                         "4 4 aaa 3")

    def test_validate_int_fail_custom_error_code_error_message_and_custom_value(self):
        validator = EqualTo(comp_value=3,
                            error_code_map={EqualTo.NOT_EQUAL: "newError"},
                            error_messages={EqualTo.NOT_EQUAL: "$value $value aaa $comp_value $value1 $value2"},
                            message_values={"value1": "aaaaaa1", "value2": "eeeeee1"})

        result = validator.is_valid(4)

        self.assertFalse(result)
        self.assertEqual(len(result.error_messages), 1)
        self.assertEqual(result.error_messages[0].code, 'newError')
        self.assertEqual(result.error_messages[0].msg,
                         '4 4 aaa 3 aaaaaa1 eeeeee1')


class TestNotEqualTo(TestCase):

    def test_validate_str_success(self):
        validator = NotEqualTo(comp_value="aaa")

        result = validator.is_valid('aqaa')
        self.assertTrue(result)
        self.assertEqual(result.error_messages, [])

    def test_validate_str_fail(self):
        validator = NotEqualTo(comp_value="aaa")

        result = validator.is_valid('aaa')
        self.assertFalse(result)
        self.assertEqual(len(result.error_messages), 1)
        self.assertEqual(result.error_messages[0].code, NotEqualTo.IS_EQUAL)
        self.assertEqual(result.error_messages[0].msg, "'aaa' is equal to 'aaa'")

    def test_validate_int_success(self):
        validator = NotEqualTo(comp_value=3)

        result = validator.is_valid(4)
        self.assertTrue(result)
        self.assertEqual(result.error_messages, [])

    def test_validate_int_fail(self):
        validator = NotEqualTo(comp_value=3)
        result = validator.is_valid(3)

        self.assertFalse(result)
        self.assertEqual(len(result.error_messages), 1)
        self.assertEqual(result.error_messages[0].code, NotEqualTo.IS_EQUAL)
        self.assertEqual(result.error_messages[0].msg, "'3' is equal to '3'")


class TestStringNotContaining(TestCase):

    def setUp(self):
        self.validator = StringNotContaining(token='Test_TOKEN')

    def test_validate_string_contains(self):
        result = self.validator.is_valid('This string contains Test_TOKEN for sure')

        self.assertFalse(result)
        self.assertEqual(len(result.error_messages), 1)
        self.assertEqual(result.error_messages[0].code, StringNotContaining.NOT_CONTAINS)
        self.assertEqual(result.error_messages[0].msg,
                         "'This string contains Test_TOKEN for sure' contains 'Test_TOKEN'")

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

    def test_validate_str_fail_short(self):
        result = self.validator.is_valid("aa")
        self.assertFalse(result)
        self.assertEqual(len(result.error_messages), 1)
        self.assertEqual(result.error_messages[0].code, Length.TOO_SHORT)
        self.assertEqual(result.error_messages[0].msg,
                         "'aa' is less than 3 unit length")

    def test_validate_str_fail_long(self):
        result = self.validator.is_valid("aabbnnmm")
        self.assertFalse(result)
        self.assertEqual(len(result.error_messages), 1)
        self.assertEqual(result.error_messages[0].code, Length.TOO_LONG)
        self.assertEqual(result.error_messages[0].msg,
                         "'aabbnnmm' is more than 6 unit length")

    def test_validate_int_fail(self):
        result = self.validator.is_valid(5)
        self.assertFalse(result)
        self.assertEqual(len(result.error_messages), 1)
        self.assertEqual(result.error_messages[0].code, Length.INVALID_TYPE)
        self.assertEqual(result.error_messages[0].msg,
                         "'5' has no length")

    def test_validate_list_success(self):
        self.assertTrue(self.validator.is_valid(["1a", "32d", "tr", "wq"]))

    def test_validate_list_fail_short(self):
        result = self.validator.is_valid(["1a"])
        self.assertFalse(result)
        self.assertEqual(len(result.error_messages), 1)
        self.assertEqual(result.error_messages[0].code, Length.TOO_SHORT)
        self.assertEqual(result.error_messages[0].msg,
                         "'['1a']' is less than 3 unit length")

    def test_validate_list_fail_long(self):
        result = self.validator.is_valid(["1a", "32d", "tr", "wq", "qwqw", "dd", "as", "er"])
        self.assertFalse(result)
        self.assertEqual(len(result.error_messages), 1)
        self.assertEqual(result.error_messages[0].code, Length.TOO_LONG)
        self.assertEqual(result.error_messages[0].msg,
                         "'['1a', '32d', 'tr', 'wq', 'qwqw', 'dd', 'as', 'er']' is more than 6 unit length")


class TestNumberRange(TestCase):

    def setUp(self):
        self.validator = NumberRange(min=3, max=4)

    def tearDown(self):
        pass

    def test_validate_int_success(self):
        self.assertTrue(self.validator.is_valid(4))

    def test_validate_int_fail(self):
        result = self.validator.is_valid(5)
        self.assertFalse(result)
        self.assertEqual(len(result.error_messages), 1)
        self.assertEqual(result.error_messages[0].code, NumberRange.OUT_OF_RANGE)
        self.assertEqual(result.error_messages[0].msg,
                         "'5' is out of range (3, 4)")

    def test_validate_int_no_min_success(self):
        validator = NumberRange(max=4)
        self.assertTrue(validator.is_valid(1))

    def test_validate_int_no_min_fail(self):
        validator = NumberRange(max=4)

        result = validator.is_valid(5)
        self.assertFalse(result)
        self.assertEqual(len(result.error_messages), 1)
        self.assertEqual(result.error_messages[0].code, NumberRange.OUT_OF_RANGE)
        self.assertEqual(result.error_messages[0].msg,
                         "'5' is out of range (None, 4)")

    def test_validate_int_no_max_success(self):
        validator = NumberRange(min=4)
        self.assertTrue(validator.is_valid(5))

    def test_validate_int_no_max_fail(self):
        validator = NumberRange(min=4)
        result = validator.is_valid(1)
        self.assertFalse(result)
        self.assertEqual(len(result.error_messages), 1)
        self.assertEqual(result.error_messages[0].code, NumberRange.OUT_OF_RANGE)
        self.assertEqual(result.error_messages[0].msg,
                         "'1' is out of range (4, None)")


class TestRegexp(TestCase):

    def setUp(self):
        self.validator = Regexp(regex="^aa.+bb$")

    def tearDown(self):
        pass

    def test_validate_str_success(self):
        self.assertTrue(self.validator.is_valid("aarrbb"))

    def test_validate_str_fail(self):
        self.assertFalse(self.validator.is_valid("aarrbbcc"))

        result = self.validator.is_valid("aarrbbcc")
        self.assertFalse(result)
        self.assertEqual(len(result.error_messages), 1)
        self.assertEqual(result.error_messages[0].code, Regexp.NOT_MATCH)
        self.assertEqual(result.error_messages[0].msg,
                         "'aarrbbcc' does not match against pattern '^aa.+bb$'")

    def test_validate_str_case_sensitive_fail(self):
        result = self.validator.is_valid("Aarrbb")
        self.assertFalse(result)
        self.assertEqual(len(result.error_messages), 1)
        self.assertEqual(result.error_messages[0].code, Regexp.NOT_MATCH)
        self.assertEqual(result.error_messages[0].msg,
                         "'Aarrbb' does not match against pattern '^aa.+bb$'")

    def test_validate_str_case_insensitive_success(self):
        self.validator = Regexp(regex="^aa.+bb$", flags=re.IGNORECASE)
        self.assertTrue(self.validator.is_valid("Aarrbb"))

    def test_validate_int_fail(self):
        result = self.validator.is_valid(6)
        self.assertFalse(result)
        self.assertEqual(len(result.error_messages), 1)
        self.assertEqual(result.error_messages[0].code, Regexp.NOT_MATCH)
        self.assertEqual(result.error_messages[0].msg,
                         "'6' does not match against pattern '^aa.+bb$'")


class TestEmail(TestCase):

    def setUp(self):
        self.validator = Email()

    def tearDown(self):
        pass

    def test_validate_str_success(self):
        self.assertTrue(self.validator.is_valid("aarrbb@aaaa.com"))

    def test_validate_str_fail(self):
        result = self.validator.is_valid("aarrbbaaaa@sas.c")
        self.assertFalse(result)
        self.assertEqual(len(result.error_messages), 1)
        self.assertEqual(result.error_messages[0].code, Email.NOT_MAIL)
        self.assertEqual(result.error_messages[0].msg,
                         "'aarrbbaaaa@sas.c' is not a valid email address.")

    def test_validate_int_fail(self):
        result = self.validator.is_valid(4)
        self.assertFalse(result)
        self.assertEqual(len(result.error_messages), 1)
        self.assertEqual(result.error_messages[0].code, Email.NOT_MAIL)
        self.assertEqual(result.error_messages[0].msg,
                         "'4' is not a valid email address.")


class TestIPAddress(TestCase):

    def setUp(self):
        self.validator = IPAddress()

    def test_validate_str_ipv4_success(self):
        self.assertTrue(self.validator.is_valid("192.168.2.2"))

    def test_validate_str_ipv4_fail(self):
        result = self.validator.is_valid("192.168.2.277")
        self.assertFalse(result)
        self.assertEqual(len(result.error_messages), 1)
        self.assertEqual(result.error_messages[0].code, IPAddress.NOT_IP_ADDRESS)
        self.assertEqual(result.error_messages[0].msg,
                         "'192.168.2.277' does not appear to be a valid IP address. Allowed ipv4")

    def test_validate_str_ipv6_not_allowed_fail(self):
        result = self.validator.is_valid("2001:0db8:85a3:08d3:1319:8a2e:0370:7334")
        self.assertFalse(result)
        self.assertEqual(len(result.error_messages), 1)
        self.assertEqual(result.error_messages[0].code, IPAddress.IPV6_NOT_ALLOWED)
        self.assertEqual(result.error_messages[0].msg,
                         "'2001:0db8:85a3:08d3:1319:8a2e:0370:7334' is "
                         "an ipv6 address that is not allowed. Allowed ipv4")

    def test_validate_str_ipv6_success(self):
        validator = IPAddress(ipv4=False, ipv6=True)
        self.assertTrue(validator.is_valid("2001:0db8:85a3:08d3:1319:8a2e:0370:7334"))

    def test_validate_str_ipv6_reduced_success(self):
        validator = IPAddress(ipv4=False, ipv6=True)
        self.assertTrue(validator.is_valid("2001:0db8:85a3::8a2e:0370:7334"))

    def test_validate_str_ipv6_reduced_localhost_success(self):
        validator = IPAddress(ipv4=False, ipv6=True)
        self.assertTrue(validator.is_valid("::1"))

    def test_validate_str_ipv6_fail(self):
        validator = IPAddress(ipv4=False, ipv6=True)

        result = validator.is_valid("2001:0db8:85a3:08d3:1319:8a2e:0370:733T")
        self.assertFalse(result)
        self.assertEqual(len(result.error_messages), 1)
        self.assertEqual(result.error_messages[0].code, IPAddress.NOT_IP_ADDRESS)
        self.assertEqual(result.error_messages[0].msg,
                         "'2001:0db8:85a3:08d3:1319:8a2e:0370:733T' does "
                         "not appear to be a valid IP address. Allowed ipv6")

    def test_validate_str_ipv6_too_large_fail(self):
        validator = IPAddress(ipv4=False, ipv6=True)
        result = validator.is_valid("2001:0db8:85a3:08d3:1319:8a2e:0370:7333:3333:3333")
        self.assertFalse(result)
        self.assertEqual(len(result.error_messages), 1)
        self.assertEqual(result.error_messages[0].code, IPAddress.NOT_IP_ADDRESS)
        self.assertEqual(result.error_messages[0].msg,
                         "'2001:0db8:85a3:08d3:1319:8a2e:0370:7333:3333:3333' does "
                         "not appear to be a valid IP address. Allowed ipv6")

    def test_validate_str_ipv6_too_big_fail(self):
        validator = IPAddress(ipv4=False, ipv6=True)
        result = validator.is_valid("2001:0db8:85a3:08d3:1319:8a2e:0370:7333FFF")
        self.assertFalse(result)
        self.assertEqual(len(result.error_messages), 1)
        self.assertEqual(result.error_messages[0].code, IPAddress.NOT_IP_ADDRESS)
        self.assertEqual(result.error_messages[0].msg,
                         "'2001:0db8:85a3:08d3:1319:8a2e:0370:7333FFF' does "
                         "not appear to be a valid IP address. Allowed ipv6")

    def test_validate_str_ipv6_bad_white_spaces_fail(self):
        validator = IPAddress(ipv4=False, ipv6=True)
        result = validator.is_valid(":0db8:")
        self.assertFalse(result)
        self.assertEqual(len(result.error_messages), 1)
        self.assertEqual(result.error_messages[0].code, IPAddress.NOT_IP_ADDRESS)
        self.assertEqual(result.error_messages[0].msg,
                         "':0db8:' does "
                         "not appear to be a valid IP address. Allowed ipv6")

    def test_validate_str_ipv4_not_allowed_fail(self):
        validator = IPAddress(ipv4=False, ipv6=True)
        result = validator.is_valid("192.168.2.233")
        self.assertFalse(result)
        self.assertEqual(len(result.error_messages), 1)
        self.assertEqual(result.error_messages[0].code, IPAddress.IPV4_NOT_ALLOWED)
        self.assertEqual(result.error_messages[0].msg,
                         "'192.168.2.233' is an ipv4 address that is not allowed. Allowed ipv6")

    def test_validate_str_ipv4_ipv6_using_ipv4_success(self):
        validator = IPAddress(ipv4=True, ipv6=True)
        self.assertTrue(validator.is_valid("192.168.2.2"))

    def test_validate_str_ipv4_ipv6_using_ipv6_success(self):
        validator = IPAddress(ipv4=True, ipv6=True)
        self.assertTrue(validator.is_valid("2001:0db8:85a3:08d3:1319:8a2e:0370:7334"))

    def test_validate_str_ipv4_ipv6_using_ipv6_reduced_success(self):
        validator = IPAddress(ipv4=True, ipv6=True)
        self.assertTrue(validator.is_valid("2001:0db8:85a3::8a2e:0370:7334"))

    def test_validate_str_ipv4_ipv6_using_wrong_ipv4_fail(self):
        validator = IPAddress(ipv4=True, ipv6=True)
        result = validator.is_valid("192.168.2.277")
        self.assertFalse(result)
        self.assertEqual(len(result.error_messages), 1)
        self.assertEqual(result.error_messages[0].code, IPAddress.NOT_IP_ADDRESS)
        self.assertEqual(result.error_messages[0].msg,
                         "'192.168.2.277' does not appear to be a valid IP address. Allowed ipv4 and ipv6")

    def test_validate_str_ipv4_ipv6_using_wrong_ipv6_fail(self):
        validator = IPAddress(ipv4=True, ipv6=True)

        result = validator.is_valid("2001:0db8:85a3:08d3:1319:8a2e:0370:733T")
        self.assertFalse(result)
        self.assertEqual(len(result.error_messages), 1)
        self.assertEqual(result.error_messages[0].code, IPAddress.NOT_IP_ADDRESS)
        self.assertEqual(result.error_messages[0].msg,
                         "'2001:0db8:85a3:08d3:1319:8a2e:0370:733T' does not "
                         "appear to be a valid IP address. Allowed ipv4 and ipv6")

    def test_validate_int_fail(self):
        validator = IPAddress(ipv4=True, ipv6=True)

        result = validator.is_valid(2323)
        self.assertFalse(result)
        self.assertEqual(len(result.error_messages), 1)
        self.assertEqual(result.error_messages[0].code, IPAddress.NOT_IP_ADDRESS)
        self.assertEqual(result.error_messages[0].msg,
                         "'2323' does not appear to be a valid IP address. Allowed ipv4 and ipv6")

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

    def test_validate_str_fail(self):
        result = self.validator.is_valid("aarrbba@sas.c")
        self.assertFalse(result)
        self.assertEqual(len(result.error_messages), 1)
        self.assertEqual(result.error_messages[0].code, MacAddress.INVALID_MAC_ADDRESS)
        self.assertEqual(result.error_messages[0].msg,
                         "'aarrbba@sas.c' is not a valid mac address.")

    def test_validate_int_fail(self):
        result = self.validator.is_valid(4)
        self.assertFalse(result)
        self.assertEqual(len(result.error_messages), 1)
        self.assertEqual(result.error_messages[0].code, MacAddress.INVALID_MAC_ADDRESS)
        self.assertEqual(result.error_messages[0].msg,
                         "'4' is not a valid mac address.")


class TestURL(TestCase):

    def setUp(self):
        self.validator = URL()

    def tearDown(self):
        pass

    def test_validate_str_required_tld_http_success(self):
        self.assertTrue(self.validator.is_valid("http://www.google.com"))

    def test_validate_str_required_tld_git_success(self):
        self.assertTrue(self.validator.is_valid("git://github.com"))

    def test_validate_str_no_protocol_fail(self):
        result = self.validator.is_valid("google.com")
        self.assertFalse(result)
        self.assertEqual(len(result.error_messages), 1)
        self.assertEqual(result.error_messages[0].code, URL.INVALID_URL)
        self.assertEqual(result.error_messages[0].msg,
                         "'google.com' is not a valid url.")

    def test_validate_int_fail(self):
        result = self.validator.is_valid(4)
        self.assertFalse(result)
        self.assertEqual(len(result.error_messages), 1)
        self.assertEqual(result.error_messages[0].code, URL.INVALID_URL)
        self.assertEqual(result.error_messages[0].msg,
                         "'4' is not a valid url.")

    def test_validate_str_not_required_tld_http_success(self):
        validator = URL(require_tld=False)
        self.assertTrue(validator.is_valid("http://google"))

    def test_validate_str_not_required_tld_git_success(self):
        validator = URL(require_tld=False)
        self.assertTrue(validator.is_valid("git://github"))

    def test_validate_str_not_required_tld_s3_success(self):
        validator = URL(require_tld=False)
        self.assertTrue(validator.is_valid("s3://my_bucket"))

    def test_validate_str_composed_scheme_plus_success(self):
        self.assertTrue(self.validator.is_valid("git+ssh://github.com"))

    def test_validate_str_composed_scheme_colon_success(self):
        self.assertTrue(self.validator.is_valid("jdbc:postgresql://mydb.com"))


class TestURI(TestCase):

    def setUp(self):
        self.validator = URI()

    def tearDown(self):
        pass

    def test_validate_str_http_success(self):
        self.assertTrue(self.validator.is_valid("http://www.google.com"))

    def test_validate_str_s3_success(self):
        self.assertTrue(self.validator.is_valid("s3://www.google.com"))

    def test_validate_str_required_tld_git_success(self):
        self.assertTrue(self.validator.is_valid("git://github.com"))

    def test_validate_str_no_protocol_fail(self):
        result = self.validator.is_valid("google.com")
        self.assertFalse(result)
        self.assertEqual(len(result.error_messages), 1)
        self.assertEqual(result.error_messages[0].code, URI.INVALID_URI)
        self.assertEqual(result.error_messages[0].msg,
                         "'google.com' is not a valid uri.")

    def test_validate_int_fail(self):
        result = self.validator.is_valid(4)
        self.assertFalse(result)
        self.assertEqual(len(result.error_messages), 1)
        self.assertEqual(result.error_messages[0].code, URI.INVALID_URI)
        self.assertEqual(result.error_messages[0].msg,
                         "'4' is not a valid uri.")

    def test_validate_str_not_required_tld_http_success(self):
        self.validator = URL(require_tld=False)
        self.assertTrue(self.validator.is_valid("http://google"))

    def test_validate_str_not_required_tld_git_success(self):
        self.validator = URL(require_tld=False)
        self.assertTrue(self.validator.is_valid("git://github"))

    def test_validate_str_composed_scheme_plus_success(self):
        self.assertTrue(self.validator.is_valid("git+ssh://github.com/sdss"))

    def test_validate_str_composed_scheme_colon_success(self):
        self.assertTrue(self.validator.is_valid("jdbc:postgresql://mydb.com/dcdgfd"))

    def test_validate_str_composed_scheme_plus_no_host_success(self):
        self.assertTrue(self.validator.is_valid("hdfs+csv:///sdss"))

    def test_validate_str_composed_scheme_plus_no_host_2_success(self):
        self.assertTrue(self.validator.is_valid("hdfs+csv:/sdss"))


class TestUUID(TestCase):

    def setUp(self):
        self.validator = UUID()

    def tearDown(self):
        pass

    def test_validate_str_success(self):
        self.assertTrue(self.validator.is_valid("550e8400-e29b-41d4-a716-446655440000"))

    def test_validate_str_fail(self):
        result = self.validator.is_valid("aarrbbaaaa@sas.c")
        self.assertFalse(result)
        self.assertEqual(len(result.error_messages), 1)
        self.assertEqual(result.error_messages[0].code, UUID.INVALID_UUID)
        self.assertEqual(result.error_messages[0].msg,
                         "'aarrbbaaaa@sas.c' is not a valid UUID.")

    def test_validate_int_fail(self):
        result = self.validator.is_valid(4)
        self.assertFalse(result)
        self.assertEqual(len(result.error_messages), 1)
        self.assertEqual(result.error_messages[0].code, UUID.INVALID_UUID)
        self.assertEqual(result.error_messages[0].msg,
                         "'4' is not a valid UUID.")


class TestAnyOf(TestCase):

    def setUp(self):
        self.validator = AnyOf(values=[1, "2", "aaas", "ouch"])

    def tearDown(self):
        pass

    def test_validate_str_success(self):
        self.assertTrue(self.validator.is_valid("aaas"))

    def test_validate_int_success(self):
        self.assertTrue(self.validator.is_valid(1))

    def test_validate_str_fail(self):
        result = self.validator.is_valid('lass')
        self.assertFalse(result)
        self.assertEqual(len(result.error_messages), 1)
        self.assertEqual(result.error_messages[0].code, AnyOf.NOT_IN_LIST)
        self.assertEqual(result.error_messages[0].msg,
                         "'lass' is none of 1, '2', 'aaas', 'ouch'.")

    def test_validate_int_as_str_fail(self):
        result = self.validator.is_valid(4)
        self.assertFalse(result)
        self.assertEqual(len(result.error_messages), 1)
        self.assertEqual(result.error_messages[0].code, AnyOf.NOT_IN_LIST)
        self.assertEqual(result.error_messages[0].msg,
                         "'4' is none of 1, '2', 'aaas', 'ouch'.")


class TestNoneOf(TestCase):

    def setUp(self):
        self.validator = NoneOf(values=[1, "2", "aaas", "ouch"])

    def tearDown(self):
        pass

    def test_validate_str_success(self):
        self.assertTrue(self.validator.is_valid("aaaaaas"))

    def test_validate_int_success(self):
        self.assertTrue(self.validator.is_valid(9))

    def test_validate_int_as_str_success(self):
        self.assertTrue(self.validator.is_valid(2))

    def test_validate_str_fail(self):
        result = self.validator.is_valid("ouch")
        self.assertFalse(result)
        self.assertEqual(len(result.error_messages), 1)
        self.assertEqual(result.error_messages[0].code, NoneOf.IN_LIST)
        self.assertEqual(result.error_messages[0].msg,
                         "'ouch' is one of 1, '2', 'aaas', 'ouch'.")


class TestEmpty(TestCase):

    def setUp(self):
        self.validator = IsEmpty()

    def test_validate_str_empty(self):
        self.assertTrue(self.validator.is_valid(""))

    def test_validate_class_empty(self):
        class EmptyClass:

            def __len__(self):
                return 0

        self.assertTrue(self.validator.is_valid(EmptyClass()))

    def test_validate_not_empty_class(self):
        class NotEmptyClass:

            def __repr__(self):
                return "NotEmptyClass"

        result = self.validator.is_valid(NotEmptyClass())
        self.assertFalse(result)
        self.assertEqual(len(result.error_messages), 1)
        self.assertEqual(result.error_messages[0].code, IsEmpty.EMPTY)
        self.assertEqual(result.error_messages[0].msg,
                         "'NotEmptyClass' must be empty")

    def test_validate_none_ok(self):
        self.assertTrue(self.validator.is_valid(None))

    def test_float_ok(self):
        self.assertTrue(self.validator.is_valid(0.0))


class TestNotEmpty(TestCase):

    def setUp(self):
        self.validator = NotEmpty()

    def test_validate_str_empty(self):
        result = self.validator.is_valid('')
        self.assertFalse(result)
        self.assertEqual(len(result.error_messages), 1)
        self.assertEqual(result.error_messages[0].code, NotEmpty.NOT_EMPTY)
        self.assertEqual(result.error_messages[0].msg,
                         "Value can not be empty")

    def test_validate_class_empty(self):
        class EmptyClass:

            def __len__(self):
                return 0

        self.assertFalse(self.validator.is_valid(EmptyClass()))

    def test_validate_not_empty_class(self):
        class NotEmptyClass:
            pass

        self.assertTrue(self.validator.is_valid(NotEmptyClass()))

    def test_validate_none_raises(self):
        self.assertFalse(self.validator.is_valid(None))

    def test_float_raises(self):
        self.assertFalse(self.validator.is_valid(0.0))


class TestNotEmptyString(TestCase):

    def setUp(self):
        self.validator = NotEmptyString()

    def test_validate_str_empty(self):
        result = self.validator.is_valid('')
        self.assertFalse(result)
        self.assertEqual(len(result.error_messages), 1)
        self.assertEqual(result.error_messages[0].code, NotEmptyString.NOT_EMPTY)
        self.assertEqual(result.error_messages[0].msg,
                         "Value can not be empty")

    def test_validate_str_more_whites_empty(self):
        result = self.validator.is_valid("        ")
        self.assertFalse(result)
        self.assertEqual(len(result.error_messages), 1)
        self.assertEqual(result.error_messages[0].code, NotEmptyString.NOT_EMPTY)
        self.assertEqual(result.error_messages[0].msg,
                         "Value can not be empty")

    def test_validate_not_str(self):
        result = self.validator.is_valid(3)
        self.assertFalse(result)
        self.assertEqual(len(result.error_messages), 1)
        self.assertEqual(result.error_messages[0].code, NotEmptyString.NOT_STRING)
        self.assertEqual(result.error_messages[0].msg,
                         "Value must be a string")

    def test_validate_not_empty(self):
        self.assertTrue(self.validator.is_valid("Batman"))


class TestIsNone(TestCase):

    def setUp(self):
        self.validator = IsNone()

    def test_validate_str_empty(self):
        result = self.validator.is_valid("")
        self.assertFalse(result)
        self.assertEqual(len(result.error_messages), 1)
        self.assertEqual(result.error_messages[0].code, IsNone.NONE)
        self.assertEqual(result.error_messages[0].msg,
                         "'' must be None")

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
        result = self.validator.is_valid(None)
        self.assertFalse(result)
        self.assertEqual(len(result.error_messages), 1)
        self.assertEqual(result.error_messages[0].code, NotNone.NOT_NONE)
        self.assertEqual(result.error_messages[0].msg,
                         NotNone.error_messages[NotNone.NOT_NONE])

    def test_empty_class_ok(self):
        class EmptyClass:

            def __len__(self):
                return 0

        self.assertTrue(self.validator.is_valid(EmptyClass()))
