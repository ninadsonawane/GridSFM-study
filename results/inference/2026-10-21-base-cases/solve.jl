using PowerModels, Ipopt, JuMP, JSON, LinearAlgebra
const PM = PowerModels
const OUT = @__DIR__
BLAS.set_num_threads(1)
# ACP polar formulation, preserving MATPOWER's unbounded +/-360 angle semantics.
# All branches in these two inputs have disabled angle limits; no finite angle
# restriction is introduced by PowerModels' normal correction path.
function build_original_opf(pm)
    PM.variable_bus_voltage(pm)
    PM.variable_gen_power(pm)
    PM.variable_branch_power(pm)
    PM.variable_dcline_power(pm)
    PM.objective_min_fuel_and_flow_cost(pm)
    PM.constraint_model_voltage(pm)
    for i in PM.ids(pm, :ref_buses)
        PM.constraint_theta_ref(pm, i)
    end
    for i in PM.ids(pm, :bus)
        PM.constraint_power_balance(pm, i)
    end
    for i in PM.ids(pm, :branch)
        b=PM.ref(pm,:branch,i)
        @assert b["angmin"] <= -2pi && b["angmax"] >= 2pi
        PM.constraint_ohms_yt_from(pm,i)
        PM.constraint_ohms_yt_to(pm,i)
        PM.constraint_thermal_limit_from(pm,i)
        PM.constraint_thermal_limit_to(pm,i)
    end
    @assert isempty(PM.ids(pm,:dcline))
end
optimizer=JuMP.optimizer_with_attributes(Ipopt.Optimizer,
    "tol"=>1e-9,"constr_viol_tol"=>1e-10,"acceptable_tol"=>1e-9,
    "bound_relax_factor"=>0.0,"max_iter"=>1000,"max_cpu_time"=>180.0,
    "print_level"=>5)
for name in ["case300","case300x2"]
    println("BEGIN ",name); flush(stdout)
    data=PM.parse_matpower(joinpath(OUT,name*".m");validate=false)
    PM.make_per_unit!(data)
    open(joinpath(OUT,name*"-powermodels-input.json"),"w") do io
        JSON.print(io,data,2)
    end
    t=time()
    result=PM.solve_model(data,PM.ACPPowerModel,optimizer,build_original_opf)
    result["elapsed_including_build_seconds"]=time()-t
    result["reference_policy"]="PowerModels ACP/Ipopt local AC-OPF; validate=false, per-unit only; no relaxation, angle constraints omitted only for original +/-360 disabled bounds; default solver initialization"
    result["versions"]=Dict("Julia"=>string(VERSION),"PowerModels"=>string(pkgversion(PM)),"Ipopt"=>string(pkgversion(Ipopt)))
    open(joinpath(OUT,name*"-reference-raw.json"),"w") do io
        JSON.print(io,result,2)
    end
    println("END ",name," ", result["termination_status"]," objective=",result["objective"]);flush(stdout)
end
