#ifndef _NPY_CORE_SRC_UMATH_HIGHWAY_TRANSFORM_H_
#define _NPY_CORE_SRC_UMATH_HIGHWAY_TRANSFORM_H_

#include "simd/simd.h"
#include <hwy/highway.h>
#include <numpy/npy_common.h>

HWY_BEFORE_NAMESPACE();
namespace hwy {
namespace HWY_NAMESPACE {

// Sets `out[idx]` to `Func(d, in[idx])`
// Useful for math routines.
template <class D, class Func, typename T = TFromD<D>>
HWY_ATTR void
Transform1(D d, const T *HWY_RESTRICT in, const npy_intp in_stride,
           T *HWY_RESTRICT out, const npy_intp out_stride, size_t count,
           const Func &func)
{
    using VI = Vec<RebindToSigned<D>>;
    const RebindToSigned<D> di;

    const size_t lanes = Lanes(d);
    const VI src_index = Mul(Iota(di, 0), Set(di, in_stride));
    const VI dst_index = Mul(Iota(di, 0), Set(di, out_stride));

    Vec<D> v;
    size_t idx = 0;

    if (count >= lanes) {
        for (; idx < count - lanes; in += in_stride*lanes, out += out_stride*lanes, idx += lanes) {
            if (in_stride == 1) {
                v = LoadU(d, in);
            }
            else {
                v = GatherIndex(d, in, src_index);
            }
            if (out_stride == 1) {
                StoreU(func(v), d, out);
            }
            else {
                ScatterIndex(func(v), d, out, dst_index);
            }
            npyv_cleanup();
        }
    }

    // `count` was a multiple of the vector length `N`: already done.
    if (HWY_UNLIKELY(idx == count))
        return;

    const size_t remaining = count - idx;
    HWY_DASSERT(0 != remaining && remaining < N);
    if (in_stride == 1) {
        v = LoadN(d, in, remaining);
    }
    else {
        v = GatherIndexN(d, in, src_index, remaining);
    }
    if (out_stride == 1) {
        StoreN(func(v), d, out, remaining);
    }
    else {
        ScatterIndexN(func(v), d, out, dst_index, remaining);
    }
    npyv_cleanup();
}

}  // namespace HWY_NAMESPACE
}  // namespace hwy
HWY_AFTER_NAMESPACE();

#endif
