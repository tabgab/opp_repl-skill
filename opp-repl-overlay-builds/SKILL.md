---
name: opp-repl-overlay-builds
description: Out-of-tree builds with fuse-overlayfs — build a project into a writable overlay layer on top of a read-only source tree without modifying the checkout. Set overlay_name in the .opp file. list_overlays / cleanup_overlays / clear_build_root manage them. Load when testing patches, comparing builds across git commits, or doing parallel multi-mode builds.
---

# Overlay builds

Overlay builds use `fuse-overlayfs` to create a writable layer over
a read-only source tree.  Builds happen in the overlay; the
original source stays pristine.  This is what
`compare_simulations_between_commits()` uses internally, and it's
available standalone too.

Upstream reference:
https://github.com/omnetpp/opp_repl/blob/main/doc/overlay_builds.md

## Requirements

- `fuse-overlayfs` installed and user-mountable.
- On Linux; macOS has no fuse-overlayfs.

    sudo apt install fuse-overlayfs     # Debian/Ubuntu
    sudo dnf install fuse-overlayfs     # Fedora

## Enabling an overlay

Set `overlay_name` in the `.opp` file; builds happen in a layer
named by that string:

    SimulationProject(
        name="inet+omnetpp",
        root_folder=".",
        omnetpp_project="omnetpp",
        overlay_name="inet+omnetpp",     # key line
        library_folder="src",
        bin_folder="bin",
        build_types=["dynamic library"],
        dynamic_libraries=["INET"],
        ...
    )

The overlay build root defaults to a per-user cache; override with
`overlay_build_root=` (relative paths resolved against the `.opp`
file's directory).

## Management API

    from opp_repl.simulation.overlay import *

    list_overlays()          # names of overlay layers under the root
    cleanup_overlays()       # unmount all overlays
    clear_build_root()       # unmount + wipe all overlay data

## When to use overlays

- Testing a patch series without a git worktree.
- Building the same sources in multiple modes (release, debug,
  sanitize) without Makefile collisions.
- Feeding a read-only CI cache of sources to many parallel builds.
- Underpinning `compare_simulations_between_commits()`.

## Pitfalls

- Stale mounts accumulate after crashes.  `cleanup_overlays()` and
  `clear_build_root()` are your friends; run them in CI cleanup.
- macOS cannot use overlays.  Use git worktrees there instead.
- Permission issues: the user running opp_repl must be in `fuse`
  group, or `user_allow_other` must be set in
  `/etc/fuse.conf`.
- Overlays are per-path; two different `.opp` files with the same
  `overlay_name` but different `root_folder` values will conflict.

## See also

- `opp-repl-opp-files` — where `overlay_name` gets set.
- `opp-repl-comparing-simulations` — uses overlays under the hood.
- `opp-repl-opp-env-integration` — alternative installation method.
