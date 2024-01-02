import pytest

import operator
import numpy as np

from numpy.testing import assert_array_equal, assert_raises


COMPARISONS = [
    (operator.eq, np.equal, "=="),
    (operator.ne, np.not_equal, "!="),
    (operator.lt, np.less, "<"),
    (operator.le, np.less_equal, "<="),
    (operator.gt, np.greater, ">"),
    (operator.ge, np.greater_equal, ">="),
]

MAX = np.iinfo(np.int64).max


@pytest.mark.parametrize(["op", "ufunc", "sym"], COMPARISONS)
def test_mixed_string_comparison_ufuncs_fail(op, ufunc, sym):
    arr_string = np.array(["a", "b"], dtype="S")
    arr_unicode = np.array(["a", "c"], dtype="U")

    with pytest.raises(TypeError, match="did not contain a loop"):
        ufunc(arr_string, arr_unicode)

    with pytest.raises(TypeError, match="did not contain a loop"):
        ufunc(arr_unicode, arr_string)

@pytest.mark.parametrize(["op", "ufunc", "sym"], COMPARISONS)
def test_mixed_string_comparisons_ufuncs_with_cast(op, ufunc, sym):
    arr_string = np.array(["a", "b"], dtype="S")
    arr_unicode = np.array(["a", "c"], dtype="U")

    # While there is no loop, manual casting is acceptable:
    res1 = ufunc(arr_string, arr_unicode, signature="UU->?", casting="unsafe")
    res2 = ufunc(arr_string, arr_unicode, signature="SS->?", casting="unsafe")

    expected = op(arr_string.astype("U"), arr_unicode)
    assert_array_equal(res1, expected)
    assert_array_equal(res2, expected)


@pytest.mark.parametrize(["op", "ufunc", "sym"], COMPARISONS)
@pytest.mark.parametrize("dtypes", [
        ("S2", "S2"), ("S2", "S10"),
        ("<U1", "<U1"), ("<U1", ">U1"), (">U1", ">U1"),
        ("<U1", "<U10"), ("<U1", ">U10")])
@pytest.mark.parametrize("aligned", [True, False])
def test_string_comparisons(op, ufunc, sym, dtypes, aligned):
    # ensure native byte-order for the first view to stay within unicode range
    native_dt = np.dtype(dtypes[0]).newbyteorder("=")
    arr = np.arange(2**15).view(native_dt).astype(dtypes[0])
    if not aligned:
        # Make `arr` unaligned:
        new = np.zeros(arr.nbytes + 1, dtype=np.uint8)[1:].view(dtypes[0])
        new[...] = arr
        arr = new

    arr2 = arr.astype(dtypes[1], copy=True)
    np.random.shuffle(arr2)
    arr[0] = arr2[0]  # make sure one matches

    expected = [op(d1, d2) for d1, d2 in zip(arr.tolist(), arr2.tolist())]
    assert_array_equal(op(arr, arr2), expected)
    assert_array_equal(ufunc(arr, arr2), expected)
    assert_array_equal(
        np.char.compare_chararrays(arr, arr2, sym, False), expected
    )

    expected = [op(d2, d1) for d1, d2 in zip(arr.tolist(), arr2.tolist())]
    assert_array_equal(op(arr2, arr), expected)
    assert_array_equal(ufunc(arr2, arr), expected)
    assert_array_equal(
        np.char.compare_chararrays(arr2, arr, sym, False), expected
    )


@pytest.mark.parametrize(["op", "ufunc", "sym"], COMPARISONS)
@pytest.mark.parametrize("dtypes", [
        ("S2", "S2"), ("S2", "S10"), ("<U1", "<U1"), ("<U1", ">U10")])
