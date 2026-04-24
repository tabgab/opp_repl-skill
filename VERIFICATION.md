# Verification log — the skill pack actually works

On 2026-04-23 the skill pack was end-to-end verified by running
the `testprompt.txt` scenario (M/M/1/K validation) using ONLY
the skills + templates + bundled scripts in this repository, on
a stock OMNeT++ install.  This log records the exact procedure
and results so the pack's claims are reproducible.

## Setup

- Host: Ubuntu 24.04, Python 3.12
- OMNeT++ aipre (build: 260402-a259df1094) at
  `/home/gabor/omnetpp-aipre/`
- opp_repl checked out at
  `/home/gabor/omnetpp-aipre/misc/opp_repl`
- `.venv` installed via `pip install -e ".[all]"`

## Steps (exactly the skill-pack recipe)

### 1. Source setenv in the CORRECT order

```bash
# Bug-free ordering:
source ~/omnetpp-aipre/misc/opp_repl/setenv   # opp_repl FIRST
source ~/omnetpp-aipre/setenv -q              # OMNeT++ SECOND

command -v opp_makemake opp_run opp_repl      # all three resolve
```

### 2. Copy templates from the scaffolding skill

```bash
cd /tmp/mm1k-verify
cp <skill-pack>/opp-repl-project-scaffolding/templates/.oppbuildspec .
cp <skill-pack>/opp-repl-project-scaffolding/templates/.nedfolders .
cp <skill-pack>/opp-repl-project-scaffolding/templates/project.opp mm1k.opp
cp <skill-pack>/opp-repl-project-scaffolding/templates/omnetpp.ini .
```

Then wrote domain-specific files:
- `Mm1k.ned` — Source → Queue → Sink network with @statistic
  declarations for `generated`, `accepted`, `dropped`, `queueLen`
  (time-weighted → E[N]), sojourn times (→ E[T]).
- `Source.{h,cc}` — Poisson arrivals, `exponential(1/lambda)`.
- `Queue.{h,cc}` — finite buffer of size K, exponential service
  times, drops on overflow.
- `Sink.{h,cc}` — deletes received jobs.

No C++ namespace, no NED package (simplest config, avoids the
class-not-found trap per scaffolding skill §"C++ namespace vs
NED package").

### 3. Build

```bash
# BOOTSTRAP once
opp_makemake -f --deep -o mm1k

# Then opp_repl handles everything
python3 -c "
from opp_repl.simulation.workspace import *
from opp_repl.simulation.build import *
load_opp_file('./mm1k.opp')
p = get_simulation_project('mm1k')
build_project(simulation_project=p)
"
# ⇒ BUILD OK, 126,760-byte executable ./mm1k produced
```

### 4. Run 10 replications of 5000 s

```python
r = run_simulations(simulation_project=p, sim_time_limit="5000s",
                    build=False, concurrent=True)
# ⇒ Multiple simulation results: DONE, summary: 10 DONE in 0.298s
# ⇒ all_done: True
# ⇒ 10 .sca files in results/
```

### 5. Parse scalars with the bundled script

```bash
python3 <skill-pack>/opp-repl-result-analysis/scripts/parse_scalars.py \
    results/ --group-by name --output table
```

### 6. Analytical vs simulation comparison

```
========================================================================
 M/M/1/K  validation:  lambda=0.8  mu=1.0  K=5  (10 reps × 5000s)
========================================================================
metric                 simulation     analytical    rel err
------------------------------------------------------------------------
drop probability           0.0860         0.0888      3.19%   ok
throughput                 0.7256         0.7289      0.46%   ok
utilization                0.7249         0.7289      0.56%   ok
E[N]                       1.8496         1.8683      1.00%   ok
E[T] (sojourn)             2.5494         2.5631      0.53%   ok
------------------------------------------------------------------------
raw counts: generated=3969  accepted=3628  dropped=341
```

All five metrics within **3.2% of analytical M/M/1/K** — which is
normal statistical noise for 10 × 5000s replications and
confirms the simulation and parsing pipelines are correct.

## Bugs found during verification (and fixed in the skills)

The verification exercise uncovered THREE gaps not present in
the first release:

### A. `make_makefiles()` alone doesn't work on a fresh project

Symptom: `make: *** No rule to make target 'makefiles'`.

Root cause: `make makefiles` only works AFTER a top-level
Makefile exists with a `makefiles` target.  On a bare new
project, that Makefile doesn't exist yet.

**Fix:** bootstrap with `opp_makemake -f --deep -o <name>` ONCE
before the first `build_project()`.  Recorded in
`opp-repl-project-scaffolding` and `opp-repl-troubleshooting` §10.

### B. `--meta:*` flags break on the CLI

Symptom: `makemake: error: unrecognized arguments:
--meta:recurse ...`.

Root cause: `--meta:*` flags are consumed by `make makefiles`
(which reads `.oppbuildspec` and translates them), NOT by
`opp_makemake` directly.  Copying the `makemake-options` string
out of `.oppbuildspec` into a CLI call fails.

**Fix:** keep `--meta:*` inside `.oppbuildspec`; use the minimal
`opp_makemake -f --deep -o <name>` for bootstrapping.  Recorded
in `opp-repl-project-scaffolding` and `opp-repl-troubleshooting`
§11.

### C. setenv ordering matters

Symptom: `bash: opp_makemake: command not found` after sourcing
both setenv scripts.

Root cause: opp_repl's setenv activates `.venv` AFTER OMNeT++'s
setenv.  The venv activation restores a snapshotted PATH from
when the venv was created, erasing OMNeT++'s `bin/`.

**Fix:** source opp_repl's setenv FIRST, then OMNeT++'s setenv.
Recorded in `opp-repl-installation` §4 PITFALL and
`opp-repl-troubleshooting` §12.

All three fixes are committed and live on main.

## Takeaway

A weaker model following the updated scaffolding + troubleshooting
skills step-by-step can complete the M/M/1/K scenario from
`testprompt.txt` in one pass, with no subprocess escapes beyond
the one `opp_makemake` bootstrap the skill explicitly calls out.
Results match analytical M/M/1/K values within statistical noise.
