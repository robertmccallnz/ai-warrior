# Site analytics — Cloudflare Web Analytics

Privacy-first, cookieless, GDPR/NZ-Privacy-Act-friendly. No consent banner required.
Free for the volumes this site will see.

## One-time setup

1. Sign in at <https://dash.cloudflare.com/> → **Analytics & Logs** → **Web Analytics**.
2. Click **Add a site** → choose **Manual setup** (we're not proxying DNS through Cloudflare; GitHub Pages stays as the host).
3. Enter the hostname `robertmccallnz.github.io` (path `/ai-warrior/` is fine — Cloudflare tracks the full URL).
4. Cloudflare gives you a snippet like:
   ```html
   <script defer src='https://static.cloudflareinsights.com/beacon.min.js'
           data-cf-beacon='{"token": "abc123…"}'></script>
   ```
   Copy the `token` value only.
5. In this repo, go to **Settings → Secrets and variables → Actions → Variables → New repository variable**:
   - Name: `CF_ANALYTICS_TOKEN`
   - Value: the token from step 4
6. Trigger a deploy (push to `main`, or run **Deploy to GitHub Pages** manually from the Actions tab). The workflow substitutes the token into every HTML page at build time.

## How it works in this repo

- Every page (`index.html`, `index-mi.html`, `partners.html`, `partners-mi.html`) has a beacon stub:
  ```html
  <script defer src="https://static.cloudflareinsights.com/beacon.min.js"
          data-cf-beacon='{"token": "CF_ANALYTICS_TOKEN"}'></script>
  ```
- The deploy workflow [`.github/workflows/deploy.yml`](../.github/workflows/deploy.yml) substitutes
  the literal `CF_ANALYTICS_TOKEN` with the value of the `CF_ANALYTICS_TOKEN` repo variable on every deploy.
- If the variable isn't set yet, the workflow **strips** the beacon line entirely so no broken script ships.

The token is *not* a secret in the traditional sense — it ends up in public HTML once deployed —
but keeping it in a repo variable (not committed) means you can rotate it without a code change.

## What you'll see

In the Cloudflare dashboard, after ~24 hours of traffic:

- **Page views and visits** (a visit = a session, deduped by browser fingerprint without cookies)
- **Top pages** — useful for seeing whether the MI translation is being read
- **Referrers** — Substack, social, search, direct
- **Countries** — useful for seeing Aotearoa vs. international reach
- **Devices / browsers** — to spot rendering issues

## Weekly digest (optional)

Once the Cloudflare connector is connected in this Perplexity session, ask me to set up a recurring
weekly engagement digest — I'll pull pageviews, top pages, and EN vs MI split, and send it as an
in-app notification every Monday morning NZT.
