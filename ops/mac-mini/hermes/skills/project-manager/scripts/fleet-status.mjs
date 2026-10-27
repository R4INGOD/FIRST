#!/usr/bin/env node
// Fleet digest from the Jalon agents board, for the project-manager skill. Reads NAVI_URL / NAVI_AGENT_TOKEN,
// falling back to ~/.navi/config.json. Prints Markdown, or the raw snapshot with --json. Exit 0 always.
import { readFileSync, existsSync } from "node:fs";
import { join } from "node:path";

const home = process.env.HOME || "";
let c = {};
const f = join(home, ".navi", "config.json");
if (existsSync(f)) { try { c = JSON.parse(readFileSync(f, "utf8")); } catch { /* env only */ } }
const url = (process.env.NAVI_URL || c.url || "").replace(/\/$/, "");
const token = process.env.NAVI_AGENT_TOKEN || c.token || "";
if (!url) { console.log("NAVI_URL manquant : pas de lecture de la flotte."); process.exit(0); }

const headers = { authorization: `Bearer ${token}` };
if (c.cfAccessClientId && c.cfAccessClientSecret) { headers["CF-Access-Client-Id"] = c.cfAccessClientId; headers["CF-Access-Client-Secret"] = c.cfAccessClientSecret; }

const WORKING_STALE = 10 * 60_000, IDLE_STALE = 6 * 3_600_000;
const status = (w, now) => {
  if (w.status === "offline") return "offline";
  const silent = now - w.lastSeen;
  if ((w.status === "working" || w.status === "waiting" || w.status === "blocked") && silent > WORKING_STALE) return "offline";
  if (w.status === "idle" && silent > IDLE_STALE) return "offline";
  return w.status;
};
const dur = (ms) => { const s = Math.max(0, Math.round(ms / 1000)); if (s < 60) return `${s} s`; const m = Math.floor(s / 60); if (m < 60) return `${m} min`; const h = Math.floor(m / 60); return h < 48 ? `${h} h ${String(m % 60).padStart(2, "0")}` : `${Math.floor(h / 24)} j`; };
const when = (ts) => new Intl.DateTimeFormat("fr-CA", { timeZone: "America/Toronto", weekday: "short", day: "numeric", month: "short", hour: "2-digit", minute: "2-digit", hourCycle: "h23" }).format(new Date(ts));

try {
  const res = await fetch(`${url}/api/agents`, { headers, signal: AbortSignal.timeout(8000) });
  if (!res.ok) { console.log(`Jalon a répondu HTTP ${res.status} sur /api/agents.`); process.exit(0); }
  const d = await res.json();
  if (process.argv.includes("--json")) { console.log(JSON.stringify(d, null, 2)); process.exit(0); }
  const now = d.now ?? Date.now();
  const ws = d.workers.map((w) => ({ ...w, st: status(w, now) }));
  const needs = ws.filter((w) => !w.job && (w.st === "waiting" || w.st === "blocked"));
  const running = ws.filter((w) => w.st === "working");
  const doneRecent = ws.filter((w) => w.st === "idle" && w.note && now - w.lastSeen < 12 * 3_600_000);
  const failedJobs = d.jobs.filter((j) => j.last && j.last.ok === false);
  const silentMidTask = ws.filter((w) => w.st === "offline" && w.status === "working" && !w.job);
  const out = [];
  out.push(`# Flotte · ${when(now)}`);
  out.push(`${ws.filter((w) => w.st !== "offline").length} unités en ligne · ${[...new Set(ws.map((w) => w.host))].length} machines · ${running.reduce((n, w) => n + w.subagents.length, 0)} sous-agents`);
  out.push("", "## Besoin de James");
  if (!needs.length && !failedJobs.length && !silentMidTask.length) out.push("- rien");
  for (const w of needs) out.push(`- **${w.agent}** ${w.st === "waiting" ? "attend" : "bloqué"} : ${w.pending ?? w.note ?? w.task ?? "?"} (depuis ${dur(now - w.lastSeen)})`);
  for (const j of failedJobs) out.push(`- job **${j.name}** (${j.host}) en ÉCHEC ${when(j.last.end ?? j.last.start)} : ${j.last.text ?? ""}`);
  for (const w of silentMidTask) out.push(`- **${w.agent}** silencieux depuis ${dur(now - w.lastSeen)} en plein travail : « ${w.task ?? "?"} »`);
  out.push("", "## En cours");
  if (!running.length) out.push("- rien");
  for (const w of running) out.push(`- **${w.agent}** · ${w.task ?? "?"}${w.tool ? ` · ${w.tool}` : ""}${w.progress != null ? ` · ${Math.round(w.progress * 100)} %` : ""} · ${dur(now - (w.taskSince ?? w.since))}${w.subagents.length ? ` · ${w.subagents.length} sous-agent(s) : ${w.subagents.map((s) => s.task).join(", ")}` : ""}`);
  out.push("", "## Terminé récemment");
  if (!doneRecent.length) out.push("- rien");
  for (const w of doneRecent) out.push(`- **${w.agent}** · ${w.task ?? ""} → ${w.note}`);
  out.push("", "## Jobs");
  if (!d.jobs.length) out.push("- aucun job connu");
  for (const j of d.jobs) out.push(`- ${j.name} (${j.host}) · dernier ${j.last ? `${when(j.last.start)} ${j.last.end === null ? "en cours" : j.last.ok === false ? "ÉCHEC" : "OK"}` : "jamais"} · ${j.runs7d} run(s) 7 j${j.failed7d ? `, ${j.failed7d} échec(s)` : ""}${j.nextRun ? ` · prochain dans ${dur(j.nextRun - now)}` : ""}`);
  const pendingBriefs = (d.briefs ?? []).filter((b) => !b.delivered);
  if (pendingBriefs.length) { out.push("", "## Briefs en attente de livraison"); for (const b of pendingBriefs) out.push(`- → ${b.to} : ${b.text}`); }
  console.log(out.join("\n"));
} catch (e) { console.log(`Jalon injoignable (${e.message}).`); }
