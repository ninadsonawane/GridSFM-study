function report = study_check_solution(input_case, result)
%STUDY_CHECK_SOLUTION Recompute physics from solved V and ORIGINAL equipment.
% Prototype, not executed here. Thresholds match docs/technical/matpower.md.
define_constants;
report.success=logical(result.success);
report.accepted_feasible=false;
assert(isequal(input_case.bus(:,BUS_I),result.bus(:,BUS_I)));
assert(isequal(input_case.gen(:,GEN_BUS),result.gen(:,GEN_BUS)));
assert(isequal(input_case.branch(:,[F_BUS T_BUS]),result.branch(:,[F_BUS T_BUS])));
% Start from original physics with solved state; never inherit stale order.
m=input_case;
m.bus(:,[VM VA])=result.bus(:,[VM VA]);
m.gen(:,[PG QG])=result.gen(:,[PG QG]);
if isfield(m,'order'), m=rmfield(m,'order'); end
m=ext2int(m);
[Y,Yf,Yt]=makeYbus(m.baseMVA,m.bus,m.branch);
V=m.bus(:,VM).*exp(1j*pi/180*m.bus(:,VA));
Snet=V.*conj(Y*V);
Sinj=makeSbus(m.baseMVA,m.bus,m.gen);
mis=Sinj-Snet;
Sf=V(m.branch(:,F_BUS)).*conj(Yf*V)*m.baseMVA;
St=V(m.branch(:,T_BUS)).*conj(Yt*V)*m.baseMVA;
report.max_p_residual_pu=max(abs(real(mis)));
report.max_q_residual_pu=max(abs(imag(mis)));
report.max_voltage_violation_pu=max([0; m.bus(:,VM)-m.bus(:,VMAX); m.bus(:,VMIN)-m.bus(:,VM)]);
report.max_pg_violation_MW=max([0; m.gen(:,PG)-m.gen(:,PMAX); m.gen(:,PMIN)-m.gen(:,PG)]);
report.max_qg_violation_MVAr=max([0; m.gen(:,QG)-m.gen(:,QMAX); m.gen(:,QMIN)-m.gen(:,QG)]);
rated=m.branch(:,RATE_A)>0;
report.rated_branch_count=sum(rated);
report.unrated_branch_count=sum(~rated);
report.max_rated_branch_excess_MVA=max([0; abs(Sf(rated))-m.branch(rated,RATE_A); abs(St(rated))-m.branch(rated,RATE_A)]);
% Use MATPOWER's own exact angle-bound convention, including one-sided zero.
opt=mpoption('opf.ignore_angle_lim',0);
[Aa,lo,hi]=makeAang(m.baseMVA,m.branch,size(m.bus,1),opt);
ad=Aa*(m.bus(:,VA)*pi/180);
report.max_angle_bound_violation_deg=max([0;lo-ad;ad-hi])*180/pi;
report.active_loss_MW=sum(real(Sf+St));
report.shunt_active_demand_MW=sum(m.bus(:,GS).*m.bus(:,VM).^2);
report.global_active_balance_MW=sum(m.gen(:,PG))-sum(m.bus(:,PD))-report.shunt_active_demand_MW-report.active_loss_MW;
if size(result.branch,2)>=QT
    rows=m.order.branch.status.on;
    reported=result.branch(rows,PF)+1j*result.branch(rows,QF);
    reported_t=result.branch(rows,PT)+1j*result.branch(rows,QT);
    report.max_flow_recomputation_difference_MVA=max([abs(Sf-reported);abs(St-reported_t)]);
end
ng=size(m.gen,1);
report.recomputed_objective=sum(totcost(m.gencost(1:ng,:),m.gen(:,PG)));
if size(m.gencost,1)==2*ng
    report.recomputed_objective=report.recomputed_objective+sum(totcost(m.gencost(ng+1:end,:),m.gen(:,QG)));
end
if isfield(result,'f'), report.objective_difference=report.recomputed_objective-result.f; end
metrics=[report.max_p_residual_pu,report.max_q_residual_pu,report.max_voltage_violation_pu, ...
    report.max_pg_violation_MW,report.max_qg_violation_MVAr,report.max_rated_branch_excess_MVA,report.max_angle_bound_violation_deg];
report.accepted_feasible=report.success && all(isfinite(metrics)) && ...
    all(metrics <= [1e-6 1e-6 1e-5 .0001 .0001 .0001 1e-4]);
report.scope='Voltage, rectangular generator limits, nodal AC balance, configured angle bounds, rated branch MVA at both ends; unlimited branches not thermally certified';
end
