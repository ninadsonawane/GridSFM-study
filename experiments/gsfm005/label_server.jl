using PowerModels,Ipopt,JuMP,JSON,LinearAlgebra
const PM=PowerModels
BLAS.set_num_threads(1)
function build_original(pm)
    PM.variable_bus_voltage(pm);PM.variable_gen_power(pm);PM.variable_branch_power(pm);PM.variable_dcline_power(pm)
    PM.objective_min_fuel_and_flow_cost(pm);PM.constraint_model_voltage(pm)
    for i in PM.ids(pm,:ref_buses);PM.constraint_theta_ref(pm,i);end
    for i in PM.ids(pm,:bus);PM.constraint_power_balance(pm,i);end
    for i in PM.ids(pm,:branch)
        b=PM.ref(pm,:branch,i);@assert b["angmin"]<=-2pi && b["angmax"]>=2pi
        PM.constraint_ohms_yt_from(pm,i);PM.constraint_ohms_yt_to(pm,i)
        PM.constraint_thermal_limit_from(pm,i);PM.constraint_thermal_limit_to(pm,i)
    end
    @assert isempty(PM.ids(pm,:dcline))
end
opt=JuMP.optimizer_with_attributes(Ipopt.Optimizer,"tol"=>1e-9,"constr_viol_tol"=>1e-10,"acceptable_tol"=>1e-9,"bound_relax_factor"=>0.0,"max_iter"=>1000,"max_cpu_time"=>180.0,"print_level"=>0)
println("READY");flush(stdout)
for line in eachline(stdin)
    req=JSON.parse(line);get(req,"quit",false)&&break
    try
        result=open(req["log_path"],"w") do io
            redirect_stdout(io) do
                data=PM.parse_matpower(req["matpower_path"];validate=false);PM.make_per_unit!(data)
                r=PM.solve_model(data,PM.ACPPowerModel,opt,build_original)
                open(req["result_path"],"w") do f;JSON.print(f,r,2);end
                Dict("status"=>string(r["termination_status"]),"objective"=>r["objective"])
            end
        end
        println(JSON.json(result));flush(stdout)
    catch e
        println(JSON.json(Dict("status"=>"ERROR","error"=>sprint(showerror,e,catch_backtrace()))));flush(stdout)
    end
end
