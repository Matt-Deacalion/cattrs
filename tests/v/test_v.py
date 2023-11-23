"""Tests for the cattrs.v framework."""
from typing import (
    Dict,
    List,
    MutableMapping,
    MutableSequence,
    Optional,
    Sequence,
    Tuple,
)

from attrs import Factory, define
from pytest import raises

from cattrs import Converter, IterableValidationError, transform_error
from cattrs._compat import Mapping, TypedDict
from cattrs.gen import make_dict_structure_fn
from cattrs.v import format_exception


def test_attribute_errors(c: Converter) -> None:
    @define
    class C:
        a: int
        b: int = 0

    try:
        c.structure({}, C)
    except Exception as exc:
        assert transform_error(exc) == ["required field missing @ $.a"]

    try:
        c.structure({"a": 1, "b": "str"}, C)
    except Exception as exc:
        assert transform_error(exc) == [
            "invalid value for type, expected int (invalid literal for int() with base 10: 'str') @ $.b"
        ]

    @define
    class D:
        c: C

    try:
        c.structure({}, D)
    except Exception as exc:
        assert transform_error(exc) == ["required field missing @ $.c"]

    try:
        c.structure({"c": {}}, D)
    except Exception as exc:
        assert transform_error(exc) == ["required field missing @ $.c.a"]

    try:
        c.structure({"c": 1}, D)
    except Exception as exc:
        assert transform_error(exc) == ["invalid value for type, expected C @ $.c"]

    try:
        c.structure({"c": {"a": "str"}}, D)
    except Exception as exc:
        assert transform_error(exc) == [
            "invalid value for type, expected int (invalid literal for int() with base 10: 'str') @ $.c.a"
        ]

    @define
    class E:
        a: Optional[int]

    with raises(Exception) as exc:
        c.structure({"a": "str"}, E)

    # Complicated due to various Python versions.
    tn = (
        Optional[int].__name__
        if hasattr(Optional[int], "__name__")
        else repr(Optional[int])
    )
    assert transform_error(exc.value) == [
        f"invalid value for type, expected {tn} (invalid literal for int() with base 10: 'str') @ $.a"
    ]


def test_class_errors(c: Converter) -> None:
    """Errors not directly related to attributes are parsed correctly."""

    @define
    class C:
        a: int
        b: int = 0

    c.register_structure_hook(
        C, make_dict_structure_fn(C, c, _cattrs_forbid_extra_keys=True)
    )

    try:
        c.structure({"d": 1}, C)
    except Exception as exc:
        assert transform_error(exc) == [
            "required field missing @ $.a",
            "extra fields found (d) @ $",
        ]


def test_sequence_errors(c: Converter) -> None:
    try:
        c.structure(["str", 1, "str"], List[int])
    except Exception as exc:
        assert transform_error(exc) == [
            "invalid value for type, expected int (invalid literal for int() with base 10: 'str') @ $[0]",
            "invalid value for type, expected int (invalid literal for int() with base 10: 'str') @ $[2]",
        ]

    try:
        c.structure(1, List[int])
    except Exception as exc:
        assert transform_error(exc) == [
            "invalid value for type, expected an iterable @ $"
        ]

    try:
        c.structure(["str", 1, "str"], Tuple[int, ...])
    except Exception as exc:
        assert transform_error(exc) == [
            "invalid value for type, expected int (invalid literal for int() with base 10: 'str') @ $[0]",
            "invalid value for type, expected int (invalid literal for int() with base 10: 'str') @ $[2]",
        ]

    try:
        c.structure(["str", 1, "str"], Sequence[int])
    except Exception as exc:
        assert transform_error(exc) == [
            "invalid value for type, expected int (invalid literal for int() with base 10: 'str') @ $[0]",
            "invalid value for type, expected int (invalid literal for int() with base 10: 'str') @ $[2]",
        ]

    try:
        c.structure(["str", 1, "str"], MutableSequence[int])
    except Exception as exc:
        assert transform_error(exc) == [
            "invalid value for type, expected int (invalid literal for int() with base 10: 'str') @ $[0]",
            "invalid value for type, expected int (invalid literal for int() with base 10: 'str') @ $[2]",
        ]

    @define
    class C:
        a: List[int]
        b: List[List[int]] = Factory(list)

    try:
        c.structure({"a": ["str", 1, "str"]}, C)
    except Exception as exc:
        assert transform_error(exc) == [
            "invalid value for type, expected int (invalid literal for int() with base 10: 'str') @ $.a[0]",
            "invalid value for type, expected int (invalid literal for int() with base 10: 'str') @ $.a[2]",
        ]

    try:
        c.structure({"a": [], "b": [[], ["str", 1, "str"]]}, C)
    except Exception as exc:
        assert transform_error(exc) == [
            "invalid value for type, expected int (invalid literal for int() with base 10: 'str') @ $.b[1][0]",
            "invalid value for type, expected int (invalid literal for int() with base 10: 'str') @ $.b[1][2]",
        ]


