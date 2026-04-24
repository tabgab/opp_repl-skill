# skills4_opp_repl

A composable Agent-Skills pack for **opp_repl**, the interactive
Python REPL + CLI tools + MCP server for OMNeT++ simulations.

Upstream: https://github.com/omnetpp/opp_repl

Each subdirectory is a self-contained skill conforming to the
Anthropic Agent Skills format (SKILL.md with YAML frontmatter,
optional `templates/` / `references/` / `scripts/`).  The skills
are:

- **portable** — nothing opp_repl-version-specific in the
  frontmatter; they work on any client that honours Agent Skills.
- **composable** — skills reference each other by name under a
  "See also" heading at the bottom of each file.
- **progressively disclosed** — SKILL.md files stay short and
  hand off to bundled references / templates when more context is
  needed.

## Quick links

- `WINDSURF.md` — **step-by-step Windsurf installation**
  (global, workspace, and UI options).
- `USAGE_EXAMPLES.md` — seven end-to-end prompt/response scenarios
  showing which skills load when.
- `TROUBLESHOOTING.md` — symptom-to-skill lookup for common
  build / run / analysis failures (read this when things break).
- `opp-repl-overview/SKILL.md` — the entry-point skill, with a
  decision tree that maps tasks to the exact siblings to load.
- `opp-repl-ai-workflows/SKILL.md` — cookbook for agents driving
  opp_repl via MCP or shell.

## What's new since initial release

- **3 new skills** targeting the hardest friction points real AI
  agents hit when using opp_repl:
  - `opp-repl-project-scaffolding` — create a new OMNeT++ project
    from zero (.opp, .oppbuildspec, .nedfolders, NED+C++ skeletons,
    correct `make_makefiles()` + `build_project()` sequence).
  - `opp-repl-result-analysis` — read `.sca`/`.vec` with either
    `opp_scavetool` or the `omnetpp.scave.results` Python API;
    bundles `scripts/parse_scalars.py` that works both ways.
  - `opp-repl-troubleshooting` — decode every common opaque error
    (exit 127, "Building X failed", "Class not found", ...) to
    its cause and fix.
- **Hardened existing skills** with the pitfalls these real users
  hit — `opp-repl-running-simulations`, `opp-repl-tasks-and-results`,
  `opp-repl-opp-files` all now explicitly warn about
  `tr.subprocess_result.stderr` being the source of truth on
  ERRORs, the `executables=[...]` requirement, and the Makefile
  pre-generation step.

## How to load

### For Claude (Claude Desktop, Claude Code, Claude API with
agent-skills enabled)

Place the skills in one of these locations (or symlink from here):

- Global: `~/.claude/skills/`
- Project: `.claude/skills/` in your workspace

The skill at `opp-repl-overview` is the entry point.  Load it
first; it lists every sibling skill and when to use each.

### For Windsurf (Codeium Cascade)

See `WINDSURF.md` for the full guide.  TL;DR:

```bash
# Global install for every Windsurf workspace
git clone https://github.com/tabgab/opp_repl-skill.git ~/opp_repl-skill
mkdir -p ~/.codeium/windsurf/skills
for dir in ~/opp_repl-skill/opp-repl-*; do
    ln -sfn "$dir" ~/.codeium/windsurf/skills/
done
```

Windsurf auto-discovers all 26 skills; @-mention them in Cascade.

### For other agent frameworks

The SKILL.md front-matter fields (`name`, `description`) are the
ones Anthropic standardised; most other frameworks read the body
as plain markdown.  You can treat the whole pack as a library of
runbooks — feed the `description` lines into the agent's system
prompt and let it pull full bodies on demand.

## Skill index

### Foundations
| Skill                                 | What it covers                                        |
|---------------------------------------|-------------------------------------------------------|
| `opp-repl-overview`                   | Entry point + decision tree + feature-to-skill map    |
| `opp-repl-installation`               | pip, extras, setenv, Ubuntu PEP-668                   |
| `opp-repl-concepts`                   | Workspace / Project / Config / Task / Result model    |
| `opp-repl-opp-files`                  | `.opp` descriptor format (+ 7 ready templates)        |
| `opp-repl-project-scaffolding`        | **New project from zero** (+ 7 file templates)        |

