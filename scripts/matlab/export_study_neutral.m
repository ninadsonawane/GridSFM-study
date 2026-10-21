function export_study_neutral(input_case, result, map, out_prefix)
%EXPORT_STUDY_NEUTRAL Separate inference INPUTS from solved LABELS.
% Prototype unexecuted. JSON encoding requires a modern MATLAB/Octave runtime.
% Results remain external-row-aligned; physical IDs persist through outages.
define_constants;
input=struct('version','2','baseMVA',input_case.baseMVA, ...
    'bus',input_case.bus(:,1:13),'gen',input_case.gen(:,1:21), ...
    'branch',input_case.branch(:,1:13),'gencost',input_case.gencost);
input.bus_ids=map.bus_ids; input.gen_ids=map.gen_ids; input.branch_ids=map.branch_ids;
write_json([out_prefix '-input.json'],input);
write_json([out_prefix '-map.json'],map);
if isempty(result), return; end
check=study_check_solution(input_case,result);
label=struct('vm',result.bus(:,VM),'va_deg',result.bus(:,VA), ...
    'pg_mw',result.gen(:,PG),'qg_mvar',result.gen(:,QG), ...
    'pf_mw',result.branch(:,PF),'qf_mvar',result.branch(:,QF), ...
    'pt_mw',result.branch(:,PT),'qt_mvar',result.branch(:,QT), ...
    'objective',check.recomputed_objective,'solver_success',logical(result.success), ...
    'accepted_feasible',check.accepted_feasible);
write_json([out_prefix '-labels.json'],label);
write_json([out_prefix '-validation.json'],check);
end

function write_json(path, data)
fid=fopen(path,'w'); assert(fid~=-1,'Cannot open output');
cleanup=onCleanup(@() fclose(fid)); %#ok<NASGU>
fprintf(fid,'%s\n',jsonencode(data));
end
