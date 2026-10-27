# Hermes on the Mac mini: Jalon board + project manager

Two pieces, both to do from the Mac mini (Remote Control session or ssh).

## 1. Hermes reports to the Jalon board

From a clone of `R4INGOD/jalon` (branch `agents-view` until merged):

```bash
scripts/install-navi-hook.sh https://jalon.milestone.uno "$NAVI_AGENT_TOKEN" mini
```

That installs the Claude Code hook for the mini's own sessions and leaves `~/.navi/hermes-hooks.yaml`. Merge its
`hooks:` block into `~/.hermes/config.yaml`, then:

```bash
hermes hooks list        # accept the new commands when prompted, or set hooks_auto_accept: true
hermes hooks test pre_tool_call --for-tool terminal
```

Hermes then appears as `mini/hermes` on `/agents` with its tools and sub-agents, and a brief typed on the board
for "Hermes" reaches it as context on its next turn.

## 2. Project-manager skill

```bash
mkdir -p ~/.hermes/skills/operations
cp -R ops/mac-mini/hermes/skills/project-manager ~/.hermes/skills/operations/
chmod +x ~/.hermes/skills/operations/project-manager/scripts/*.mjs
```

On first use Hermes asks for `NAVI_URL` and `NAVI_AGENT_TOKEN` (same values as `~/.navi/config.json`) and saves
them in `~/.hermes/.env`. Then, in Mattermost: `/project-manager standup`. Daily standup:

```bash
hermes cron create "45 7 * * 1-5" "/project-manager standup du matin : qu'est-ce qui a besoin de James, qu'est-ce qui tourne, qu'est-ce qui a échoué cette nuit, prochaines tâches. [SILENT] si rien." --name "Fleet standup" --deliver origin
```

Run it once from the Mattermost home channel so `origin` is that channel.