### Execution & control
| Skill                                 | What it covers                                        |
|---------------------------------------|-------------------------------------------------------|
| `opp-repl-repl-usage`                 | IPython launch, namespace, autoreload                 |
| `opp-repl-cli-tools`                  | Shell wrappers for CI                                 |
| `opp-repl-running-simulations`        | `build_project` + `run_simulations`                   |
| `opp-repl-filtering`                  | Shared filter vocabulary                              |
| `opp-repl-tasks-and-results`          | Task hierarchy, rerun, drill-down                     |
| `opp-repl-troubleshooting`            | **Symptom -> cause -> fix catalogue**                 |

### Regression tests
| Skill                                 | What it covers                                        |
|---------------------------------------|-------------------------------------------------------|
| `opp-repl-smoke-tests`                | Start / terminate checks                              |
| `opp-repl-fingerprint-tests`          | Event-level behavioural regression                    |
| `opp-repl-statistical-tests`          | Scalar-level regression                               |
| `opp-repl-speed-tests`                | CPU-instruction-count regression                      |
| `opp-repl-chart-tests`                | Image-based regression                                |
| `opp-repl-sanitizer-tests`            | ASAN / UBSan runs                                     |
| `opp-repl-feature-and-release-tests`  | Aggregate suites                                      |

### Analysis
| Skill                                 | What it covers                                        |
|---------------------------------------|-------------------------------------------------------|
| `opp-repl-result-analysis`            | **Read .sca/.vec** (+ bundled `parse_scalars.py`)     |
| `opp-repl-comparing-simulations`      | Cross-project / cross-commit comparison               |
| `opp-repl-parameter-optimization`     | scipy Nelder-Mead tuning                              |
| `opp-repl-coverage-reports`           | LLVM line coverage                                    |
| `opp-repl-profiling`                  | perf + Hotspot                                        |

### Infrastructure
| Skill                                 | What it covers                                        |
|---------------------------------------|-------------------------------------------------------|
| `opp-repl-overlay-builds`             | fuse-overlayfs layers                                 |
| `opp-repl-ssh-cluster`                | Dask over SSH                                         |
| `opp-repl-github-actions`             | `dispatch_workflow` / `dispatch_all_workflows`        |
| `opp-repl-opp-env-integration`        | Routing through `opp_env run`                         |

### AI integration
| Skill                                 | What it covers                                        |
|---------------------------------------|-------------------------------------------------------|
| `opp-repl-mcp-server`                 | MCP endpoint (`execute_python`, `opp-repl://` URIs)   |
| `opp-repl-ai-workflows`               | Seven end-to-end recipes for agents                   |

## Dependency hints

Almost every skill has a "See also" section.  Key paths:

- New to opp_repl → `opp-repl-overview` → `opp-repl-installation`
  → `opp-repl-concepts` → `opp-repl-opp-files`.
- Running sims → `opp-repl-running-simulations`
  (+ `opp-repl-filtering` + `opp-repl-tasks-and-results`).
- Test-authoring → pick the specific `opp-repl-*-tests` skill
  (all depend on `opp-repl-running-simulations` and
  `opp-repl-tasks-and-results`).
- Agent integration → `opp-repl-mcp-server` + `opp-repl-ai-workflows`
  (+ whichever task-specific skills the recipe uses).

## Authoring notes

- Each SKILL.md deliberately stays under ~200 lines.  When more
  detail is needed, linked files under `templates/` or
  `references/` carry the weight.
- `opp-repl-opp-files/templates/` contains 7 canonical `.opp`
  descriptors ready to copy-paste.
- No scripts are bundled — opp_repl's own shell wrappers and the
  MCP `execute_python` tool cover programmatic use.  If you need
  project-local scripts, add them under `scripts/` in the relevant
  skill directory.
- Upstream doc URLs in each skill target the `main` branch on
  GitHub, so they stay current as opp_repl evolves.

## License

Follows the upstream opp_repl project (LGPL-3.0-or-later). The
skill texts themselves are freely reusable under the same terms.
