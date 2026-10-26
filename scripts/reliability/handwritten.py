"""Independent hand-written text fixtures; separate from the acceptance corpus."""

import json


def expected(variables, costs=None, rows=(), *, constant=0, sense="minimize"):
    return {"name": "hand", "sense": sense, "variables": variables,
            "objective": {"coefficients": costs or {}, "constant": constant},
            "constraints": list(rows)}


def v(name="x", lo=0, hi=None, typ="continuous"):
    return {"name": name, "lower": lo, "upper": hi, "type": typ}


def r(name="r", cost=1, lo=None, hi=2):
    return {"name": name, "coefficients": {"x": cost}, "lower": lo, "upper": hi}


LP_CASES = [
    ("Minimize\n obj: 2 x + 3\nSubject To\n r: x + 1 <= 3\nEnd\n",
     expected([v()], {"x": 2}, [r()], constant=3)),
    ("MAX\n - x + 0 y - .5\nST\n eq: x - y = 2\nBounds\n x free\n y = 1\nEnd\n",
     expected([v(lo=None), v("y", 1, 1)], {"x": -1, "y": 0},
              [{"name": "eq", "coefficients": {"x": 1, "y": -1}, "lower": 2, "upper": 2}],
              constant=-0.5, sense="maximize")),
    ("Minimum\n x + 2 x\n + .5 - .25\nSuch That\n floor: x\n >= 1\n"
     "Bound\n -2 <= x <= 4\nGeneral\n x\nEnd\n",
     expected([v(lo=-2, hi=4, typ="integer")], {"x": 3}, [r("floor", lo=1, hi=None)],
              constant=0.25)),
    ("Min\n 0 x + y\nS.T.\n cap: y <= 1\nBounds\n x <= 3\n y >= -2\n"
     "Binaries\n y\nEnd\n",
     expected([v(hi=3), v("y", 0, 1, "binary")], {"x": 0, "y": 1},
              [{"name": "cap", "coefficients": {"y": 1}, "lower": None, "upper": 1}])),
    ("Maximize\n 1e-1 x + 2E+0\nSubject To\n r: .5 x - .25 >= .75\n"
     "Bounds\n 3 >= x\nEnd\n",
     expected([v(hi=3)], {"x": 0.1}, [r(cost=0.5, lo=1, hi=None)],
              constant=2, sense="maximize")),
    ("\\ comment\nMinimize\n x - x + 0 z\nSubject To\n x <= 2\n"
     " row_1: z >= -1\nBounds\n x free\n z = 0\nEnd \\ done\n",
     expected([v(lo=None), v("z", 0, 0)], {"x": 0, "z": 0},
              [r("row_2"), {"name": "row_1", "coefficients": {"z": 1},
                            "lower": -1, "upper": None}])),
]

MPS_CASES = [
    ("NAME hand\nROWS\n N obj\n L r\nCOLUMNS\n x obj 2 r 1\nRHS\n b r 2 obj -3\nENDATA\n",
     expected([v()], {"x": 2}, [r()], constant=3)),
    ("NAME hand\nOBJSENSE\n MAX\nROWS\n N obj\n G r\nCOLUMNS\n x obj -1 r 2\n"
     "RHS\n b r -2\nBOUNDS\n FR b x\nENDATA\n",
     expected([v(lo=None)], {"x": -1}, [r(cost=2, lo=-2, hi=None)], sense="maximize")),
    ("NAME hand\nROWS\n N obj\n E r\nCOLUMNS\n x obj 1 r 1\nRHS\n b r 1\n"
     "BOUNDS\n FX b x 1\nENDATA\n", expected([v(lo=1, hi=1)], {"x": 1}, [r(lo=1, hi=1)])),
    ("NAME hand\nROWS\n N obj\n L r\nCOLUMNS\n x obj 0 r .5\nRHS\n b r 3\n"
     "RANGES\n q r 2\nBOUNDS\n MI b x\n UP b x 8\nENDATA\n",
     expected([v(lo=None, hi=8)], {"x": 0}, [r(cost=0.5, lo=1, hi=3)])),
    ("NAME hand\nROWS\n N obj\nCOLUMNS\n x obj -1\nBOUNDS\n LI b x -1\n UI b x 3\nENDATA\n",
     expected([v(lo=-1, hi=3, typ="integer")], {"x": -1})),
    ("NAME hand\nROWS\n N obj\nCOLUMNS\n x obj 2\nBOUNDS\n BV b x\nENDATA\n",
     expected([v(hi=1, typ="binary")], {"x": 2})),
]

JSON_CASES = [
    ('{"variables":[{"name":"x"}],"objective":{"coefficients":{"x":2},"constant":3},'
     '"constraints":[{"name":"r","coefficients":{"x":1},"sense":"<=","rhs":2}]}',
     expected([v()], {"x": 2}, [r()], constant=3)),
    ('{"sense":"maximize","variables":[{"name":"x","lower":null,"upper":3}],'
     '"objective":{"coefficients":{"x":-1},"constant":0.5},'
     '"constraints":[{"name":"r","coefficients":{"x":1},"lower":-2,"upper":2}]}',
     expected([v(lo=None, hi=3)], {"x": -1}, [r(lo=-2)], constant=0.5, sense="maximize")),
    ('{"variables":[{"name":"x","lower":-1,"upper":2,"type":"integer"}],'
     '"objective":{"coefficients":{"x":1}}}',
     expected([v(lo=-1, hi=2, typ="integer")], {"x": 1})),
    ('{"variables":[{"name":"x","type":"binary","upper":1}],'
     '"constraints":[{"name":"r","coefficients":{"x":1},"lower":1,"upper":1}],'
     '"objective":{"constant":2}}',
     expected([v(hi=1, typ="binary")], {}, [r(lo=1, hi=1)], constant=2)),
]

INVALID_LP = [
    "", "Minimize\n x\nSubject To\n", "x\nEnd", "Minimize\n x\nEnd",
    "Minimize\n x\nSubject To\n r: x <=\nEnd",
    "Minimize\n 2x\nSubject To\nEnd", "Minimize\n x[0]\nSubject To\nEnd",
    "Minimize\n x + 1e\nSubject To\nEnd", "Minimize\n NaN x\nSubject To\nEnd",
    "Minimize\n 1e999 x\nSubject To\nEnd", "Minimize\n 1e-999 x\nSubject To\nEnd",
    "Minimize\n x^2\nSubject To\nEnd", "Minimize\n x * y\nSubject To\nEnd",
    "Minimize\n x\nSubject To\nSOS\nEnd",
    "Minimize\n x\nSubject To\n r: x <= y\nEnd",
    "Minimize\n x\nSubject To\n r: 0 <= x <= 2\nEnd",
    "Minimize\n x\nSubject To\nBounds\n 2 <= x <= 1\nEnd",
    "Minimize\n x\nSubject To\nBounds\n x >= 0\n x >= 1\nEnd",
    "Minimize\n x\nSubject To\nGenerals\n x x\nEnd",
    "Minimize\n x\nSubject To\nGenerals\n x\nBinaries\n x\nEnd",
    "Minimize\n x\nSubject To\nEnd\n x",
    "Minimize\n x\nSubject To\n r: x <= 1\n r: x >= 0\nEnd",
    "Minimize\n x\nSubject To\nBounds\n x >= inf\nEnd",
    "Minimize\n x\nSubject To\nBounds\n x = -inf\nEnd",
    "Minimize\n 9007199254740993 x\nSubject To\nEnd",
]


def parsed_json(text):
    return json.loads(text)
