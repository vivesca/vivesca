# Next.js Gotchas

## Next.js 16: middleware renamed to proxy.ts

Next.js 16 renamed `middleware.ts` → `proxy.ts`, and the export must be `export async function proxy()` (not `middleware`). The old name silently fails — session cookies don't refresh, auth breaks without error.

**Fix:** Use `proxy.ts` at project root with `export async function proxy()`.

## Supabase SSR: empty env vars throw at build time

`createBrowserClient('')` and `createServerClient('', '')` throw immediately, which breaks SSR prerender (including `/_not-found`, `404`, etc.).

**Fix:** Use `|| 'https://placeholder.supabase.co'` and `|| 'placeholder-anon-key'` fallbacks in `lib/supabase/client.ts` and `lib/supabase/server.ts`. These values are never used at runtime (real env vars are set in Vercel), but prevent the build-time throw.

Also: move `createClient()` calls inside `useEffect`/`useRef` in client components — never at module top level, which runs during SSR.

## Supabase SSR: chunked cookies not reflected in UI

After OAuth callback, `@supabase/ssr` stores the session as chunked cookies (`sb-*-auth-token.0` / `.1`). The cookies are set correctly server-side, but `createBrowserClient` may not reflect the signed-in user in React UI despite `document.cookie` showing the tokens.

**Root cause:** `createBrowserClient` self-initializes on mount — but async initialization and singleton state can race or return stale data. The UI shows "Sign in" even though the user is authenticated.

**Fix:** Don't self-initialize in the client component. Instead, read the user server-side in the layout (using `createServerClient` + `supabase.auth.getUser()`), pass it as `initialUser` prop to `AuthButton`, and use `onAuthStateChange` only for subsequent client-side changes (sign-out, token refresh).

```tsx
// layout.tsx (server component) — make it async
const supabase = await createClient()  // lib/supabase/server.ts
const { data: { user } } = await supabase.auth.getUser()
// ...
<AuthButton initialUser={user} />

// AuthButton.tsx
export function AuthButton({ initialUser }: { initialUser?: User | null }) {
  const [user, setUser] = useState<User | null>(initialUser ?? null)
  useEffect(() => {
    // onAuthStateChange only — no getUser() needed
    const { data: { subscription } } = supabase.auth.onAuthStateChange((_, session) => {
      setUser(session?.user ?? null)
    })
    return () => subscription.unsubscribe()
  }, [])
}
```

**Confirmed working:** profile row created in Supabase DB, JWT present in browser cookies — it was purely a UI read issue, not an auth failure.

## Supabase SSR: `createBrowserClient` hangs when NEXT_PUBLIC env vars are placeholders

If `NEXT_PUBLIC_SUPABASE_URL` isn't bundled at Vercel build time, `createBrowserClient` falls back to `https://placeholder.supabase.co`. Calls like `supabase.auth.getUser()` or `supabase.from('profiles')` make real network requests to that placeholder URL — they never resolve (no rejection, just hang), silently blocking any logic gated on them.

**Symptoms:** React state that depends on `getUser()` never updates; `authChecked` stays false; deliberation never starts; Supabase client DB queries hang indefinitely. No console error.

**Fix pattern — apply to every page that needs auth:**
1. Make `page.tsx` an `async` server component (no `'use client'`)
2. Read user server-side via `createServerClient`
3. Pass as `initialUser?: User | null` prop to the client component
4. Client component initialises: `useState(initialUser ?? null)` and `useState(initialUser !== undefined)`
5. Skip browser `getUser()` when `initialUser !== undefined`
6. Replace any `supabase.from(...)` calls inside `execute()` with API routes (`/api/runs/limit` already returns `tier`)

**Pattern (run page):**
```tsx
// app/run/page.tsx — server component, no 'use client'
import { createClient } from '@/lib/supabase/server'
import { Suspense } from 'react'
import { RunContent } from './RunContent'

export default async function RunPage() {
  const supabase = await createClient()
  const { data: { user } } = await supabase.auth.getUser()
  return (
    <Suspense fallback={<div>Loading...</div>}>
      <RunContent initialUser={user} />
    </Suspense>
  )
}

// app/run/RunContent.tsx — 'use client'
export function RunContent({ initialUser }: { initialUser?: User | null }) {
  const [user, setUser] = useState<User | null>(initialUser ?? null)
  const [authChecked, setAuthChecked] = useState(initialUser !== undefined)

  useEffect(() => {
    if (initialUser !== undefined) return  // skip — already have user from server
    const supabase = createClient()
    supabase.auth.getUser()
      .then(({ data }) => { setUser(data.user); setAuthChecked(true) })
      .catch(() => setAuthChecked(true))
  }, [])
  // ...
}
```

**Also:** don't call `supabase.from(...)` in async functions inside client components. Route all DB reads through server API endpoints instead.

## Vercel env vars: trailing `\n` corrupts everything silently

When setting Vercel env vars via copy-paste (or `vercel env add` with stdin), the value may include a trailing newline that gets stored literally. This corrupts:
- Supabase URL → `createBrowserClient` hangs (DNS fails with `\n` in URL)
- Stripe key → `StripeConnectionError` (malformed Authorization header)
- URLs in Stripe checkout → "Not a valid URL"

**Diagnosis:** `vercel env pull .env.local` then check: `grep '\\n"' .env.local` — any match means the var is corrupted.

**Fix (Python):**
```python
import re, subprocess

with open('.env.local') as f:
    content = f.read()

for line in content.split('\n'):
    m = re.match(r'^(\w+)="(.+)"$', line)
    if m and '\\n' in m.group(2):
        name = m.group(1)
        value = m.group(2).replace('\\n', '').strip()
        subprocess.run(['vercel', 'env', 'rm', name, 'production', '-y'], check=True)
        # IMPORTANT: pass value WITHOUT trailing newline — 'input=value' not 'input=value + "\n"'
        subprocess.run(['vercel', 'env', 'add', name, 'production'], input=value, text=True, check=True)
```

**Root cause of all consilium.sh scrub test failures (Mar 7 2026):** every single production env var had `\n` from initial setup via copy-paste. Caused Supabase browser client to hang (→ authChecked never true), Stripe SDK to throw StripeConnectionError, and URLs to be malformed.
