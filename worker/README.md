# AI Warrior Tutor — Cloudflare Worker

The Worker behind the `<ai-warrior-widget>` drop-in. Proxies AI requests through
**Cloudflare AI Gateway** into **Workers AI** (Llama 3.1 on the edge), enforces
per-subscriber monthly quotas in KV, and surfaces a **Perplexity Pro referral**
when a user hits their limit.

## Why this design

| Concern | How it's handled |
|---|---|
| API keys leaking | Never in the browser. Never in this repo. Stored as `wrangler secret put` only. |
| Cost runaway | KV-backed quota per subscriber + per IP. Free tier = 20/month, Pro = 1000/month (both env-configurable). |
| Cost pass-through | Subscribers pay you (via Substack). When their quota runs out, the widget shows an upgrade card with two CTAs: re-up the subscription, or get Perplexity Pro through your referral link. |
| Observability | AI Gateway logs every request, caches identical ones, tracks tokens and cost per provider. Open at `dash.cloudflare.com → AI → AI Gateway`. |
| Provider lock-in | Workers AI today, swap to Claude/GPT by changing `TUTOR_MODEL` env var. Same gateway, same logs. |

## Security model — what's public, what's secret

| Lives in repo (anyone can read) | Lives in Cloudflare only (encrypted) |
|---|---|
| Worker source code | `ANTHROPIC_API_KEY` (if you add Claude later) |
| `wrangler.toml` config | `OPENAI_API_KEY` (if you add GPT later) |
| Public env vars (account ID, gateway name, model names, quota limits, referral URL) | `SUBSTACK_API_KEY` (for paid-subscriber verification) |
| AI Gateway URL pattern | KV namespace contents (quota counters) |
| Perplexity referral URL (it's a public sharable link by design) | |

If someone clones this repo, they get the **logic** — fine, it's educational —
but they can't deploy to *your* Worker, can't call *your* gateway, can't read
*your* KV. To deploy their own copy they'd need to log into their own Cloudflare
account, costing them money, billing them.

## One-time setup

Prerequisites: a Cloudflare account (you have one — `063ea8fc4f5e84d72b9a09933215d0e1`),
Node 20+, and `npm` or `pnpm`.

```bash
cd worker
npm install
npx wrangler login    # opens browser, links to your Cloudflare account
```

### 1. Create the KV namespace

```bash
npx wrangler kv:namespace create QUOTA
```

Copy the returned `id` into `wrangler.toml`, replacing `REPLACE_WITH_KV_ID_AFTER_FIRST_CREATE`.

### 2. Create the AI Gateway

In the Cloudflare dashboard:

1. Go to <https://dash.cloudflare.com/063ea8fc4f5e84d72b9a09933215d0e1/ai/ai-gateway>
2. Click **Create a custom gateway**
3. Slug: `ai-warrior-gateway` (must match `AI_GATEWAY_NAME` in `wrangler.toml`)
4. Enable: **Cache**, **Log requests** (this is the whole point)

### 3. Paste your Perplexity referral code

1. Open <https://www.perplexity.ai/settings/account> → **Refer a friend**
2. Copy the referral URL
3. Edit `wrangler.toml` → replace `REPLACE_ME` in `PPLX_REFERRAL_URL`

### 4. Deploy

```bash
npm run deploy
```

You'll get a URL like `https://ai-warrior-tutor.YOURNAME.workers.dev`.

### 5. Tell the website where the Worker lives

In GitHub repo → **Settings → Secrets and variables → Actions → Variables**:

- New variable `WORKER_ENDPOINT` = the workers.dev URL from step 4

The next Pages deploy will inject it into `tutor.html` automatically.

### 6. (Optional) Custom domain

In `wrangler.toml`, uncomment the `[[routes]]` block and edit for your zone.
Re-deploy. Workers AI now answers from `tutor.kiwidialectic.com` (or wherever).

## Local development

```bash
npm run dev
```

Opens a local server with hot reload. Workers AI calls work in dev as long as
you're logged in via wrangler.

To test the widget locally, open `tutor.html` and replace `WORKER_ENDPOINT`
with `http://localhost:8787`.

## Endpoints

### `POST /reo` and `POST /tutor`

Request:
```json
{
  "messages": [
    { "role": "user", "content": "Translate 'mutual aid' into te reo" }
  ],
  "subscriber_id": "kiriana@example.com"
}
```

`subscriber_id` is optional. Without it, the caller is treated as anonymous and
gets the free tier quota keyed by IP.

Success (`200`):
```json
{
  "reply": "…",
  "usage": { "used": 7, "limit": 1000, "is_pro": true },
  "tokens": 312
}
```

Quota exhausted (`402`):
```json
{
  "error": "quota_exhausted",
  "message": "You've used your 1000 messages this month. To keep going, top up via the upgrade link, or sharpen your own AI toolkit with Perplexity Pro.",
  "used": 1000,
  "limit": 1000,
  "is_pro": true,
  "upgrade_url": "https://kiwidialectic.com/subscribe",
  "perplexity_referral_url": "https://www.perplexity.ai/pro?referral_code=…"
}
```

### `GET /health`

```json
{ "ok": true, "service": "ai-warrior-tutor", "gateway": "ai-warrior-gateway", "endpoints": ["/reo", "/tutor"] }
```

## Tuning costs

- **Workers AI free tier**: 10,000 neurons/day (a Llama 3.1 8B response uses ~5-10 neurons; 70B uses ~50-100). For the volumes a course site will see, you're effectively free until you cross ~100 daily active users.
- **Cache TTL**: 1 hour by default (see `wrangler.toml`). Same question = cached response, free.
- **Quotas**: lower `QUOTA_FREE` if you see anon abuse; raise `QUOTA_PRO` if subscribers complain.
- **Model swap**: edit `TUTOR_MODEL` to `@cf/meta/llama-3.1-8b-instruct` to halve costs, or `@cf/qwen/qwen2.5-7b-instruct` for a different voice.

## Future: real subscriber identification

Right now `subscriber_id` is trusted from the client. That's fine for an MVP
(worst case a bad actor steals your friend's quota — they can't escalate to
your API keys). Real options when usage grows:

1. **Substack API check**: Worker calls Substack's `/v1/subscribers` with `SUBSTACK_API_KEY` to verify the email is on the paid list. Cache result for an hour.
2. **Magic-link JWT**: Worker emails the subscriber a signed JWT; widget stores in `localStorage`; verified per request.
3. **Cloudflare Access**: bind the Worker behind Access, use email-based one-time-pin login. No code in the widget.

Pick when traffic justifies it.
