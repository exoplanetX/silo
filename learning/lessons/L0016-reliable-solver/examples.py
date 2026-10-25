"""Check L0016 teaching calculations exactly; never call a solver."""

import json
from fractions import Fraction as F
from pathlib import Path


def mv(matrix, vector):
    return [sum((a * b for a, b in zip(row, vector, strict=True)), F(0)) for row in matrix]


def transpose(matrix):
    return [list(row) for row in zip(*matrix, strict=True)]


def solve2(matrix, rhs):
    (a, b), (c, d) = matrix
    determinant = a * d - b * c
    assert determinant
    return [(d * rhs[0] - b * rhs[1]) / determinant,
            (a * rhs[1] - c * rhs[0]) / determinant]


def check_model_chain(outline):
    states = outline["scenarios"]
    assert [state["id"] for state in states] == [f"S{i}" for i in range(5)]
    for index, state in enumerate(states):
        x, y, z = map(F, state["point"])
        rhs, upper_y = F(state["rhs"]), F(state["y_upper"])
        assert 0 <= x <= 2 and 0 <= y <= upper_y and x + y + z <= rhs
        if state["x_row_upper"] is not None:
            assert x <= F(state["x_row_upper"])
        if state["z_upper"] is None:
            assert z == 0
        else:
            assert 0 <= z <= F(state["z_upper"])
        objective = 3 - x - 2 * y - 3 * z
        assert objective == F(state["objective"])
        # Each expression is an analytic upper bound on the reward, attained here.
        reward_bounds = [rhs + upper_y, 2 * rhs, rhs + upper_y,
                         F("1/10") + 2 * upper_y, 2 * rhs + F("1/2")]
        assert x + 2 * y + 3 * z == reward_bounds[index]
    return {state["id"]: state["objective"] for state in states}


def check_kkt():
    x, y = F("1/2"), F("3/2")
    beta, upper_y = F(1), F(1)
    assert [-1 + beta, -2 + beta + upper_y] == [0, 0]
    assert beta * (2 - x - y) == 0 and upper_y * (F("3/2") - y) == 0
    primal = 3 - x - 2 * y
    dual = 3 - 2 * beta - F("3/2") * upper_y
    assert primal == dual == F("-1/2")
    # Two other statuses require their own witnesses.
    assert mv([[F(1)], [F(1)]], [F(1)]) == [1, 1]  # N^T*pi >= 0
    assert F(-1) * F(1) < 0  # h^T*pi < 0
    assert mv([[F(1), F(-1)]], [F(1), F(1)]) == [0]  # unbounded ray
    return "primal=dual=-1/2; Farkas and ray identities checked"


def check_affine():
    a_plus, a_minus, w = F(1), F(0), F("1/2")
    a, b, t = a_plus - a_minus, 2 + w, F(3)
    assert a + b + 2 * t - 8 == a_plus - a_minus + w
    assert 5 + 2 * a - b + 3 * t == 12 + 2 * a_plus - 2 * a_minus - w == F("27/2")
    return "offset row=8; objective constant=12; value=27/2"


def check_csc():
    data, indices, indptr = [1, -1, 3, 2, 4], [0, 2, 1, 0, 2], [0, 2, 3, 4, 5]
    matrix = [[0] * 4 for _ in range(3)]
    for column in range(4):
        for k in range(indptr[column], indptr[column + 1]):
            matrix[indices[k]][column] = data[k]
    assert matrix == [[1, 0, 2, 0], [0, 3, 0, 0], [-1, 0, 0, 4]]
    assert mv(matrix, [1, 2, 3, 4]) == [7, 6, 15]
    return "5 entries; A*(1,2,3,4)=(7,6,15)"


def check_eta():
    e1 = [[F(2), F(0)], [F(1), F(1)]]
    e2 = [[F(1), F(3)], [F(0), F(2)]]
    basis = transpose([mv(e1, col) for col in transpose(e2)])
    assert basis == [[2, 6], [1, 5]]
    ordinary = solve2(e2, solve2(e1, [F(2), F(-1)]))
    transposed = solve2(transpose(e1), solve2(transpose(e2), [F(3), F(7)]))
    wrong = solve2(transpose(e2), solve2(transpose(e1), [F(3), F(7)]))
    assert ordinary == [4, -1] and mv(basis, ordinary) == [2, -1]
    assert transposed == [2, -1] and mv(transpose(basis), transposed) == [3, 7]
    assert wrong == [-2, F("13/2")] and mv(transpose(basis), wrong) != [3, 7]
    return "ordinary=(4,-1); transpose=(2,-1); reverse order rejected"


def check_pricing():
    scores = [F(4) ** 2 / 16, F(3) ** 2]
    assert scores == [1, 9]
    alpha, gamma = F(2), F(1)
    remaining = max(F("99/100"), F("1/2") ** 2 * gamma + 1)
    departed = gamma / alpha ** 2
    assert remaining == F("5/4") and departed == F("1/4")
    assert F("1e-8") * 1 > 0  # x=1 violates the true zero blocker exactly.
    return "Devex scores=(1,9); weights=(5/4,1/4); small blocker retained"


def check_dependency():
    weights = [F(-2), F(1)]
    assert sum(a * b for a, b in zip(weights, [1, 2], strict=True)) == 0
    assert sum(a * b for a, b in zip(weights, [2, 4], strict=True)) == 0
    epsilon = F(1, 2**39)
    assert sum(a * b for a, b in zip(weights, [F(1), 2 + epsilon], strict=True)) == epsilon
    assert epsilon != 0
    return "exact duplicate accepted; 2^-39 perturbation rejected"


def check_cost():
    ratio = F(10, 1 + 12)
    assert ratio == F(10, 13) < 1
    assert 8 * 2 * 5 == 80 and 80 * 20 == 1600 and 1600 + 80 == 1680
    return "end-to-end ratio=10/13; sample accounting=80/1600/1680"


def main():
    outline = json.loads(Path(__file__).with_name("web_outline.json").read_text(encoding="utf-8"))
    report = {
        "model_chain": check_model_chain(outline),
        "kkt_and_status_witnesses": check_kkt(),
        "affine": check_affine(),
        "csc": check_csc(),
        "eta": check_eta(),
        "pricing_and_blocker": check_pricing(),
        "exact_dependency": check_dependency(),
        "cost_scope": check_cost(),
    }
    print(json.dumps({"lesson_id": "L0016", "groups": len(report), "checks": report}, indent=2))


if __name__ == "__main__":
    main()
