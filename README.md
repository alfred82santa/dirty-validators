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
- Specific error control messages.
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
    from dirty_validators.complex import Optional

    validator = Optional(validators=[EqualTo(comp_value="test")])

    assert validator.is_valid("test") is True

    # Chained validation
    validator_chain = Chain(validators=[Length(min=14, max=16), Regexp(regex='^abc'), Email()])

    assert validator_chain.is_valid('abcdefg@test.com')

.. note::
    Look at tests for more examples


