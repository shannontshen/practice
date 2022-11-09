# NOTE: Numpy's mypy plugin is used for importing the correct
# platform-specific `ctypes._SimpleCData[int]` sub-type
import ctypes
import os
import sys
from collections.abc import Iterable, Sequence
from ctypes import c_int64 as _c_intp
from typing import Any, ClassVar, Generic
from typing import Literal as L
from typing import TypeVar, Union, overload

from numpy import (bool_, byte, double, dtype, generic, int_, intc, longdouble,
                   longlong, ndarray, short, single, ubyte, uint, uintc,
                   ulonglong, ushort, void)
from numpy._typing import (DTypeLike, NDArray,  # Arrays; Shapes; DTypes
                           _ArrayLike, _BoolCodes, _ByteCodes, _DoubleCodes,
                           _DTypeLike, _IntCCodes, _IntCodes, _LongDoubleCodes,
                           _LongLongCodes, _ShapeLike, _ShortCodes,
                           _SingleCodes, _UByteCodes, _UIntCCodes, _UIntCodes,
                           _ULongLongCodes, _UShortCodes, _VoidDTypeLike)
from numpy.core._internal import _ctypes
from numpy.core.multiarray import flagsobj

# TODO: Add a proper `_Shape` bound once we've got variadic typevars
_DType = TypeVar("_DType", bound=dtype[Any])
_DTypeOptional = TypeVar("_DTypeOptional", bound=None | dtype[Any])
_SCT = TypeVar("_SCT", bound=generic)

_FlagsKind = L[
    'C_CONTIGUOUS', 'CONTIGUOUS', 'C',
    'F_CONTIGUOUS', 'FORTRAN', 'F',
    'ALIGNED', 'A',
    'WRITEABLE', 'W',
    'OWNDATA', 'O',
    'WRITEBACKIFCOPY', 'X',
]

# TODO: Add a shape typevar once we have variadic typevars (PEP 646)
class _ndptr(ctypes.c_void_p, Generic[_DTypeOptional]):
    # In practice these 4 classvars are defined in the dynamic class
    # returned by `ndpointer`
    _dtype_: ClassVar[_DTypeOptional]
    _shape_: ClassVar[None]
    _ndim_: ClassVar[None | int]
    _flags_: ClassVar[None | list[_FlagsKind]]

    @overload
    @classmethod
    def from_param(cls: type[_ndptr[None]], obj: ndarray[Any, Any]) -> _ctypes: ...
    @overload
    @classmethod
    def from_param(cls: type[_ndptr[_DType]], obj: ndarray[Any, _DType]) -> _ctypes: ...

class _concrete_ndptr(_ndptr[_DType]):
    _dtype_: ClassVar[_DType]
    _shape_: ClassVar[tuple[int, ...]]
    @property
    def contents(self) -> ndarray[Any, _DType]: ...

def load_library(
    libname: str | bytes | os.PathLike[str] | os.PathLike[bytes],
    loader_path: str | bytes | os.PathLike[str] | os.PathLike[bytes],
) -> ctypes.CDLL: ...

__all__: list[str]

c_intp = _c_intp

@overload
def ndpointer(
    dtype: None = ...,
    ndim: int = ...,
    shape: None | _ShapeLike = ...,
    flags: None | _FlagsKind | Iterable[_FlagsKind] | int | flagsobj = ...,
) -> type[_ndptr[None]]: ...
@overload
def ndpointer(
    dtype: _DTypeLike[_SCT],
    ndim: int = ...,
    *,
    shape: _ShapeLike,
    flags: None | _FlagsKind | Iterable[_FlagsKind] | int | flagsobj = ...,
) -> type[_concrete_ndptr[dtype[_SCT]]]: ...
@overload
def ndpointer(
    dtype: DTypeLike,
    ndim: int = ...,
    *,
    shape: _ShapeLike,
    flags: None | _FlagsKind | Iterable[_FlagsKind] | int | flagsobj = ...,
) -> type[_concrete_ndptr[dtype[Any]]]: ...
@overload
def ndpointer(
    dtype: _DTypeLike[_SCT],
    ndim: int = ...,
    shape: None = ...,
    flags: None | _FlagsKind | Iterable[_FlagsKind] | int | flagsobj = ...,
) -> type[_ndptr[dtype[_SCT]]]: ...
@overload
def ndpointer(
    dtype: DTypeLike,
    ndim: int = ...,
    shape: None = ...,
    flags: None | _FlagsKind | Iterable[_FlagsKind] | int | flagsobj = ...,
) -> type[_ndptr[dtype[Any]]]: ...

