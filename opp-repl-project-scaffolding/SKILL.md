---
name: opp-repl-project-scaffolding
description: Create a NEW OMNeT++ project from scratch that works with opp_repl — the complete required-file set (.opp, .oppbuildspec, .nedfolders, omnetpp.ini, NED, C++, Makefile). Covers the single most common failure mode ("build_project failed with no explanation" = no Makefile yet) and the exact opp_repl call sequence to go from zero files to a working simulation. Load BEFORE building any project that doesn't already have a Makefile checked in. Required when the user says "create a new simulation" or "build an OMNeT++ example from scratch".
---

# Creating a new OMNeT++ project for opp_repl

Every OMNeT++ project needs a specific set of files on disk before
opp_repl can build it.  Missing any of them produces cryptic
errors ("Building X failed", exit code 127, "Class not found").
This skill gives you the exact template set and the call sequence
that always works.

## The canonical file set

| File                | Purpose                                           | Required? |
|---------------------|---------------------------------------------------|-----------|
| `<project>.opp`     | opp_repl project descriptor                       | **YES**   |
| `.oppbuildspec`     | OMNeT++ makemake options (XML)                    | **YES**   |
| `.nedfolders`       | NED source roots (text, one folder per line)      | **YES**   |
| `omnetpp.ini`       | Simulation config                                 | **YES**   |
| `*.ned`             | Network / module definitions                      | **YES**   |
| `*.cc` / `*.h`      | C++ simple-module implementations                 | usually   |
| `*.msg`             | Message class declarations                        | often     |
| `Makefile`          | Generated on first build, commit only if stable   | **YES at build time** |

All are bundled as templates under `templates/` in this skill.

## The five-step recipe that always works

    # 0. Pre-reqs: OMNeT++ setenv sourced, opp_repl installed,
    #    pwd is the new project directory.

    # 1. Write the files.
    #    Use the templates in this skill:
    #      templates/project.opp
    #      templates/.oppbuildspec
    #      templates/.nedfolders
    #      templates/omnetpp.ini
    #      templates/Source.{h,cc}    (example module)
    #      templates/Network.ned      (example network)

    # 2. BOOTSTRAP: generate the Makefile ONCE via opp_makemake.
    #    This is the step most commonly missed.  .oppbuildspec
    #    isn't enough on its own — `make makefiles` only works
    #    AFTER a Makefile already exists, so you need this shell
    #    call the first time:
    #
    #        opp_makemake -f --deep -o <project_name>
    #
    #    From inside opp_repl, use subprocess:
    import subprocess
    subprocess.run(["opp_makemake", "-f", "--deep", "-o", "mm1k"],
                   cwd=mm1k_project.root_folder, check=True)

    # 2b. AFTER the first Makefile exists, future regenerations
    #     (when .oppbuildspec changes) can use make_makefiles():
    from opp_repl.simulation.build import make_makefiles
    make_makefiles(simulation_project=mm1k_project)

    # 3. Build.
    build_project(simulation_project=mm1k_project)

    # 4. Run.
    r = run_simulations(simulation_project=mm1k_project,
                        sim_time_limit="100s")
    assert r.is_all_results_done()

Single shell-equivalent recipe:

    opp_makemake -f --deep -o mm1k
    make MODE=release -j$(nproc)
    opp_run -r 0 -c General omnetpp.ini

## Why `build_project()` fails with "no explanation"

`build_project()` calls `make MODE=release` under the hood.  If
there is no `Makefile` in the project root, `make` fails with
`No targets specified and no makefile found` — but opp_repl's
exception message swallows the stderr.  Symptoms:

    Exception: Building mm1k failed
    # (no further info)

**Fix: bootstrap the Makefile with `opp_makemake` first**, then
use `make_makefiles()` for future regenerations:

    # Step 1 (once per project) — create the initial Makefile.
    # Run this in a shell (or via subprocess from opp_repl) at
    # the project root:
    opp_makemake -f --deep -o <project_name>

    # Step 2 (from now on) — `make_makefiles()` works because
    # the top-level Makefile now has a `makefiles` target.
    # Call this after every .oppbuildspec change:
    make_makefiles(simulation_project=p)

**DO NOT** put `--meta:recurse` or `--meta:export-library` or
any other `--meta:*` flag on the `opp_makemake` command line.
Those flags are consumed by `make makefiles` (which parses
`.oppbuildspec` and translates them), not by `opp_makemake`
itself — passing them directly gives:

    makemake: error: unrecognized arguments: --meta:recurse ...

It is fine — and idiomatic — to keep `--meta:*` flags inside
`.oppbuildspec`.  Just don't duplicate them on the CLI.

## Why the executable is named wrong

