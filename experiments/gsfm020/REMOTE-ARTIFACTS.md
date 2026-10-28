# GSFM-020: access from another device

The completed 26 October 2026 analysis is now prepared for the user's 28 October request to push all analysis and evidence to this repository. No new experiment is part of this transfer.

- [Read the full report](REPORT.md), including the compact comparison table and three confirmed findings.
- [Browse all 104 method rows](../../results/comparisons/GSFM-020/20261026-local-operating-conditions/live-table.md).
- [Download the full evidence release](https://github.com/ninadsonawane/GridSFM-study/releases/tag/gsfm-020-2026-10-26).
- [Direct evidence ZIP](https://github.com/ninadsonawane/GridSFM-study/releases/download/gsfm-020-2026-10-26/GSFM-020-evidence.zip) and [SHA-256 file](https://github.com/ninadsonawane/GridSFM-study/releases/download/gsfm-020-2026-10-26/GSFM-020-evidence.zip.sha256).

The repository contains the new experiment code, protocol, frozen plans, summary tables, figures, diagnostic review, confirmation evidence and independent verification. The release asset retains every attempted input, native tensor return, prepared tensor, clamp observation, solver trace, failed iterate, large location table and the original delivery manifest. It also includes the prior tracked study snapshot as it stood during the experiment. Small derived cycle caches saved inside diagnostic attempts are included; installed runtimes, model checkpoint binaries and global runtime caches are not.

Evidence ZIP: **54,872,758 bytes**. SHA-256:

```text
32f6dda1ea3238d78920f8efd212139f0dad65eea44cf3098eaee70855e62754
```

On the other device, open the report directly on GitHub, or pull `main`. Download and extract the ZIP into a separate folder; `report.md` is its reading entry point and `study/` contains the complete evidence snapshot. Keeping that extraction separate preserves its original hashes and avoids replacing the newer repository entry points.

```sh
git clone https://github.com/ninadsonawane/GridSFM-study.git
# For an existing clean checkout instead:
git pull --ff-only

# Optional if GitHub CLI is available:
gh release download gsfm-020-2026-10-26 --repo ninadsonawane/GridSFM-study --pattern 'GSFM-020-evidence.zip*'
```

Windows checksum check: `Get-FileHash -Algorithm SHA256 GSFM-020-evidence.zip`.
macOS/Linux checksum check: `shasum -a 256 GSFM-020-evidence.zip`.

The saved results require no model/runtime installation to read. Recomputing numerical audits requires the dependencies in [REPRODUCE.md](REPRODUCE.md); those Windows paths describe the actual run, not an already configured environment on the other device. Exact checkpoint/source URLs and hashes are retained. The original full final verifier enforces its historical deadline; the later saved-state review entry points are documented separately. This transfer does not authorize or launch further experiments.

The repository README and HANDOFF receive dated entry points on 28 October. The immutable ZIP preserves all 929 earlier tracked file hashes and the full original local verification record. Historical statements that raw results were local-only describe their earlier release status; this asset supplies durable access to the GSFM-020 bundle, not to missing raw files from other experiments.

Data provenance is retained in the archive: MATPOWER 8.1 case300, pinned source hash and original UW/PSTCA attribution. MATPOWER's software BSD license excludes case data; the [UW archive policy](https://labs.ece.uw.edu/pstca/pg_tcaintro.htm) describes research and educational use, and the [IEEE300 page](https://labs.ece.uw.edu/pstca/pf300/pg_tca300bus.htm) supplies provenance. No BSD license is asserted for the case data.
