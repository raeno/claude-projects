# Zarianka Pots — Website TODO

## Project
Static landing page for Julia Yakutova's pottery studio "Zarianka Pots" (zarianka.ru).
Stack: Astro + Clay theme. Logo: robin bird SVG.
Social: vk.ru/zarianka_pots

## Design Decisions
- Base theme: Clay (advitiyan-png/clay-astro-theme)
- Color palette:
  - Background: #F5F0E8 (warm cream)
  - Text: #3D2B1F (deep warm brown)
  - Primary accent: #C37A67 (terracotta)
  - Robin/CTA accent: #D4703A (burnt orange)
  - Nature accent: #7A8C6E (sage)
  - Dark mode: bg #1E1610, text #E8DDD4
- Fonts: Cormorant Garamond (added), EB Garamond (body), League Spartan (nav/headings)
- Language: Russian (lang="ru")
- Aesthetic: organic, earthy, artisan

## Completed ✓

### Foundation
- [x] Scaffold Astro project with Clay theme
- [x] Install npm dependencies
- [x] Build passes (16 pages)

### Styles & Layout
- [x] Update color palette (terracotta/cream/sage)
- [x] Add Cormorant Garamond to Google Fonts
- [x] Update dark mode colors to warm earthy dark
- [x] Change lang="ru" in Layout.astro

### Components
- [x] Header: Russian nav (Главная, О мастере, Работы, Новости, Под заказ, Контакт)
- [x] Header: Robin bird SVG logo (inline SVG)
- [x] Header: VK social link with icon
- [x] Footer: Julia's name and VK link
- [x] Contact template: Russian form labels
- [x] Work template: Use CSS var for link color

### Content (all in Russian)
- [x] pages/index.md — Зарянка Поттери homepage
- [x] pages/bio.md — About Julia Yakutova
- [x] pages/work.md — Work section
- [x] pages/news.md — News section
- [x] pages/sold.md — Под заказ (custom orders)
- [x] pages/contact.md — Contact with VK link
- [x] work/mugs.md — Кружки
- [x] work/bowls.md — Пиалы и миски
- [x] work/vases.md — Вазы и горшочки
- [x] news/welcome.md — Зарянка открылась
- [x] news/spring-collection.md — Весенняя коллекция
- [x] news/fair-may.md — Ярмарка в мае
- [x] sold/custom-mug-set.md — Именные кружки
- [x] sold/plant-pots.md — Кашпо под заказ

### Assets
- [x] favicon.svg — Robin bird SVG

## Deployment
- [x] Makefile with build/deploy targets (rsync → nginx via my_server SSH alias)
- [ ] Configure nginx vhost for zarianka.ru on my_server
- [ ] Configure domain DNS → 95.216.27.23

## Pending / Nice-to-Have

### Content to confirm with Julia
- [ ] Real bio text and backstory
- [ ] Real location / city
- [ ] Actual product photos (replace /img/clay-* placeholder images)
- [ ] Real pricing if wanted
- [ ] Workshop / event dates
- [ ] Email address for contact form

### Polish
- [ ] Custom OG image for social sharing
- [ ] pages/elements.md — remove or keep (currently hidden from nav)
- [ ] contact/thanks.astro — Russify the thank you page
- [ ] Add Google Analytics / Yandex Metrika snippet
- [ ] Smooth scroll to sections if needed

### Deployment
- [ ] Configure domain zarianka.ru
- [ ] Deploy to Netlify / Vercel / static host
  - For Netlify: enable form submissions (data-netlify="true" already set)
- [ ] Configure _redirects if needed

## Commands
```bash
npm run dev    # dev server at localhost:4321
npm run build  # production build in /dist
npm run preview # preview built site
```
