# Project Guidelines — zarianka.ru

## Overview
Static portfolio/landing site for **Julia Yakutova's pottery studio "Zarianka Pots"** (zarianka.ru). Built with Astro 5 + Clay theme. All UI and content is in **Russian** (`lang="ru"`).

## Build and Test
```bash
npm install        # Install dependencies
npm run dev        # Dev server at localhost:4321
npm run build      # Production build to dist/
npm run preview    # Preview production build
```
No test framework is configured. Validate changes by running `npm run build` — it will catch type errors and broken references.

## Architecture
- **Static SSG** — no SSR, no client-side framework. Only vanilla JS for nav toggle and dark mode.
- **Client Router** — Astro View Transitions (`<ClientRouter />`) for SPA-like navigation. Scripts must listen for `astro:page-load` and `astro:after-swap` events instead of `DOMContentLoaded`.
- **Template dispatch** — `templateKey` frontmatter field routes pages to templates in `src/templates/` via conditionals in [src/pages/[...slug].astro](src/pages/%5B...slug%5D.astro). Key values: `contact-page`, `work-page`, `news-page`, `exhibitions-page`, `bio-page`, `index-page`.
- **Homepage curation** — Items appear on homepage when frontmatter has `pagetype: [main]`. Sort order is controlled by `number` field.
- **4 content collections** (`news`, `work`, `sold`, `pages`) all share one permissive schema in [src/content/config.ts](src/content/config.ts).
- **Images** are static files in `public/img/`, referenced as absolute paths (e.g. `/img/pottery/children/photo.jpg`).

## Code Style
- **CSS**: No preprocessor. Uses PostCSS with `@import` aggregation, compiled CSS custom properties (`preserve: false`), and `color()` function. Design tokens live in [src/styles/vars.css](src/styles/vars.css). Component-scoped styles use Astro `<style>` blocks.
- **Color palette**: `--color-primary: #C37A67` (terracotta), `--color-base: #3D2B1F`, `--color-bg: #F5F0E8`, `--color-accent: #D4703A`, `--color-sage: #7A8C6E`.
- **Dark mode**: `data-theme="dark"` on `<html>`, persisted in `localStorage`. Override colors defined in `[data-theme='dark']` selector in vars.css.
- **Fonts**: League Spartan / Futura (nav/headings, small-caps), EB Garamond (body), Cormorant Garamond (decorative).
- **TypeScript**: `astro/tsconfigs/strict` base. No path aliases.

## Project Conventions
- **Content files** use YAML frontmatter. Required fields vary, but `title`, `templateKey`, `date`, and `thumbnail` are standard. See [src/content/work/children.md](src/content/work/children.md) for a representative example.
- **Navigation** is hardcoded in [src/components/Header.astro](src/components/Header.astro) — update it directly when adding pages.
- **Prev/next navigation** for collection items is computed in the `[slug].astro` page files, sorted by date DESC.
- **PostCard** component alternates layout: every 3rd card is full-width (`post-card-large`).

## Integration Points
- **Netlify**: Contact form uses `data-netlify="true"`. Site is deployed to Netlify.
- **Decap CMS**: Config exists at `public/admin/config.yml.disabled` — intentionally disabled.
- **Sitemap**: `@astrojs/sitemap` integration generates sitemap automatically.
