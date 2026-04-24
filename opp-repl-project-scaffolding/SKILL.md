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

    # 2. Build.
    #    On current opp_repl main (>= commit 21ea1f0, Apr 2026),
    #    build_project() auto-generates the Makefile by calling
    #    generate_makefile() internally — it reads .oppbuildspec,
    #    strips --meta:* flags, adds `-o <project_name>` when
    #    build_types includes "executable", and runs opp_makemake.
    #    You just call:
    build_project(simulation_project=mm1k_project)

    # 3. Run.
    r = run_simulations(simulation_project=mm1k_project,
                        sim_time_limit="100s")
    assert r.is_all_results_done()

    # ── for older opp_repl (pre-21ea1f0) the bootstrap used
    # ── to need an explicit opp_makemake call first:
    #     import subprocess
    #     subprocess.run(["opp_makemake", "-f", "--deep", "-o", "mm1k"],
    #                    cwd=p.root_folder, check=True)
    #     build_project(simulation_project=p)
    # If `build_project()` fails with "No targets specified and no
    # makefile found", you're on older opp_repl — either update or
    # use the workaround above.

Single shell-equivalent recipe:

    opp_makemake -f --deep -o mm1k
    make MODE=release -j$(nproc)
    opp_run -r 0 -c General omnetpp.ini

## Why `build_project()` used to fail with "no explanation"

On older opp_repl (before commit 21ea1f0, "Added generate_makefile
using .oppbuildspec if found, otherwise use sensible defaults"),
`build_project()` called `make MODE=release` with no Makefile
present and failed with:

    Exception: Building mm1k failed
    # (no further info)

**This is fixed on current main.**  `build_project()` now detects
a missing `Makefile` and auto-runs `generate_makefile()`, which
reads `.oppbuildspec` and invokes `opp_makemake` with the right
flags (stripping `--meta:*` which is only valid inside
.oppbuildspec, adding `-o <project_name>` when the project is
declared as an executable).

If you're on older opp_repl, bootstrap manually:

    opp_makemake -f --deep -o <project_name>

then call `build_project()` as usual.

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
