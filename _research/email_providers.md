# Email Provider Comparison for Te Pā Trust (hello@te-pa.org)

**Prepared:** June 2026  
**Context:** Small kaupapa Māori charitable trust, Port Chalmers, Dunedin, NZ. 1 mailbox needed now (hello@te-pa.org), up to 3 eventually. Working-class budget, privacy-conscious, domain hosted on Vercel.

---

## Summary Comparison Table

| | Cloudflare Routing + Gmail | Fastmail Individual | Google Workspace Starter |
|---|---|---|---|
| **Monthly cost (NZD)** | Free (NZ$0) | ~NZ$10.80/mo (USD $6) | NZ$12.60/mo (flexible) or NZ$10.50/mo (annual) |
| **Mailboxes included** | 0 (forwarding only — uses your existing Gmail) | 1 (Individual plan) | 1 (per licence; add more at same rate) |
| **Storage** | Gmail's 15 GB (shared with Drive/Photos) | 60 GB (50 GB mail + 10 GB files) | 30 GB pooled |
| **Custom-domain send** | Partial — requires workaround (Gmail SMTP "send as", or third-party relay) | Full — native SMTP send from hello@te-pa.org | Full — native Gmail with your domain |
| **Calendar/contacts** | Google Calendar (personal) | Yes — full Fastmail calendar + contacts | Yes — Google Calendar + all Workspace apps |
| **Privacy jurisdiction** | Google (USA, GDPR-adjacent) | Australian company, servers in USA (Philadelphia/New Jersey) | Google (USA) |
| **Setup complexity (1–5)** | 4 — free but fiddly send-as config | 2 — clean guided setup | 3 — straightforward but involves Google account |
| **"Via" warning on sent mail** | Yes, if using Gmail SMTP "send as" freebie workaround | No | No |
| **NZ-friendly billing** | N/A | Yes — NZD billing available at checkout | Yes — NZD billing available |
| **Deliverability (2026)** | Moderate — depends heavily on your Gmail reputation + relay config | Very good — established IP reputation, DKIM/SPF handled | Excellent — Google infrastructure |

---

## Recommendation

**For Te Pā right now: Fastmail Individual plan (NZ$10.80/month, or ~NZ$9/month on annual billing).**

It is the cleanest path for a small trust that needs a professional `hello@te-pa.org` address without Google dependency. Full send-and-receive on your custom domain works out of the box — no "sent via" caveats, no Gmail fiddling. Fastmail is an Australian company with strong privacy values, accepts NZD, and offers a 30-day free trial with no credit card required. When you need a second or third mailbox for Jeffrey or Rebecca McCall, the **Fastmail Duo plan (NZ$18/month for 2 users)** or **Family plan (NZ$25.20/month for up to 6 users)** scale cheaply — far cheaper than adding extra Google Workspace licences at NZ$12.60 each. The only meaningful trade-off is that Fastmail's servers are physically in the USA (Philadelphia/New Jersey), which the trust should be aware of, but the company operates under Australian privacy law and has no ad model — your email is not the product.

Google Workspace is a fine choice if the trustees want the full Google Suite (Docs, Sheets, Meet) and are already comfortable in that ecosystem; at NZ$10.50/user/month on an annual plan it is comparable in cost but adds per-user charges quickly as the board grows, and keeps Te Pā's data firmly inside a US surveillance-economy company. Cloudflare Email Routing is genuinely free but should only be considered as a transitional stopgap — the inability to send cleanly from `hello@te-pa.org` without a separate workaround (Gmail SMTP "send as" adds a visible "via" header in many clients) makes it unsuitable for professional trust communications.

---

## Option 1: Cloudflare Email Routing + Gmail "Send As"

