# Project scaffolding templates

Copy these into a fresh project directory, then edit each file:

1. `project.opp`       — rename to `<yourname>.opp`; change `mm1k` everywhere
2. `.oppbuildspec`     — replace `-o mm1k` with `-o <yourname>`
3. `.nedfolders`       — usually leave as-is (single dot)
4. `omnetpp.ini`       — adjust `network = ...` and configs
5. `Network.ned`       — rename + edit the network you want to simulate
6. `Source.h` / `.cc`  — rename / duplicate per simple module

After copying, run these exact calls in opp_repl:

    from opp_repl.simulation.build import make_makefiles
    make_makefiles(simulation_project=get_simulation_project("<yourname>"))
    build_project(simulation_project=get_simulation_project("<yourname>"))
    run_simulations(simulation_project=get_simulation_project("<yourname>"),
                    sim_time_limit="100s")
