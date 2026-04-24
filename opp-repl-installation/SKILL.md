---
name: opp-repl-installation
description: Install opp_repl from PyPI or source, pick the right optional extras (mcp, cluster, chart, optimize, github, ide, all), and set up the shell environment (source OMNeT++ setenv, then opp_repl setenv). Use before any other opp-repl-* skill. Covers Python 3.10+ venv pattern, Ubuntu PEP-668 pitfall, and how to verify the install.
---

# Installing opp_repl

opp_repl requires **Python 3.10+** on Linux or macOS.  It depends on
IPython and pandas out of the box; everything else is opt-in.

Upstream reference:
https://github.com/omnetpp/opp_repl/blob/main/doc/installation.md

## 1. Pick an install mode

### From PyPI (fastest, production)

    pip install opp_repl
    # or with extras:
    pip install "opp_repl[all]"

### From source (recommended for developers / contributors)

    git clone https://github.com/omnetpp/opp_repl.git
    cd opp_repl
    pip install -e ".[all]"

Installing in editable mode means `git pull` immediately picks up
upstream changes — no re-install.

## 2. Optional extras

Pick the minimum set you need.  `[all]` pulls everything.

| Extra      | Packages                    | Enables                                           |
|------------|-----------------------------|---------------------------------------------------|
| `mcp`      | mcp                         | MCP server for AI assistants                      |
| `optimize` | scipy, optimparallel        | `optimize_simulation_parameters()`                |
| `chart`    | matplotlib, numpy           | Chart tests, rendered-image baselines             |
| `cluster`  | dask, distributed           | SSH cluster execution                             |
| `github`   | requests                    | GitHub Actions workflow dispatch                  |
| `ide`      | py4j                        | OMNeT++ Eclipse IDE bridge                        |
| `all`      | (all of the above)          | everything                                        |

## 3. Ubuntu / Debian PEP-668 pitfall

Modern Debian-family distros mark the system Python as
"externally managed".  `pip install -e .` fails with:

    error: externally-managed-environment

**Do NOT** pass `--break-system-packages`.  Use a dedicated venv:

    cd /path/to/opp_repl
    python3 -m venv .venv
    . .venv/bin/activate
    pip install --upgrade pip
    pip install -e ".[all]"

opp_repl's own `setenv` auto-activates a `.venv/` at its root if one
exists, so keeping the venv in-tree is the cleanest pattern.

## 4. Environment setup

Order matters — OMNeT++ first (so `opp_run*` binaries and
`__omnetpp_root_dir` are on PATH), then opp_repl:

    cd ~/workspace/omnetpp && . setenv
    cd ~/workspace/opp_repl && . setenv   # activates .venv, extends PATH

After this, `opp_repl`, `opp_build_project`, `opp_run_simulations`,
and every `opp_run_*_tests` / `opp_update_*_test_results` wrapper is
on PATH.

### PITFALL — the setenv order trap

Sourcing opp_repl's setenv AFTER OMNeT++'s setenv activates
opp_repl's `.venv`, which **restores a snapshotted PATH from the
moment the venv was created** — typically a PATH that does NOT
have OMNeT++'s `bin/` on it.  Symptoms:

    $ source ~/omnetpp/setenv -q
    $ source ~/opp_repl/setenv
    $ opp_makemake --help
    bash: opp_makemake: command not found        # ← wrong

The fix is to source them in the REVERSE order:

    cd ~/workspace/opp_repl && . setenv   # opp_repl FIRST (activates venv)
    cd ~/workspace/omnetpp && . setenv    # OMNeT++ SECOND (prepends its bin)

After this ordering, `opp_makemake`, `opp_run`, `opp_scavetool`,
AND every `opp_repl` / `opp_run_*` wrapper are all reachable.
**Always verify with `command -v opp_makemake opp_run opp_repl`
after sourcing; if any is missing, re-order the sourcing.**

Alternatively, create the opp_repl venv AFTER first sourcing
OMNeT++'s setenv — then the snapshotted PATH already contains
OMNeT++'s `bin/`, and either sourcing order works.

## 5. Verify

    opp_repl --help            # should print the CLI usage
    opp_run_simulations --help # shell wrapper also resolves
    python -c "import opp_repl; print(opp_repl.__version__)"

A quick smoke-test against OMNeT++'s built-in `aloha` sample:

    cd $__omnetpp_root_dir/samples/aloha
    opp_run_simulations --filter PureAloha -t 0.1s --no-build

Expect a short summary ending in `DONE` for each PureAloha run.

## Pitfalls

- Installing globally and then using a venv-local opp_repl can leave
  two competing entry points on PATH.  Check `which opp_repl`.
- The `py4j` startup warning ("optional opp_repl.common.ide package
  will not work") is benign — py4j is only needed for IDE bridge.
- matplotlib's `NotoColorEmoji.ttf` font warning is cosmetic noise.
- If `__omnetpp_root_dir` is unset, projects that rely on the
  auto-detected OMNeT++ installation will fail with confusing errors;
  always source OMNeT++'s `setenv` first.
- **The setenv-order trap** (see §4 above) — sourcing opp_repl
  setenv AFTER OMNeT++ setenv can erase OMNeT++'s bin from PATH
  because the venv activation restores a snapshotted PATH.  If
  `opp_makemake` or `opp_run` goes missing after sourcing, reverse
  the order: opp_repl FIRST, then OMNeT++.  Always verify with
  `command -v opp_makemake opp_run opp_repl`.

## See also

- `opp-repl-opp-files` — write `.opp` project descriptors.
- `opp-repl-repl-usage` — launch flags and the IPython UX.
- `opp-repl-cli-tools` — use the shell wrappers without IPython.
- `opp-repl-mcp-server` — enable the MCP endpoint for agents.
