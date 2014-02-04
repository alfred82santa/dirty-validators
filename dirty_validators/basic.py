"""
Validators library
"""
from string import Template
import re


class BaseValidator:
    error_code_map = {}
    error_messages = {}

    message_values = {}

    def __init__(self, error_code_map=None, error_messages=None,
                 message_values=None, *args, **kwargs):

        self.error_code_map = {key: new_key for key, new_key in self.error_code_map.items()}
        if error_code_map:
            self.error_code_map = error_code_map

        self.error_messages = {key: message for key, message in self.error_messages.items()}
        if error_messages:
            self.error_messages.update(error_messages)

        self.message_values = {placeholder: value for placeholder, value in self.message_values.items()}
        if message_values:
            self.message_values.update(message_values)

        self.messages = {}

    def error(self, error_code, value, **kwargs):
        try:
            code = self.error_code_map[error_code]
        except KeyError:
            code = error_code

        try:
            message = Template(self.error_messages[code])
        except KeyError:
            message = Template(self.error_messages[error_code])

        message = Template(message.safe_substitute(value=value))
        message = Template(message.safe_substitute(**kwargs))

        self.messages[code] = message.safe_substitute(self.message_values)

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
    Check whether a value is distinct of static value.
    """
    IS_EQUAL = 'isEqual'

    error_messages = {IS_EQUAL: "'$value' is equal to '$comp_value'"}

    def __init__(self, comp_value=None, *args, **kwargs):
        super(NotEqualTo, self).__init__(*args, **kwargs)
        self.comp_value = comp_value
        self.message_values.update({'comp_value': self.comp_value})

    def _internal_is_valid(self, value, *args, **kwargs):
        if value == self.comp_value:
            self.error(self.IS_EQUAL, value)
            return False
        return True


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

    error_messages = {
        TOO_LONG: "'$value' is more than $max unit length",
        TOO_SHORT: "'$value' is less than $min unit length"
    }

    def __init__(self, min=-1, max=-1, *args, **kwargs):
        super(Length, self).__init__(*args, **kwargs)
        assert min != -1 or max != -1, 'At least one of `min` or `max` must be specified.'
        assert max == -1 or min <= max, '`min` cannot be more than `max`.'
        self.min = min
        self.max = max

        self.message_values.update({"min": self.min, "max": self.max})

    def _internal_is_valid(self, value, *args, **kwargs):
        l = len(value) or 0
        if l < self.min:
            self.error(self.TOO_SHORT, value)
            return False
        if self.max != -1 and l > self.max:
            self.error(self.TOO_LONG, value)
            return False
        return True


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

        types = []
        if self.ipv4:
            types.append('ipv4')

        if self.ipv6:
            types.append('ipv6')

        self.message_values.update({'types': ' and '.join(types)})

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

        if len(parts) > 8:
            return False

        if len(parts) < 2:
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
            values_formatter = lambda v: ', '.join(str(x) if not isinstance(x, str) else "'%s'" % x for x in values)
        self.values_formatter = values_formatter

    def _internal_is_valid(self, value, *args, **kwargs):
        if value in self.values:
            self.error(self.IN_LIST, value, values=self.values_formatter(self.values))
            return False
        return True
