t_process=time()
using PowerModels, Ipopt, JuMP, JSON, LinearAlgebra
const PM=PowerModels
const MOI=JuMP.MOI
const OUT=@__DIR__
BLAS.set_num_threads(1)
function build_original(pm)
    PM.variable_bus_voltage(pm);PM.variable_gen_power(pm);PM.variable_branch_power(pm);PM.variable_dcline_power(pm)
    PM.objective_min_fuel_and_flow_cost(pm);PM.constraint_model_voltage(pm)
    for i in PM.ids(pm,:ref_buses); PM.constraint_theta_ref(pm,i); end
    for i in PM.ids(pm,:bus); PM.constraint_power_balance(pm,i); end
    for i in PM.ids(pm,:branch)
        b=PM.ref(pm,:branch,i)
        if b["angmin"] > -2pi || b["angmax"] < 2pi; PM.constraint_voltage_angle_difference(pm,i); end
        PM.constraint_ohms_yt_from(pm,i);PM.constraint_ohms_yt_to(pm,i)
        PM.constraint_thermal_limit_from(pm,i);PM.constraint_thermal_limit_to(pm,i)
    end
    @assert isempty(PM.ids(pm,:dcline))
end
const OPTS=Dict("tol"=>1e-9,"constr_viol_tol"=>1e-10,"acceptable_tol"=>1e-9,"bound_relax_factor"=>0.0,"max_iter"=>3000,"max_cpu_time"=>120.0,"print_level"=>0)
println(JSON.json(Dict("ready"=>true,"julia_import_seconds"=>time()-t_process,"julia"=>string(VERSION),"PowerModels"=>string(pkgversion(PM)),"Ipopt"=>string(pkgversion(Ipopt)),"options"=>OPTS)));flush(stdout)
for line in eachline(stdin)
    req=JSON.parse(line);get(req,"quit",false) && break
    id=req["run_id"];logpath=req["log_path"]
    try
        result=open(logpath,"w") do logio
            redirect_stdout(logio) do
                t=time_ns()
                data=PM.parse_matpower(req["matpower_file"];validate=false);PM.make_per_unit!(data)
                if req["method"]=="flat"
                    for (bid,b) in data["bus"];b["vm_start"]=clamp(1.,b["vmin"],b["vmax"]);b["va_start"]=0.;end
                    for (gid,g) in data["gen"];g["pg_start"]=(g["pmin"]+g["pmax"])/2;g["qg_start"]=(g["qmin"]+g["qmax"])/2;end
                elseif req["method"]=="gridsfm"
                    s=JSON.parsefile(req["initialization_file"])
                    for (bid,b) in data["bus"]
                        v=s["bus"][bid];b["vm_start"]=v["vm"];b["va_start"]=v["va"]
                    end
                    for (gid,g) in data["gen"]
                        v=s["gen"][gid];g["pg_start"]=v["pg"];g["qg_start"]=v["qg"]
                    end
                    for (eid,b) in data["branch"]
                        v=s["branch"][eid]
                        for k in ["pf","qf","pt","qt"]; b[k*"_start"]=v[k]; end
                    end
                end
                network_fields=Dict("branch"=>Dict(k=>Dict(n=>b[n] for n in ["br_r","br_x","br_b","tap","shift","angmin","angmax"] if haskey(b,n)) for (k,b) in data["branch"]),"gen"=>Dict(k=>Dict(n=>g[n] for n in ["pmin","pmax","qmin","qmax"]) for (k,g) in data["gen"]))
                for (k,b) in data["branch"]; if haskey(b,"rate_a");network_fields["branch"][k]["rate_a"]=b["rate_a"];end;end
                pm=PM.instantiate_model(data,PM.ACPPowerModel,build_original)
                # Record all JuMP VariablePrimalStart values in the actual model.
                starts=Dict{String,Any}()
                for sym in [:vm,:va,:pg,:qg,:p,:q]
                    vs=PM.var(pm,sym)
                    starts[string(sym)]=Dict(string(k)=>JuMP.start_value(vs[k]) for k in axes(vs,1))
                end
                initial_iterate=Dict{String,Any}();trace=Any[]
                cb=function(alg,iter,obj,inf_pr,inf_du,mu,d_norm,reg,ad,ap,ls)
                    push!(trace,Dict("iteration"=>iter,"objective"=>obj,"primal_infeasibility"=>inf_pr,"dual_infeasibility"=>inf_du))
                    if iter==0 && isempty(initial_iterate)
                        for sym in [:vm,:va,:pg,:qg,:p,:q]
                            vs=PM.var(pm,sym)
                            initial_iterate[string(sym)]=Dict(string(k)=>JuMP.callback_value(pm.model,vs[k]) for k in axes(vs,1))
                        end
                        if get(req,"capture_internal_iterate",false)
                            backend=JuMP.unsafe_backend(pm.model);prob=backend.inner
                            xx=zeros(prob.n);zl=zeros(prob.n);zu=zeros(prob.n);gg=zeros(prob.m);ll=zeros(prob.m)
                            Ipopt.GetIpoptCurrentIterate(prob,false,prob.n,xx,zl,zu,prob.m,gg,ll)
                            live=Dict{String,Any}()
                            for sym in [:vm,:va,:pg,:qg,:p,:q]
                                vs=PM.var(pm,sym)
                                live[string(sym)]=Dict(string(k)=>xx[Ipopt.column(JuMP.optimizer_index(vs[k]))] for k in axes(vs,1))
                            end
                            initial_iterate["actual_internal_unscaled_primal"]=live
                        end
                    end
                    return (time_ns()-t)/1e9 < req["remaining_seconds"]
                end
                JuMP.set_attribute(pm.model,Ipopt.CallbackFunction(),cb)
                opts=copy(OPTS);opts["max_cpu_time"]=max(0.001,req["remaining_seconds"]-(time_ns()-t)/1e9)
                optimizer=JuMP.optimizer_with_attributes(Ipopt.Optimizer,[k=>v for (k,v) in opts]...)
                t_build=(time_ns()-t)/1e9;t_solve=time_ns()
                r=PM.optimize_model!(pm;optimizer=optimizer)
                elapsed=(time_ns()-t_solve)/1e9
                r["parsed_network"]=data;r["network_fields"]=network_fields
                r["iterations"]=JuMP.get_attribute(pm.model,MOI.BarrierIterations())
                r["initial_starts"]=starts;r["iteration_zero_primal"]=initial_iterate;r["iteration_trace"]=trace
                r["parse_build_seconds"]=t_build;r["optimize_call_seconds"]=elapsed;r["method"]=req["method"]
                r["run_id"]=id;r["load_scale"]=req["load_scale"];r["options"]=OPTS
                open(req["result_path"],"w") do io;JSON.print(io,r,2);end
                Dict("ok"=>true,"result_path"=>req["result_path"],"iterations"=>r["iterations"],"termination_status"=>string(r["termination_status"]))
            end
        end
        println(JSON.json(result));flush(stdout)
    catch e
        failure=Dict("ok"=>false,"error"=>sprint(showerror,e,catch_backtrace()),"request"=>req)
        open(req["result_path"]*"-failure.json","w") do io;JSON.print(io,failure,2);end
        println(JSON.json(failure));flush(stdout)
    end
end
