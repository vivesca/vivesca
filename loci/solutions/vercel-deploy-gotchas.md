# Vercel Deployment Gotchas

## git push doesn't auto-deploy

`git push origin main` to GitHub does NOT guarantee Vercel auto-deploys. The Doumei project doesn't have GitHub integration (or webhook is broken).

**Always verify after push:**
```bash
pnpm vercel ls  # check if new deployment appeared
```

**If no new deployment, force it:**
```bash
pnpm vercel --prod  # deploys from local working directory
```

## iOS PWA service worker update

Even with `skipWaiting()` and full cache clear in the activate handler, iOS Safari PWA serves stale content until the app is fully closed and reopened.

**User fix:** Close PWA from app switcher → reopen.
**Nuclear option:** Settings → Safari → Advanced → Website Data → delete domain → reopen.

The SW update flow is: fetch new sw.js → install → skipWaiting → activate (clears caches) → claim clients. But on iOS the "fetch new sw.js" step only happens on navigation, and the PWA may serve the cached page before checking.

## iOS PWA status bar meta is install-time only

`apple-mobile-web-app-status-bar-style` is read when the user adds to home screen. Changing it in code has NO effect on already-installed PWAs.

**Fix:** Delete the PWA from home screen → re-add from Safari.

Values: `default` (white bar), `black` (black bar), `black-translucent` (transparent — page background shows through, content extends under status bar, use with `env(safe-area-inset-top)` padding).

## Safari may ignore dual theme-color meta tags

Two `<meta name="theme-color">` with `media="(prefers-color-scheme: ...)"` attributes may not work in all Safari versions.

**Workaround:** Single meta tag + JS listener:
```js
const meta = document.querySelector('meta[name="theme-color"]');
const mq = window.matchMedia('(prefers-color-scheme: dark)');
const sync = () => { meta.content = mq.matches ? '#0C0C0C' : '#F3F3EE'; };
sync();
mq.addEventListener('change', sync);
```
