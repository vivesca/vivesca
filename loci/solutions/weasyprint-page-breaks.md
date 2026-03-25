# WeasyPrint Page Break Control

## Problem

`page-break-inside: avoid` on container divs (e.g., `.project`) causes large blank gaps when the entire block doesn't fit on the current page — pushes the whole section to the next page.

## Fix

Remove `page-break-inside: avoid` from the container. Instead, use `page-break-after: avoid` on the title/header element inside it. This keeps the title with its first content line but allows the block to split mid-content.

```css
/* Bad — causes large gaps */
.project {
    page-break-inside: avoid;
}

/* Good — title stays with content, block can split */
.project-title {
    page-break-after: avoid;
}
```

## Context

Discovered during CBA CV generation (Feb 2026). Four project blocks in CNCBI section — `page-break-inside: avoid` on each caused 40% blank space on page 1 when the third project didn't fit.