When `opp_makemake` runs without `-o <name>`, it derives the
target name from the directory name.  opp_repl's `SimulationTask`
expects the binary to match the **project name** in the `.opp`
file.  Mismatches produce:

    ERROR (Non-zero exit code: 127)
    # and inside tr.subprocess_result.stderr:
    # nice: execvp: No such file or directory

**Three prevention strategies** (pick one):

1. **Easiest** — name the project directory the same as the
   project, and let `opp_makemake` pick the default.  E.g. put
   the project in `mm1k/` and call it `name="mm1k"`.

2. **Explicit in .oppbuildspec** — add `-o <name>` to the
   `makemake-options` attribute:

       <dir makemake-options="--deep -o mm1k ..." path="." type="makemake"/>

   Then `make_makefiles()` passes `-o mm1k` automatically.

3. **Explicit in the SimulationProject** — declare the
   executable name in the `.opp` file so opp_repl's `build_types`
   machinery uses it:

       SimulationProject(
           name="mm1k",
           root_folder=".",
           omnetpp_project="omnetpp",
           build_types=["executable"],
           executables=["mm1k"],     # <- this line
           ned_folders=["."],
           ini_file_folders=["."],
       )

## C++ namespace vs NED package (the "Class not found" trap)

If you write:

    // Source.cc
    namespace mm1k {
        Define_Module(Source);   // registers as mm1k::Source
    }

then the simulation will fail with `Class 'Source' not found`
unless your NED also declares the same package:

    // Source.ned
    package mm1k;
    simple Source { ... }

**Rules**:
- Either use `package X;` in ALL your .ned files AND
  `namespace X { ... }` in ALL your .cc files, with `X` matching.
- Or use NEITHER — no package, no namespace.

Diagnostic check: after a failed run, inspect registered classes:

    # In a shell
    opp_run_release -a omnetpp.ini | grep "Source"
    # Expected: "Module 'mm1k::Source' (Source)"
    # If you see "mm1k::Source" but your .ned uses just "Source",
    # add `package mm1k;` to the .ned files (or remove the C++
    # namespace).

## Minimal .opp for a new executable project

    # mm1k.opp
    SimulationProject(
        name="mm1k",
        root_folder=".",
        omnetpp_project="omnetpp",
        build_types=["executable"],
        executables=["mm1k"],
        ned_folders=["."],
        ini_file_folders=["."],
    )

## Minimal .oppbuildspec

    <?xml version="1.0" encoding="UTF-8" standalone="no"?>
    <buildspec version="4.0">
        <dir
            makemake-options="--deep --meta:recurse --meta:export-library --meta:use-exported-libs -o mm1k"
            path="."
            type="makemake"/>
    </buildspec>

Note the `-o mm1k` — this makes make_makefiles()'s output binary
match the project name automatically.

## Minimal .nedfolders

    .

(One line.  A dot means "scan this folder and subfolders".)

## Iteration loop

After editing any source file:

    # Re-build incrementally (Makefile picks up timestamps)
    build_project(simulation_project=mm1k_project)

    # Re-run
    r = run_simulations(simulation_project=mm1k_project,
                        sim_time_limit="100s")

After editing `.oppbuildspec` or adding/removing NED/C++ source
files:

    make_makefiles(simulation_project=mm1k_project)
    build_project(simulation_project=mm1k_project)

After editing `.ned` files only — no rebuild needed, NED is
loaded at runtime.  Just re-run.

## Verification script

Drop this into a Python one-liner to confirm the project is
wired up before trusting a first build:

    p = get_simulation_project("mm1k")
    assert p.build_types == ["executable"], "must be executable"
    assert p.executables == ["mm1k"], "executable name must match project"
    import os
    root = p.get_full_path(".")
    for f in [".oppbuildspec", ".nedfolders", "mm1k.opp", "omnetpp.ini"]:
        assert os.path.exists(os.path.join(root, f)), f"missing {f}"
    print("Project scaffold OK")

## Pitfalls

- **NEVER edit the generated `Makefile`** — it will be overwritten
  on the next `make_makefiles()` call.  Change `.oppbuildspec`
  instead.
- **The `<project>.opp` file MUST sit inside the project root**
  (or you must specify `root_folder` as an absolute path).  The
  auto-detect-project-from-CWD feature uses the `.opp` file's
  directory as the root.
- **Dependencies** — if your project uses INET or another library,
  list it in `used_projects=["inet"]` on the SimulationProject AND
  make sure an `inet.opp` is loaded.
- **Case sensitivity** — NED type names, class names, and the
  `Define_Module()` argument are all case-sensitive and must match
  exactly across .ned, .cc, and .ini.

## See also

- `opp-repl-opp-files` — full `.opp` descriptor syntax and templates.
- `opp-repl-running-simulations` — what `build_project()` /
  `run_simulations()` actually do.
- `opp-repl-troubleshooting` — decoding "exit 127", "class not found",
  "building X failed".
- `opp-repl-result-analysis` — reading .sca results once runs succeed.
