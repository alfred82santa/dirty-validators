"""
Validators library
"""
import re
from string import Template


class ValidatorMetaclass(type):

    def __new__(cls, name, bases, classdict):
        error_code_map = {}
        error_messages = {}
        message_values = {}

        for base in reversed(bases):
            try:
                error_code_map.update(base.error_code_map)
            except AttributeError:
                pass

            try:
                error_messages.update(base.error_messages)
            except AttributeError:
                pass

            try:
                message_values.update(base.message_values)
            except AttributeError:
                pass

        try:
            error_code_map.update(classdict.pop('error_code_map'))
        except KeyError:
            pass

        try:
            error_messages.update(classdict.pop('error_messages'))
        except KeyError:
            pass

        try:
            message_values.update(classdict.pop('message_values'))
        except KeyError:
            pass

        classdict['error_code_map'] = error_code_map
        classdict['error_messages'] = error_messages
        classdict['message_values'] = message_values

        return super(ValidatorMetaclass, cls).__new__(cls, name, bases, classdict)


class BaseValidator(metaclass=ValidatorMetaclass):
    error_code_map = {}
    error_messages = {}
    message_values = {}
    hidden_value = '**Hidden**'

    def __init__(self, error_code_map=None, error_messages=None,
                 message_values=None, hidden=False, *args, **kwargs):
        """
        :param error_code_map: Map of orginial error codes to custom error codes
        :rparam error_code_map: dict
        :param error_messages: Map of error codes to error messages
        :rparam error_messages: dict
        :param message_values: Map of placeholders to values
        :rparam error_messages: dict
        """
        self.error_code_map = self.error_code_map.copy()
        self.error_messages = self.error_messages.copy()
        self.message_values = self.message_values.copy()

        if error_code_map:
            self.error_code_map.update(error_code_map)

        if error_messages:
            self.error_messages.update(error_messages)

        if message_values:
            self.message_values.update(message_values)

        self.messages = {}
        self.hidden = hidden

    def error(self, error_code, value, **kwargs):
        """
        Helper to add error to messages field. It fills placeholder with extra call parameters
        or values from message_value map.

        :param error_code: Error code to use
        :rparam error_code: str
        :param value: Value checked
        :param kwargs: Map of values to use in placeholders
        """
        code = self.error_code_map.get(error_code, error_code)

        try:
            message = Template(self.error_messages[code])
        except KeyError:
            message = Template(self.error_messages[error_code])

        placeholders = {"value": self.hidden_value if self.hidden else value}
        placeholders.update(kwargs)
        placeholders.update(self.message_values)

        self.messages[code] = message.safe_substitute(placeholders)

    def is_valid(self, value, *args, **kwargs):
        self.messages = {}
        return self._internal_is_valid(value, *args, **kwargs)

    def _internal_is_valid(self, value, *args, **kwargs):
        return True


class EqualTo(BaseValidator):
    """
    Compares value with a static value.
    """
    NOT_EQUAL = 'notEqual'

    error_messages = {NOT_EQUAL: "'$value' is not equal to '$comp_value'"}

    def __init__(self, comp_value=None, *args, **kwargs):
        """
        :param comp_value: Static value to use on check
        """
        super(EqualTo, self).__init__(*args, **kwargs)
        self.comp_value = comp_value
        self.message_values.update({'comp_value': self.comp_value})

    def _internal_is_valid(self, value, *args, **kwargs):
        if value != self.comp_value:
            self.error(self.NOT_EQUAL, value)
            return False
        return True


class NotEqualTo(BaseValidator):
    """
    Checks whether a value is distinct of static value.
    """
    IS_EQUAL = 'isEqual'

    error_messages = {IS_EQUAL: "'$value' is equal to '$comp_value'"}

    def __init__(self, comp_value=None, *args, **kwargs):
        """
        :param comp_value: Static value to use on check
        """
        super(NotEqualTo, self).__init__(*args, **kwargs)
        self.comp_value = comp_value
        self.message_values.update({'comp_value': self.comp_value})

    def _internal_is_valid(self, value, *args, **kwargs):
        if value == self.comp_value:
            self.error(self.IS_EQUAL, value)
            return False
        return True


