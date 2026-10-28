# Import/readiness audit only. This script does not construct or solve a model.
using PowerModels, Ipopt, JuMP, JSON, LinearAlgebra, SHA
@assert VERSION == v"1.11.9"
@assert pkgversion(PowerModels) == v"0.21.5"
@assert pkgversion(Ipopt) == v"1.14.0"
@assert pkgversion(JuMP) == v"1.29.4"
@assert pkgversion(JSON) == v"0.21.4"
BLAS.set_num_threads(1)
record = Dict(
    "status" => "READY_IMPORTS_ONLY",
    "electrical_inputs_prepared" => 0,
    "solver_calls" => 0,
    "julia" => string(VERSION),
    "PowerModels" => string(pkgversion(PowerModels)),
    "Ipopt_jl" => string(pkgversion(Ipopt)),
    "JuMP" => string(pkgversion(JuMP)),
    "JSON" => string(pkgversion(JSON)),
    "MathOptInterface" => string(pkgversion(JuMP.MOI)),
    "active_project" => Base.active_project(),
    "depot_path" => DEPOT_PATH,
    "cpu" => Sys.CPU_NAME,
    "kernel" => string(Sys.KERNEL),
    "architecture" => string(Sys.ARCH),
    "blas" => sprint(show, BLAS.get_config()),
    "blas_threads" => BLAS.get_num_threads(),
    "project_sha256" => bytes2hex(sha256(read(joinpath(@__DIR__, "Project.toml")))),
    "manifest_sha256" => bytes2hex(sha256(read(joinpath(@__DIR__, "Manifest.toml"))))
)
println(JSON.json(record))
