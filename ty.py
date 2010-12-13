#!/usr/bin/env python
# -*- coding: UTF-8 -*-

"""
TY.PY
************************************

This module allows you to quickly implement the full-fledged
type-checking in your functions!
"""

# Lack of callable() in Python 3

try:
    callable(lambda x: x)
except NameError:
    def callable(obj):
        return hasattr(obj, "__call__")

#
# EXCEPTIONS
# Defined here are exceptions raised whenever the
# type-checking fails (incorrect input or output
# values are detected).
#

class TypeCheckError(TypeError):

    """
    Base exception for errors raised whenever
    types defined and types used are mismatched.
    """

    def __init__(self, var_name, var_value, expected):
        self._var_name = var_name
        self._var_value = var_value
        self._expected = expected

    @property
    def name(self):
        "Name of the element that failed the type check."
        return self._var_name

    @property
    def value(self):
        "Value of the element that failed the type check."
        return self._var_value

    @property
    def expected(self):
        "Test (type, class, callable) that the element failed."
        return self._expected

    def repr(self):
        return "TypeCheckError({0}, {1}, {2})".format(
            repr(self._var_name),
            repr(self._var_value),
            self._expected.__name__
        )

    def str(self):
        return "'{0}' has failed the type check. " + \
               "Value {1} did not satisty the type-check " + \
               "condition {2}".format(
                    repr(self._var_name),
                    repr(self._var_value),
                    self._expected.__name__
                )

class InputTypeCheckError(TypeCheckError):

    """
    Type-checking exception raised when
    there's problem with provided arguments.
    """
    
    def __init__(self, var_name, var_value, expected):

        # If name of the faulty arg is "return",
        # that means output instead of input. Raise
        # error and inform user about using proper
        # exception types.

        if var_name == "return":
            raise TypeError("Input exception used on output. For output, use OutputTypeCheckError.")
        super().__init__(var_name, var_value, expected)

class OutputTypeCheckError(TypeCheckError):

    """
    Type-checking exception raised when
    there's problem with the output value.
    """

    def __init__(self, var_value, expected):
        super().__init__("return", var_value, expected)

#
# MAIN FUNCTIONS
# The main functionality of the module.
# Contains typecheck() decorator used to add type-checking
# functionality with help of annotations.
#

def _check(subject, test):

    """
    Check whether the subject passes the type-check
    of provided sort. The value returned is True if
    subject has passed the test, False otherwise.

    If test is a type or class (either built-in or
    custom), _check() returns True if subject is an
    instance of that type or class:
    >>> _check(15, int)
    True
    >>> _check("foo", str)
    True
    >>> _check([1, 2, 3], dict)
    False
    >>> from collections import OrderedDict
    >>> _check(OrderedDict([('pear', 1), ('apple', 4), ('orange', 2), ('banana', 3)]), dict)
    True

    Else, if test is a callable object (function,
    method or class with __call__() defined), it will
    be executed with one argument only and the boolean
    result will be used:
    >>> is_even = lambda x: (x + 1) % 2
    >>> _check(24, is_even)
    True
    >>> _check(27, is_even)
    False

    For all other values, True is always returned:
    >>> _check("foo", "bar")
    True
    >>> _check(15, 12.5)
    True
    >>> _check(["spam", "spam", "bacon", "spam"], None)
    True
    """

    # Type / class check
    if type(test) == type:
        return isinstance(subject, test)

    # Callable check
    elif callable(test):
        return bool(test(subject))

    # For everything else (like actual annotations), just let it pass
    else:
        return True

def typecheck(f):

    """
    Implement type-checking through the annotations.
    To implement the type-checking, specify enforced types / classes / functions
    as annotations, then decorate it with typecheck():

    >>> @typecheck
    ... def test_sum(firstarg:int, secondarg:int) -> float:
    ...     return (firstarg + secondarg) * 1.0

    Such notation would mean that test_sum() requires
    first argument as integer, second argument as integer and
    the return value as float:

    >>> test_sum(1, 3)
    4.0
    >>> test_sum(4, 6)
    10.0
    >>> test_sum(2.5, 2.5)
    Traceback (most recent call last):
        ...
    InputTypeCheckError

    In addition to types and classes, callables can be used
    in annotations. Such callable should be able to take just
    one argument. If the callable returns False, an exception
    is raised:

    >>> @typecheck
    ... def test_sum_2(firstarg:int, secondarg:int) -> lambda x: (x + 1) % 2:
    ...     return (firstarg + secondarg)
    >>> test_sum_2(4, 6)
    10
    >>> test_sum_2(4, 7)
    Traceback (most recent call last):
        ...
    OutputTypeCheckError
    """

    # If no annotations are specified, do not decorate function
    if not hasattr(f, "__annotations__"):
        return f

    from inspect import getfullargspec
    from itertools import chain
    from functools import wraps

    argspec = getfullargspec(f)

    @wraps(f)
    def wrapper(*args, **kwargs):

        # First, attempt to type-check all positional arguments
        for name, value in zip(argspec.args, args):

            if name in argspec.annotations:
                result = _check(value, argspec.annotations[name])
                if not result:
                    raise InputTypeCheckError(name, value, argspec.annotations[name])

        # Then, test the keyword arguments
        for name, value in kwargs:

            if name in argspec.annotations:
                result = _check(value, argspec.annotations[name])
                if not result:
                    raise InputTypeCheckError(name, value, argspec.annotations[name])

        # Input arguments have passed, execute function
        output = f(*args, **kwargs)

        # Test output
        if "return" in argspec.annotations:
            result = _check(output, argspec.annotations["return"])
            if not result:
                raise OutputTypeCheckError(value, argspec.annotations[name])

        return output

    return wrapper

#
# Doctest
#
if __name__ == "__main__":
    import doctest
    doctest.testmod()
