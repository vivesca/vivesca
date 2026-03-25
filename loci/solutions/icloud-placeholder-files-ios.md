# iCloud Drive Placeholder Files on iOS

## Problem

`FileManager.contentsOfDirectory` with `.skipsHiddenFiles` silently hides iCloud files that haven't been downloaded to the device. These appear as hidden placeholder files named `.filename.ext.icloud`.

## Fix

1. Scan **without** `.skipsHiddenFiles`
2. Detect placeholders: `name.hasPrefix(".") && name.hasSuffix(".icloud")`
3. Derive real filename: strip leading `.` and trailing `.icloud`
4. Trigger download: `FileManager.startDownloadingUbiquitousItem(at:)`
5. Deduplicate — during sync, both placeholder and real file may coexist

## Example

```swift
if name.hasPrefix(".") && name.hasSuffix(".icloud") {
    let stripped = String(name.dropFirst().dropLast(7))
    try? FileManager.default.startDownloadingUbiquitousItem(at: url)
    let realURL = folder.appendingPathComponent(stripped)
    // use realURL
}
```

## Context

Hit in quies-ios (Feb 2026). Dark ambient tracks from iCloud Drive were invisible because the scan filtered them as hidden files.
