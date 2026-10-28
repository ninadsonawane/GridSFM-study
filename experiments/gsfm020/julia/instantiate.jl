# Instantiate the pinned upstream Julia project in an externally set isolated depot.
# No electrical input is prepared or solved by this script. JULIA_DEPOT_PATH must
# point to the task-local work directory before Julia starts.
using Pkg
Pkg.instantiate(; allow_autoprecomp=false)
