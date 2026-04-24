# Project scaffolding templates

Copy these into a fresh project directory, then edit each file:

1. `project.opp`       — rename to `<yourname>.opp`; change `mm1k` everywhere
2. `.oppbuildspec`     — replace `-o mm1k` with `-o <yourname>`
3. `.nedfolders`       — usually leave as-is (single dot)
4. `omnetpp.ini`       — adjust `network = ...` and configs
5. `Network.ned`       — rename + edit the network you want to simulate
6. `Source.h` / `.cc`  — rename / duplicate per simple module

After copying, run these exact calls in opp_repl:

    # Load project
    load_opp_file("./<yourname>.opp")
    p = get_simulation_project("<yourname>")

    # Build — on current opp_repl main, this auto-generates the
    # Makefile from .oppbuildspec on first call.
    build_project(simulation_project=p)

    # Run
    run_simulations(simulation_project=p, sim_time_limit="100s")

If you later edit `.oppbuildspec` or reorganise the source layout:

    from opp_repl.simulation.build import generate_makefile
    generate_makefile(simulation_project=p)
    build_project(simulation_project=p)

Older opp_repl (before April 2026 / commit 21ea1f0) required a
manual `opp_makemake -f --deep -o <yourname>` before the first
build.  If `build_project()` fails with "Building X failed" on
a fresh project, you're on older opp_repl — use the manual
bootstrap or update opp_repl.
