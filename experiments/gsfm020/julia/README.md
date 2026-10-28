# Local Julia solver environment

The portable Windows Julia 1.11.9 archive matches the official SHA-256
`1ae5f16cb10cf23089e002626304c467a8d14ba750a7e02dff32df7cdec85074`.
The adjacent Project/Manifest files are unchanged copies from Microsoft GridSFM
commit `1ca775fd436d7ce013a1c0ab946e61ac7ef59ad6`, directory
`power_grid/US/topology_solver_pipeline/`.

Verified imports: PowerModels 0.21.5, Ipopt.jl 1.14.0, JuMP 1.29.4,
JSON 0.21.4, MathOptInterface 1.49.0. The exact historical server at
`../solver_server.jl` starts successfully and reports the original tolerances.
The setup audit sent only a quit request: no network was prepared or solved.
See `environment-readiness.json` for absolute paths, hashes and setup incidents.

From the task workspace in PowerShell:

```powershell
$env:JULIA_DEPOT_PATH = Join-Path (Get-Location) 'work\julia\depot'
$env:OPENBLAS_NUM_THREADS = '1'
$julia = 'work\julia\julia-1.11.9\bin\julia.exe'
$project = 'work/GridSFM-study/experiments/gsfm020/julia'
& $julia --startup-file=no --history-file=no --project=$project "$project/instantiate.jl"
& $julia --startup-file=no --history-file=no --compiled-modules=existing --project=$project "$project/verify_environment.jl"
'{"quit":true}' | & $julia --startup-file=no --history-file=no --compiled-modules=existing --project=$project 'work/GridSFM-study/experiments/gsfm020/solver_server.jl'
```

The upstream lock targets Julia 1.11.5; 1.11.9 matches the documented historical
runtime. Pkg warned that the unchanged upstream Project/Manifest pair had stale
dependency metadata. No resolve or update was run, and both file hashes remain
unchanged. The historical Mac transitive environment is unavailable; this local
installation matches recorded main-package versions, not the complete Mac
environment. Every actual AC reference still needs independent physical checks.
