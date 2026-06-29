# Custom Domain Setup — aiwarrior.nz

This repo is configured to publish at **https://aiwarrior.nz** via GitHub Pages. The
`CNAME` file at the repository root tells GitHub Pages which custom domain to serve.

> Current state at time of writing: the `CNAME` file is committed, but `aiwarrior.nz`
> has no DNS records yet — so the site is still only reachable at
> https://robertmccallnz.github.io/ai-warrior/. Complete the DNS steps below to bring
> the custom domain online.

## DNS records to add at your registrar

`aiwarrior.nz` is a `.nz` domain, so the registrar is most likely Domain Name
Commission NZ (DNC) via a NZ-resident registrar (Freeparking, IANZ, OpenSRS, etc.).
The steps are the same regardless of registrar.

### Option A — apex (aiwarrior.nz) + www subdomain

This is what GitHub recommends. The apex domain uses **A records** pointing at GitHub's
four anycast IPs, and a **CNAME** record on `www` redirects to the canonical project URL.

**For `aiwarrior.nz` (apex / root):**

| Type | Name | Value | TTL |
|---|---|---|---|
| A | `@` (or blank) | `185.199.108.153` | 3600 |
| A | `@` (or blank) | `185.199.109.153` | 3600 |
| A | `@` (or blank) | `185.199.110.153` | 3600 |
| A | `@` (or blank) | `185.199.111.153` | 3600 |

**For `www.aiwarrior.nz`:**

| Type | Name | Value | TTL |
|---|---|---|---|
| CNAME | `www` | `robertmccallnz.github.io.` | 3600 |

(Note the trailing dot on the CNAME value — most registrar UIs add it automatically.)

### Option B — subdomain only (e.g. only www.aiwarrior.nz)

If you prefer to publish at `www.aiwarrior.nz` rather than the bare apex, replace the
four A records with a single CNAME and change the `CNAME` file in this repo to
`www.aiwarrior.nz`:

| Type | Name | Value | TTL |
|---|---|---|---|
| CNAME | `www` | `robertmccallnz.github.io.` | 3600 |

We've shipped with apex (Option A) by default since the existing footer links across
the ecosystem already point at `https://aiwarrior.nz`.

## After DNS propagates

1. Wait 5–60 minutes for DNS to propagate (test with `dig aiwarrior.nz +short`).
2. Go to **Settings → Pages** on this repo.
3. Under **Custom domain**, you should see `aiwarrior.nz` already populated (from the
   `CNAME` file). GitHub will run a DNS check.
4. Once the DNS check passes, tick **Enforce HTTPS**. (GitHub provisions a free
   Let's Encrypt cert automatically — give it ~10 minutes.)
5. Visit https://aiwarrior.nz — you should see the AI Warrior site.

## How to verify

```bash
# DNS is propagating
dig aiwarrior.nz +short
# Should return four 185.199.x.x IPs

dig www.aiwarrior.nz +short
# Should return robertmccallnz.github.io (and resolve from there)

# Site is live
curl -sI https://aiwarrior.nz/ | head -5
# Should return HTTP/2 200 with server: GitHub.com
```

## Rollback

If anything goes wrong, delete the DNS records at your registrar and remove the
`CNAME` file from this repo. The site continues to be served at
`robertmccallnz.github.io/ai-warrior/` regardless.

## Why this matters

The ecosystem footer strip (added in PR #4) and several media-kit / press-release
documents now reference `https://aiwarrior.nz/` as the canonical URL. Once DNS is in
place, every link in the wild lands on the right place; until then, those links 404
and visitors must use the `github.io` URL.

## References

- [GitHub Docs — Managing a custom domain for your GitHub Pages site](https://docs.github.com/en/pages/configuring-a-custom-domain-for-your-github-pages-site)
- [GitHub Pages anycast IPs](https://docs.github.com/en/pages/configuring-a-custom-domain-for-your-github-pages-site/managing-a-custom-domain-for-your-github-pages-site#configuring-an-apex-domain) (current as of June 2026: `185.199.108–111.153`)
