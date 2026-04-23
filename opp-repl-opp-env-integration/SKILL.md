---
name: opp-repl-opp-env-integration
description: Route opp_repl's build and run commands through `opp_env run` for OMNeT++ installations managed by the opp_env tool. Set opp_env_workspace + opp_env_project on the OmnetppProject or SimulationProject. Load when working with pinned opp_env stacks (e.g. omnetpp-6.3.0 + inet-4.6.0) alongside opp_repl.
---

# opp_env integration

[opp_env](https://github.com/omnetpp/opp_env) is the OMNeT++
version-manager: it can stand up a clean (omnetpp, inet, simu5g,
...) stack on demand.  opp_repl integrates by routing build and
run commands through `opp_env run`.

Upstream reference (covered in multiple docs):
- https://github.com/omnetpp/opp_repl/blob/main/doc/omnetpp_projects.md#opp_env-integration
- https://github.com/omnetpp/opp_repl/blob/main/doc/simulation_projects.md#opp_env-integration

## Opting in

Add `opp_env_workspace` and `opp_env_project` to the `.opp` file.
BOTH the `OmnetppProject` and each dependent `SimulationProject`
should point at the same opp_env workspace:

    # OmnetppProject
    OmnetppProject(
        name="omnetpp-6.3.0-opp_env",
        root_folder=".",
        opp_env_workspace="/home/user/opp_env",
        opp_env_project="omnetpp-6.3.0",
    )

    # Matching SimulationProject
    SimulationProject(
        name="inet-4.6.0-opp_env",
        root_folder=".",
        omnetpp_project="omnetpp-6.3.0-opp_env",
        opp_env_workspace="/home/user/opp_env",
        opp_env_project="inet-4.6.0",
        library_folder="src",
        bin_folder="bin",
        build_types=["dynamic library"],
        dynamic_libraries=["INET"],
        ned_folders=["src", "examples", "showcases", "tutorials"],
        ini_file_folders=["examples"],
    )

Templates for both files ship with `opp-repl-opp-files`
(`templates/opp_env.opp`, `templates/opp_env_sim.opp`).

## Under the hood

When a project has `opp_env_workspace` set, opp_repl automatically
chooses the `opp_env` simulation runner.  Every build and run goes
through:

    opp_env run --workspace <opp_env_workspace> \
                --project  <opp_env_project> \
                -- <command>

The environment (PATH, LD_LIBRARY_PATH, __omnetpp_root_dir) is set
up by opp_env just for the duration of that subprocess.

## When to use opp_env routing

- You need to run old versions of INET / OMNeT++ alongside current
  ones without manual env juggling.
- You want reproducible-by-construction CI pipelines (opp_env
  fetches exact source trees on demand).
- You're sharing `.opp` files across machines with different
  OMNeT++ installs.

## Pitfalls

- The first build triggers opp_env to download + install the
  project.  It can take minutes; be patient and make sure the
  network is open.
- Mixing opp_env and non-opp_env projects in the same workspace
  works, but makes sure each `SimulationProject` references the
  matching `OmnetppProject`.  Cross-linking an opp_env INET to a
  non-opp_env OMNeT++ leads to subtle PATH mismatches.
- opp_env is a separate tool with its own versioning; `pip install
  opp_env` or follow its README.

## See also

- `opp-repl-opp-files` — descriptor templates for opp_env projects.
- `opp-repl-overlay-builds` — alternative way to test multiple
  versions side-by-side.
- `opp-repl-running-simulations` — runner selection logic.
