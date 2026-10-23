---
name: twenty-crm
description: Read and update Milestone's Twenty CRM (crm.milestone.uno) — people, companies, deals (opportunities), tasks and notes. Use whenever someone asks about a client, member, podcast client, lead, deal, pipeline, follow-up or anything "in the CRM".
---

# Milestone CRM (Twenty)

Milestone's CRM is a self-hosted Twenty at `crm.milestone.uno`, behind Cloudflare Access.
Every request needs **both** the Twenty API key and the Cloudflare service token.
They are set as environment variables in `~/.claude/settings.json` on this Mac mini:

- `TWENTY_URL` (https://crm.milestone.uno)
- `TWENTY_API_KEY`
- `CF_ACCESS_CLIENT_ID`, `CF_ACCESS_CLIENT_SECRET`

Never print, echo, log or paste these values. Never write them into a file, a commit or a message.

## Calling the API

Define this once per shell, then use it:

```bash
twenty() { # usage: twenty METHOD /rest/path [json-body]
  curl -sS -X "$1" "$TWENTY_URL$2" \
    -H "Authorization: Bearer $TWENTY_API_KEY" \
    -H "CF-Access-Client-Id: $CF_ACCESS_CLIENT_ID" \
    -H "CF-Access-Client-Secret: $CF_ACCESS_CLIENT_SECRET" \
    -H "Content-Type: application/json" ${3:+--data "$3"}
}
```

- List: `twenty GET '/rest/people?limit=20'` → `{ "data": { "people": [...] }, "totalCount": n }`
- Filter: `twenty GET '/rest/people?filter=emails.primaryEmail[eq]:"a@b.com"&limit=1'`
  - Operators: `[eq] [neq] [gt] [gte] [lt] [lte] [like] [in]`; combine with commas (AND),
    e.g. `filter=dueAt[lt]:"2026-10-23T04:00:00Z",status[neq]:"DONE"`. URL-encode spaces and `%` (for `[like]` use `%25`).
- One record: `twenty GET /rest/people/<id>`
- Create: `twenty POST /rest/people '{"name":{"firstName":"Ana","lastName":"Roy"},"emails":{"primaryEmail":"ana@x.com"}}'`
- Update: `twenty PATCH /rest/opportunities/<id> '{"stage":"PROPOSAL"}'`
- Pipe through `jq` to keep output short.

If a field name is uncertain, fetch one existing record and read its keys before writing.

### Troubleshooting

- **HTML or a redirect to a Cloudflare login page:** the Cloudflare service token is missing or not allowed on the CRM's Access policy.
- **401:** the Twenty API key is wrong or revoked.
- **400 on a filter:** check quoting. Values in double quotes, the whole URL in single quotes.

## Milestone's data model

- **people:** `name {firstName, lastName}`, `emails {primaryEmail}`, `phones`, `company`, and the custom field
  **`milestoneRelation`**:
  - `MEMBER`: holds a studio membership
  - `PODCAST_CLIENT`: bought a podcast season. This tag wins: never change a PODCAST_CLIENT to MEMBER.
  - The Milestone app (app.milestone.uno) syncs new members and podcast clients into People every hour, matched by email.
- **companies:** organisations: brands, labels, agencies.
- **opportunities** (deals): `name`, `stage`, `pipeline`, `dealType`, `amount {amountMicros, currencyCode}`, `pointOfContactId`, `companyId`.
  - Pipelines: `OCCUPANCY` (studio bookings and memberships), `AGENCY` (creative and video projects), `MARKETPLACE`.
  - The last stage, `CUSTOMER`, means won. Every other stage is open.
  - Amounts are in **micros**: $1 = 1,000,000. $2,500 CAD = `{"amountMicros": 2500000000, "currencyCode": "CAD"}`. Milestone prices in CAD.
- **tasks:** `title`, `bodyV2`, `status` (`TODO`, `IN_PROGRESS`, `DONE`), `dueAt`, `assigneeId`. They link to records through `taskTargets`.
- **notes:** `title`, `bodyV2`. They link to records through `noteTargets`.
  - Before creating a task or note target for the first time, read an existing one to copy its shape.

## Rules

1. **Read freely.** Answer questions from live CRM data, not from memory. Say how many records you looked at.
2. **Search before you create.** Look a person up by email, and a company by name, so you never make duplicates.
3. **Writes need a yes.** Before any create or update, show exactly what will change (record, field, old → new) and wait for a yes. Batches: show the list, one yes covers it.
4. **Never delete** (people, companies, deals, tasks, notes) unless the person explicitly asks to delete that specific record. Prefer marking it instead, like a stage or a status.
5. **Don't touch `milestoneRelation` by hand** unless asked. The app manages it.
6. **Emails and messages to clients are drafts only.** Write them in French by default (Quebec, tutoiement for artists, vous for brands and companies) unless the client writes in English. Never send them.
7. **Privacy:** client data stays in the CRM and in this conversation. Don't paste it into other tools or files unless asked.

## Useful recipes

- **Today's follow-ups:**
  `twenty GET '/rest/tasks?filter=dueAt[lt]:"<tomorrow 04:00Z>",status[neq]:"DONE"&limit=50'`
  Montreal midnight is 04:00Z in summer (EDT) and 05:00Z in winter (EST).
- **Open deals by pipeline:** list `opportunities` (`limit=200`), group by `pipeline`, skip `stage == "CUSTOMER"`, and sum `amountMicros / 1e6`.
- **Who joined this week:** `twenty GET '/rest/people?filter=createdAt[gte]:"<monday 04:00Z>"&limit=50'`
- **Log a call:** find the person by email, then propose a note (title plus a short body), linked to them, for a yes.