class StringNotContaining(BaseValidator):
    """
    Checks that the value does not contain a static substring
    """
    NOT_CONTAINS = 'notContains'

    error_messages = {NOT_CONTAINS: "'$value' contains '$token'"}

    def __init__(self, token=None, case_sensitive=True, *args, **kwargs):
        """
        :param token: Static value to see check it is contained in the string
        :param case_sensitive: Boolean to check the string matching case or not
        """
        super(StringNotContaining, self).__init__(*args, **kwargs)
        self.token = token
        self.case_sensitive = case_sensitive
        self.message_values.update({'token': self.token})

    def _internal_is_valid(self, value, *args, **kwargs):
        if (not self.case_sensitive and (self.token.lower() not in value.lower())) or \
                (self.case_sensitive and (self.token not in value)):
            return True

        self.error(self.NOT_CONTAINS, value)
        return False


class Length(BaseValidator):
    """
    Validates the length of a string.

    :param min:
    The minimum required length of the string. If not provided, minimum
    length will not be checked.
    :param max:
    The maximum length of the string. If not provided, maximum length
    will not be checked.
    """

    TOO_LONG = 'tooLong'
    TOO_SHORT = 'tooShort'
    INVALID_TYPE = 'notLength'

    error_messages = {
        TOO_LONG: "'$value' is more than $max unit length",
        TOO_SHORT: "'$value' is less than $min unit length",
        INVALID_TYPE: "'$value' has no length"
    }

    def __init__(self, min=-1, max=-1, *args, **kwargs):
        super(Length, self).__init__(*args, **kwargs)
        assert min != -1 or max != -1, 'At least one of `min` or `max` must be specified.'
        assert max == -1 or min <= max, '`min` cannot be more than `max`.'
        self.min = min
        self.max = max

        self.message_values.update({"min": self.min, "max": self.max})

    def _internal_is_valid(self, value, *args, **kwargs):
        try:
            length = len(value) or 0
            if length < self.min:
                self.error(self.TOO_SHORT, value)
                return False
            if self.max != -1 and length > self.max:
                self.error(self.TOO_LONG, value)
                return False
            return True
        except TypeError:
            self.error(self.INVALID_TYPE, value)
            return False


class NumberRange(BaseValidator):
    """
    Validates that a number is of a minimum and/or maximum value, inclusive.
    This will work with any comparable number type, such as floats and
    decimals, not just integers.

    :param min:
    The minimum required value of the number. If not provided, minimum
    value will not be checked.
    :param max:
    The maximum value of the number. If not provided, maximum value
    will not be checked.
    """

    OUT_OF_RANGE = 'outOfRange'

    error_messages = {
        OUT_OF_RANGE: "'$value' is out of range ($min, $max)",
    }

    def __init__(self, min=None, max=None, *args, **kwargs):
        super(NumberRange, self).__init__(*args, **kwargs)
        self.min = min
        self.max = max

        self.message_values.update({"min": self.min, "max": self.max})

    def _internal_is_valid(self, value, *args, **kwargs):
        if value is None or (self.min is not None and value < self.min) or \
                (self.max is not None and value > self.max):
            self.error(self.OUT_OF_RANGE, value)
            return False
        return True


class Regexp(BaseValidator):
    """
    Validates the field against a user provided regexp.

    :param regex:
    The regular expression string to use. Can also be a compiled regular
    expression pattern.
    :param flags:
    The regexp flags to use, for example re.IGNORECASE. Ignored if
    `regex` is not a string.
    """

    NOT_MATCH = "notMatch"

    error_messages = {
        NOT_MATCH: "'$value' does not match against pattern '$regex'",
    }

    def __init__(self, regex, flags=0, *args, **kwargs):
        super(Regexp, self).__init__(*args, **kwargs)
        if isinstance(regex, str):
            regex = re.compile(regex, flags)
        self.regex = regex

        self.message_values.update({"regex": self.regex.pattern})

    def _internal_is_valid(self, value, *args, **kwargs):
        try:
            if not self.regex.match(value or ''):
                self.error(self.NOT_MATCH, value)
                return False
            return True
        except TypeError:
            self.error(self.NOT_MATCH, value)


