# iOS Security-Scoped Bookmarks

## The Gotcha

When using `.fileImporter` to pick a folder and saving a security-scoped bookmark, the folder's security scope must stay active for as long as files within it are being accessed.

**Wrong pattern:**
```swift
// In scan():
folder.startAccessingSecurityScopedResource()
defer { folder.stopAccessingSecurityScopedResource() }
// scan files...

// In onChange: individual file URLs from contentsOfDirectory are NOT security-scoped
url.startAccessingSecurityScopedResource()  // This doesn't work — file URLs aren't bookmarked
```

**Right pattern:**
```swift
// Activate folder scope once (e.g., on init/restore), keep active for app lifetime
func activateFolderAccess() {
    guard let folder = folderURL, !folderAccessActive else { return }
    folder.startAccessingSecurityScopedResource()
    folderAccessActive = true
}

// Files within the folder are accessible as long as folder scope is active
// No per-file startAccessing needed
```

## Key Facts

- `contentsOfDirectory` returns regular URLs, not security-scoped ones
- The parent folder's scope grants access to all children
- `startAccessingSecurityScopedResource` is reference-counted — each `start` needs a `stop`
- For streaming playback (`AVAudioPlayerNode.scheduleFile`), the scope must persist — `defer { stop }` kills access before playback begins

## Context

Discovered in quies iOS app (Feb 2026). iCloud Drive folder picker + audio streaming.
