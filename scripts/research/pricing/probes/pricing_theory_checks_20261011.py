"""Exact finite probes of formulas/counterexamples, not an incremental solver."""
from fractions import Fraction as F
from itertools import product
import json

def dot(a, b):
    return sum((x*y for x, y in zip(a, b)), F(0))

def rc(c, a, pi):
    return F(c) - dot(a, pi)

out = {}
# Same feasible continuation, different master-row incidences.
labels = [(0, (F(1), F(0))), (0, (F(0), F(1)))]
old = [rc(c,a,(F(1),F(0))) for c,a in labels]
new = [rc(c,a,(F(0),F(1))) for c,a in labels]
assert old == [F(-1),F(0)] and new == [F(0),F(-1)]
assert min(new) < 0 and new[0] >= 0
out['deleted_label_resurrection'] = {'old':list(map(str,old)), 'new':list(map(str,new)), 'unsafe_survivor_only_misses_negative':True}

# Old suffix lower bound must move when the dual changes.
old_lb = F(1)
actual_new = rc(1,(F(1),),(F(2),))
transported = old_lb - F(2)
assert old_lb >= 0 and actual_new == transported == -1
out['stale_bound'] = {'old_lb':str(old_lb), 'new_min':str(actual_new), 'transported_lb':str(transported)}

# Exact support and enclosing-box support both give valid transported bounds.
suffixes = [(F(3),(F(0),F(2))), (F(-1),(F(2),F(0))), (F(2),(F(1),F(1)))]
anchor = (F(1,3),F(-2,3))
anchor_lb = min(rc(c,a,anchor) for c,a in suffixes)
grid = [F(-1),F(-1,2),F(0),F(1,2),F(1)]
n = 0
for delta in product(grid,repeat=2):
    current = tuple(p+d for p,d in zip(anchor,delta))
    exact = min(rc(c,a,current) for c,a in suffixes)
    support = max(dot(delta,a) for _,a in suffixes)
    box_support = sum(max(F(0),2*d) for d in delta)
    assert anchor_lb-support <= exact
    assert anchor_lb-box_support <= exact
    n += 1
out['bound_transport'] = {'queries':n,'exact_and_box_support_valid':True}

# A margin/norm test is sufficient, with the dual norm in the denominator.
margin = F(2)
diff = (F(2),F(-2))
radius = margin/sum(abs(x) for x in diff)
n = 0
for delta in product([F(-1,2),F(-1,4),F(0),F(1,4),F(1,2)],repeat=2):
    assert max(abs(d) for d in delta) <= radius
    assert margin-dot(delta,diff) >= 0
    n += 1
out['dominance_radius'] = {'queries':n,'linfty_radius':str(radius),'all_margins_nonnegative':True}

# Bounded total variation permits a sign switch at every update.
pi = [F(1)+F((-1)**t,2**t) for t in range(1,13)]
switches = sum((pi[t]-1)*(pi[t-1]-1) < 0 for t in range(1,len(pi)))
variation = sum(abs(pi[t]-pi[t-1]) for t in range(1,len(pi)))
assert switches == 11 and variation < F(3,2)
out['small_variation_many_crossings'] = {'queries':len(pi),'crossings':switches,'total_variation':str(variation),'upper_bound':'3/2'}

# A common reduced-cost shift preserves the minimizer, but changes termination.
values = [F(-1),F(1)]
shifted = [v+2 for v in values]
assert values.index(min(values)) == shifted.index(min(shifted))
assert min(values) < 0 and min(shifted) > 0
out['common_shift'] = {'same_argmin':True,'negative_existence_changed':True}

# Exhaustive finite probes of the FIXED-pair hysteresis inequality.
eta = F(1)
n = 0
for margins in product([F(-1),F(0),F(1),F(3,2),F(2),F(3)],repeat=5):
    dormant = False
    events = 0
    for margin in margins:
        next_dormant = dormant
        if not dormant and margin >= 2*eta:
            next_dormant = True
        elif dormant and margin <= eta:
            next_dormant = False
        events += next_dormant != dormant
        dormant = next_dormant
        assert not dormant or margin > eta
    variation = sum(abs(b-a) for a,b in zip(margins,margins[1:]))
    assert events <= 1+variation/eta
    n += 1
out['fixed_pair_two_threshold_hysteresis'] = {'sequences':n,'length':5,'eta':'1','switch_bound_and_pruning_safety_valid':True}

# Exponentially many winning affine pieces do not imply an implicit memory bound.
d = 4
subsets = list(product([0,1],repeat=d))
for signs in product([-1,1],repeat=d):
    values = [-sum(a*p for a,p in zip(subset,signs)) for subset in subsets]
    expected = -sum(max(p,0) for p in signs)
    assert min(values) == expected and values.count(expected) == 1
out['explicit_envelope_vs_factorization'] = {'dimension':d,'pieces':len(subsets),'dual_corners':2**d,'unique_winner_at_each_corner_and_factorized_value_match':True}

# One changed residual arc can flip a pair at every incomparable resource state.
resources = [tuple(y for bit in bits for y in (bit,1-bit)) for bits in product([0,1],repeat=d)]
for a in resources:
    for b in resources:
        if a != b:
            assert not all(x<=y for x,y in zip(a,b))
flipped = 0
for state in resources:
    # Two initial alternatives followed by identical zero-cost binary stages.
    # Only the via-e prefix receives the changed residual; both reach this state.
    labels_here = [(False,state,F(0),F(0)), (True,state,F(-1),F(1))]
    old_winner = min(labels_here,key=lambda label:label[2])
    new_winner = min(labels_here,key=lambda label:label[3])
    assert old_winner[0] and not new_winner[0]
    flipped += 1
out['single_residual_arc_fanout'] = {'binary_stages':d,'incomparable_states':len(resources),'fixed_pairs_flipped':flipped,'changed_residual_arcs':1}

print(json.dumps({'scope':'finite rational formula and counterexample checks only','checks':out},ensure_ascii=False,indent=2))
