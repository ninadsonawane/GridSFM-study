import datetime, hashlib, json, pathlib, subprocess, zipfile

workspace = pathlib.Path(__file__).resolve().parent.parent
repo = pathlib.Path(r'C:\Users\Ninad\Documents\Codex\2026-10-26\don-t-wait-for-max-anything\work\GridSFM-study')
prior = workspace / 'outputs/GridSFM-loading-study'
source_repo = repo.parent / 'runtime/sources/newer'
pin = '517a07531ea55a11bd81a89a6c6879695a2ba4b4'
extension = repo / 'studies/2026-11-04-official-pf-completion'
assert not extension.exists(), 'Refusing to replace an existing extension'
for folder in ('code', 'paper', 'literature', 'manifests', 'validation', 'results'):
    (extension / folder).mkdir(parents=True)
objective = pathlib.Path(r'C:\Users\Ninad\.codex\attachments\bead3fb5-7f6c-4357-928e-d6e7375a11d9\pasted-text-1.txt')
(extension / 'protocol-objective.txt').write_bytes(objective.read_bytes())
inventory = json.loads((prior / 'artifact-sha256.json').read_text())
for relative, digest in inventory.items():
    assert hashlib.sha256((prior / relative).read_bytes()).hexdigest() == digest, relative
manifest = json.loads((prior / 'manifest.json').read_text())
plan = json.loads((prior / 'scenario-plan.json').read_text())
verification = json.loads((prior / 'final-verification.json').read_text())
archive = workspace / 'outputs/GridSFM-loading-study-evidence.zip'
archive_sha = hashlib.sha256(archive.read_bytes()).hexdigest()
assert archive_sha == '185cc64b3e08416c6adae56f6efb00a4781068d920457968ff9c5486ed0414c6'
assert subprocess.check_output(['git','rev-parse','HEAD'], cwd=source_repo, text=True).strip() == pin
source_dest = repo / 'work/official-v2-517a075'
source_zip = workspace / 'work/official-v2-517a075.zip'
if not source_dest.exists():
    subprocess.run(['git','archive','--format=zip','--output='+str(source_zip),pin], cwd=source_repo, check=True)
    with zipfile.ZipFile(source_zip) as z:
        for item in z.infolist():
            target = (source_dest / item.filename).resolve()
            assert target.is_relative_to(source_dest.resolve())
        z.extractall(source_dest)
source_hashes = {str(p.relative_to(source_dest)).replace('\\','/'): hashlib.sha256(p.read_bytes()).hexdigest()
                 for p in source_dest.rglob('*') if p.is_file()}
audit = {'status':'PASS', 'checked_UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),
         'prior_files_verified':len(inventory), 'prior_archive_sha256':archive_sha,
         'prior_inventory_sha256':hashlib.sha256((prior/'artifact-sha256.json').read_bytes()).hexdigest(),
         'prior_revision':subprocess.check_output(['git','rev-parse','HEAD'], cwd=repo,text=True).strip(),
         'prior_results':verification, 'source_commit':pin,
         'source_export':'git archive of exact committed tree; does not reuse dirty working files',
         'source_files':source_hashes,
         'environment_location_note':'Requested macOS paths are not mounted on this Windows host. Existing verified Windows repository and runtime are reused. The referenced Mac checklist/audit notes are unavailable locally; the complete new objective controls this extension.'}
