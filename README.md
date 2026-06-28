# Become an AI Warrior

A single-page course site for **The Kiwi Dialectic** — a working-class course in AI literacy, ideological clarity, and systems thinking. Built in a Te Papa × Soviet-constructivist aesthetic.

> The most dangerous tool is a trained mind.

## What's inside

- **`index.html`** — full production site (single file, no build step)
- **`assets/logo.svg`** — K + koru spiral mark
- **`assets/hero-poster.svg`** — constructivist hero poster
- **`assets/social-kit/`** — eight free download-ready posters for **Twitter/X, LinkedIn, Instagram** in correct platform sizes, plus a bundled `.zip`
- **`make_kit.py`** — Python/Pillow generator (regenerate or remix the kit)
- **`.github/workflows/deploy.yml`** — auto-deploys to GitHub Pages on every push to `main`

## Sections

1. Hero — AI Warrior call-out
2. Manifesto — Freire, Gramsci, the case for the course
3. Six course modules (linked to Kiwi Dialectic lessons)
4. Six thinkers — Gramsci, Kropotkin, Graeber, Freire, Deleuze, Bakunin
5. Five pillars + $7/month pricing card
6. Tools — Perplexity, AI building, Substack, arts as pedagogy, systems thinking
7. **Social Kit** — free PNG downloads + suggested captions for X, LinkedIn, Instagram
8. About Robert
9. CTA banner

## Social Media Kit

Posters in **eight platform sizes**, all free to download once you've completed the course:

| Platform | Size | File |
| --- | --- | --- |
| Twitter / X · Post | 1600 × 900 | `tw-post-1600x900.png` |
| Twitter / X · Header | 1500 × 500 | `tw-header-1500x500.png` |
| LinkedIn · Post | 1200 × 627 | `li-post-1200x627.png` |
| LinkedIn · Banner | 1584 × 396 | `li-banner-1584x396.png` |
| Instagram · Square | 1080 × 1080 | `ig-square-1080x1080.png` |
| Instagram · Portrait | 1080 × 1350 | `ig-portrait-1080x1350.png` |
| Instagram · Story / Reel | 1080 × 1920 | `ig-story-1080x1920.png` |
| Profile · Avatar | 1000 × 1000 | `avatar-1000x1000.png` |

Bundled as `assets/social-kit/ai-warrior-social-kit.zip`. The "Suggested Posts" block on the site provides copy-to-clipboard captions for each platform.

To regenerate or remix the kit:

```bash
python make_kit.py
cd assets/social-kit && zip -q ai-warrior-social-kit.zip *.png
```

## Deploy

1. Push to `main`
2. GitHub → **Settings → Pages → Source → GitHub Actions**
3. The included `deploy.yml` workflow handles the rest

Live URL: `https://<your-username>.github.io/ai-warrior/`

## Local preview

```bash
python -m http.server 8000
# then open http://localhost:8000
```

## Credits

By Robert McCall, Ōtepoti / Dunedin, Aotearoa.
Course at [kiwidialectic.com](https://kiwidialectic.com).
