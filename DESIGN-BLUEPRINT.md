# ComplianceKit — Final Design Blueprint v2
## Based on analysis of Vanta, Drata, Secureframe, Sprinto, Linear, Stripe

---

## CRITICAL DECISION: LIGHT MODE

Every real compliance SaaS (Vanta, Drata, Secureframe, Sprinto) uses a WHITE background.
Dark mode = developer tool / AI toy. Light mode = enterprise trust / professional.
ComplianceKit switches to LIGHT MODE effective immediately.

---

## COLOR SYSTEM

| Token | Hex | Use |
|-------|-----|-----|
| --bg | #ffffff | Page background |
| --bg-subtle | #f8f9fa | Alternating sections, card backgrounds |
| --bg-card | #ffffff | Cards (with border) |
| --border | #e5e7eb | All borders (gray-200) |
| --border-hover | #d1d5db | Hover state borders (gray-300) |
| --text | #111827 | Primary text (gray-900) |
| --text-secondary | #4b5563 | Body copy (gray-600) |
| --text-muted | #9ca3af | Captions, labels (gray-400) |
| --accent | #2563eb | Brand color — buttons and links only (blue-600) |
| --accent-hover | #1d4ed8 | Button hover (blue-700) |
| --accent-light | #eff6ff | Accent backgrounds (blue-50) |
| --green | #16a34a | Success states only (green-600) |
| --red | #dc2626 | Competitor prices in table (red-600) |

Rules:
- ZERO gradients anywhere
- Accent (#2563eb) used ONLY on primary buttons and key links
- Gray palette from Tailwind gray (not zinc, not slate)
- No colored backgrounds on sections — white or #f8f9fa only

---

## TYPOGRAPHY

Font: Inter (matches Vanta, Linear, most modern SaaS)

| Element | Size | Weight | Color | Line-height | Letter-spacing |
|---------|------|--------|-------|-------------|----------------|
| H1 | 48px | 700 | --text | 1.1 | -1.2px |
| H2 | 36px | 700 | --text | 1.15 | -0.8px |
| H3 | 20px | 600 | --text | 1.3 | -0.2px |
| Body | 16px | 400 | --text-secondary | 1.7 | 0 |
| Small | 14px | 400 | --text-muted | 1.6 | 0 |
| Overline | 13px | 600 | --accent | 1 | 0.5px uppercase |
| Nav links | 14px | 500 | --text-secondary | 1 | 0 |

Weights allowed: 400, 500, 600, 700 ONLY.

---

## SPACING (8pt strict)

| Use | Value |
|-----|-------|
| Nav height | 64px |
| Container max-width | 1120px |
| Section padding | 96px top/bottom |
| Between heading and content | 48px |
| Card padding | 32px |
| Grid gap | 24px |
| Between elements inside cards | 16px |
| Inline spacing | 8px |

---

## BORDER RADIUS

| Element | Radius |
|---------|--------|
| Cards | 12px |
| Buttons | 8px |
| Badges/pills | 100px |

Three values only. No 6px, 10px, 16px, 20px.

---

## BUTTONS

| Type | Styles |
|------|--------|
| Primary | bg: #2563eb, color: white, padding: 12px 24px, radius: 8px, weight: 600, size: 15px |
| Secondary | bg: white, border: 1px solid #e5e7eb, color: #111827, same padding/radius |
| Hover | Primary darkens to #1d4ed8. Secondary border darkens to #d1d5db. |

No gradients. No glow. No shine sweep. No shadows on hover.

---

## NAV

- Height: 64px
- Background: white
- Border-bottom: 1px solid #e5e7eb
- Logo: text only, no icon box (or simple one-color mark)
- Links: 14px, weight 500, color #4b5563, hover to #111827
- Sticky: yes, with background: rgba(255,255,255,0.95) + backdrop-filter:blur(8px)

---

## ANIMATIONS

ONLY allowed:
1. Subtle fade-in on scroll (opacity 0→1, translateY 6px→0, duration 0.4s)
2. Button hover transitions (background-color 0.15s)

NOTHING ELSE. No particles, no glow, no shimmer, no floating, no counting, no marquee.

---

## SECTIONS (Landing Page)

1. Nav
2. Hero — headline, subtitle, 1-2 buttons, framework tags
3. Logos/trust strip — "Compliance frameworks we support" with text badges
4. Problem — 3 columns, text only, numbered
5. Comparison table — vs Vanta/Drata/Secureframe (factual pricing)
6. Features — 2x3 grid, clean cards with number + title + description
7. How it works — 3 numbered steps, simple text
8. Pricing — 3 tier cards, white bg, blue border on featured
9. FAQ — 2 column grid
10. CTA — simple centered text + button
11. Footer — minimal, one row

Alternating backgrounds: white (#fff) and subtle gray (#f8f9fa) for visual separation.

---

## SECTIONS (Dashboard App)

Login page:
- White background (not dark)
- Centered card with shadow
- Logo at top
- Email + password fields
- Blue primary button
- Link to sign up / back to home

Dashboard:
- White sidebar with gray-50 background
- Gray border separating sidebar from content
- Content area: white background
- Cards: white bg, 1px gray border, 12px radius
- Stats: large numbers, small labels below
- Tables: clean rows, alternating gray-50 backgrounds
- NO colored sidebar, no gradients, no glow effects

---

## WHAT NOT TO DO

- No dark mode on either page
- No gradients (linear-gradient, conic-gradient, radial-gradient)
- No particles, canvas, or animated backgrounds
- No glow orbs or blur effects
- No shimmer/shine borders
- No emojis in UI
- No animated text
- No fake testimonials
- No "Trusted by 500+" without proof
- No translateY hover on cards
- No box-shadow on hover
- No font-weight above 700
- No more than 1 animation type
