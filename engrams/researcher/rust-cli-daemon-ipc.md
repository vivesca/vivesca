# Rust CLI Daemon IPC — Research Notes (Feb 2026)

## Consensus Pattern: Unix Socket + Tokio

The dominant real-world pattern for Rust CLI audio daemons is:
- **Transport:** Unix domain socket at a fixed path (e.g. `/tmp/appname.sock` or `$XDG_RUNTIME_DIR/appname.sock`)
- **Wire format:** Line-delimited JSON or bincode-serialized structs (not gRPC for simple tools)
- **Async runtime:** Tokio with `tokio::net::UnixListener` / `UnixStream`
- **Single binary:** Daemon and client in one binary. On invocation: try `UnixStream::connect`. If success → send command + exit. If `ConnectionRefused` → start daemon mode (bind socket, spawn audio thread, loop).

## Real-World Examples Found

| Tool | Language | IPC | Notes |
|------|----------|-----|-------|
| MPD | C | TCP + Unix socket | Line-based text protocol (`setvol 75\n` → `OK\n`) |
| cmus | C | Unix socket (cmus-remote) | Same line-based pattern |
| termusic | Rust | gRPC (tonic/prost) over Unix socket | Two binaries: termusic + termusic-server |
| music-player (tsirysndr) | Rust | gRPC + GraphQL | Single binary that auto-detects role |
| vfs (kostDev) | Rust | Unix socket + bincode | `/tmp/vfs.sock`, two binaries |
| PipeWire | C | Custom binary protocol | `$XDG_RUNTIME_DIR/pipewire-0`, fd passing |

## Key Crates

### Daemonization
- **`daemonize`** (crates.io) — Classic Unix double-fork, pid file, redirect stdio. Simple.
- **`daemonizr`** — Extended: pid file locking + `AlreadyRunning` detection + `.search()` to get existing daemon's PID. Better for "am I already running?" check.
- **`fork`** crate — Low-level `fork()` + `setsid()` if you want manual control.
- **Do NOT use `daemonize` on macOS in 2025+** — macOS deprecated `fork()` after `exec()` in sandboxed contexts. Simpler: just `std::process::Command::new(std::env::current_exe()).spawn()` + detach parent.

### IPC Transport
- **`tokio::net::UnixListener`** (std tokio) — Zero-dependency, just tokio. The minimal choice.
- **`interprocess`** (v2.4.0, Feb 2026, actively maintained, 694K monthly downloads) — Cross-platform abstraction: Unix socket on Unix, named pipe on Windows. Good if cross-platform matters.
- **`tokio-unix-ipc`** (mitsuhiko) — Minimal tokio wrapper, supports fd passing + serde/bincode serialization. Good for Rust-to-Rust typed IPC.
- **`hyperlocal`** — Unix socket as HTTP transport (hyper). Heavier but gives you HTTP semantics (routes, status codes).
- **`ryankurte/rust-daemon`** — Higher-level typed request/response over Unix socket with JSON codec. Older but shows the pattern cleanly.

### Audio
- **`rodio`** — `Sink::set_volume(f32)`, `Sink::pause()`, `Sink::stop()`, `Sink::play()`. Sink lives in daemon thread; commands sent via `tokio::sync::mpsc` channel.
- **`cpal`** — Lower level, rodio builds on it.

## The Minimal Proven Pattern

```
mytool start         → detect no socket → daemonize → bind socket → audio loop
mytool stop          → connect socket → send "stop" → daemon exits
mytool volume 0.5    → connect socket → send "volume 0.5"
mytool               → (no subcommand) → same as start
```

**Wire protocol:** newline-terminated strings is simplest. JSON if you want structured.

**Single-binary auto-detect pattern:**
```rust
// On invocation, try to connect first
match UnixStream::connect(&socket_path).await {
    Ok(stream) => { /* client mode: send command */ }
    Err(e) if e.kind() == ErrorKind::ConnectionRefused => {
        // No daemon running — clean stale socket, become daemon
        let _ = fs::remove_file(&socket_path);
        become_daemon().await;  // bind socket + spawn audio
    }
    Err(e) => { /* real error */ }
}
```

**Daemon-mode socket cleanup:** Always `fs::remove_file(socket_path)` on startup (stale from crash) and on SIGTERM/SIGINT.

## Alternatives Considered and Why Rejected for Simple Audio Tool

- **gRPC (tonic):** Used by termusic but adds build-time protobuf compilation, heavier deps. Overkill for 3-4 commands.
- **D-Bus:** Linux-specific (macOS support fragile). Heavy runtime dep.
- **HTTP (hyperlocal):** HTTP over Unix socket is elegant for REST-style APIs with many endpoints. Overhead for start/stop/volume.
- **Named pipes / FIFO:** One-directional, awkward for request-response.
- **Shared memory:** Fastest but complex synchronisation. Not needed for control commands.

## Socket Path Convention

- `/tmp/<appname>.sock` — simple, survives reboots (but `/tmp` can be cleared)
- `$XDG_RUNTIME_DIR/<appname>.sock` — Linux standard for user-session daemons (PipeWire, PulseAudio use this)
- macOS: `$TMPDIR/<appname>.sock` — `$XDG_RUNTIME_DIR` not set on macOS; use `dirs::runtime_dir()` with fallback to `/tmp`

## Sources
- MPD protocol: https://mpd.readthedocs.io/en/stable/protocol.html
- interprocess crate: https://lib.rs/crates/interprocess
- tokio-unix-ipc: https://github.com/mitsuhiko/tokio-unix-ipc
- rust-daemon pattern: https://github.com/ryankurte/rust-daemon
- vfs example: https://github.com/kostDev/vfs
- daemonizr: https://docs.rs/daemonizr/latest/daemonizr/
- daemonize blog: https://tuttlem.github.io/2024/11/16/building-a-daemon-using-rust.html
- IPC ping-pong comparison: https://3tilley.github.io/posts/simple-ipc-ping-pong/
