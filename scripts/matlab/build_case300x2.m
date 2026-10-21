function [mpc, map] = build_case300x2(source_case, cfg)
%BUILD_CASE300X2 Two copies, two physical circuits at the same terminal pair.
% Prototype: structurally mirrored/tested in Python; MATLAB/Octave not run.
% source_case must be the pinned UNSOLVED external-numbered case. No order
% metadata or OPF extension fields are accepted silently. cfg=jsondecode(...).
define_constants;
if ~isstruct(source_case), source_case = loadcase(source_case); end
s = source_case;
allowed = {'version','baseMVA','bus','gen','branch','gencost'};
extra = setdiff(fieldnames(s), allowed);
assert(isempty(extra), 'Unexpected fields/order: remap deliberately before construction');
assert(strcmp(s.version,'2') && s.baseMVA > 0);
n = size(s.bus,1); ng = size(s.gen,1); nl = size(s.branch,1);
assert(size(s.bus,2)==13 && size(s.branch,2)==13, 'Use unsolved matrices');
assert(size(s.gen,2)>=21 && isfield(s,'gencost'));
assert(ismember(size(s.gencost,1), [ng 2*ng]), 'P/Q cost row mismatch');
assert(numel(unique(s.bus(:,BUS_I)))==n);
assert(all(s.bus(:,BUS_TYPE)~=NONE), 'Minimum study excludes isolated source buses');
assert(numel(find(s.bus(:,BUS_TYPE)==REF))==1, 'Source must have one reference');
assert(study_is_connected(s), 'Source must be connected');
term = cfg.terminal_external_ids(:);
assert(numel(term)==2);
[found,tr] = ismember(term,s.bus(:,BUS_I));
assert(all(found), 'Terminals are original external IDs, not row numbers');
assert(s.bus(tr(1),BASE_KV)==s.bus(tr(2),BASE_KV), 'Tie terminals must have same kV');
assert(all(ismember(cfg.tie_status(:),[0 1])) && numel(cfg.tie_status)==2);
assert(sum(cfg.tie_status)>=1, 'Both-ties-out requires explicit island treatment');
assert(cfg.load_lambda>0 && abs(cfg.load_delta)<1);
t = cfg.tie;
assert(t.r_pu>=0 && t.x_pu>0 && t.rateA_MVA>0);
assert(ismember(t.tap,[0 1]) && t.shift_deg==0, 'Tie must be a unity-ratio line');
assert(t.angmin_deg<t.angmax_deg);
[found,gr] = ismember(s.gen(:,GEN_BUS),s.bus(:,BUS_I)); assert(all(found));
[found,fr] = ismember(s.branch(:,F_BUS),s.bus(:,BUS_I)); assert(all(found));
[found,tt] = ismember(s.branch(:,T_BUS),s.bus(:,BUS_I)); assert(all(found));
mpc = struct('version','2','baseMVA',s.baseMVA, ...
    'bus',zeros(2*n,size(s.bus,2)), 'gen',zeros(2*ng,size(s.gen,2)), ...
    'branch',zeros(2*nl+2,size(s.branch,2)));
map = struct();
map.bus = zeros(2*n,4); % [copy_index original_row original_external_ID new_ID]
map.gen = zeros(2*ng,4); % [copy_index original_row new_row new_P_cost_row]
map.branch = zeros(2*nl+2,3); % [copy_index original_row new_row]; tie copy=0
map.bus_ids = cell(2*n,1); map.gen_ids = cell(2*ng,1); map.branch_ids = cell(2*nl+2,1);
tags = 'AB';
for area=1:2
    br = (1:n)+(area-1)*n; gg=(1:ng)+(area-1)*ng; ll=(1:nl)+(area-1)*nl;
    b=s.bus; g=s.gen; l=s.branch;
    b(:,BUS_I)=(1:n)'+(area-1)*n;
    scale=cfg.load_lambda*(1+(3-2*area)*cfg.load_delta);
    b(:,[PD QD])=b(:,[PD QD])*scale;
    b(:,BUS_AREA)=b(:,BUS_AREA)+(area-1)*max(s.bus(:,BUS_AREA));
    b(:,ZONE)=b(:,ZONE)+(area-1)*max(s.bus(:,ZONE));
    if area==2, b(b(:,BUS_TYPE)==REF,BUS_TYPE)=PV; end
    g(:,GEN_BUS)=gr+(area-1)*n;
    l(:,F_BUS)=fr+(area-1)*n; l(:,T_BUS)=tt+(area-1)*n;
    mpc.bus(br,:)=b; mpc.gen(gg,:)=g; mpc.branch(ll,:)=l;
    map.bus(br,:)=[area*ones(n,1),(1:n)',s.bus(:,BUS_I),b(:,BUS_I)];
    map.gen(gg,:)=[area*ones(ng,1),(1:ng)',gg',gg'];
    map.branch(ll,:)=[area*ones(nl,1),(1:nl)',ll'];
    for j=1:n, map.bus_ids{br(j)}=sprintf('%c:bus:%d',tags(area),s.bus(j,BUS_I)); end
    for j=1:ng, map.gen_ids{gg(j)}=sprintf('%c:gen:%d',tags(area),j); end
    for j=1:nl, map.branch_ids{ll(j)}=sprintf('%c:branch:%d',tags(area),j); end
end
% Generator ordering is A then B. Costs must be [P_A; P_B; Q_A; Q_B].
mpc.gencost=[s.gencost(1:ng,:); s.gencost(1:ng,:)];
if size(s.gencost,1)==2*ng
    mpc.gencost=[mpc.gencost; s.gencost(ng+1:end,:); s.gencost(ng+1:end,:)];
    map.q_cost_rows=(2*ng+1:4*ng)';
end
for k=1:2
    rr=2*nl+k;
    mpc.branch(rr,:)=[tr(1),tr(2)+n,t.r_pu,t.x_pu,t.b_pu, ...
        t.rateA_MVA,t.rateB_MVA,t.rateC_MVA,t.tap,t.shift_deg, ...
        cfg.tie_status(k),t.angmin_deg,t.angmax_deg];
    map.branch(rr,:)=[0,k,rr]; map.branch_ids{rr}=sprintf('tie:%d',k);
end
assert(sum(mpc.bus(:,BUS_TYPE)==REF)==1);
ref=mpc.bus(mpc.bus(:,BUS_TYPE)==REF,BUS_I);
assert(any(mpc.gen(:,GEN_BUS)==ref & mpc.gen(:,GEN_STATUS)>0));
assert(study_is_connected(mpc));
assert(size(mpc.bus,1)==2*n && size(mpc.gen,1)==2*ng && size(mpc.branch,1)==2*nl+2);
map.config=cfg;
% No 'order' carried across concatenation. Obtain fresh ext2int metadata only
% after construction; use status.on/i2e maps when joining results by ID.
end

function yes = study_is_connected(m)
n=size(m.bus,1);
[a,fr]=ismember(m.branch(:,1),m.bus(:,1)); [b,tr]=ismember(m.branch(:,2),m.bus(:,1));
assert(all(a)&all(b));
on=m.branch(:,11)>0;
A=sparse([fr(on);tr(on)],[tr(on);fr(on)],1,n,n);
seen=false(n,1); todo=1;
while ~isempty(todo)
    u=todo(end); todo(end)=[];
    if seen(u), continue; end
    seen(u)=true; next=find(A(u,:)); todo=[todo,next(~seen(next))]; %#ok<AGROW>
end
yes=all(seen);
end
