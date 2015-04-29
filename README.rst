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