(extension/'manifests/reuse-audit.json').write_text(json.dumps(audit,indent=2)+'\n',encoding='utf-8')
(workspace/'work/pf-extension-locations.json').write_text(json.dumps({'repo':str(repo),'extension':str(extension),'prior':str(prior),'source':str(source_dest)},indent=2)+'\n')
(extension/'.gitattributes').write_text('* -text whitespace=cr-at-eol\n',encoding='utf-8')
(extension/'.gitignore').write_text('results/\n__pycache__/\npaper/*.aux\npaper/*.log\npaper/*.out\npaper/*.bbl\npaper/*.blg\n',encoding='utf-8')
(extension/'README.md').write_text('''# Official V2 power-flow completion extension

Status: ACTIVE. This is a new authorized extension of [the completed independent P/Q loading study](../2026-11-04-independent-pq-loading/README.md). Earlier stop instructions are historical for this explicitly requested work. No prior study file is overwritten.

Question: when P and Q demand change independently, which observed errors arise in native GridSFM output, which persist in predicted controls after the author Newton completion, and which operating limits remain unsatisfied?

## Scope and completion ledger

- [x] Read complete objective and current repository instructions; confirm main and origin/main match before work.
- [x] Verify every prior artifact hash and the full published archive; reuse existing 59 inputs and states.
- [x] Export the exact author revision from its Git object database, independent of working-tree newline changes.
- [ ] Inspect primary literature sections and complete the prior-work distinction table.
- [ ] Map official callers, presets, preprocessing, physics and stage availability.
- [ ] Validate case500goc integration, then all three networks and reference-control/perturbation gates.
- [ ] Freeze adapter settings and provenance; expand the three nominal baseline tables.
- [ ] Run all 59 matched frozen V2 + official PF inputs and verified compatible adapted stages.
- [ ] Complete all metrics, failure/coverage records and loading figures.
- [ ] Integrate case 3 with exact electrical accounting.
- [ ] Perform final focused endpoint sensitivity; no extra variation family.
- [ ] Falsify candidate claims against matched results and closest literature.
- [ ] Compile actual IEEE source; inspect five-page PDF including references; draft unsent Dr. Li note.
- [ ] Audit every requirement and publish durable reproducibility artifacts with checksums.

The full controlling protocol is [protocol-objective.txt](protocol-objective.txt). Raw extension outputs live in `results/`, separate from native states linked through the prior archive. Installed dependencies and checkpoint binaries remain outside Git. Paid compute, long training, correspondence and submission are not authorized.
''',encoding='utf-8')
(extension/'paper/manuscript.tex').write_text(r'''\documentclass[conference]{IEEEtran}
\usepackage{amsmath,graphicx,booktabs,url}
\title{Native and Newton-Completed GridSFM Responses to Independent Active and Reactive Loading}
\author{\IEEEauthorblockN{Author list pending confirmation}}
\begin{document}
\maketitle
\begin{abstract}
This working skeleton asks which errors of frozen GridSFM persist after the released Newton power-flow completion under matched active and reactive loading. Results and contribution statements remain pending the extension audit and execution.
\end{abstract}
\begin{IEEEkeywords}Optimal power flow, power flow, neural networks, physical feasibility\end{IEEEkeywords}
\section{Introduction and Related Work}
The central question separates native prediction errors, errors in prescribed controls after completion, and operational constraint violations. Generic accuracy--feasibility differences are established knowledge; an additional contribution requires a matched, literature-bounded observation.
\section{Matched Study and Official Workflow}
Reuse the frozen three-network, 59-input protocol. Distinguish native outputs, frozen controls plus official completion, verified target-adapted controls plus completion, and downstream procedures outside this scope.
\section{Baseline and Independent P/Q Loading}
Pending validated stage integration and complete matched evaluation.
\section{Case-3 Electrical Accounting}
Pending matched native/completed distribution and equipment comparison.
\section{Focused Response Sensitivity}
Pending endpoint reuse; separate baseline offsets from direction and magnitude errors.
\section{Supported Understanding and Limitations}
No novelty, model benefit, speedup, objective-quality or generalization claim is established by this skeleton.
\bibliographystyle{IEEEtran}
\bibliography{references}
\end{document}
''',encoding='utf-8')
(extension/'literature/comparison.md').write_text('''# Primary-literature comparison (started before new results)

Status: full-text section inspection in progress; no novelty conclusion yet.

| Primary source | Prior question/task | Evaluated workflow and relevant finding | Exact distinction to test | Section evidence |
|---|---|---|---|---|
| [GridSFM V2](https://arxiv.org/html/2609.30173v2) | AC-OPF foundation model, target-grid adaptation and completion | Pending sections IV/VI plus pinned source/callers | Matched native frozen controls versus the same controls completed; target adaptation separately | Pending |
| [Singh, Kekatos and Giannakis](https://arxiv.org/abs/2103.14779) | Sensitivity-informed AC-OPF training | Pending full methods/results inspection | Post-hoc directional finite differences of frozen/completed stages; no sensitivity-informed training implemented | Pending |
| [Liu, Wu and Zhu](https://arxiv.org/abs/2205.10129) | Topology-aware AC-OPF prediction and feasibility | Pending full methods/results inspection | Separate equality completion from original-equipment feasibility under independently varied P/Q | Pending |
| [Huang, Chen and Low](https://www.mhchen.com/papers/DeepOPF_NGT.TPS.24.pdf) | Unsupervised AC-OPF learning without ground-truth training labels | Pending full methods/results inspection | Frozen released outputs and author completion, without learning a new load-solution mapping | Pending |
| [Physics-Informed but Not Physics-Consistent](https://arxiv.org/html/2610.05959v1) | Neural AC-PF output-error geometry and projection | Pending full methods/results inspection | Distinguish AC-PF from released AC-OPF control prediction, Newton completion and original operational constraints | Pending |
''',encoding='utf-8')
print(json.dumps({'extension':str(extension),'prior_files_verified':len(inventory),'source_files':len(source_hashes),'source':str(source_dest),'prior_verification':verification},indent=2))