class Email(Regexp):
    """
    Validates an email address. Note that this uses a very primitive regular
    expression and should only be used in instances where you later verify by
    other means, such as email activation or lookups.
    """

    NOT_MAIL = "notMail"
    error_code_map = {Regexp.NOT_MATCH: NOT_MAIL}
    error_messages = {NOT_MAIL: "'$value' is not a valid email address."}

    def __init__(self, *args, **kwargs):
        super(Email, self).__init__(r'^.+@[^.].*\.[a-z]{2,10}$', re.IGNORECASE, *args, **kwargs)


class IPAddress(BaseValidator):
    """
    Validates an IP address.

    :param ipv4:
    If True, accept IPv4 addresses as valid (default True)
    :param ipv6:
    If True, accept IPv6 addresses as valid (default False)
    """

    NOT_IP_ADDRESS = 'notIdAddress'
    IPV4_NOT_ALLOWED = 'ipv4NotAllowed'
    IPV6_NOT_ALLOWED = 'ipv6NotAllowed'

    error_messages = {
        NOT_IP_ADDRESS: "'$value' does not appear to be a valid IP address. Allowed $types",
        IPV4_NOT_ALLOWED: "'$value' is an ipv4 address that is not allowed. Allowed $types",
        IPV6_NOT_ALLOWED: "'$value' is an ipv6 address that is not allowed. Allowed $types",
    }

    def __init__(self, ipv4=True, ipv6=False, *args, **kwargs):
        super(IPAddress, self).__init__(*args, **kwargs)
        if not ipv4 and not ipv6:
            raise ValueError('IP Address Validator must have at least one of ipv4 or ipv6 enabled.')
        self.ipv4 = ipv4
        self.ipv6 = ipv6

        self.message_values.update({'types': ' and '.join([x for x in ('ipv4', 'ipv6') if getattr(self, x)])})

    def _internal_is_valid(self, value, *args, **kwargs):
        if self.check_ipv4(value):
            if not self.ipv4:
                self.error(self.IPV4_NOT_ALLOWED, value)
                return False
            return True

        if self.check_ipv6(value):
            if not self.ipv6:
                self.error(self.IPV6_NOT_ALLOWED, value)
                return False
            return True

        self.error(self.NOT_IP_ADDRESS, value)
        return False

    def check_ipv4(self, value):
        try:
            parts = value.split('.')
        except AttributeError:
            return False

        if len(parts) == 4 and all(x.isdigit() for x in parts):
            numbers = list(int(x) for x in parts)
            return all(num >= 0 and num < 256 for num in numbers)
        return False

    def check_ipv6(self, value):
        try:
            parts = value.split(':')
        except AttributeError:
            return False

        if not 2 <= len(parts) <= 8:
            return False

        num_blank = 0
        for part in parts:
            if not part:
                num_blank += 1
            else:
                try:
                    value = int(part, 16)
                except ValueError:
                    return False
                else:
                    if value < 0 or value >= 65536:
                        return False

        if num_blank < 2:
            return True
        elif num_blank == 2 and not parts[0] and not parts[1]:
            return True
        return False


class MacAddress(Regexp):
    """
    Validates a MAC address.
    """
    INVALID_MAC_ADDRESS = 'invalidMacAddress'
    error_code_map = {Regexp.NOT_MATCH: INVALID_MAC_ADDRESS}
    error_messages = {INVALID_MAC_ADDRESS: "'$value' is not a valid mac address."}

    def __init__(self, *args, **kwargs):
        pattern = r'^(?:[0-9a-fA-F]{2}:){5}[0-9a-fA-F]{2}$'
        super(MacAddress, self).__init__(pattern, *args, **kwargs)


class URL(Regexp):
    """
    Simple regexp based url validation. Much like the email validator, you
    probably want to validate the url later by other means if the url must
    resolve.

    :param require_tld:
    If true, then the domain-name portion of the URL must contain a .tld
    suffix. Set this to false if you want to allow domains like
    `localhost`.
    """

    INVALID_URL = 'invalidUrl'

    error_code_map = {Regexp.NOT_MATCH: INVALID_URL}
    error_messages = {INVALID_URL: "'$value' is not a valid url."}

    def __init__(self, require_tld=True, *args, **kwargs):
        tld_part = (require_tld and r'\.[a-z]{2,10}' or '')
        regex = r'^[a-z]+://([^/:]+%s|([0-9]{1,3}\.){3}[0-9]{1,3})(:[0-9]+)?(\/.*)?$' % tld_part
        super(URL, self).__init__(regex, re.IGNORECASE, *args, **kwargs)