@overload
def as_ctypes_type(dtype: _BoolCodes | _DTypeLike[bool_] | type[ctypes.c_bool]) -> type[ctypes.c_bool]: ...
@overload
def as_ctypes_type(dtype: _ByteCodes | _DTypeLike[byte] | type[ctypes.c_byte]) -> type[ctypes.c_byte]: ...
@overload
def as_ctypes_type(dtype: _ShortCodes | _DTypeLike[short] | type[ctypes.c_short]) -> type[ctypes.c_short]: ...
@overload
def as_ctypes_type(dtype: _IntCCodes | _DTypeLike[intc] | type[ctypes.c_int]) -> type[ctypes.c_int]: ...
@overload
def as_ctypes_type(dtype: _IntCodes | _DTypeLike[int_] | type[int | ctypes.c_long]) -> type[ctypes.c_long]: ...
@overload
def as_ctypes_type(dtype: _LongLongCodes | _DTypeLike[longlong] | type[ctypes.c_longlong]) -> type[ctypes.c_longlong]: ...
@overload
def as_ctypes_type(dtype: _UByteCodes | _DTypeLike[ubyte] | type[ctypes.c_ubyte]) -> type[ctypes.c_ubyte]: ...
@overload
def as_ctypes_type(dtype: _UShortCodes | _DTypeLike[ushort] | type[ctypes.c_ushort]) -> type[ctypes.c_ushort]: ...
@overload
def as_ctypes_type(dtype: _UIntCCodes | _DTypeLike[uintc] | type[ctypes.c_uint]) -> type[ctypes.c_uint]: ...
@overload
def as_ctypes_type(dtype: _UIntCodes | _DTypeLike[uint] | type[ctypes.c_ulong]) -> type[ctypes.c_ulong]: ...
@overload
def as_ctypes_type(dtype: _ULongLongCodes | _DTypeLike[ulonglong] | type[ctypes.c_ulonglong]) -> type[ctypes.c_ulonglong]: ...
@overload
def as_ctypes_type(dtype: _SingleCodes | _DTypeLike[single] | type[ctypes.c_float]) -> type[ctypes.c_float]: ...
@overload
def as_ctypes_type(dtype: _DoubleCodes | _DTypeLike[double] | type[float | ctypes.c_double]) -> type[ctypes.c_double]: ...
@overload
def as_ctypes_type(dtype: _LongDoubleCodes | _DTypeLike[longdouble] | type[ctypes.c_longdouble]) -> type[ctypes.c_longdouble]: ...
@overload
def as_ctypes_type(dtype: _VoidDTypeLike) -> type[Any]: ...  # `ctypes.Union` or `ctypes.Structure`
@overload
def as_ctypes_type(dtype: str) -> type[Any]: ...

@overload
def as_array(obj: ctypes._PointerLike, shape: Sequence[int]) -> NDArray[Any]: ...
@overload
def as_array(obj: _ArrayLike[_SCT], shape: None | _ShapeLike = ...) -> NDArray[_SCT]: ...
@overload
def as_array(obj: object, shape: None | _ShapeLike = ...) -> NDArray[Any]: ...

@overload
def as_ctypes(obj: bool_) -> ctypes.c_bool: ...
@overload
def as_ctypes(obj: byte) -> ctypes.c_byte: ...
@overload
def as_ctypes(obj: short) -> ctypes.c_short: ...
@overload
def as_ctypes(obj: intc) -> ctypes.c_int: ...
@overload
def as_ctypes(obj: int_) -> ctypes.c_long: ...
@overload
def as_ctypes(obj: longlong) -> ctypes.c_longlong: ...
@overload
def as_ctypes(obj: ubyte) -> ctypes.c_ubyte: ...
@overload
def as_ctypes(obj: ushort) -> ctypes.c_ushort: ...
@overload
def as_ctypes(obj: uintc) -> ctypes.c_uint: ...
@overload
def as_ctypes(obj: uint) -> ctypes.c_ulong: ...
@overload
def as_ctypes(obj: ulonglong) -> ctypes.c_ulonglong: ...
@overload
def as_ctypes(obj: single) -> ctypes.c_float: ...
@overload
def as_ctypes(obj: double) -> ctypes.c_double: ...
@overload
def as_ctypes(obj: longdouble) -> ctypes.c_longdouble: ...
@overload
def as_ctypes(obj: void) -> Any: ...  # `ctypes.Union` or `ctypes.Structure`
@overload
def as_ctypes(obj: NDArray[bool_]) -> ctypes.Array[ctypes.c_bool]: ...
@overload
def as_ctypes(obj: NDArray[byte]) -> ctypes.Array[ctypes.c_byte]: ...
@overload
def as_ctypes(obj: NDArray[short]) -> ctypes.Array[ctypes.c_short]: ...
@overload
def as_ctypes(obj: NDArray[intc]) -> ctypes.Array[ctypes.c_int]: ...
@overload
def as_ctypes(obj: NDArray[int_]) -> ctypes.Array[ctypes.c_long]: ...
@overload
def as_ctypes(obj: NDArray[longlong]) -> ctypes.Array[ctypes.c_longlong]: ...
@overload
def as_ctypes(obj: NDArray[ubyte]) -> ctypes.Array[ctypes.c_ubyte]: ...
@overload
def as_ctypes(obj: NDArray[ushort]) -> ctypes.Array[ctypes.c_ushort]: ...
@overload
def as_ctypes(obj: NDArray[uintc]) -> ctypes.Array[ctypes.c_uint]: ...
@overload
def as_ctypes(obj: NDArray[uint]) -> ctypes.Array[ctypes.c_ulong]: ...
@overload
def as_ctypes(obj: NDArray[ulonglong]) -> ctypes.Array[ctypes.c_ulonglong]: ...
@overload
def as_ctypes(obj: NDArray[single]) -> ctypes.Array[ctypes.c_float]: ...
@overload
def as_ctypes(obj: NDArray[double]) -> ctypes.Array[ctypes.c_double]: ...
@overload
def as_ctypes(obj: NDArray[longdouble]) -> ctypes.Array[ctypes.c_longdouble]: ...
@overload
def as_ctypes(obj: NDArray[void]) -> ctypes.Array[Any]: ...  # `ctypes.Union` or `ctypes.Structure`
