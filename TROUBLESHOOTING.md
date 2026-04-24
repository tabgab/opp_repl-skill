# Troubleshooting opp_repl — quick reference

If you hit an opp_repl error and don't know which skill to load,
start here.  This file is an **index** into
`opp-repl-troubleshooting/SKILL.md`, which contains the full
decode table for every common failure.

## Symptom lookup

| What you see                                               | Load skill + section                          |
|------------------------------------------------------------|-----------------------------------------------|
| `Exception: Building <X> failed` (no other info)           | `opp-repl-troubleshooting` §1                 |
| `ERROR (Non-zero exit code: 127)` on every simulation run  | `opp-repl-troubleshooting` §2                 |
| `tr.stdout` / `tr.stderr` is `None` after ERROR            | `opp-repl-troubleshooting` §3                 |
| `Class '<Name>' not found` during simulation startup       | `opp-repl-troubleshooting` §4                 |
| `No targets specified and no makefile found`               | `opp-repl-troubleshooting` §1, §5             |
| `make: *** No rule to make target 'makefiles'`             | `opp-repl-troubleshooting` §10                |
| `makemake: error: unrecognized arguments: --meta:...`      | `opp-repl-troubleshooting` §11                |
| `opp_makemake: command not found` after sourcing setenv    | `opp-repl-troubleshooting` §12                |
| Simulations run but the numbers look wrong                 | `opp-repl-result-analysis`                    |
| A test reports `SKIP` instead of PASS/FAIL                 | `opp-repl-troubleshooting` §8                 |
| `Address already in use` on `--mcp-port`                   | `opp-repl-troubleshooting` §9                 |
| Agent wrote a regex parser for .sca                        | `opp-repl-result-analysis` (use the bundled script) |
| Agent called `subprocess.run(["opp_makemake", ...])`       | That's correct for the BOOTSTRAP step — see `opp-repl-project-scaffolding` |

## The three highest-leverage fixes

(based on real-world friction captured in `skilldebug.md`)

### 1. "Building X failed" with no detail

**Root cause:** no Makefile yet.
**Fix:** bootstrap with `opp_makemake` first, then use
`make_makefiles()` for subsequent regenerations:

    # Step 1 (once per project): bootstrap the Makefile
    opp_makemake -f --deep -o <project_name>

    # Step 2 (now and forever): opp_repl handles the rest
    from opp_repl.simulation.build import make_makefiles
    make_makefiles(simulation_project=my_project)
    build_project(simulation_project=my_project)

Full detail: `opp-repl-project-scaffolding` + `opp-repl-troubleshooting` §1, §10.

### 2. Exit code 127 on every run

**Root cause:** binary name mismatch between `opp_makemake` output
and `SimulationProject.name`.
**Fix:**

- In `.oppbuildspec`, include `-o <project_name>` in `makemake-options`.
- In the `.opp` file, add `executables=["<project_name>"]`.

Full detail: `opp-repl-project-scaffolding` §"Why the executable is named wrong" + `opp-repl-troubleshooting` §2.

### 3. Need to read `.sca` results

**Root cause:** opp_repl doesn't ship a `read_scalars()` helper —
but OMNeT++ itself does, and this skill pack bundles a script that
wraps it.
**Fix:**

    # Via the bundled script (works regardless of Python binding availability):
    python3 opp-repl-result-analysis/scripts/parse_scalars.py results/

    # Or directly in the REPL:
    import os, sys
    sys.path.insert(0, os.path.join(os.environ["__omnetpp_root_dir"], "python"))
    from omnetpp.scave.results import read_result_files, get_scalars
    scalars = get_scalars(read_result_files("results/*.sca",
                                            include_fields_as_scalars=True))

Full detail: `opp-repl-result-analysis`.

## If none of the above matches

1. Load `opp-repl-troubleshooting` (the full skill, not just this index).
2. Follow the "Generic debug recipe" at the bottom of that skill.
3. If you're building an autonomous agent that keeps hitting the
   SAME issue that isn't documented, open an issue on
   https://github.com/tabgab/opp_repl-skill — the friction log
   feeds back into these skills.