def test_string_comparisons_empty(op, ufunc, sym, dtypes):
    arr = np.empty((1, 0, 1, 5), dtype=dtypes[0])
    arr2 = np.empty((100, 1, 0, 1), dtype=dtypes[1])

    expected = np.empty(np.broadcast_shapes(arr.shape, arr2.shape), dtype=bool)
    assert_array_equal(op(arr, arr2), expected)
    assert_array_equal(ufunc(arr, arr2), expected)
    assert_array_equal(
        np.char.compare_chararrays(arr, arr2, sym, False), expected
    )


@pytest.mark.parametrize("str_dt", ["S", "U"])
@pytest.mark.parametrize("float_dt", np.typecodes["AllFloat"])
def test_float_to_string_cast(str_dt, float_dt):
    float_dt = np.dtype(float_dt)
    fi = np.finfo(float_dt)
    arr = np.array([np.nan, np.inf, -np.inf, fi.max, fi.min], dtype=float_dt)
    expected = ["nan", "inf", "-inf", str(fi.max), str(fi.min)]
    if float_dt.kind == "c":
        expected = [f"({r}+0j)" for r in expected]

    res = arr.astype(str_dt)
    assert_array_equal(res, np.array(expected, dtype=str_dt))


@pytest.mark.parametrize("dt", ["S", "U"])
class TestMethods:

    @pytest.mark.parametrize("in1,in2,out", [
        ("", "", ""),
        ("abc", "abc", "abcabc"),
        ("12345", "12345", "1234512345"),
        ("MixedCase", "MixedCase", "MixedCaseMixedCase"),
        ("12345 \0 ", "12345 \0 ", "12345 \0 12345 \0 "),
        ("UPPER", "UPPER", "UPPERUPPER"),
        (["abc", "def"], ["hello", "world"], ["abchello", "defworld"]),
    ])
    def test_add(self, in1, in2, out, dt):
        in1 = np.array(in1, dtype=dt)
        in2 = np.array(in2, dtype=dt)
        out = np.array(out, dtype=dt)
        assert_array_equal(np.strings.add(in1, in2), out)

    @pytest.mark.parametrize("in_,out", [
        ("", False),
        ("a", True),
        ("A", True),
        ("\n", False),
        ("abc", True),
        ("aBc123", False),
        ("abc\n", False),
        (["abc", "aBc123"], [True, False]),
    ])
    def test_isalpha(self, in_, out, dt):
        in_ = np.array(in_, dtype=dt)
        assert_array_equal(np.strings.isalpha(in_), out)

    @pytest.mark.parametrize("in_,out", [
        ("", False),
        ("a", False),
        ("0", True),
        ("012345", True),
        ("012345a", False),
        (["a", "012345"], [False, True]),
    ])
    def test_isdigit(self, in_, out, dt):
        in_ = np.array(in_, dtype=dt)
        assert_array_equal(np.strings.isdigit(in_), out)

    @pytest.mark.parametrize("in_,out", [
        ("", False),
        ("a", False),
        ("1", False),
        (" ", True),
        ("\t", True),
        ("\r", True),
        ("\n", True),
        (" \t\r \n", True),
        (" \t\r\na", False),
        (["\t1", " \t\r \n"], [False, True])
    ])
    def test_isspace(self, in_, out, dt):
        in_ = np.array(in_, dtype=dt)
        assert_array_equal(np.strings.isspace(in_), out)

    @pytest.mark.parametrize("in_,out", [
        ("", False),
        ("a", False),
        ("0", True),
        ("\u2460", False),  # CIRCLED DIGIT 1
        ("\xbc", False),  # VULGAR FRACTION ONE QUARTER
        ("\u0660", True),  # ARABIC_INDIC DIGIT ZERO
        ("012345", True),
        ("012345a", False),
        (["0", "a"], [True, False]),
    ])
    def test_isdecimal_unicode(self, in_, out, dt):
        if dt == "S":
            pytest.skip("np.strings.isdecimal only supports unicode")
        in_ = np.array(in_)
        assert_array_equal(np.strings.isdecimal(in_), out)

    def test_isdecimal_bytes(self, dt):
        if dt == "U":
            pytest.skip("test_isdecimal_bytes only tests that "
                        "np.strings.isdecimal raises when given a bytes "
                        "object")
        with assert_raises(TypeError):
            in_ = np.array(b"1")
            np.strings.isdecimal(in_)

    @pytest.mark.parametrize("in_,out", [
        ("", False),
        ("a", False),
        ("0", True),
        ("\u2460", True),  # CIRCLED DIGIT 1
        ("\xbc", True),  # VULGAR FRACTION ONE QUARTER
        ("\u0660", True),  # ARABIC_INDIC DIGIT ZERO
        ("012345", True),
        ("012345a", False),
        (["0", "a"], [True, False]),
    ])
    def test_isnumeric_unicode(self, in_, out, dt):
        if dt == "S":
            pytest.skip("np.strings.isnumeric only supports unicode")
        in_ = np.array(in_)
        assert_array_equal(np.strings.isnumeric(in_), out)

    def test_isnumeric_bytes(self, dt):
        if dt == "U":
            pytest.skip("test_isnumeric_bytes only tests that "
                        "np.strings.isnumeric raises when given a bytes "
                        "object")
        with assert_raises(TypeError):
            in_ = np.array(b"1")
            np.strings.isnumeric(in_)

    @pytest.mark.parametrize("in_,out", [
        ("", 0),
        ("abc", 3),
        ("12345", 5),
        ("MixedCase", 9),
        ("12345 \x00 ", 8),
        ("UPPER", 5),
        (["abc", "12345 \x00 "], [3, 8]),
    ])
    def test_str_len(self, in_, out, dt):
        in_ = np.array(in_, dtype=dt)
        assert_array_equal(np.strings.str_len(in_), out)

    @pytest.mark.parametrize("in1,in2,in3,in4,out", [
        ("abcdefghiabc", "abc", 0, MAX, 0),
        ("abcdefghiabc", "abc", 1, MAX, 9),
        ("abcdefghiabc", "def", 4, MAX, -1),
        ("abc", "", 0, MAX, 0),
        ("abc", "", 3, MAX, 3),
        ("abc", "", 4, MAX, -1),
        ("rrarrrrrrrrra", "a", 0, MAX, 2),
        ("rrarrrrrrrrra", "a", 4, MAX, 12),
        ("rrarrrrrrrrra", "a", 4, 6, -1),
        ("", "", 0, MAX, 0),
        ("", "", 1, 1, -1),
        ("", "", MAX, 0, -1),
        ("", "xx", 0, MAX, -1),
        ("", "xx", 1, 1, -1),
        ("", "xx", MAX, 0, -1),
        pytest.param(99*"a" + "b", "b", 0, MAX, 99,
                     id='99*a+b-b-0-MAX-99'),
        pytest.param(98*"a" + "ba", "ba", 0, MAX, 98,
                     id='98*a+ba-ba-0-MAX-98'),
        pytest.param(100*"a", "b", 0, MAX, -1,
                     id='100*a-b-0-MAX--1'),
        pytest.param(30000*"a" + 100*"b", 100*"b", 0, MAX, 30000,
                     id='30000*a+100*b-100*b-0-MAX-30000'),
        pytest.param(30000*"a", 100*"b", 0, MAX, -1,
                     id='30000*a-100*b-0-MAX--1'),
        pytest.param(15000*"a" + 15000*"b", 15000*"b", 0, MAX, 15000,
                     id='15000*a+15000*b-15000*b-0-MAX-15000'),
        pytest.param(15000*"a" + 15000*"b", 15000*"c", 0, MAX, -1,
                     id='15000*a+15000*b-15000*c-0-MAX--1'),
        (["abcdefghiabc", "rrarrrrrrrrra"], ["def", "arr"], [0, 3],
         [MAX, MAX], [3, -1]),
    ])
    def test_find(self, in1, in2, in3, in4, out, dt):
        in1 = np.array(in1, dtype=dt)
        in2 = np.array(in2, dtype=dt)
        assert_array_equal(np.strings.find(in1, in2, in3, in4), out)

    @pytest.mark.parametrize("in1,in2,in3,in4,out", [
        ("abcdefghiabc", "abc", 0, MAX, 9),
        ("abcdefghiabc", "", 0, MAX, 12),
        ("abcdefghiabc", "abcd", 0, MAX, 0),
        ("abcdefghiabc", "abcz", 0, MAX, -1),
        ("abc", "", 0, MAX, 3),
        ("abc", "", 3, MAX, 3),
        ("abc", "", 4, MAX, -1),
        ("rrarrrrrrrrra", "a", 0, MAX, 12),
        ("rrarrrrrrrrra", "a", 4, MAX, 12),
        ("rrarrrrrrrrra", "a", 4, 6, -1),
        (["abcdefghiabc", "rrarrrrrrrrra"], ["abc", "a"], [0, 0],
         [MAX, MAX], [9, 12]),
    ])
    def test_rfind(self, in1, in2, in3, in4, out, dt):
        in1 = np.array(in1, dtype=dt)
        in2 = np.array(in2, dtype=dt)
        assert_array_equal(np.strings.rfind(in1, in2, in3, in4), out)

    @pytest.mark.parametrize("in1,in2,in3,in4,out", [
        ("aaa", "a", 0, MAX, 3),
        ("aaa", "b", 0, MAX, 0),
        ("aaa", "a", 1, MAX, 2),
        ("aaa", "a", 10, MAX, 0),
        ("aaa", "a", -1, MAX, 1),
        ("aaa", "a", -10, MAX, 3),
        ("aaa", "a", 0, 1, 1),
        ("aaa", "a", 0, 10, 3),
        ("aaa", "a", 0, -1, 2),
        ("aaa", "a", 0, -10, 0),
        ("aaa", "", 1, MAX, 3),
        ("aaa", "", 3, MAX, 1),
        ("aaa", "", 10, MAX, 0),
        ("aaa", "", -1, MAX, 2),
        ("aaa", "", -10, MAX, 4),
        ("aaa", "aaaa", 0, MAX, 0),
        pytest.param(98*"a" + "ba", "ba", 0, MAX, 1,
                     id='98*a+ba-ba-0-MAX-1'),
        pytest.param(30000*"a" + 100*"b", 100*"b", 0, MAX, 1,
                     id='30000*a+100*b-100*b-0-MAX-1'),
        pytest.param(30000*"a", 100*"b", 0, MAX, 0,
                     id='30000*a-100*b-0-MAX-0'),
        pytest.param(30000*"a" + 100*"ab", "ab", 0, MAX, 100,
                     id='30000*a+100*ab-ab-0-MAX-100'),
        pytest.param(15000*"a" + 15000*"b", 15000*"b", 0, MAX, 1,
                     id='15000*a+15000*b-15000*b-0-MAX-1'),
        pytest.param(15000*"a" + 15000*"b", 15000*"c", 0, MAX, 0,
                     id='15000*a+15000*b-15000*c-0-MAX-0'),
        ("", "", 0, MAX, 1),
        ("", "", 1, 1, 0),
        ("", "", MAX, 0, 0),
        ("", "xx", 0, MAX, 0),
        ("", "xx", 1, 1, 0),
        ("", "xx", MAX, 0, 0),
        (["aaa", ""], ["a", ""], [0, 0], [MAX, MAX], [3, 1])
    ])
    def test_count(self, in1, in2, in3, in4, out, dt):
        in1 = np.array(in1, dtype=dt)
        in2 = np.array(in2, dtype=dt)
        assert_array_equal(np.strings.count(in1, in2, in3, in4), out)

    @pytest.mark.parametrize("in1,in2,in3,in4,out", [
        ("hello", "he", 0, MAX, True),
        ("hello", "hello", 0, MAX, True),
        ("hello", "hello world", 0, MAX, False),
        ("hello", "", 0, MAX, True),
        ("hello", "ello", 0, MAX, False),
        ("hello", "ello", 1, MAX, True),
        ("hello", "o", 4, MAX, True),
        ("hello", "o", 5, MAX, False),
        ("hello", "", 5, MAX, True),
        ("hello", "lo", 6, MAX, False),
        ("helloworld", "lowo", 3, MAX, True),
        ("helloworld", "lowo", 3, 7, True),
        ("helloworld", "lowo", 3, 6, False),
        ("", "", 0, 1, True),
        ("", "", 0, 0, True),
        ("", "", 1, 0, False),
        ("hello", "he", 0, -1, True),
        ("hello", "he", -53, -1, True),
        ("hello", "hello", 0, -1, False),
        ("hello", "hello world", -1, -10, False),
        ("hello", "ello", -5, MAX, False),
        ("hello", "ello", -4, MAX, True),
        ("hello", "o", -2, MAX, False),
        ("hello", "o", -1, MAX, True),
        ("hello", "", -3, -3, True),
        ("hello", "lo", -9, MAX, False),
        (["hello", ""], ["he", ""], [0, 0], [MAX, 1], [True, True]),
    ])
    def test_startswith(self, in1, in2, in3, in4, out, dt):
        in1 = np.array(in1, dtype=dt)
        in2 = np.array(in2, dtype=dt)
        assert_array_equal(np.strings.startswith(in1, in2, in3, in4), out)

    @pytest.mark.parametrize("in1,in2,in3,in4,out", [
        ("hello", "lo", 0, MAX, True),
        ("hello", "he", 0, MAX, False),
        ("hello", "", 0, MAX, True),
        ("hello", "hello world", 0, MAX, False),
        ("helloworld", "worl", 0, MAX, False),
        ("helloworld", "worl", 3, 9, True),
        ("helloworld", "world", 3, 12, True),
        ("helloworld", "lowo", 1, 7, True),
        ("helloworld", "lowo", 2, 7, True),
        ("helloworld", "lowo", 3, 7, True),
        ("helloworld", "lowo", 4, 7, False),
        ("helloworld", "lowo", 3, 8, False),
        ("ab", "ab", 0, 1, False),
        ("ab", "ab", 0, 0, False),
        ("", "", 0, 1, True),
        ("", "", 0, 0, True),
        ("", "", 1, 0, False),
        ("hello", "lo", -2, MAX, True),
        ("hello", "he", -2, MAX, False),
        ("hello", "", -3, -3, True),
        ("hello", "hello world", -10, -2, False),
        ("helloworld", "worl", -6, MAX, False),
        ("helloworld", "worl", -5, -1, True),
        ("helloworld", "worl", -5, 9, True),
        ("helloworld", "world", -7, 12, True),
        ("helloworld", "lowo", -99, -3, True),
        ("helloworld", "lowo", -8, -3, True),
        ("helloworld", "lowo", -7, -3, True),
        ("helloworld", "lowo", 3, -4, False),
        ("helloworld", "lowo", -8, -2, False),
        (["hello", "helloworld"], ["lo", "worl"], [0, -6], [MAX, MAX],
         [True, False]),
    ])
    def test_endswith(self, in1, in2, in3, in4, out, dt):
        in1 = np.array(in1, dtype=dt)
        in2 = np.array(in2, dtype=dt)
        assert_array_equal(np.strings.endswith(in1, in2, in3, in4), out)

    @pytest.mark.parametrize("in_,out", [
        ("", ""),
        ("   hello   ", "hello   "),
        ("hello", "hello"),
        (" \t\n\r\f\vabc \t\n\r\f\v", "abc \t\n\r\f\v"),
        (["   hello   ", "hello"], ["hello   ", "hello"]),
    ])
    def test_lstrip_whitespace(self, in_, out, dt):
        in_ = np.array(in_, dtype=dt)
        out = np.array(out, dtype=dt)
        assert_array_equal(np.strings.lstrip(in_), out)

    @pytest.mark.parametrize("in1,in2,out", [
        ("", "", ""),
        ("", "xyz", ""),
        ("hello", "", "hello"),
        ("xyzzyhelloxyzzy", "xyz", "helloxyzzy"),
        ("hello", "xyz", "hello"),
        ("xyxz", "xyxz", ""),
        ("xyxzx", "x", "yxzx"),
        (["xyzzyhelloxyzzy", "hello"], ["xyz", "xyz"],
         ["helloxyzzy", "hello"]),
    ])
    def test_lstrip_args(self, in1, in2, out, dt):
        in1 = np.array(in1, dtype=dt)
        in2 = np.array(in2, dtype=dt)
        out = np.array(out, dtype=dt)
        assert_array_equal(np.strings.lstrip(in1, in2), out)

    @pytest.mark.parametrize("in_,out", [
        ("", ""),
        ("   hello   ", "   hello"),
        ("hello", "hello"),
        (" \t\n\r\f\vabc \t\n\r\f\v", " \t\n\r\f\vabc"),
        (["   hello   ", "hello"], ["   hello", "hello"]),
    ])
    def test_rstrip_whitespace(self, in_, out, dt):
        in_ = np.array(in_, dtype=dt)
        out = np.array(out, dtype=dt)
        assert_array_equal(np.strings.rstrip(in_), out)

    @pytest.mark.parametrize("in1,in2,out", [
        ("", "", ""),
        ("", "xyz", ""),
        ("hello", "", "hello"),
        ("xyzzyhelloxyzzy", "xyz", "xyzzyhello"),
        ("hello", "xyz", "hello"),
        ("xyxz", "xyxz", ""),
        ("xyxzx", "x", "xyxz"),
        (["xyzzyhelloxyzzy", "hello"], ["xyz", "xyz"],
         ["xyzzyhello", "hello"]),
    ])
    def test_rstrip_args(self, in1, in2, out, dt):
        in1 = np.array(in1, dtype=dt)
        in2 = np.array(in2, dtype=dt)
        out = np.array(out, dtype=dt)
        assert_array_equal(np.strings.rstrip(in1, in2), out)

    @pytest.mark.parametrize("in_,out", [
        ("", ""),
        ("   hello   ", "hello"),
        ("hello", "hello"),
        (" \t\n\r\f\vabc \t\n\r\f\v", "abc"),
        (["   hello   ", "hello"], ["hello", "hello"]),
    ])
    def test_strip_whitespace(self, in_, out, dt):
        in_ = np.array(in_, dtype=dt)
        out = np.array(out, dtype=dt)
        assert_array_equal(np.strings.strip(in_), out)

    @pytest.mark.parametrize("in1,in2,out", [
        ("", "", ""),
        ("", "xyz", ""),
        ("hello", "", "hello"),
        ("xyzzyhelloxyzzy", "xyz", "hello"),
        ("hello", "xyz", "hello"),
        ("xyxz", "xyxz", ""),
        ("xyxzx", "x", "yxz"),
        (["xyzzyhelloxyzzy", "hello"], ["xyz", "xyz"],
         ["hello", "hello"]),
    ])
    def test_strip_args(self, in1, in2, out, dt):
        in1 = np.array(in1, dtype=dt)
        in2 = np.array(in2, dtype=dt)
        out = np.array(out, dtype=dt)
        assert_array_equal(np.strings.strip(in1, in2), out)

    @pytest.mark.parametrize("in1,in2,in3,in4,out", [
        ("", "", "", MAX, ""),
        ("", "", "A", MAX, "A"),
        ("", "A", "", MAX, ""),
        ("", "A", "A", MAX, ""),
        ("", "", "", 100, ""),
        ("", "", "A", 100, "A"),
        ("A", "", "", MAX, "A"),
        ("A", "", "*", MAX, "*A*"),
        ("A", "", "*1", MAX, "*1A*1"),
        ("A", "", "*-#", MAX, "*-#A*-#"),
        ("AA", "", "*-", MAX, "*-A*-A*-"),
        ("AA", "", "*-", -1, "*-A*-A*-"),
        ("AA", "", "*-", 4, "*-A*-A*-"),
        ("AA", "", "*-", 3, "*-A*-A*-"),
        ("AA", "", "*-", 2, "*-A*-A"),
        ("AA", "", "*-", 1, "*-AA"),
        ("AA", "", "*-", 0, "AA"),
        ("A", "A", "", MAX, ""),
        ("AAA", "A", "", MAX, ""),
        ("AAA", "A", "", -1, ""),
        ("AAA", "A", "", 4, ""),
        ("AAA", "A", "", 3, ""),
        ("AAA", "A", "", 2, "A"),
        ("AAA", "A", "", 1, "AA"),
        ("AAA", "A", "", 0, "AAA"),
        ("AAAAAAAAAA", "A", "", MAX, ""),
        ("ABACADA", "A", "", MAX, "BCD"),
        ("ABACADA", "A", "", -1, "BCD"),
        ("ABACADA", "A", "", 5, "BCD"),
        ("ABACADA", "A", "", 4, "BCD"),
        ("ABACADA", "A", "", 3, "BCDA"),
        ("ABACADA", "A", "", 2, "BCADA"),
        ("ABACADA", "A", "", 1, "BACADA"),
        ("ABACADA", "A", "", 0, "ABACADA"),
        ("ABCAD", "A", "", MAX, "BCD"),
        ("ABCADAA", "A", "", MAX, "BCD"),
        ("BCD", "A", "", MAX, "BCD"),
        ("*************", "A", "", MAX, "*************"),
        ("^"+"A"*1000+"^", "A", "", 999, "^A^"),
        ("the", "the", "", MAX, ""),
        ("theater", "the", "", MAX, "ater"),
        ("thethe", "the", "", MAX, ""),
        ("thethethethe", "the", "", MAX, ""),
        ("theatheatheathea", "the", "", MAX, "aaaa"),
        ("that", "the", "", MAX, "that"),
        ("thaet", "the", "", MAX, "thaet"),
        ("here and there", "the", "", MAX, "here and re"),
        ("here and there and there", "the", "", -1, "here and re and re"),
        ("here and there and there", "the", "", 3, "here and re and re"),
        ("here and there and there", "the", "", 2, "here and re and re"),
        ("here and there and there", "the", "", 1, "here and re and there"),
        ("here and there and there", "the", "", 0, "here and there and there"),
        ("here and there and there", "the", "", MAX, "here and re and re"),
        ("abc", "the", "", MAX, "abc"),
        ("abcdefg", "the", "", MAX, "abcdefg"),
        ("bbobob", "bob", "", MAX, "bob"),
        ("bbobobXbbobob", "bob", "", MAX, "bobXbob"),
        ("aaaaaaabob", "bob", "", MAX, "aaaaaaa"),
        ("aaaaaaa", "bob", "", MAX, "aaaaaaa"),
        ("Who goes there?", "o", "o", MAX, "Who goes there?"),
        ("Who goes there?", "o", "O", MAX, "WhO gOes there?"),
        ("Who goes there?", "o", "O", -1, "WhO gOes there?"),
        ("Who goes there?", "o", "O", 3, "WhO gOes there?"),
        ("Who goes there?", "o", "O", 2, "WhO gOes there?"),
        ("Who goes there?", "o", "O", 1, "WhO goes there?"),
        ("Who goes there?", "o", "O", 0, "Who goes there?"),
        ("Who goes there?", "a", "q", MAX, "Who goes there?"),
        ("Who goes there?", "W", "w", MAX, "who goes there?"),
        ("WWho goes there?WW", "W", "w", MAX, "wwho goes there?ww"),
        ("Who goes there?", "?", "!", MAX, "Who goes there!"),
        ("Who goes there??", "?", "!", MAX, "Who goes there!!"),
        ("Who goes there?", ".", "!", MAX, "Who goes there?"),
        ("This is a tissue", "is", "**", MAX, "Th** ** a t**sue"),
        ("This is a tissue", "is", "**", -1, "Th** ** a t**sue"),
        ("This is a tissue", "is", "**", 4, "Th** ** a t**sue"),
        ("This is a tissue", "is", "**", 3, "Th** ** a t**sue"),
        ("This is a tissue", "is", "**", 2, "Th** ** a tissue"),
        ("This is a tissue", "is", "**", 1, "Th** is a tissue"),
        ("This is a tissue", "is", "**", 0, "This is a tissue"),
        ("bobob", "bob", "cob", MAX, "cobob"),
        ("bobobXbobobob", "bob", "cob", MAX, "cobobXcobocob"),
        ("bobob", "bot", "bot", MAX, "bobob"),
        ("Reykjavik", "k", "KK", MAX, "ReyKKjaviKK"),
        ("Reykjavik", "k", "KK", -1, "ReyKKjaviKK"),
        ("Reykjavik", "k", "KK", 2, "ReyKKjaviKK"),
        ("Reykjavik", "k", "KK", 1, "ReyKKjavik"),
        ("Reykjavik", "k", "KK", 0, "Reykjavik"),
        ("A.B.C.", ".", "----", MAX, "A----B----C----"),
        ("Reykjavik", "q", "KK", MAX, "Reykjavik"),
        ("spam, spam, eggs and spam", "spam", "ham", MAX,
            "ham, ham, eggs and ham"),
        ("spam, spam, eggs and spam", "spam", "ham", -1,
            "ham, ham, eggs and ham"),
        ("spam, spam, eggs and spam", "spam", "ham", 4,
            "ham, ham, eggs and ham"),
        ("spam, spam, eggs and spam", "spam", "ham", 3,
            "ham, ham, eggs and ham"),
        ("spam, spam, eggs and spam", "spam", "ham", 2,
            "ham, ham, eggs and spam"),
        ("spam, spam, eggs and spam", "spam", "ham", 1,
            "ham, spam, eggs and spam"),
        ("spam, spam, eggs and spam", "spam", "ham", 0,
            "spam, spam, eggs and spam"),
        ("bobobob", "bobob", "bob", MAX, "bobob"),
        ("bobobobXbobobob", "bobob", "bob", MAX, "bobobXbobob"),
        ("BOBOBOB", "bob", "bobby", MAX, "BOBOBOB"),
        ("one!two!three!", "!", "@", 1, "one@two!three!"),
        ("one!two!three!", "!", "", MAX, "onetwothree"),
        ("one!two!three!", "!", "@", 2, "one@two@three!"),
        ("one!two!three!", "!", "@", 3, "one@two@three@"),
        ("one!two!three!", "!", "@", 4, "one@two@three@"),
        ("one!two!three!", "!", "@", 0, "one!two!three!"),
        ("one!two!three!", "!", "@", MAX, "one@two@three@"),
        ("one!two!three!", "x", "@", MAX, "one!two!three!"),
        ("one!two!three!", "x", "@", 2, "one!two!three!"),
        ("abc", "", "-", MAX, "-a-b-c-"),
        ("abc", "", "-", 3, "-a-b-c"),
        ("abc", "", "-", 0, "abc"),
        ("abc", "ab", "--", 0, "abc"),
        ("abc", "xy", "--", MAX, "abc"),
    ])
    def test_replace(self, in1, in2, in3, in4, out, dt):
        in1 = np.array(in1, dtype=dt)
        in2 = np.array(in2, dtype=dt)
        in3 = np.array(in3, dtype=dt)
        out = np.array(out, dtype=dt)
        assert_array_equal(np.strings.replace(in1, in2, in3, in4), out)

    def test_replace_unicode(self, dt):
        if dt == "S":
            pytest.skip("test_replace_unicode is only for U dtype")
        assert_array_equal(np.strings.replace(
            "...\u043c......<", "<", "&lt;", MAX), '...\u043c......&lt;')
