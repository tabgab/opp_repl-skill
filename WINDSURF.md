# Windsurf Integration Guide

This skill pack is in the **native Anthropic Agent Skills format** —
Windsurf (Codeium's Cascade agent) reads this format directly.  No
conversion required.  Drop the skills into one of the folders below
and Cascade will auto-discover them.

Reference: https://docs.windsurf.com/windsurf/cascade/skills

═══════════════════════════════════════════════════════
OPTION A — GLOBAL INSTALL (recommended)
═══════════════════════════════════════════════════════

Makes every opp-repl-* skill available in EVERY Windsurf workspace
on your machine.  Best when you work with multiple OMNeT++ projects.

### Linux / macOS

```bash
# Clone the pack (or reuse your existing checkout)
git clone https://github.com/tabgab/opp_repl-skill.git ~/opp_repl-skill

# Wire it into Windsurf's global skill directory
mkdir -p ~/.codeium/windsurf/skills
for dir in ~/opp_repl-skill/opp-repl-*; do
    ln -sfn "$dir" ~/.codeium/windsurf/skills/
done

# Verify
ls ~/.codeium/windsurf/skills/
#   opp-repl-ai-workflows        opp-repl-installation
#   opp-repl-chart-tests         opp-repl-mcp-server
#   ... 26 total
```

Using symlinks (as above) means `git pull` in the repo updates
every skill instantly.

Prefer copies instead of symlinks?

```bash
cp -r ~/opp_repl-skill/opp-repl-* ~/.codeium/windsurf/skills/
```

### Windows (PowerShell)

```powershell
git clone https://github.com/tabgab/opp_repl-skill.git $HOME\opp_repl-skill
$target = "$HOME\.codeium\windsurf\skills"
New-Item -ItemType Directory -Force $target | Out-Null
Get-ChildItem $HOME\opp_repl-skill -Directory `
    -Filter 'opp-repl-*' | ForEach-Object {
    Copy-Item $_.FullName $target -Recurse -Force
}
```

(Symlink equivalent needs `mklink /D` in an Admin `cmd.exe`.)

═══════════════════════════════════════════════════════
OPTION B — WORKSPACE INSTALL
═══════════════════════════════════════════════════════

Bundles the skills WITH a specific OMNeT++ / INET project — the
whole team gets the same Cascade behaviour when they clone.

```bash
cd /path/to/your/omnetpp-project
mkdir -p .windsurf/skills

# Vendor the skills into the project (submodule is cleanest)
git submodule add https://github.com/tabgab/opp_repl-skill.git \
    .windsurf/skills/_opp-repl-skill

# Symlink each skill out of the submodule so Windsurf finds them
for dir in .windsurf/skills/_opp-repl-skill/opp-repl-*; do
    ln -sfn "../_opp-repl-skill/$(basename $dir)" .windsurf/skills/
done

# Commit and push — teammates just need `git submodule update --init`
git add .windsurf/skills .gitmodules
git commit -m "Add opp_repl skill pack via submodule"
```

═══════════════════════════════════════════════════════
OPTION C — UI-BASED INSTALL (per skill)
═══════════════════════════════════════════════════════

Quickest way if you only need a handful of skills:

1. Open Windsurf.
2. Launch the **Cascade panel** (Ctrl-L / Cmd-L).
3. Click the three dots (**⋯**) in the top right of the panel.
4. Pick **Skills** in the menu.
5. Click **+ Workspace** or **+ Global**.
6. When the scaffolded `SKILL.md` opens, paste the contents of
   `opp-repl-overview/SKILL.md` (or whichever one you want).
7. Repeat for each skill you need.

Option A or B is faster for the full pack — the UI is one-at-a-time.

═══════════════════════════════════════════════════════
VERIFICATION
═══════════════════════════════════════════════════════

1. Restart Windsurf (or reload the window: Cmd-Shift-P → "Reload
   Window").
2. In the Cascade panel, type `@` and wait for the autocomplete.
   You should see every `opp-repl-*` skill listed.
3. Pick `@opp-repl-overview` — Cascade will acknowledge the skill
   and load its full body into context on demand.

If the autocomplete is empty:
- Double-check the path: `ls ~/.codeium/windsurf/skills/`.
- Confirm each `SKILL.md` is DIRECTLY inside its skill dir, not a
  subfolder.  Structure must be:
      `~/.codeium/windsurf/skills/opp-repl-overview/SKILL.md`
- Confirm YAML frontmatter is intact (starts AND ends with `---`).

═══════════════════════════════════════════════════════
USING THE SKILLS IN WINDSURF
═══════════════════════════════════════════════════════

### Automatic invocation

Cascade reads every skill's frontmatter `description` at startup.
When your prompt matches a description's trigger, the skill is
pulled in automatically.  Examples that will auto-load skills:

> "Install opp_repl on this machine."
> — auto-loads `opp-repl-installation`

> "Write a .opp file for an INET-based project."
> — auto-loads `opp-repl-opp-files` (with the INET template)

> "Run fingerprint tests on the examples/ethernet configs."
> — auto-loads `opp-repl-fingerprint-tests` (and probably
>   `opp-repl-running-simulations` and `opp-repl-filtering`)

### Manual invocation

For tasks Cascade doesn't immediately recognise, @-mention the
skill yourself:

> @opp-repl-ai-workflows
> Walk me through investigating a fingerprint regression on INET.

> @opp-repl-ssh-cluster @opp-repl-parameter-optimization
> Distribute a parameter sweep for Aloha.SlottedAloha1 across
> node1.local and node2.local to maximize channelUtilization.

You can @-mention multiple skills in one message; Cascade loads all
of them.

### Hand-off with MCP

If you also run `opp_repl --mcp-port 9966`, combine these skills
with Windsurf's MCP feature (`docs.windsurf.com/windsurf/cascade/mcp`)
to let Cascade actually EXECUTE the recipes it reads.  Add to your
Windsurf MCP config:

```json
{
  "mcpServers": {
    "opp_repl": {
      "url": "http://127.0.0.1:9966/mcp"
    }
  }
}
```

Then `@opp-repl-ai-workflows` recipes become single-turn actions.

═══════════════════════════════════════════════════════
CROSS-AGENT COMPATIBILITY
═══════════════════════════════════════════════════════

Windsurf scans several sibling locations for skills:

- `~/.codeium/windsurf/skills/`   (Windsurf native)
- `~/.claude/skills/`             (shared with Claude Desktop / Code)
- `~/.claude_desktop/skills/`     (shared with Claude Desktop)
- `~/.agents/skills/`             (cross-agent directory)

If you already keep skills under `~/.claude/skills/`, Windsurf
will pick them up with no action needed.  You can also install
ONCE into `~/.agents/skills/` and have every compatible agent on
your machine find them.

═══════════════════════════════════════════════════════
UPDATING
═══════════════════════════════════════════════════════

Global install (symlinks):

```bash
cd ~/opp_repl-skill && git pull
```

Global install (copies): re-run the `cp` step from Option A.

Workspace install (submodule):

```bash
git submodule update --remote --merge .windsurf/skills/_opp-repl-skill
git commit -am "Update opp_repl skill pack"
```

═══════════════════════════════════════════════════════
UNINSTALL
═══════════════════════════════════════════════════════

Global:

```bash
rm -rf ~/.codeium/windsurf/skills/opp-repl-*
```

Workspace:

```bash
rm -rf .windsurf/skills/opp-repl-* .windsurf/skills/_opp-repl-skill
git submodule deinit .windsurf/skills/_opp-repl-skill
```
