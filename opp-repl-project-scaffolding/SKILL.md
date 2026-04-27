---
name: opp-repl-project-scaffolding
description: Create a NEW OMNeT++ project from scratch that works with opp_repl. On current opp_repl (Apr 2026+) this is a single function call — `create_project(name, path=..., namespace=False)` — which generates every required file (.opp, .oppbuildspec, .nedfolders, package.ned, omnetpp.ini). Load BEFORE building any project that doesn't already have a Makefile checked in. Required when the user says "create a new simulation" or "build an OMNeT++ example from scratch".
---

# Creating a new OMNeT++ project for opp_repl

On current opp_repl main (>= commit a17fcab, Apr 2026), scaffolding
a new project is ONE function call.  Older opp_repl requires copying
the templates bundled with this skill.  Both paths are documented
below; prefer the one-call path if `create_project()` is available.

## The canonical file set

| File             | Purpose                                           | Required? |
|------------------|---------------------------------------------------|-----------|
| `<project>.opp`  | opp_repl project descriptor                       | **YES**   |
| `.oppbuildspec`  | OMNeT++ makemake options (XML)                    | **YES**   |
| `.nedfolders`    | NED source roots (one folder per line)            | **YES**   |
| `package.ned`    | NED package declaration (usually empty)           | **YES**   |
| `omnetpp.ini`    | Simulation config                                 | **YES**   |
| `*.ned`          | Network / module definitions                      | **YES**   |
| `*.cc` / `*.h`   | C++ simple-module implementations                 | usually   |
| `*.msg`          | Message class declarations                        | often     |
| `Makefile`       | Generated on first build                          | **YES at build time** |

## Path A — `create_project()` (recommended, current opp_repl)

    from opp_repl.simulation.project import create_project

    p = create_project(
        "mm1k",             # project name
        path="/tmp",        # parent dir; omit for cwd
        namespace=False,    # True wraps NED in @namespace and expects
                            # matching `namespace mm1k { }` in C++
        template="executable",
        omnetpp_project="omnetpp",
    )
    # Creates /tmp/mm1k/ with:
    #   mm1k.opp   .oppbuildspec   .nedfolders
    #   package.ned   omnetpp.ini
    # Loads the .opp into the workspace and returns a SimulationProject.

After this, add your NED network and C++ source files, then:

    p.build()
    r = run_simulations(simulation_project=p, sim_time_limit="100s")

The generated `omnetpp.ini` is a bare `[General]` — you'll almost
always add a `network = ...` line and parameter assignments.

`create_project()` raises if the target directory exists and is not
empty.

Reference:
https://github.com/omnetpp/opp_repl/blob/main/doc/simulation_projects.md#creating-a-project-from-scratch

## Path B — copy the templates (older opp_repl, or when you need full control)

Bundled under `templates/` (edit each one, replacing `mm1k` with your
project name):

| File                                  | Use case                            |
|---------------------------------------|-------------------------------------|
| `templates/project.opp`               | The `<name>.opp` descriptor         |
| `templates/.oppbuildspec`             | makemake flags (valid XML, no `--` in comments) |
| `templates/.nedfolders`               | NED roots (one dot)                 |
| `templates/omnetpp.ini`               | Minimal runnable config             |
| `templates/Network.ned`               | 1-module network skeleton           |
| `templates/Source.{h,cc}`             | Skeleton simple module              |

Then:

    load_opp_file("./mm1k.opp")
    p = get_simulation_project("mm1k")
    p.build()   # auto-generates Makefile on opp_repl >= 21ea1f0

On older opp_repl (pre-21ea1f0) you also need a one-time bootstrap:

    opp_makemake -f --deep -o mm1k

## The namespace / package trap

If your C++ wraps `Define_Module()` in `namespace mm1k { ... }`, your
NED **must** declare a matching package.  `create_project()` handles
this via the `namespace=True` flag — it writes `@namespace(mm1k);`
into `package.ned`, and you wrap every `.cc` that registers a module
in `namespace mm1k { ... }`.

If they don't match, every run fails with:

    Class 'Source' not found

Simplest rule: **pick one and apply it everywhere, or use neither**.
`create_project(..., namespace=False)` (the default) produces an
empty `package.ned` and expects no C++ namespace — fewest traps.

Diagnostic: after a failed run, list registered class names from the
binary and compare against the NED types used in the network:

    opp_run_release -a omnetpp.ini | grep "Source"
    # Module 'mm1k::Source' (Source)  ← namespace is 'mm1k'
    # If your .ned uses `Source` (no package), add `package mm1k;`
    # or `@namespace(mm1k);` — or strip the C++ namespace.

## Minimal `.opp` for a new executable project

This is what `create_project()` writes; it's also what you'd hand-
author for Path B:

    SimulationProject(
        name="mm1k",
        root_folder=".",
        omnetpp_project="omnetpp",
        build_types=["executable"],
        ned_folders=["."],
        ini_file_folders=["."],
    )

On recent opp_repl you no longer need `executables=["mm1k"]` —
`generate_makefile()` auto-adds `-o mm1k` when `build_types`
contains `"executable"`.  Older opp_repl needs the explicit list.

## Iteration loop

- Edit `.ned` files — no rebuild needed, NED loads at runtime.
- Edit `.cc` / `.h` / `.msg` — call `p.build()` or
  `build_project(simulation_project=p)`.
- Edit `.oppbuildspec` or add/remove source files that change the
  target list — regenerate:

      from opp_repl.simulation.build import generate_makefile
      generate_makefile(simulation_project=p)
      p.build()

## Verification script

Drop this into a Python one-liner to confirm the project is wired
up before trusting a first build:

    p = get_simulation_project("mm1k")
    assert p.build_types == ["executable"]
    import os
    root = p.get_full_path(".")
    for f in [".oppbuildspec", ".nedfolders", "mm1k.opp", "omnetpp.ini"]:
        assert os.path.exists(os.path.join(root, f)), f"missing {f}"
    print("Project scaffold OK")

## Pitfalls

- **NEVER edit the generated `Makefile`** — overwritten on next
  Makefile regeneration.  Change `.oppbuildspec` instead.
- **Invalid XML in `.oppbuildspec`** — the new
  `generate_makefile()` parses it strictly; XML comments cannot
  contain `--`, so `<!-- --deep ... -->` is rejected.  See
  `opp-repl-troubleshooting` §11.
- **The `<project>.opp` file MUST sit inside the project root**
  (or you must specify `root_folder` as an absolute path).  The
  auto-detect-project-from-CWD feature uses the `.opp` file's
  directory as the root.
- **Dependencies** — if your project uses INET or another library,
  list it in `used_projects=["inet"]` AND make sure an `inet.opp`
  is loaded.
- **Case sensitivity** — NED type names, class names, and the
  `Define_Module()` argument must match exactly across `.ned`,
  `.cc`, and `.ini`.

## See also

- `opp-repl-opp-files` — full `.opp` descriptor syntax and templates.
- `opp-repl-running-simulations` — what `build_project()` /
  `run_simulations()` do.
- `opp-repl-troubleshooting` — decoding "exit 127", "class not found",
  "building X failed".
- `opp-repl-result-analysis` — reading .sca results once runs succeed.
