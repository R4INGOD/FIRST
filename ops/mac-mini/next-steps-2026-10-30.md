# Mac mini · next steps (Oct 30, 2026)

Two things James approved in the cloud session "AI agents dashboard" that need this machine's logins. Run top to
bottom; each step says what to check. Nothing here touches member data.

## A. Welcome offer on the boutique (merged: milestone-app #8, #9; milestone-site #6)

1. **Stripe** (James's dashboard, not this machine): Products → Coupons → New: 10 % off, duration "once",
   limit "first-time order" if offered; then a promotion code `BIENVENUE10`, once per customer. If James prefers
   another code or percentage, change `app_settings.welcome_code` / `welcome_percent` in step 2 to match.
2. **Supabase**, MILESTONE APP production, SQL editor: paste `supabase/migrations/20261030100000_welcome_offer.sql`
   from milestone-app (main), run it. Then, only once the Stripe code exists:
   `update public.app_settings set value = 'true'::jsonb where key = 'welcome_offer_live';`
   Check: `select key, value from app_settings where key like 'welcome_%';` shows the three rows.
3. **App**: Coolify redeploys app.milestone.uno from main by itself. Check `https://app.milestone.uno/api/welcome`
   answers `{"live":true,"percent":10,...}` after step 2.
4. **Website** (no auto-deploy): in the milestone-site clone on this Mac,
   `git pull origin main && npm run deploy` (the Cloudflare account that owns the Worker `milestone-site`; if
   `npm ci` fails on peer deps, use `npm install --legacy-peer-deps` first; `bun install` also works).
   Check: open https://milestone.uno/shop in a private window; the box appears after 4 s.
5. Tell James where the answers show: app admin dashboard, card "D'où viennent les visiteurs · 30 j", and #leads.

## B. Agents board in Jalon (merged: jalon `agents-view` → main)

1. **Coolify**, app Jalon: add env `NAVI_AGENT_TOKEN` = `openssl rand -hex 32` (keep the value for step 3), add a
   persistent volume mounted at `/app/data`, redeploy. Optional: `MATTERMOST_WEBHOOK_URL` (an incoming webhook in
   the #hermes or #general channel) so briefs typed on the board reach Hermes on Mattermost.
2. **Cloudflare Access**, application Jalon: add a policy "Agents ingest", action Bypass, for paths
   `/api/agents/event` and `/api/agents/outbox` (the bearer token guards them). Everything else stays behind the PIN.
   Check: `curl -s -o /dev/null -w "%{http_code}" -X POST https://jalon.milestone.uno/api/agents/event` → 401 (not a Cloudflare login page).
3. **Hook on this Mac**: in the jalon clone, `git pull origin main`, then
   `scripts/install-navi-hook.sh https://jalon.milestone.uno "<NAVI_AGENT_TOKEN>" mini`.
   Check: `~/.navi/navi-event.mjs chat.message mini/test "hello"` → the event shows on https://jalon.milestone.uno/agents.
4. **Hermes**: merge the `hooks:` block of `~/.navi/hermes-hooks.yaml` into `~/.hermes/config.yaml`, then
   `hermes hooks list` and accept the commands (or set `hooks_auto_accept: true`). Copy the project-manager skill:
   `cp -R <FIRST repo>/ops/mac-mini/hermes/skills/project-manager ~/.hermes/skills/operations/` and
   `chmod +x ~/.hermes/skills/operations/project-manager/scripts/*.mjs`. First use asks for NAVI_URL and the token.
   Check: Hermes appears as `mini/hermes` on the board; `/project-manager standup` in Mattermost answers.
5. **Old MacBook Pro** (milestone-agent-mbp, over ssh): same installer with host name `mbp`.
   **Windows PC** (WSL Ubuntu, over Tailscale ssh): same installer with host name `win`, inside WSL where
   Claude Code runs.
6. Optional: `~/.hermes/scripts` jobs and the 02:30 invoice job wrap their runs with
   `~/.navi/navi-event.mjs job.start <name>` / `job.end <name> ok|fail`, so they show in the board's Workflows table.

## C. Still James only

- milestone-app PR #4 (`/api/agent/navi`): merge, then set `MILESTONE_API_URL` and `AGENT_API_KEY` in Jalon's
  Coolify env so the money and bookings channels light up.
