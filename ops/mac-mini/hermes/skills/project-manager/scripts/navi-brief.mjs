#!/usr/bin/env node
// Send a brief from Hermes to a worker on the Jalon board: navi-brief.mjs "<host/project>|hermes" "<text>".
// The target gets it as context on its next prompt. Exit 0 always.
import { readFileSync, existsSync } from "node:fs";
import { join } from "node:path";

const [to, ...rest] = process.argv.slice(2);
const text = rest.join(" ").trim();
const home = process.env.HOME || "";
let c = {};
const f = join(home, ".navi", "config.json");
if (existsSync(f)) { try { c = JSON.parse(readFileSync(f, "utf8")); } catch { /* env only */ } }
const url = (process.env.NAVI_URL || c.url || "").replace(/\/$/, "");
if (!to || !text || !url) { console.log('usage: navi-brief.mjs "<host/project>|hermes" "<text>" (NAVI_URL requis)'); process.exit(0); }
const headers = { "content-type": "application/json", authorization: `Bearer ${process.env.NAVI_AGENT_TOKEN || c.token || ""}` };
if (c.cfAccessClientId && c.cfAccessClientSecret) { headers["CF-Access-Client-Id"] = c.cfAccessClientId; headers["CF-Access-Client-Secret"] = c.cfAccessClientSecret; }
try {
  const r = await fetch(`${url}/api/agents/brief`, { method: "POST", headers, body: JSON.stringify({ to, text }), signal: AbortSignal.timeout(8000) });
  const j = await r.json().catch(() => ({}));
  console.log(r.ok && j.ok ? `brief envoyé à ${to} (${j.brief?.via === "mattermost" ? "Mattermost" : "file, livré au prochain prompt"})` : `échec : ${j.error ?? `HTTP ${r.status}`}`);
} catch (e) { console.log(`échec : ${e.message}`); }
