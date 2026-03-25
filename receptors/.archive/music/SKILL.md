---
name: music
description: Control Spotify on Sonos via sonoscli. "play music", "play lofi", "pause", "skip", "volume", "what's playing"
user_invocable: true
---

# Music (Spotify + Sonos)

Control Spotify playback on Sonos speakers via `sonoscli`. Default room: Sonos Move.

## Trigger

Use when:
- User says "play music", "play [genre/artist/song]", "pause", "skip", "volume", "what's playing"
- User shares a Spotify link or URI
- User says "music", "sonos", "spotify"

## Quick Reference

```bash
# Playback
sonos play                        # resume
sonos pause                       # pause
sonos stop                        # stop
sonos next                        # skip track
sonos prev                        # previous track

# Status
sonos status                      # what's playing now
sonos status --format json        # machine-readable

# Volume
sonos volume get                  # current volume
sonos volume set 30               # set 0-100

# Play Spotify content
sonos open "https://open.spotify.com/..."          # share link
sonos open spotify:track:6NmXV4o6bmp704aPGyTVVG    # Spotify URI
sonos enqueue "https://open.spotify.com/..."       # add to queue without playing

# Search (requires SMAPI auth)
sonos smapi search --service "Spotify" --category tracks "chet baker"
sonos smapi search --service "Spotify" --category playlists "lofi sleep"
sonos smapi search --service "Spotify" --category albums "kind of blue"
sonos smapi search --service "Spotify" --category artists "miles davis"

# Favorites & Queue
sonos favorites list              # Sonos favorites
sonos favorites open --index 1    # play a favorite
sonos queue list                  # current queue
sonos queue clear                 # clear queue

# Grouping (multi-room)
sonos group status                # show groups
sonos group party                 # all speakers, same music
sonos group dissolve              # ungroup all

# Scenes
sonos scene save chill            # save current grouping + volumes
sonos scene apply chill           # restore scene
sonos scene list                  # list saved scenes
```

## Workflow

1. **Direct Spotify link/URI** — `sonos open <link>`
2. **Search request** — `sonos smapi search --service "Spotify" --category <type> "<query>"`, then `sonos open <uri>` from results
3. **Simple controls** — map to play/pause/next/prev/volume/status

## SMAPI Auth

If SMAPI search returns "service not authenticated":
```bash
sonos auth smapi begin --service "Spotify"
# User opens the URL and links account
sonos auth smapi complete --service "Spotify" --code <CODE> --wait 5m
```

This is one-time setup. Credentials persist in `~/.config/sonoscli/`.

## Error Handling

- **If speaker not found**: Run `sonos discover --timeout 10s`. Speaker must be on same LAN.
- **If SMAPI auth expired**: Re-run auth flow above.
- **If Spotify link doesn't play**: Ensure Spotify is linked in the Sonos app. Try `sonos open` with the canonical `spotify:` URI format.
- **If volume too loud**: Default to 25-30 for background music. Always confirm before setting above 50.

## Config

- **Binary**: `/opt/homebrew/bin/sonos` (v0.1.1)
- **Config**: `~/.config/sonoscli/config.json`
- **Default room**: Sonos Move (set via `sonos config set defaultRoom "Sonos Move"`)
- **SMAPI categories**: tracks, playlists, albums, artists
