---
name: opp-repl-github-actions
description: Dispatch GitHub Actions CI workflows from opp_repl. Requires `github` extra, a personal access token at ~/.ssh/github_repo_token (repo + workflow scopes), and github_owner/github_repository/github_workflows parameters in the project's .opp file. dispatch_workflow and dispatch_all_workflows fire workflow_dispatch events; combine with `opp-repl-fingerprint-tests` etc. locally.
---

# GitHub Actions integration

Fire `workflow_dispatch` events on the project's GitHub repository
directly from opp_repl.  Handy for triggering expensive CI suites
(full fingerprint run, cluster tests) without leaving the REPL.

Upstream reference:
https://github.com/omnetpp/opp_repl/blob/main/doc/github_actions.md

## Prerequisites

1. `pip install "opp_repl[github]"` (pulls `requests`).
2. Personal access token in `~/.ssh/github_repo_token`
   (file permissions 600) with scopes `repo` and `workflow`.
3. `.opp` file includes GitHub fields:

       SimulationProject(
           name="inet",
           root_folder=".",
           ...,
           github_owner="inet-framework",
           github_repository="inet",
           github_workflows=[
               "fingerprint-tests.yml",
               "statistical-tests.yml",
               "chart-tests.yml",
           ],
       )

## Python API

    # Dispatch a single workflow
    dispatch_workflow("fingerprint-tests.yml")

    # Dispatch all configured workflows for the default project
    dispatch_all_workflows()

    # Target a specific project and branch
    dispatch_workflow("fingerprint-tests.yml",
                      simulation_project=inet_project,
                      ref="topic/my-feature")

Returns the HTTP response from GitHub.  No CLI wrapper is bundled
for this function; use the REPL or an ad-hoc `python -c`.

## Typical workflow

1. Finish a local change and run smoke tests locally.
2. `dispatch_workflow("fingerprint-tests.yml", ref="my-branch")` to
   kick a longer CI run while you context-switch.
3. Inspect the results in GitHub Actions UI when ready.

## Pitfalls

- The token file must not be group/world readable.  GitHub will
  400 / 401 with ambiguous messages otherwise.
- `github_workflows` lists YAML file names, not display names.
  Check `.github/workflows/` in the repo.
- `workflow_dispatch` must be declared in the workflow YAML
  itself (`on: [workflow_dispatch]`), or the API returns 422.
- `dispatch_workflow()` just TRIGGERS the run; results live on
  GitHub.  If you need local verdicts, run the equivalent
  `run_*_tests()` instead.

## See also

- `opp-repl-opp-files` — where `github_*` parameters go.
- Every `opp-repl-*-tests` skill — what workflows typically run.
