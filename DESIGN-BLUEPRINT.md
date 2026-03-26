# ComplianceKit — Design Blueprint
## Anti-Vibe-Coded Rebuild Spec

---

## 1. COLOR SYSTEM — No Gradients

**Rule: Single flat brand color + neutral palette. Zero gradients on text or backgrounds.**

| Token | Value | Use |
|-------|-------|-----|
| --bg | #09090b | Page background (zinc-950) |
| --bg-card | #111113 | Card background |
| --border | #1e1e24 | All borders — ONE value |
| --text | #ededef | Primary text |
| --text-muted | #71717a | Secondary text (zinc-500) |
| --accent | #2563eb | ONLY brand color — buttons, links, highlights |
| --accent-hover | #1d4ed8 | Hover state for accent |
| --green | #22c55e | Success/positive only |
| --red | #ef4444 | Danger/negative only |

**Rules:**
- NO gradients anywhere (no linear-gradient, no conic-gradient, no radial-gradient on UI elements)
- NO glow orbs, no shimmer borders, no particle canvas
- Accent color used sparingly — only on CTA buttons and key highlights
- Cards use solid bg + single border color, never glassmorphism

---

## 2. TYPOGRAPHY — Strict Scale

**Font:** Inter (keep it — it's industry standard, fine when used with proper hierarchy)

| Element | Size | Weight | Line-height | Letter-spacing |
|---------|------|--------|-------------|----------------|
| H1 (hero) | 48px | 700 | 1.1 | -1.5px |
| H2 (section) | 32px | 700 | 1.2 | -0.8px |
| H3 (card title) | 18px | 600 | 1.3 | -0.3px |
| Body | 15px | 400 | 1.7 | 0 |
| Small/caption | 13px | 500 | 1.5 | 0 |
| Overline/tag | 11px | 700 | 1 | 1.5px uppercase |

**Rules:**
- Max 3 font weights used: 400, 600, 700
- No 800 or 900 weight (too heavy = screams AI)
- No animated gradient text
- No text shadows

---

## 3. SPACING — 8pt Grid (Strict)

Every margin, padding, and gap must be a multiple of 8.

| Token | Value | Use |
|-------|-------|-----|
| --space-1 | 8px | Icon-to-text gap |
| --space-2 | 16px | Inside components |
| --space-3 | 24px | Between related elements |
| --space-4 | 32px | Card padding |
| --space-6 | 48px | Between groups |
| --space-8 | 64px | Between sub-sections |
| --space-12 | 96px | Between major sections |
| --space-16 | 128px | Section padding (top/bottom) |

**Rules:**
- Section padding: 128px top, 128px bottom (not 100px — 100 breaks the 8pt grid)
- Card padding: 32px
- Max content width: 1088px (divisible by 8)
- Never use odd values (5px, 14px, 28px, etc.)

---

## 4. BORDER RADIUS — One Value

**Rule: Pick ONE radius and use it everywhere.**

| Element | Radius |
|---------|--------|
| Cards | 12px |
| Buttons | 8px |
| Inputs | 8px |
| Badges/pills | 100px (only pills) |

That's it. No 6px, no 10px, no 16px, no 20px. Only 8px, 12px, and 100px.

---

## 5. ANIMATIONS — Almost None

**Rule: Max 2 animations on the entire page.**

Allowed:
- Blur-fade-in on scroll (sections appear) — subtle, 0.5s, ease
- Button hover: background-color change, 0.15s transition

NOT allowed:
- Shimmer borders
- Particle canvas
- Floating glow orbs
- Card translateY on hover
- Animated gradient text
- Marquee scrolling
- Number ticker counting up
- Shine sweep on buttons
- Conic-gradient rotation
- Border beam effects

**Every hover:** Only `border-color` or `background-color` change. No transform. No translateY. No scale.

---

## 6. SOCIAL PROOF — Honest Only

**Rules:**
- NO fake testimonials with fake names
- NO "Trusted by 500+ teams" without proof
- NO fake company logos
- NO fake YC batch references

Allowed alternatives:
- Framework badges (SOC 2, HIPAA, GDPR — these are real)
- Use case scenarios (honest descriptions of who this is for)
- "Early access" or "Join the waitlist" messaging
- Transparent pricing comparison vs named competitors (factual)

---

## 7. EMOJIS — Removed

**Rule: Zero emojis in headings, navigation, or card titles.**

Allowed: Framework-specific icons if they're actual SVG icons, not emoji.
For now: Use simple text or single-character symbols (✓, →, ·) only.

---

## 8. SECTIONS — Lean

**Only these sections, in this order:**
1. Nav (fixed, solid bg, no blur/glass)
2. Hero (headline + subtitle + 1 CTA button + framework list)
3. Problem (3 pain points — text only, no cards)
4. Comparison table (vs Vanta/Drata — factual)
5. Features (6 items, simple grid, no bento)
6. How it works (3 steps, inline, no cards)
7. Pricing (3 tiers, clean, no strikethrough gimmick)
8. FAQ (accordion or simple grid)
9. CTA (one line + one button)
10. Footer

**Removed:**
- Product mockup (fake dashboard screenshots = vibe-coded tell)
- Marquee
- Number ticker stats
- Testimonials section
- Glow orbs / particles / dot pattern

---

## 9. BUTTONS — Two Styles Only

| Type | Style |
|------|-------|
| Primary | Solid accent bg (#2563eb), white text, 8px radius |
| Ghost | Transparent bg, border, muted text |

No shine sweep. No glow on hover. No gradient. Just:
```css
.btn:hover { background: #1d4ed8; }
```

---

## 10. PAGE BACKGROUND

- Solid #09090b. Nothing else.
- No dot pattern
- No particle canvas
- No glow orbs
- No radial gradient masks

Clean. Quiet. Professional.
