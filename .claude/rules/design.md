# Design Rules

Source of truth: DESIGN-BLUEPRINT.md in project root.

## Hard Constraints
- LIGHT MODE ONLY. No dark mode. No dark backgrounds. Ever.
- ZERO gradients anywhere in the product.
- ONE animation type allowed: fade-in on scroll (opacity + translateY 6px, 0.4s).
- Font: Inter. Weights: 400, 500, 600, 700 only.
- 8pt spacing grid. No arbitrary values.
- Max container width: 1120px, centered.

## Card Pattern
- Background: white
- Border: 1px solid #e5e7eb
- Border-radius: 12px
- Padding: 32px
- No box-shadow on hover. No translateY on hover.

## Do NOT Add
- Particles, canvas, animated backgrounds
- Glow orbs, blur effects, shimmer borders
- Emojis in UI
- Animated text or number tickers
- Fake testimonials or unverifiable stats
- Colored section backgrounds (only white or #f8f9fa)

## When in Doubt
Look at Vanta.com or Linear.app. Match their restraint.