class UUID(Regexp):
    """
    Validates a UUID.
    """
    INVALID_UUID = 'invalidUuid'

    error_code_map = {Regexp.NOT_MATCH: INVALID_UUID}
    error_messages = {INVALID_UUID: "'$value' is not a valid UUID."}

    def __init__(self, *args, **kwargs):
        pattern = r'^[0-9a-fA-F]{8}-([0-9a-fA-F]{4}-){3}[0-9a-fA-F]{12}$'
        super(UUID, self).__init__(pattern, *args, **kwargs)


class AnyOf(BaseValidator):
    """
    Compares the incoming data to a sequence of valid inputs.

    :param values:
    A sequence of valid inputs.
    :param values_formatter:
    Function used to format the list of values in the error message.
    """
    NOT_IN_LIST = 'notInList'

    error_messages = {NOT_IN_LIST: "'$value' is none of $values."}

    def __init__(self, values, values_formatter=None, *args, **kwargs):
        super(AnyOf, self).__init__(*args, **kwargs)
        self.values = values
        if values_formatter is None:
            values_formatter = self.default_values_formatter
        self.values_formatter = values_formatter

    def _internal_is_valid(self, value, *args, **kwargs):
        if value not in self.values:
            self.error(self.NOT_IN_LIST, value, values=self.values_formatter(self.values))
            return False
        return True

    @staticmethod
    def default_values_formatter(values):
        return ', '.join(str(x) if not isinstance(x, str) else "'%s'" % x for x in values)


class NoneOf(BaseValidator):
    """
    Compares the incoming data to a sequence of invalid inputs.

    :param values:
    A sequence of invalid inputs.
    :param values_formatter:
    Function used to format the list of values in the error message.
    """

    IN_LIST = 'inList'

    error_messages = {IN_LIST: "'$value' is one of $values."}

    def __init__(self, values, values_formatter=None, *args, **kwargs):
        super(NoneOf, self).__init__(*args, **kwargs)
        self.values = values
        if values_formatter is None:
            def values_formatter(v): return ', '.join(str(x) if not isinstance(x, str) else "'%s'" % x for x in values)
        self.values_formatter = values_formatter

    def _internal_is_valid(self, value, *args, **kwargs):
        if value in self.values:
            self.error(self.IN_LIST, value, values=self.values_formatter(self.values))
            return False
        return True


class IsEmpty(BaseValidator):
    """
    Compares the incoming value with an empty one
    """
    EMPTY = 'Empty'

    error_messages = {EMPTY: "'$value' must be empty"}

    def _internal_is_valid(self, value, *args, **kwargs):
        if value:
            self.error(self.EMPTY, value)
            return False
        return True


class NotEmpty(BaseValidator):
    """
    Raise error when it is empty
    """
    NOT_EMPTY = 'notEmpty'

    error_messages = {NOT_EMPTY: "Value can not be empty"}

    def _internal_is_valid(self, value, *args, **kwargs):
        if not value:
            self.error(self.NOT_EMPTY, value)
            return False
        return True


class NotEmptyString(NotEmpty):
    """
    Raise error when it is empty
    """
    NOT_EMPTY = 'notEmpty'
    NOT_STRING = 'notString'

    error_messages = {
        NOT_EMPTY: "Value can not be empty",
        NOT_STRING: "Value must be a string"
    }

    def _internal_is_valid(self, value, *args, **kwargs):
        if not isinstance(value, str):
            self.error(self.NOT_STRING, value)
            return False

        return super(NotEmptyString, self)._internal_is_valid(value.strip(), args, kwargs)


class IsNone(BaseValidator):
    """
    Raise error if it is not None
    """

    NONE = 'None'

    error_messages = {NONE: "'$value' must be None"}

    def _internal_is_valid(self, value, *args, **kwargs):
        if value is not None:
            self.error(self.NONE, value)
            return False
        return True


class NotNone(BaseValidator):
    """
    Raise error if it is None
    """

    NOT_NONE = 'notNone'

    error_messages = {NOT_NONE: "Value must not be None"}

    def _internal_is_valid(self, value, *args, **kwargs):
        if value is None:
            self.error(self.NOT_NONE, value)
            return False
        return True
