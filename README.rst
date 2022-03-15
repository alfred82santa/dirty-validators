|travis-master| |coverall-master|

.. |travis-master| image:: https://travis-ci.org/alfred82santa/dirty-validators.svg?branch=master
   :target: https://travis-ci.org/alfred82santa/dirty-validators

.. |coverall-master| image:: https://coveralls.io/repos/alfred82santa/dirty-validators/badge.png?branch=master
   :target: https://coveralls.io/r/alfred82santa/dirty-validators?branch=master

================
dirty-validators
================


Agnostic validators for python 3

**Freely based** on [WTF-Forms](https://github.com/wtforms/wtforms) validators.

.. warning::

    Be aware about incompatible changes on `Version 0.6.0`_.

********
Features
********
- Python 3 package.
- Easy to create a validator.
- Chained validations.
- Conditional validations.
- Specific error control messages.
- Dirty model integration (https://github.com/alfred82santa/dirty-models)
- No database dependent.
- Asynchronous validators.
- Stateless validators.
- Deferred validators.

*********
Changelog
*********

-------------
Version 0.6.0
-------------

The stateless refactor. Dirty validators now are full stateless.
It means now there is no messages on validator instance. The ``is_valid`` method returns
a validation context. It is evaluated as ``True`` if there were no errors and false
otherwise. So, it is possible to still to use checks like ``if validator.is_valid(my_data):``
but we recomend to use the Walruf operator (https://peps.python.org/pep-0572/):
``if result := validator.is_valid(my_data):``.
That is important because messages are stored on context.

.. code-block:: python

    # Python +3.8
    if result := validator.is_valid(my_data):
        # some code
    else:
        print(result.error_messages)

    #or

    if not (result := validator.is_valid(my_data)):
        print(result.error_messages)

On the other hand, validation error messages now are an object. It stores error code, error message
template and context values. There is a helper function ``from_context_to_legacy_message`` in order
to convert a context to legacy message format.

- Stateless refactor
- New ``Context`` class stores state of validation process.
- New ``ValidationErrorMessage`` class to store validation error messages.
- New ``Deferred`` validator in order to build validator on runtime depending on context.
- New ``from_context_to_legacy_message`` helper.

-------------
Version 0.5.4
-------------

- Allow model validator inheritance.

-------------
Version 0.5.2
-------------

- Remove hard dependency from Dirty Models.
- Fix bug iterating ListModels.

-------------
Version 0.5.1
-------------

- Added value validators for mappings.

-------------
Version 0.5.0
-------------

- Added asynchronous validators.

-------------
Version 0.4.0
-------------

- Added ``<root>``  keyword in order to look up a field from root model of context.
- Added ``key_validator`` argument for spec validators in order to validate keys on hashmaps.

************
Installation
************
.. code-block:: bash

    $ pip install dirty-validators

***********
Basic usage
***********

.. code-block:: python

    from dirty_validators.basic import EqualTo, Length, Regexp, Email
    from dirty_validators.complex import Optional, ModelValidate

    validator = Optional(validators=[EqualTo(comp_value="test")])

    assert validator.is_valid("test") is True

    # Chained validation
    validator_chain = Chain(validators=[Length(min=14, max=16), Regexp(regex='^abc'), Email()])

    assert validator_chain.is_valid('abcdefg@test.com')

    # Model validation

    class MyModelValidator(ModelValidate):
        fieldName1 = Optional(validators=[Length(min=4, max=6)])
        fieldName2 = Optional(validators=[Length(min=1, max=2)])
        fieldName3 = Required(validators=[Length(min=7, max=8)])

    validator_model = MyModelValidator()

    data = {
        "fieldName1": "1234",
        "fieldName1": "12",
        "fieldName3": "123456qw"
     }

    assert validator_model.is_valid(FakeModel(data)) is True

.. note::

    Look at tests for more examples
