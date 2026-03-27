# Prompt: Landing Page QA

## Task
Review `public/index.html` for visual bugs, broken links, and cross-browser issues.

## Checklist
1. All CTA buttons link to `/app.html`
2. Pricing cards show correct amounts ($49.99, $99.99, $149.99) with strikethrough originals
3. Comparison table renders cleanly at all viewport widths
4. FAQ sections expand/collapse properly
5. Nav is sticky with blur backdrop
6. Fade-in animations trigger on scroll
7. No horizontal overflow at any breakpoint
8. Footer links are functional
9. Mobile hamburger menu works (if implemented)
10. Firefox: check @property CSS — shimmer may degrade

## Validator Agent Instructions
After builder fixes issues, spawn a read-only validator agent:
- Validator reads index.html and lists any remaining issues
- Validator cannot modify files
- Validator checks: accessibility (alt tags, contrast), semantic HTML, performance (no huge inline assets)
