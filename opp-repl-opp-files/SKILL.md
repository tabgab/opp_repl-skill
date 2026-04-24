---
name: opp-repl-opp-files
description: Write .opp project descriptor files that register OMNeT++ installations and simulation projects (INET, Simu5G, samples, opp_env-managed, overlay builds, git worktrees). Load this when a new project needs a descriptor or an existing one needs tweaking. Covers allowed syntax, path resolution, every constructor parameter, and ready-made templates under templates/.
---

# Project descriptor files (.opp)

A `.opp` file is a tiny Python expression containing exactly ONE
constructor call — either `OmnetppProject(...)` or
`SimulationProject(...)` — with keyword-only literal arguments
(strings, numbers, booleans, lists, dicts, None).  No variables,
no function calls, no imports.

Upstream reference:
https://github.com/omnetpp/opp_repl/blob/main/doc/opp_files.md

## Path resolution rules

- `root_folder`, `overlay_build_root`, `opp_env_workspace`:
  relative paths resolve against the **directory containing the
  `.opp` file**, not the shell's CWD.  `root_folder="."` therefore
  always means "this folder".  Absolute paths pass through.
- All other folder parameters (`bin_folder`, `ned_folders`,
  `ini_file_folders`, ...) are relative to the *project* root, not
  to the `.opp` file.

## Ways to locate the project root

Tried in order:

1. `root_folder="/abs/path"` or `root_folder="."` (most common).
2. `root_folder_environment_variable="MY_PROJECT"` -- reads the env
   var at load time.
3. `SimulationProject` also accepts
   `root_folder_environment_variable_relative_folder="samples/aloha"`
   which gets appended to the env var's value.  Handy for pointing
   at OMNeT++ samples via `__omnetpp_root_dir` without writing a
   `.opp` per sample.

## OmnetppProject parameters

| Parameter                               | Purpose                                          |
|-----------------------------------------|--------------------------------------------------|
| `name`                                  | Identifier used in `omnetpp_project=`            |
| `version`                               | Optional version string                          |
| `root_folder_environment_variable`      | Defaults to `"__omnetpp_root_dir"`               |
| `root_folder`                           | Explicit root (overrides env var)                |
| `overlay_name`                          | Enable fuse-overlayfs build layer                |
| `overlay_build_root`                    | Override the overlay build root                  |
| `opp_env_workspace` / `opp_env_project` | Route build/run through `opp_env`                |

## SimulationProject parameters (the important ones)

| Parameter              | Default                | Purpose                                   |
|------------------------|------------------------|-------------------------------------------|
| `name`                 | *(required)*           | Identifier                                |
| `omnetpp_project`      | None                   | OMNeT++ install to use, by name           |
| `root_folder`          | None                   | Usually `"."`                             |
| `build_types`          | `["dynamic library"]`  | or `["executable"]`                       |
| `executables`          | None                   | List of executable names                  |
| `dynamic_libraries`    | None                   | Shared lib names, e.g. `["INET"]`         |
| `bin_folder`           | `"."`                  | Where binaries are placed                 |
| `library_folder`       | `"."`                  | Where shared libs are placed              |
| `ned_folders`          | `["."]`                | NED source directories                    |
| `ini_file_folders`     | `["."]`                | Scanned recursively for `*.ini`           |
| `used_projects`        | `[]`                   | Dependencies by name (e.g. `["inet"]`)    |
| `fingerprint_store`    | `"fingerprint.json"`   | Baseline JSON for fingerprint tests       |
| `speed_store`          | `"speed.json"`         | Baseline JSON for speed tests             |
| `statistics_folder`    | `"."`                  | Folder for statistical-test baselines     |
| `media_folder`         | `"."`                  | Folder for chart-test baseline images     |
| `overlay_name`         | None                   | Enable overlay build                      |
| `opp_env_workspace` / `opp_env_project` | None         | Route through opp_env                     |
| `github_owner` / `github_repository` / `github_workflows` | None | GitHub Actions integration |

Full parameter list: see linked files under `templates/`.

## Loading

- CLI: `opp_repl --load "path/to/file.opp"` (globs allowed,
  flag repeatable).
- REPL: `load_opp_file("~/workspace/inet/inet.opp")` or
  `load_workspace("~/workspace")` (recursively scans for `*.opp`).
- Command-line tools auto-load all `*.opp` in CWD when no `--load`
  is given.

**OmnetppProject files are always processed before
SimulationProject files**, so simulation projects can refer to them
by name.

## Ready-made templates (bundled)

Copy and customise from `templates/`:

| File                              | Use case                                   |
|-----------------------------------|--------------------------------------------|
| `templates/omnetpp.opp`           | Standard OMNeT++ installation              |
| `templates/omnetpp_env_var.opp`   | OMNeT++ located via env var                |
| `templates/sample_executable.opp` | OMNeT++ sample (aloha/fifo) as executable  |
| `templates/inet.opp`              | INET as dynamic library                    |
| `templates/simu5g.opp`            | Simu5G (depends on INET)                   |
| `templates/overlay.opp`           | Overlay build atop an existing tree        |
| `templates/opp_env.opp`           | opp_env-managed OMNeT++ install            |
| `templates/opp_env_sim.opp`       | opp_env-managed simulation project         |

## Programmatic alternative

When the path is only known at runtime (git worktrees, generated
installs), skip the `.opp` file:

    define_omnetpp_project("omnetpp-6.1", root_folder="/tmp/omnetpp-v6.1")
    define_simulation_project("inet-4.5", root_folder="/tmp/inet-v4.5",
        omnetpp_project="omnetpp",
        library_folder="src", bin_folder="bin",
        dynamic_libraries=["INET"],
        ned_folders=["src", "examples"],
        ini_file_folders=["examples"])

## Pitfalls

- Syntax is restricted — variables / imports / function calls raise
  at load time.  Treat `.opp` files as JSON-in-Python.
- A missing `omnetpp_project=` on a SimulationProject is fine as
  long as an `OmnetppProject` is auto-detected from
  `__omnetpp_root_dir`.
- When two versions of the same project are registered, lookup by
  name alone is ambiguous: use
  `get_simulation_project("inet", version="4.5")`.
- **For executable projects, ALWAYS set `executables=["<name>"]`**
  matching the target name produced by `opp_makemake -o <name>`.
  If they disagree, `run_simulations()` fails with exit code 127
  because opp_repl looks for a binary that doesn't exist.  See
  `opp-repl-project-scaffolding` for the end-to-end setup.
- **A `.opp` file alone is not enough to build.**  You also need
  `.oppbuildspec`, `.nedfolders`, and a `Makefile` (the first two
  are committed; the third is generated by `make_makefiles()`).
  Missing any of these produces cryptic build failures.

## See also

- `opp-repl-concepts` — the object model these files feed.
- `opp-repl-project-scaffolding` — full new-project template set
  (`.opp`, `.oppbuildspec`, `.nedfolders`, NED/C++ skeletons).
- `opp-repl-overlay-builds` — `overlay_name` details.
- `opp-repl-opp-env-integration` — opp_env routing.
- `opp-repl-running-simulations` — what happens once projects load.
