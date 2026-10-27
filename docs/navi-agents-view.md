# Navi (Jalon): Agents view

Goal: one screen in Navi that shows every AI agent in the fleet, what each
is doing right now, and the sub-agents it spawned, live, in the same
phosphor-green sonar look as the rest of Jalon.

Reference: the TikTok clip of a dark chat UI with "5 running in parallel"
(rough-cut, captions-burn-in, thumbnail-maker...) and a "Video Editor" agent
card. That UI is someone's own build, not a product you can install. The two
repos named in the comments are the closest open-source equivalents:

- bagidea/bagidea-office: pixel-art office on the desktop wallpaper, agents
  walk to desks, sub-agents appear as ghost clones, workflow canvas, Mission
  Control board. Windows stable, macOS beta. Daemon on 127.0.0.1:8787 with a
  WebSocket event hub and `POST /event`.
- AgentSystemLabs/agent-office: cartoon 3D office, each Claude Code worker at
  a desk with its live terminal, GitHub issue and PR boards. Web app on
  127.0.0.1:4600. Needs Node 20 and the GitHub CLI.

Both are separate apps. Neither embeds in Jalon. So Navi gets its own view,
fed by the same hook mechanism those apps use.

## Fleet to show

| Agent | Where | How it reports |
|---|---|---|
| Claude Code sessions (Remote Control, side sessions) | Mac mini | Claude Code hooks |
| Claude Code worker jobs (`agent` screen session) | 2017 MacBook Pro | Claude Code hooks |
| Lead bot (Claude Code in WSL Ubuntu) | Windows PC | Claude Code hooks |
| Hermes (Mattermost, 8:00 brief, Twenty CRM) | Mac mini | one curl in its tool wrapper or cron |
| Scheduled jobs (whisper queue, CRM hygiene, reports) | old Mac, mini | `navi-event` at start and end |

## Design

**1. Event ingest.** `POST /api/agents/event` in Jalon, bearer token in
`NAVI_AGENT_TOKEN`. Reachable over Tailscale from every machine. Body uses
the same shape as bagidea-office so that app could be plugged in later:

```json
{ "type": "task.started", "agent": "mini/claude", "session": "abc",
  "task": "Cut the Marlowe 30s", "tool": "Bash", "text": "...", "ts": 1761580000 }
```

Types: `agent.online`, `agent.offline`, `session.start`, `session.end`,
`task.started`, `task.progress`, `task.completed`, `task.failed`,
`tool.start`, `tool.end`, `subagent.start`, `subagent.stop`,
`perm.requested`, `perm.approved`, `perm.denied`, `chat.message`.

Store: append to `data/agent-events.jsonl` (or the SQLite Jalon already
uses), keep the last 7 days, and keep an in-memory roster (agent, status,
current task, sub-agents, last seen).

**2. Live stream.** `GET /api/agents/stream` as Server-Sent Events. On
connect: roster snapshot, then each new event. Roster status per agent:
IDLE, WORKING, WAITING (permission or question), BLOCKED, OFFLINE (no event
for 10 minutes).

**3. Hook script.** One file, `scripts/navi-hook.sh`, copied to each
machine. Reads the hook JSON on stdin, maps the Claude Code hook name to an
event type, POSTs it, exits 0 always (a failing hook must never block an
agent). Install in `~/.claude/settings.json` on each machine:

- SessionStart -> session.start, SessionEnd/Stop -> session.end
- UserPromptSubmit -> task.started (first line of the prompt = task name)
- PreToolUse -> tool.start, PostToolUse -> tool.end
- SubagentStart -> subagent.start, SubagentStop -> subagent.stop
- Notification -> perm.requested (permission) or chat.message
- PermissionRequest/response -> perm.approved or perm.denied

Agent id = `<hostname>/<project folder>`; session = Claude's session id.

**4. The page `/agents`.** Same CRT and sonar vocabulary as the rest:

- Sonar scope: one blip per agent on the ring, distance from centre =
  time since last event, colour = status. A WORKING blip pulses; a WAITING
  blip blinks and shows a small "?" because that one needs James.
- Sub-agents: small satellites orbiting their parent blip, with the task
  name on hover, as the ghost clones in bagidea-office.
- Right column, "running in parallel": one row per active task with the
  tool it is on, elapsed time, and a progress bar driven by
  `task.progress` when the agent sends one, otherwise an indeterminate bar.
- Agent card on click: role, machine, model, current task, last 20 events,
  and a "draft waiting for your OK" line when a perm.requested is open.
- Bottom: a brief box. Send posts to Hermes (Mattermost) or to a chosen
  Claude Code session through the Remote Control message route, so Navi
  can also start work, not only watch it.

**5. Workflows.** Jalon already has Programmation. Add a "Workflows" tab
that lists the scheduled jobs (LaunchAgents, cron, Hermes schedules) with
last run, next run and last result, from the same event log: a job is a
session whose agent id ends in `/job-<name>`.

## Build order

1. Endpoint, token, JSONL store, SSE stream (half a day).
2. Hook script and settings on the Mac mini first; check events arrive.
3. `/agents` page with the list view only; then the sonar scope.
4. Roll the hook to the old Mac and the Windows PC; add Hermes.
5. Workflows tab.

Nothing here touches milestone-app or the money and bookings channels.
