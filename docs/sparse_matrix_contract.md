# Sparse matrix and original-space contract

Program SILO-SPARSE-LP-20261024, SP1 design, version1.0. Product implementation
starts only after the input/truth/baseline freeze and independent SP1 GO.
This document defines the same general LP as the dense referencef488189.

## Mathematical objects and import direction

Original data are `min/max c0+c'x`, `l<=A*x<=u`, `L<=x<=U`. Names and row names
retain caller order; absent sides use infinities. Integer input-conversion guards
and the actual-binary Fraction convention are unchanged. Engine selection occurs
before matrix allocation: dense uses its existing cell bound; sparse uses the
explicit sparse gates and cannot be rejected by a prospective dense workspace.

Core contains only passive options/results/snapshot records. SciPy is imported
lazily by modeling/LP sparse operations after explicit selection. No native path
may call scipy.optimize/HiGHS/another optimizer. NumPy-only dense imports continue.

## Matrix boundary

`modeling/matrix_ops.py` supplies functions over ndarray or CSR/CSC, without
forcing a new wrapper on legacy ndarray consumers. Sparse data keep coherent
row/column views; view storage is counted. Required operations are:

| Operation | Return/invariant |
|---|---|
| shape, nnz, finite coefficients | Dimensions and true stored nonzero count |
| row/column nonzeros | One-dimensional integer indices and numeric values |
| scalar/selected rows and columns | Explicit semantic order retained |
| A*x, A^T*y, abs(A)*abs(x), transpose absolute product | One-dimensional ndarray, never object/2D matrix |
| basis-column extraction | Sparse B in the declared ordered basis |
| append rows/columns, unit columns, choose/delete rows/columns | Sparse shape and stable keys checked before commit |
| row/column scaling | Positive scaling, no change of integer-grid interpretation |
| coefficient identity | Shape, canonical indices and actual float values bound together |

No unconditional `toarray`, `np.array(A)`, dense vstack/hstack or allocation of
A's full shape occurs in sparse input, edits, propagation, normalization, simplex,
snapshot or verification. Dense vectors of length m/n/p are allowed. Sparse LU
fill and bounded proof objects are accounted separately.

## Reversible normalization

`LinearData` retains its fields, with A sparse on the sparse path and all cost,
bound and integer arrays one-dimensional. Transform x=o+T*z uses an indexed
affine map: offset, original-variable index, direction and positive column scale.
There is no allocated n-by-k T. Fixed/free/reflected coordinates, interval row
sides, finite variable upper rows and row flips preserve the dense convention.

The sparse Normalization object preserves point/ray/multipliers operations,
data/offset/origins/column_origins/row_scale/col_scale/lower/upper/row_keys/column_keys.
Its transform is an indexed map, not an ndarray. The canonical objective is
MAX -s*f, s=+1 for original min and -1 for original max. Positive R/C scaling:
A_s=R*A*C, b_s=R*b, c_s=C*c, z=C*z_s; dual and reduced cost recovery retain
the existing directions. Slack/artificial columns are sparse unit columns.

## Propagation and original checks

Activity propagation iterates only row support while retaining exact-binary
Fraction arithmetic, outward bounds and reversed multiplier-source history.
Conflicts, deadlines and row redundancy keep their existing conservative rules.
KKT uses original sparse products and unchanged primal/dual/complementarity/
objective scales; primal tolerance never gains objective-pruning authority.
Exact Farkas and point/ray checks sum original nonzeros, without dense A.

`SolveResult._lp` remains `(norm,native,activity)`; native exposes matrix/rhs,
basis, row/column keys, point/dual/reduced/ray and diagnostics. Native matrix is
sparse, not None as a shortcut to avoid proof consumers. GMI and finite-pool
CG candidates explicitly adapt this representation. MIP local rows use the same
matrix append boundary; upper layers cannot force dense for sparse acceptance.

## Proof allocation and resource gates

Before any exact standard form or original-coordinate allocation, estimate its
rational cell count and check deadline/operation budget. Freeze a local workspace
ceiling of65536 rational cells; existing GMI basis80/Farkas basis160 and4096-bit/
proof-operation budgets are retained, never increased to pass a benchmark.

The gate applies once to the selected path's simultaneously live workspace,
not separately to each container. With original n variables/m rows, selected q
standard rows and p standard columns, freeze these conservative slot estimates:

- Basis-only candidate/Farkas: C=nnz(selected original rows)+4*q*q+8*q+3*n+3*m.
- Full tableau/GMI: C=q*n+q*p+p*n+4*q*q+8*q+4*p+3*n+3*m.

The terms include raw-row Fraction coefficients, standard rows, affine coordinate
vectors, original candidates, basis/transpose storage and elimination copies.
Count zero slots in dense local containers too. The implementation may omit a
term only by eliminating the corresponding live container, with allocation tests
covering that path. Use Python integer dimension/nnz arithmetic, no Fraction
conversion or model-sized temporary, to estimate C. Accept C<=65536; reject
C>=65537 before the first large Fraction container. Overestimation is safe.
Output strings are formed after temporary elimination work is released. A nested
proof path rechecks its total live estimate, including retained outer containers;
it cannot acquire several separately legal workspaces and exceed the ceiling.

Basis-only CG/Farkas reconstruction extracts selected B and original candidate
vectors directly, not all n-by-p coordinates. Full GMI views are allowed only
when their complete estimated cells fit the ceiling; otherwise skip the cut or
return the existing conservative no-proof result with a reason. Small existing
passive coordinate vectors retain their sequence contract for cuts/gmi.py.
An exact candidate is checked on all original rows and required full-pool columns;
reconstruction or traversal alone grants no optimality/infeasibility claim.

`max_sparse_nnz=1000000` bounds sparse A/standard storage before construction;
`max_factor_nnz=5000000` bounds factor storage separately. Actual nnz, double-view
storage, standard nnz, L/U nnz/fill and update vectors are reported. Zero limits
refuse allocations only when the relevant resource is needed. Resource exits are
explicit; a watchdog kill is a harness failure, not a solver-returned limit.

## Verification obligations

Track all allocation boundaries above and forbid global dense conversion in
tests. Cover fixed/free/reflected variables, min/max/constants, row intervals,
dependent/zero rows, integer-grid conversion, sparse KKT/Farkas/rays and proof
refusal. Existing dense tests remain unchanged. Sparse capacity and outside LP
success require actual correct optimal results under the fixed original checks.