def test_mapping_errors(c: Converter) -> None:
    try:
        c.structure({"a": 1, "b": "str"}, Dict[str, int])
    except Exception as exc:
        assert transform_error(exc) == [
            "invalid value for type, expected int (invalid literal for int() with base 10: 'str') @ $['b']"
        ]

    @define
    class C:
        a: Dict[str, int]

    try:
        c.structure({"a": {"a": "str", "b": 1, "c": "str"}}, C)
    except Exception as exc:
        assert transform_error(exc) == [
            "invalid value for type, expected int (invalid literal for int() with base 10: 'str') @ $.a['a']",
            "invalid value for type, expected int (invalid literal for int() with base 10: 'str') @ $.a['c']",
        ]

    try:
        c.structure({"a": 1}, C)
    except Exception as exc:
        assert transform_error(exc) == ["expected a mapping @ $.a"]

    try:
        c.structure({"a": 1, "b": "str"}, Mapping[str, int])
    except Exception as exc:
        assert transform_error(exc) == [
            "invalid value for type, expected int (invalid literal for int() with base 10: 'str') @ $['b']"
        ]

    try:
        c.structure({"a": 1, "b": "str"}, MutableMapping[str, int])
    except Exception as exc:
        assert transform_error(exc) == [
            "invalid value for type, expected int (invalid literal for int() with base 10: 'str') @ $['b']"
        ]

    try:
        c.structure({"a": 1, 2: "str"}, MutableMapping[int, int])
    except Exception as exc:
        assert transform_error(exc) == [
            "invalid value for type, expected int (invalid literal for int() with base 10: 'a') @ $['a']",
            "invalid value for type, expected int (invalid literal for int() with base 10: 'str') @ $[2]",
        ]


def test_custom_error_fn(c: Converter) -> None:
    def my_format(exc, type):
        if isinstance(exc, KeyError):
            return "no key"
        return format_exception(exc, type)

    @define
    class C:
        a: int
        b: int = 1

    try:
        c.structure({"b": "str"}, C)
    except Exception as exc:
        assert transform_error(exc, format_exception=my_format) == [
            "no key @ $.a",
            "invalid value for type, expected int (invalid literal for int() with base 10: 'str') @ $.b",
        ]


def test_custom_error_fn_nested(c: Converter) -> None:
    def my_format(exc, type):
        if isinstance(exc, TypeError):
            return "Must be correct type"
        return format_exception(exc, type)

    @define
    class C:
        a: Dict[str, int]

    try:
        c.structure({"a": {"a": "str", "b": 1, "c": None}}, C)
    except Exception as exc:
        assert transform_error(exc, format_exception=my_format) == [
            "invalid value for type, expected int (invalid literal for int() with base 10: 'str') @ $.a['a']",
            "Must be correct type @ $.a['c']",
        ]


def test_typeddict_attribute_errors(c: Converter) -> None:
    """TypedDict errors are correctly generated."""

    class C(TypedDict):
        a: int
        b: int

    try:
        c.structure({}, C)
    except Exception as exc:
        assert transform_error(exc) == [
            "required field missing @ $.a",
            "required field missing @ $.b",
        ]

    try:
        c.structure({"b": 1}, C)
    except Exception as exc:
        assert transform_error(exc) == ["required field missing @ $.a"]

    try:
        c.structure({"a": 1, "b": "str"}, C)
    except Exception as exc:
        assert transform_error(exc) == [
            "invalid value for type, expected int (invalid literal for int() with base 10: 'str') @ $.b"
        ]

    class D(TypedDict):
        c: C

    try:
        c.structure({}, D)
    except Exception as exc:
        assert transform_error(exc) == ["required field missing @ $.c"]

    try:
        c.structure({"c": {}}, D)
    except Exception as exc:
        assert transform_error(exc) == [
            "required field missing @ $.c.a",
            "required field missing @ $.c.b",
        ]

    try:
        c.structure({"c": 1}, D)
    except Exception as exc:
        assert transform_error(exc) == ["expected a mapping @ $.c"]

    try:
        c.structure({"c": {"a": "str"}}, D)
    except Exception as exc:
        assert transform_error(exc) == [
            "invalid value for type, expected int (invalid literal for int() with base 10: 'str') @ $.c.a",
            "required field missing @ $.c.b",
        ]

    class E(TypedDict):
        a: Optional[int]

    with raises(Exception) as exc:
        c.structure({"a": "str"}, E)

    # Complicated due to various Python versions.
    tn = (
        Optional[int].__name__
        if hasattr(Optional[int], "__name__")
        else repr(Optional[int])
    )
    assert transform_error(exc.value) == [
        f"invalid value for type, expected {tn} (invalid literal for int() with base 10: 'str') @ $.a"
    ]


def test_iterable_val_no_note():
    """`IterableValidationErrors` require subexceptions with notes."""
    with raises(AttributeError):
        IterableValidationError("Test", [RuntimeError()], List[str]).group_exceptions()

    r = RuntimeError()
    r.__notes__ = ["test"]
    with raises(AttributeError):
        IterableValidationError("Test", [r], List[str]).group_exceptions()


def test_typeerror_formatting():
    """`format_exception` works with non-iteration TypeErrors."""
    exc = TypeError("exception")
    assert format_exception(exc, None) == "invalid type (exception)"


def test_other_formatting():
    """`format_exception` handles unsupported errors."""
    assert format_exception(RuntimeError("test"), None) == "unknown error (test)"
