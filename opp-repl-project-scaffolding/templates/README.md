# Project scaffolding templates

Copy these into a fresh project directory, then edit each file:

1. `project.opp`       — rename to `<yourname>.opp`; change `mm1k` everywhere
2. `.oppbuildspec`     — replace `-o mm1k` with `-o <yourname>`
3. `.nedfolders`       — usually leave as-is (single dot)
4. `omnetpp.ini`       — adjust `network = ...` and configs
5. `Network.ned`       — rename + edit the network you want to simulate
6. `Source.h` / `.cc`  — rename / duplicate per simple module

After copying, run these exact calls in opp_repl:

    # Bootstrap the Makefile ONCE (the step most commonly missed)
    import subprocess
    subprocess.run(["opp_makemake", "-f", "--deep", "-o", "<yourname>"],
                   cwd=".", check=True)

    # From now on, opp_repl handles the build-run-analyse loop
    from opp_repl.simulation.build import make_makefiles
    p = get_simulation_project("<yourname>")
    build_project(simulation_project=p)
    run_simulations(simulation_project=p, sim_time_limit="100s")

If you ever edit `.oppbuildspec` or add/remove source files that
affect the target list, regenerate the Makefile with:

    make_makefiles(simulation_project=p)

If this stops working ("No rule to make target 'makefiles'"), re-
bootstrap with `opp_makemake -f --deep -o <yourname>` — the
top-level Makefile has been lost.
