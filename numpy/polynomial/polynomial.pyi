from typing import Any, List

from numpy import ndarray, dtype, int_
from numpy.polynomial._polybase import ABCPolyBase
from numpy.polynomial.polyutils import trimcoef

__all__: list[str]

polytrim = trimcoef

polydomain: ndarray[Any, dtype[int_]]
polyzero: ndarray[Any, dtype[int_]]
polyone: ndarray[Any, dtype[int_]]
polyx: ndarray[Any, dtype[int_]]

def polyline(off, scl): ...
def polyfromroots(roots): ...
def polyadd(c1, c2): ...
def polysub(c1, c2): ...
def polymulx(c): ...
def polymul(c1, c2): ...
def polydiv(c1, c2): ...
def polypow(c, pow, maxpower=...): ...
def polyder(c, m=..., scl=..., axis=...): ...
def polyint(c, m=..., k=..., lbnd=..., scl=..., axis=...): ...
def polyval(x, c, tensor=...): ...
def polyvalfromroots(x, r, tensor=...): ...
def polyval2d(x, y, c): ...
def polygrid2d(x, y, c): ...
def polyval3d(x, y, z, c): ...
def polygrid3d(x, y, z, c): ...
def polyvander(x, deg): ...
def polyvander2d(x, y, deg): ...
def polyvander3d(x, y, z, deg): ...
def polyfit(x, y, deg=..., rcond=..., full=..., w=...): ...
def polyroots(c): ...

class Polynomial(ABCPolyBase):
    domain: Any
    window: Any
    basis_name: Any
