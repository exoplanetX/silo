# Native Implementation Defer Decision

## Decision

On 2026-06-04, the user explicitly chose to defer native implementation for now.

This decision applies to the Phase 9 native implementation decision reviewed in
`notes/24_native_implementation_decision_packet.md`, including the selected
`tableau_leaving_row_ratio_test` candidate.

## Decision Meaning

The defer decision means:

- native implementation is not approved by this decision;
- the selected `tableau_leaving_row_ratio_test` candidate remains Python-reference only
  for now;
- Phase 9 may continue only with design, audit, policy, readiness, or bookkeeping tasks
  unless the user later explicitly approves a native implementation task;
- Phase 9 remains open;
- Phase 10 is not started.

## Preserved Boundaries

This decision does not:

- implement native backend code;
- add native dependencies;
- modify build or packaging files;
- change solver dispatch or backend selection behavior;
- change public CLI behavior;
- change JSON model or solution schemas;
- modify LP, MIP, presolve, cut/callback, decomposition, stochastic, or robust behavior;
- create generated native artifacts;
- close Phase 9;
- start Phase 10.

## Future Approval Boundary

Any future native implementation remains a separate L3 review gate. It must be issued as
a new atomic task and must require explicit user approval before execution.

The future approval template in `notes/24_native_implementation_decision_packet.md`
remains only a template. This defer decision is not that approval.
