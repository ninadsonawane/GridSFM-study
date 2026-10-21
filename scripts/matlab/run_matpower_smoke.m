function run_matpower_smoke(repo_root, run_dir)
%RUN_MATPOWER_SMOKE Source + synthetic AC PF/OPF; saves successes AND failures.
% Prototype NOT run in this research session (no MATLAB/Octave detected).
% Install pinned MATPOWER8.1 on current path before calling.
assert(exist('runopf','file')==2,'Install pinned MATPOWER8.1 first');
if nargin<2, run_dir=fullfile(repo_root,'runs','matpower-smoke'); end
assert(~exist(run_dir,'dir'),'Use a new run directory; preserve earlier runs');
mkdir(run_dir);
addpath(fullfile(repo_root,'scripts','matlab'));
source=loadcase(fullfile(repo_root,'data','source','matpower-8.1','case300.m'));
cfg=jsondecode(fileread(fullfile(repo_root,'configs','network-case300x2.json')));
[connected,map]=build_case300x2(source,cfg);
cfg.tie_status=[1 0]; [outage,outmap]=build_case300x2(source,cfg);
cfg.load_lambda=1; cfg.load_delta=.1; cfg.tie_status=[1 1];
[asymmetric,amap]=build_case300x2(source,cfg);
cases={source,connected,outage,asymmetric};
names={'official-case300','constructed-symmetric','constructed-one-tie','constructed-asymmetric'};
maps={make_base_map(source),map,outmap,amap};
opt=mpoption('model','AC','pf.alg','NR','pf.tol',1e-9, ...
    'pf.enforce_q_lims',1,'opf.ac.solver','MIPS','opf.start',1, ...
    'opf.flow_lim','S','opf.violation',1e-7,'mips.feastol',1e-8, ...
    'mips.gradtol',1e-8,'mips.comptol',1e-8,'mips.costtol',1e-8, ...
    'mips.max_it',150,'verbose',1,'out.all',0);
meta=struct('matpower_version',mpver,'runtime_version',version, ...
    'computer',computer,'started',datestr(now,30),'options',opt, ...
    'source_commit','1a828c7af590714499284e36ee9c81273388c594');
save(fullfile(run_dir,'environment.mat'),'meta');
diary(fullfile(run_dir,'console.log'));
diary_cleanup=onCleanup(@() diary('off')); %#ok<NASGU>
disp(meta);
for i=1:numel(cases)
    input_case=cases{i}; map=maps{i}; prefix=fullfile(run_dir,names{i});
    export_study_neutral(input_case,[],map,prefix);
    for mode=1:2
        kind={'pf','opf'}; this_kind=kind{mode};
        try
            tic;
            if mode==1, result=runpf(input_case,opt); else, result=runopf(input_case,opt); end
            elapsed=toc;
            check=study_check_solution(input_case,result); check.elapsed_seconds=elapsed;
            save([prefix '-' this_kind '.mat'],'input_case','result','check','map','opt');
            export_study_neutral(input_case,result,map,[prefix '-' this_kind]);
            disp(names{i}); disp(this_kind); disp(check);
        catch exception
            failure=struct('identifier',exception.identifier,'message',exception.message, ...
                'scope','Numerical or implementation failure; not an infeasibility certificate');
            save([prefix '-' this_kind '-failure.mat'],'input_case','failure','map','opt');
            disp(failure);
        end
    end
end
end

function map=make_base_map(m)
map.bus_ids=arrayfun(@(v) sprintf('source:bus:%d',v),m.bus(:,1),'UniformOutput',false);
map.gen_ids=arrayfun(@(v) sprintf('source:gen:%d',v),(1:size(m.gen,1))','UniformOutput',false);
map.branch_ids=arrayfun(@(v) sprintf('source:branch:%d',v),(1:size(m.branch,1))','UniformOutput',false);
end
