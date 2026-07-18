# Psic. Luis Alberto Morales Pérez — Mexicali

One-page marketing site for psychologist Luis Alberto Morales Pérez
(Mexicali, B.C.), built in the same style as the previous Netlify builds
(unreelads, happybikemalvern): static HTML/CSS/JS, zero build step, deploy
straight to Netlify.

Content sourced from his public [Psychology Today profile](https://www.psychologytoday.com/mx/psicologos/luis-alberto-morales-perez-mexicali-bn/1697881).

## Features

- Fully responsive single-page site, Spanish-first with an **ES/EN toggle** (persisted in localStorage)
- **Netlify Forms** contact/booking form with honeypot spam protection and a `/gracias.html` success page
- **Floating WhatsApp button** + click-to-call links
- Sticky header, mobile burger menu, smooth scrolling, IntersectionObserver reveal animations
- FAQ accordion, process steps, specialties cards, trust strip, CTA band
- Google Maps embed (Mexicali)
- SEO: meta description, Open Graph, Twitter cards, canonical, **JSON-LD `Psychologist` schema**
- Crisis-line disclaimer in the footer (Línea de la Vida 800 911 2000)
- Custom 404 page, security headers via `netlify.toml`
- All artwork is hand-crafted inline SVG — no external image dependencies, instant load

## Images (open-source models)

The site ships with SVG illustrations so it works out of the box. To swap in
photorealistic images generated with an **open-source model (FLUX.1-schnell /
SDXL)**, run on any machine with internet access:

```bash
python3 scripts/generate_images.py                 # hosted FLUX via Pollinations, no key
python3 scripts/generate_images.py --backend a1111 # local Stable Diffusion WebUI
```

Then point the `<img>` tags in `index.html` at the generated `.jpg` files.
(This sandboxed build environment blocks outbound requests to image APIs,
which is why generation is a post-step here.)

## Deploy

`netlify.toml` at the repo root publishes `sites/psic-luis-morales`.
Connect the repo/branch in Netlify or drag-and-drop this folder — no build
command needed. After the first deploy, enable form notifications in
Netlify → Forms so inquiries reach the client's email.

## Before going live — verify with the client

- **Phone**: 800 283 2791 ext. 33 is the number listed on Psychology Today
  (their tracked line). Replace with his direct phone/WhatsApp number —
  update the `tel:` links and the `wa.me/…` link in `index.html`.
- **Exact office address** (currently only "Mexicali, C.P. 21376") and the map embed.
- Session fees, hours, and any credentials/photo he wants displayed.
- Final domain: update `og:url` / `canonical` (currently `psicluismorales.netlify.app`).
