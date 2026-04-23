---
name: opp-repl-ssh-cluster
description: Distribute simulation tasks across multiple machines using Dask over SSH. Requires the `cluster` extra. Covers SSHCluster setup, binary distribution via rsync, scheduler="cluster", the Dask dashboard, and CLI --hosts usage. Load when a single workstation can't finish the sweep in time.
---

# SSH cluster execution (Dask)

Run simulation tasks in parallel across multiple SSH-reachable
hosts via Dask distributed.  Requires the `cluster` extra
(`dask`, `distributed`) and pre-authenticated SSH.

Upstream reference:
https://github.com/omnetpp/opp_repl/blob/main/doc/cluster.md

## Prerequisites

- `pip install "opp_repl[cluster]"`.
- SSH key-based auth set up from the launching host to every
  worker host (or an ssh-agent in the shell).
- Identical Python + opp_repl + dependency versions on every node
  (Dask serializes live Python objects).

## Setting up the cluster

    from opp_repl.common.cluster import SSHCluster

    c = SSHCluster(scheduler_hostname="node1.local",
                   worker_hostnames=["node1.local", "node2.local"])
    c.start()

Live dashboard: http://localhost:8797 (default).

Smoke-test:

    c.run_gethostname(12)
    # "node1, node2, node2, node1, ..."

## Distributing binaries

Build locally, then rsync the binary distribution to every worker:

    p = get_simulation_project("aloha")
    build_project(simulation_project=p, mode="release")
    p.copy_binary_simulation_distribution_to_cluster(
        ["node1.local", "node2.local"])

Subsequent `copy_*_to_cluster()` calls are incremental (rsync).

## Running on the cluster

Same `run_simulations()` function, extra parameters:

    run_simulations(mode="release", filter="PureAlohaExperiment",
                    scheduler="cluster", cluster=c)

Equivalent two-step form when you want to inspect the task list
before executing:

    mt = get_simulation_tasks(simulation_project=p, mode="release",
                              filter="PureAlohaExperiment",
                              scheduler="cluster", cluster=c)
    mt.run()

Exiting the Python session automatically stops the cluster.

## CLI equivalent

    opp_run_simulations -m release -t 1s \
                        --filter PureAlohaExperiment \
                        --hosts node1.local,node2.local

## Pitfalls

- Mismatched Python versions across nodes surface as opaque
  serialization errors.  Align interpreters first.
- Workers need the SAME filesystem layout as the launcher for
  project paths to resolve.  Either rsync the project tree too, or
  mount a shared NFS/SMB.
- The Dask dashboard binds locally only.  SSH-tunnel it if you
  want remote access:
  `ssh -L 8797:localhost:8797 launcher.local`.
- `scheduler="cluster"` is IGNORED without `cluster=...`; passing
  one without the other falls back to the local thread scheduler.
- Cancelling via Ctrl-C stops local task dispatch but may leave
  workers running the current task; `c.close()` before `c.start()`
  on the next session.

## See also

- `opp-repl-running-simulations` — base concurrency controls.
- `opp-repl-parameter-optimization` — parallelises well onto
  clusters.
- `opp-repl-cli-tools` — `--hosts` flag details.
