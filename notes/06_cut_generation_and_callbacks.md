# Cut Generation and Callbacks

Cut generation should enter SILO only after pure branch-and-bound works. A cut is a valid inequality added to strengthen the relaxation. A bad cut can remove feasible integer solutions, so validity and scope must be treated carefully.

The first cut API should be small. A separator receives model and relaxation information and returns candidate cuts. A cut pool stores cuts, detects duplicates, and controls when cuts are applied. The MIP solver should be able to run with cuts disabled so branch-and-bound tests remain stable.

Callbacks should not become a hidden control channel. They should have documented inputs and outputs, and they should not silently mutate core model conventions. Early callbacks can be limited to logging, incumbent notification, and experimental cut separation.

The acceptance standard is not speed. The acceptance standard is that cuts are traceable, optional, and tested on small instances where the strengthened relaxation is easy to inspect.
