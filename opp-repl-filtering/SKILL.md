---
name: opp-repl-filtering
description: The shared filter vocabulary used by EVERY opp_repl function that selects simulation configs or tasks — regex include/exclude pairs (filter/exclude_filter, working_directory_filter, ini_file_filter, config_filter, run_number_filter), the simulation_config_filter predicate, and full_match. Load whenever you need to narrow down which simulations run, test, compare, or update.
---

# Filtering configs and tasks

Virtually every opp_repl entry point — `run_simulations()`,
`get_simulation_tasks()`, `run_smoke_tests()`, `run_fingerprint_tests()`,
`update_*_test_results()`, `compare_simulations()`, ... — uses the
SAME filter vocabulary.  Learn it once; apply it everywhere.

Upstream references:
- https://github.com/omnetpp/opp_repl/blob/main/doc/concepts.md
- https://github.com/omnetpp/opp_repl/blob/main/doc/simulation_configs.md

## Regex include/exclude pairs

A config is kept ONLY when every specified include filter matches
and no exclude filter matches.  Filters are substring regex matches
unless `full_match=True`.

| Include                     | Exclude                              | Matches against              |
|-----------------------------|--------------------------------------|------------------------------|
| `filter`                    | `exclude_filter`                     | Full config string repr      |
| `working_directory_filter`  | `exclude_working_directory_filter`   | Working directory path       |
| `ini_file_filter`           | `exclude_ini_file_filter`            | INI file name                |
| `config_filter`             | `exclude_config_filter`              | `[Config X]` section name    |
| `run_number_filter`         | `exclude_run_number_filter`          | Run number as string         |

`run_number_filter` is only effective on functions that enumerate
task-level objects (`get_simulation_tasks()`, `run_simulations()`,
and the test runners).  Pure config-level functions ignore it.

## The predicate filter

`simulation_config_filter` accepts a Python callable
`(SimulationConfig) -> bool`.  It runs *after* the regex filters.
The default predicate drops abstract and emulation configs — so if
you want to run those, pass `simulation_config_filter=lambda c: True`.

Example — only fingerprint-tested configs with ≥ 10 runs:

    run_simulations(
        simulation_config_filter=lambda c: c.num_runs >= 10,
        config_filter="Fingerprint")

## full_match

`full_match=True` (default `False`) promotes regex matching from
substring to whole-string.  Handy when your pattern otherwise catches
too much:

    run_simulations(config_filter="General", full_match=True)
    # matches only `[Config General]`, not e.g. `GeneralSetup`.

## Run-number shortcuts

For single-task selection `get_simulation_task()` accepts the scalar
`run_number=N` in addition to the regex filter.  When it is set,
opp_repl narrows to exactly that run and errors out if there's still
ambiguity.

## REPL vs. CLI

The shell wrappers translate each Python keyword to the identical
kebab-case flag:

| Python keyword                       | Shell flag                            |
|--------------------------------------|---------------------------------------|
| `filter`                             | `--filter`                            |
| `working_directory_filter`           | `--working-directory-filter`          |
| `config_filter`                      | `--config-filter`                     |
| `run_number_filter`                  | `--run-number-filter`                 |
| `exclude_config_filter`              | `--exclude-config-filter`             |
| `full_match`                         | `--full-match`                        |

Predicate filters are REPL-only (they require a Python callable).

## Recipes

Just the examples/ethernet area of INET:

    run_simulations(simulation_project=inet_project,
                    working_directory_filter="examples/ethernet")

Everything EXCEPT emulation and PureAloha:

    run_simulations(exclude_working_directory_filter="emulation",
                    exclude_config_filter="PureAloha")

Only run 0 of every config:

    get_simulation_tasks(run_number_filter="^0$", full_match=True)

Abstract configs (normally excluded) — inspect only, don't run:

    cfgs = inet_project.get_simulation_configs(
        simulation_config_filter=lambda c: c.abstract)

## Pitfalls

- Regex — not glob.  `*` alone is a regex syntax error; use `.*`.
- Because filters are substring by default, `config_filter="A"`
  matches `A`, `Aloha`, `TandemA`, ... .  Anchor with `^...$` or
  set `full_match=True`.
- `run_number_filter` is a regex on the string form of the number;
  `"1"` matches `1`, `10`, `11`, ... .  Use `"^1$"` or
  `exclude_run_number_filter="[02-9]"` for exact matches.
- `simulation_config_filter` REPLACES the default predicate; passing
  one means abstract/emulation configs are no longer auto-excluded
  unless your predicate does it itself.

## See also

- `opp-repl-concepts` — how configs relate to projects and tasks.
- `opp-repl-running-simulations` — `run_simulations()` in context.
- `opp-repl-tasks-and-results` — filtering result sets after a run.