### What it is
Cloudflare Email Routing is a free DNS-level forwarding service. Incoming mail to `hello@te-pa.org` is forwarded to any destination inbox (e.g. Robert's personal Gmail). **It is receive-only** — Cloudflare provides no SMTP server for outbound mail. To reply from `hello@te-pa.org`, you must configure Gmail's "Send mail as" feature using either Gmail's own SMTP (free, but adds a "via gmail.com" header) or a paid third-party relay like Resend or Mailgun (adds cost and complexity).

### Pricing
- **Cloudflare Email Routing:** Free ([developers.cloudflare.com/email-routing](https://developers.cloudflare.com/email-routing/))
- **Gmail SMTP "send as" workaround:** Free, but recipient sees `sent via gmail.com` in some clients
- **If using a relay (e.g. Resend):** Resend free tier (3,000 emails/month) — adequate for a small trust at NZ$0, but adds another service to manage

### What's included
- Unlimited email forwarding rules (forward hello@ to any inbox)
- Catch-all rules
- No mailbox, no storage, no calendar

### Setup complexity: 4/5
The forwarding itself is simple (Cloudflare auto-adds MX records). The complication is outbound sending:
- Gmail "send as" via Gmail SMTP: moderate setup (Settings → Accounts → Add another email address), but produces "via gmail.com" disclaimer visible in Gmail, Outlook, etc.
- Gmail "send as" via external SMTP relay: requires a paid relay service account + SMTP credentials entered into Gmail settings
- This is a configuration that can break silently and confuses non-technical users

### DNS Records (Cloudflare-managed — set automatically when you enable Email Routing in Cloudflare dashboard)
Cloudflare auto-configures these when you enable Email Routing on a domain already using Cloudflare DNS. If te-pa.org is not already on Cloudflare DNS, you would either move DNS to Cloudflare or manually add:

```
Type    Name    Value                           Priority
MX      @       route1.mx.cloudflare.net        84
MX      @       route2.mx.cloudflare.net        14
MX      @       route3.mx.cloudflare.net        18
TXT     @       v=spf1 include:_spf.mx.cloudflare.net ~all
```

For the Gmail "send as" workaround, you would also need to add Google's SPF alongside Cloudflare's:
```
TXT     @       v=spf1 include:_spf.mx.cloudflare.net include:_spf.google.com ~all
TXT     _dmarc  v=DMARC1; p=none; rua=mailto:hello@te-pa.org
```

### Pros for Te Pā
- Completely free
- Zero ongoing commitment
- Good as a transitional setup while you evaluate paid options
- Works with any DNS setup including Vercel

### Cons for Te Pā
- **No outbound send from custom domain without a workaround** — "via" banner is unprofessional for press enquiries and partner emails
- Send-as in Gmail is a fiddly multi-step setup that breaks if Gmail's app password expires
- No dedicated mailbox — all trust mail mixes into Robert's personal Gmail
- No calendar sharing or contact management under the trust identity
- Not suitable as a long-term solution for a public-facing charitable trust

### Deliverability (2026)
Forwarding alone has moderate deliverability — the outbound reputation depends entirely on Gmail's or your relay's infrastructure. SPF + DKIM alignment is hard to achieve cleanly with forwarding.

### Privacy posture
Data passes through Cloudflare (US) and lands in Google Gmail (US). Subject to US jurisdiction. No ad-targeting, but Google has a commercial interest in metadata.

### Works with Vercel DNS?
Yes. Vercel supports MX and TXT records directly in its DNS UI ([vercel.com/docs/domains/managing-dns-records](https://vercel.com/docs/domains/managing-dns-records)). Alternatively, if te-pa.org already uses Cloudflare DNS (common with Vercel projects), Email Routing is a one-click enable.

### Migration / lock-in
Zero lock-in — just DNS changes. Switching to a paid provider later requires updating MX/SPF/DKIM records and potentially re-importing any saved emails.

---

## Option 2: Fastmail Individual Plan ← Recommended

### What it is
Fastmail is an Australian-founded, privacy-focused email provider (owned by Fastmail Pty Ltd, Melbourne). It offers a full hosted mailbox with native custom domain send/receive, calendar, contacts, and IMAP/SMTP access. No ads, no data selling.

### Pricing
- **Individual plan:** USD $6/month (~NZ$10.80) monthly, or USD $5/month (~NZ$9.00) on annual billing (~NZ$108/year)
- **Billing in NZD:** Yes — Fastmail added NZD billing in 2024; select NZ at checkout
- **30-day free trial:** Yes, no credit card required
- Source: [fastmail.com/pricing](https://www.fastmail.com/pricing/) | [fastmail.help/hc/en-us/articles/8033939068815](https://www.fastmail.help/hc/en-us/articles/8033939068815-2024-pricing-and-plan-updates)

Scaling options when more trustees need mailboxes:
| Plan | Users | Monthly (USD) | Est. NZD/mo |
|---|---|---|---|
| Individual | 1 | $6 | ~$10.80 |
| Duo | 2 | $10 | ~$18.00 |
| Family | Up to 6 | $14 | ~$25.20 |
| Business Standard | Per user | $5/user (annual) | ~$9/user |

The **Family plan at ~NZ$25.20/month** covers all three trustees (Robert, Jeffrey, Rebecca) with private inboxes, shared calendars, and a shared address book — highly cost-effective.

### What's included (Individual)
- 1 private mailbox
- 60 GB total storage (50 GB mail/calendar/contacts + 10 GB files)
- Custom domain send/receive (unlimited aliases like `hello@te-pa.org`, `info@te-pa.org`, etc.)
- Masked Email (privacy feature — generate unique addresses)
- Calendar + contacts (CalDAV/CardDAV, works with iPhone, Android, macOS)
- IMAP/SMTP access — works with Apple Mail, Outlook, Thunderbird
- 24/7 human support
- Scheduled Send, Snooze, offline mode

### Setup complexity: 2/5
Fastmail has a guided domain setup wizard that walks you through each DNS record. If te-pa.org DNS is managed through Vercel, you copy-paste five records into Vercel's DNS UI. No technical expertise required.

### DNS Records for Fastmail + te-pa.org

Replace `te-pa.org` with the actual domain. These are the exact records from [fastmail.help/hc/en-us/articles/360060591153](https://www.fastmail.help/hc/en-us/articles/360060591153-Setting-up-your-domain-MX-records):

#### MX Records (mail routing — required)
```
Type    Name    Value                           Priority
MX      @       in1-smtp.messagingengine.com    10
MX      @       in2-smtp.messagingengine.com    20
```

#### SPF Record (authorises Fastmail to send on your behalf — required)
```
Type    Name    Value
TXT     @       v=spf1 include:spf.messagingengine.com ?all
```

#### DKIM Records (cryptographic signing — strongly recommended, prevents spam flags)
```
Type    Name                            Value
CNAME   fm1._domainkey.te-pa.org        fm1.te-pa.org.dkim.fmhosted.com
CNAME   fm2._domainkey.te-pa.org        fm2.te-pa.org.dkim.fmhosted.com
CNAME   fm3._domainkey.te-pa.org        fm3.te-pa.org.dkim.fmhosted.com
```

#### DMARC Record (policy record — recommended, tells receivers what to do with unauthenticated mail)
```
Type    Name            Value
TXT     _dmarc          v=DMARC1; p=none;
```
Start with `p=none` (monitoring only). Once you've confirmed mail is flowing correctly, tighten to `p=quarantine` or `p=reject`.

#### Summary: 8 DNS records total
| # | Type | Name | Value | Priority |
|---|---|---|---|---|
| 1 | MX | @ | in1-smtp.messagingengine.com | 10 |
| 2 | MX | @ | in2-smtp.messagingengine.com | 20 |
| 3 | TXT | @ | v=spf1 include:spf.messagingengine.com ?all | — |
| 4 | CNAME | fm1._domainkey | fm1.te-pa.org.dkim.fmhosted.com | — |
| 5 | CNAME | fm2._domainkey | fm2.te-pa.org.dkim.fmhosted.com | — |
| 6 | CNAME | fm3._domainkey | fm3.te-pa.org.dkim.fmhosted.com | — |
| 7 | TXT | _dmarc | v=DMARC1; p=none; | — |

**Note on Vercel DNS:** If te-pa.org is using Vercel's nameservers, go to Vercel Dashboard → Domains → te-pa.org → Enable DNS Records, then add each record above. Vercel fully supports MX, TXT, and CNAME records ([vercel.com/docs/domains/managing-dns-records](https://vercel.com/docs/domains/managing-dns-records)).

### Pros for Te Pā
- **No "via" warnings** — sends cleanly from `hello@te-pa.org`
- Australian company, aligned cultural values around privacy and independence from US Big Tech
- Privacy posture: no ads, no data-selling, IMAP/SMTP open protocols mean you can switch providers without losing data
- Scales affordably: Duo (2 users) or Family (up to 6) plans cover the full board at flat rates
- NZD billing available — no currency conversion surprises
- 30-day free trial to test before committing
- Works with Robert's existing Gmail workflow via IMAP import or Apple Mail

### Cons for Te Pā
- **Servers are in the USA** (Philadelphia, PA) — Fastmail is an Australian company subject to Australian law, but the physical servers are in the US, which is a consideration for data sovereignty advocates ([fastmail.help/hc/en-us/articles/1500000280221](https://www.fastmail.help/hc/en-us/articles/1500000280221-How-Fastmail-provides-a-secure-service))
- No Google Docs / Sheets / Drive integration — the trust would use a separate tool for collaborative documents
- Slightly less familiar interface than Gmail for trustees used to Gmail

### Deliverability (2026)
Excellent. Fastmail has a strong 25-year deliverability reputation. DKIM signing is automatic once DNS CNAMEs are in place. Major providers (Google, Microsoft, Yahoo) reliably deliver Fastmail-originated mail to inbox.

### Privacy posture
- Company: Fastmail Pty Ltd, Melbourne, Australia — subject to Australian Privacy Act
- Servers: Philadelphia PA and New Jersey, USA — physically in US jurisdiction
- No advertising model, no data resale
- Encrypted at rest and in transit
- Does not scan email content for advertising

### Migration / lock-in
Low lock-in. Uses standard IMAP/SMTP — export all email via any IMAP client at any time. DNS changes take 1–48 hours to propagate when switching providers. Fastmail's domain-based setup means if you later switch to Google Workspace, it's just a DNS update.

---

## Option 3: Google Workspace Business Starter

### What it is
Google Workspace Business Starter is the paid version of Gmail with a custom domain. It gives you a full `@te-pa.org` Gmail inbox — the familiar Gmail interface, Google Calendar, Google Drive, Meet, Docs, Sheets, etc. — without any "via gmail.com" header.

### Pricing
- **NZD $10.50/user/month** on an annual commitment (billed monthly or yearly)
- **NZD $12.60/user/month** on a flexible (month-to-month) plan
- Source: [knowledge.workspace.google.com/admin/billing/compare-flexible-and-annual-fixed-term-payment-plans](https://knowledge.workspace.google.com/admin/billing/compare-flexible-and-annual-fixed-term-payment-plans)

Cost comparison as Te Pā adds trustees:
| Users | Annual plan (NZD/mo) | Flexible plan (NZD/mo) |
|---|---|---|
| 1 (hello@ only) | $10.50 | $12.60 |
| 2 trustees | $21.00 | $25.20 |
| 3 trustees | $31.50 | $37.80 |

Compare this to Fastmail Family (up to 6 users) at ~NZ$25.20/month flat.

### What's included (Business Starter)
- 1 Gmail mailbox per licence (custom domain, ad-free)
- 30 GB pooled storage per user (shared across Gmail + Drive)
- Google Calendar, Google Meet (100 participants), Google Chat
- Google Docs, Sheets, Slides, Forms, Sites
- Gemini AI assistant (basic access in Gmail)
- Google Drive for desktop
- 24/7 phone/email support
- Enterprise-grade spam/phishing filtering (99.9%+ block rate)

### Setup complexity: 3/5
Google provides a setup wizard and Vercel has a built-in DNS preset for Google Workspace. You add 6 MX records, an SPF TXT record, and a domain verification TXT record. DKIM is enabled from the Google Admin console after DNS propagation. Slightly more steps than Fastmail but well-documented.

### DNS Records for Google Workspace + te-pa.org
From [support.google.com/a/answer/140034](https://support.google.com/a/answer/140034):

#### Domain verification (temporary — Google provides a unique value)
```
Type    Name    Value
TXT     @       google-site-verification=XXXXX (unique per account — provided during setup)
```

#### MX Records
```
Type    Name    Value                           Priority
MX      @       ASPMX.L.GOOGLE.COM              1
MX      @       ALT1.ASPMX.L.GOOGLE.COM         5
MX      @       ALT2.ASPMX.L.GOOGLE.COM         5
MX      @       ALT3.ASPMX.L.GOOGLE.COM         10
MX      @       ALT4.ASPMX.L.GOOGLE.COM         10
```

#### SPF Record
```
Type    Name    Value
TXT     @       v=spf1 include:_spf.google.com ~all
```

#### DKIM Record (generated in Google Admin Console → Apps → Gmail → Authenticate email)
```
Type    Name                    Value
TXT     google._domainkey       v=DKIM1; k=rsa; p=<key generated in admin console>
```

#### DMARC Record
```
Type    Name    Value
TXT     _dmarc  v=DMARC1; p=none; rua=mailto:hello@te-pa.org
```

**Vercel DNS presets:** Vercel has a built-in Google Workspace preset in its DNS UI — adding the MX records can be done in one click. ([vercel.com/kb/guide/why-has-email-stopped-working](https://vercel.com/kb/guide/why-has-email-stopped-working))

### Pros for Te Pā
- Familiar Gmail interface — Robert already uses Gmail; zero learning curve
- Excellent deliverability (Google's own infrastructure)
- Full Google Workspace suite included (Docs, Sheets, Drive, Meet) — useful for board document collaboration
- Best spam/phishing protection available (99.9%+ filter rate)
- Well-supported in NZ (NZD billing, NZ resellers like [jrc.nz](https://jrc.nz/services-google))

### Cons for Te Pā
- **Cost scales quickly**: 3 trustees = NZ$31.50/month annual vs Fastmail Family at ~NZ$25.20/month
- **Deeply US-based**: Google LLC, servers in USA, subject to US data requests
- **Lock-in**: Google-specific formats (Docs, Sheets) create workflow dependency; migrating away later is more complex
- **Ethical alignment**: A kaupapa Māori trust may prefer not to be dependent on a US surveillance-economy corporation whose primary business is advertising
- 30 GB pooled storage per user is less than Fastmail's 60 GB individual storage

### Deliverability (2026)
Best-in-class. Google's infrastructure has the highest inbox placement rates of any provider. Major ISPs and webmail providers (including Gmail itself) treat Google Workspace-originated mail with the highest trust.

### Privacy posture
- Google LLC, USA — subject to US CLOUD Act and NSA surveillance programs
- Google Admin console provides transparency and audit logs, but data is processed by Google's US infrastructure
- No email scanning for advertising in Workspace (unlike free Gmail), but Google's general data practices apply
- GDPR-compliant for EU users; NZ Privacy Act 2020 does not regulate Google directly

### Migration / lock-in
Higher lock-in than Fastmail. Google Docs/Sheets create format dependencies. Email itself is exportable via Google Takeout (MBOX format). Switching away from Google Workspace later requires exporting email, migrating documents, and retraining trustees.

---

## Step-by-Step DNS Setup for Recommended Option: Fastmail

These steps assume te-pa.org DNS is managed through **Vercel** (Vercel nameservers active).

### Step 1: Sign up for Fastmail
1. Go to [fastmail.com/pricing](https://www.fastmail.com/pricing/) and select the **Individual** plan
2. Start 30-day free trial — no credit card needed
3. Choose NZD as your currency during signup
4. Create your Fastmail account (e.g. using `robert@fastmail.com` or a temporary address — you'll replace this with your custom domain)

### Step 2: Add te-pa.org to Fastmail
1. In Fastmail, go to **Settings → Domains → Add domain**
2. Enter `te-pa.org`
3. Fastmail will display the DNS records you need to add (same as the table above)

### Step 3: Add DNS records in Vercel
1. Log into [vercel.com/dashboard](https://vercel.com/dashboard)
2. Click **Domains** in the sidebar
3. Click on **te-pa.org** → **Advanced Settings** → **Enable DNS Records**
4. Add each record below using the **Add Record** button:

| Step | Type | Name | Value | Priority |
|---|---|---|---|---|
| 3a | MX | @ | in1-smtp.messagingengine.com | 10 |
| 3b | MX | @ | in2-smtp.messagingengine.com | 20 |
| 3c | TXT | @ | v=spf1 include:spf.messagingengine.com ?all | — |
| 3d | CNAME | fm1._domainkey | fm1.te-pa.org.dkim.fmhosted.com | — |
| 3e | CNAME | fm2._domainkey | fm2.te-pa.org.dkim.fmhosted.com | — |
| 3f | CNAME | fm3._domainkey | fm3.te-pa.org.dkim.fmhosted.com | — |
| 3g | TXT | _dmarc | v=DMARC1; p=none; | — |

> **Note:** For CNAME records in Vercel, use only the subdomain part as the Name (e.g. `fm1._domainkey`, not `fm1._domainkey.te-pa.org`).

### Step 4: Wait for propagation (up to 48 hours, usually under 1 hour)
You can check propagation at [dnschecker.org](https://dnschecker.org) — search for `te-pa.org` MX records.

### Step 5: Verify in Fastmail
1. Return to Fastmail **Settings → Domains → te-pa.org**
2. Click **Check DNS records** — Fastmail will show green ticks when all records are correctly propagated

### Step 6: Create hello@te-pa.org
1. In Fastmail, go to **Settings → Aliases → Add alias**
2. Enter `hello` under `te-pa.org`
3. This is now your primary address — you can also add `info@te-pa.org`, `robert@te-pa.org` etc. as aliases at no extra cost

### Step 7: Optional — set up on iPhone/Mac
- Fastmail supports native iOS Mail and macOS Mail via IMAP
- IMAP server: `imap.fastmail.com` port 993 (SSL)
- SMTP server: `smtp.fastmail.com` port 465 (SSL) or 587 (STARTTLS)
- Or use Fastmail's own iOS/Android app

---

## Notes

### On domain hosting: te-pa.org + Vercel
Vercel is a website deployment platform, not a DNS registrar. Whether Vercel manages DNS depends on whether te-pa.org's nameservers point to Vercel (`ns1.vercel-dns.com`). If they do, you add DNS records in Vercel's dashboard as above. If the domain was bought via a separate registrar (e.g. Namecheap, Cloudflare, iwantmyname.co.nz), you add the DNS records there instead — the process is identical, just a different dashboard.

### On upgrading to multiple mailboxes
When Jeffrey and Rebecca need their own mailboxes, Fastmail's **Family plan (~NZ$25.20/month)** covers up to 6 users with individual inboxes, shared calendar, and shared address book — ideal for a trust board. That's less than the cost of 2 Google Workspace licences on the flexible plan.

### On deliverability authentication
All three options support DKIM + SPF + DMARC. In 2024, Google and Yahoo made DKIM + DMARC mandatory for bulk senders. For a low-volume trust like Te Pā, the standards are less strictly enforced, but having all three records in place is best practice and prevents mail going to spam.

### Sources
- Cloudflare Email Routing docs: https://developers.cloudflare.com/email-routing/
- Fastmail pricing: https://www.fastmail.com/pricing/
- Fastmail 2024 pricing updates: https://www.fastmail.help/hc/en-us/articles/8033939068815-2024-pricing-and-plan-updates
- Fastmail DNS setup guide: https://www.fastmail.help/hc/en-us/articles/360060591153-Setting-up-your-domain-MX-records
- Fastmail server locations: https://www.fastmail.help/hc/en-us/articles/1500000280221-How-Fastmail-provides-a-secure-service
- Fastmail privacy policy: https://www.fastmail.com/about/privacy/
- Google Workspace NZD pricing: https://knowledge.workspace.google.com/admin/billing/compare-flexible-and-annual-fixed-term-payment-plans
- Google Workspace NZ business page: https://workspace.google.com/intl/en-GB_nz/business/
- Google Workspace DNS setup: https://support.google.com/a/answer/140034
- Vercel DNS records management: https://vercel.com/docs/domains/managing-dns-records
- Vercel email DNS guide: https://vercel.com/kb/guide/why-has-email-stopped-working
