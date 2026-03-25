# Blink Shell Theme Format

## Correct format

Plain JS, no wrapper, no comments inside arrays. Match Dracula exactly:

```js
t.prefs_.set('background-color', '#0D0F10');
t.prefs_.set('foreground-color', '#E2E4E6');
t.prefs_.set('cursor-color', '#20C5C0');
t.prefs_.set('color-palette-overrides', ['#...','#...',...]);  // 16 entries, flat array
```

## What breaks it

- **IIFE wrapper** (`(function(t){...})(term_)`) — `term_` is not defined in Blink's eval context. `t` is provided as a bare variable.
- **GitHub blob URL** (`github.com/.../blob/...`) — serves HTML, not JS. Blink rejects with "must be .js".
- **Comments inside array** — safe in JS but avoid for parity with official themes.

## Installation URL

Must use raw content URL:
```
https://raw.githubusercontent.com/<user>/<repo>/main/themes/<name>.js
```

Not the blob page URL.

## Reference

Official themes: https://github.com/blinksh/themes
Abyssos theme: https://raw.githubusercontent.com/terry-li-hm/abyssos/main/themes/abyssos.js
