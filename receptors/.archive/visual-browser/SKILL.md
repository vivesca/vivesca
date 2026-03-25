---
name: visual-browser
description: Browser automation via Gemini Flash vision. Fallback when agent-browser fails on visual UIs.
user_invocable: false
---

# Visual Browser Skill

This skill allows the agent to interact with the web using **Computer Vision** and spatial reasoning via the `browser-use` library and Gemini 3 Flash. Unlike text-only scrapers, it can "see" the page, handle complex layouts, and interact with elements based on their visual appearance.

## Usage

Invoke this skill when you need to perform a task that requires visual understanding of a website (e.g., clicking complex buttons, navigating non-standard UIs, or summarizing visual content).

```bash
uv run /Users/terry/skills/visual-browser/browse.py "Find the latest AI news on TechCrunch and summarize the top 3 stories."
```

## Capabilities

- **Visual Navigation:** Identifies elements by their visual features, not just HTML selectors.
- **Dynamic Interaction:** Handles JS-heavy sites, modals, and complex state changes.
- **Multimodal Reasoning:** Uses Gemini 3 Flash's vision capabilities to plan and execute browser actions.

## Configuration

- Requires `GOOGLE_API_KEY` in the environment.
- Uses `playwright` for browser control.
- Automatically installs dependencies via `uv run`.

## Best Practices

- Use for UI-heavy sites where standard scrapers fail.
- Provide clear, step-by-step or outcome-oriented tasks.
- For simple text retrieval, consider `WebSearch` or `WebFetch` instead to save tokens.
