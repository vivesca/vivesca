# Rust + Swift Interop on macOS — Research Notes

## Key Sources
- haim.dev/posts/2020-09-10-linking-swift-code-into-rust-app/: best practical build.rs walkthrough (display-switch project)
- shadowfacts.net/2023/rust-swift/: good 2023 guide with Linux coverage too
- github.com/Brendonovich/swift-rs: most actively maintained crate for calling Swift from Rust (~1k stars, used by Tauri)
- github.com/chinedufn/swift-bridge: bidirectional, more complete type bridging, book is sparse on distribution
- chinedufn.github.io/swift-bridge/: swift-bridge book (sparse, WIP)
- support.apple.com/en-us/106446: confirms Swift runtime ships with macOS 10.14.4+ (no Xcode needed on user machines)
- milen.me/writings/apple-link-magic-swift-runtime/: Apple linker magic and Swift runtime install names

## Fundamental Constraint
Swift does NOT support static linking of its standard library on Apple platforms (since Swift 5.0). You cannot produce a truly standalone binary. The Swift runtime lives at:
- `/usr/lib/swift/libswiftCore.dylib` on macOS 10.14.4+ (included in base OS, no Xcode needed)
- Target machines running macOS 10.14.4+ (Mojave) or later need nothing extra installed

## Approach 1: build.rs Invoking `swift build` (RECOMMENDED)

Pattern from haim.dev (display-switch project):

```rust
// build.rs
fn build_mac_ddc() {
    let profile = env::var("PROFILE").unwrap();
    let arch = env::var("CARGO_CFG_TARGET_ARCH").unwrap();

    Command::new("swift")
        .args(&["build", "-c", &profile])
        .current_dir("./mac_ddc")
        .status().unwrap();

    // Link the static .a output
    println!("cargo:rustc-link-search=native=./mac_ddc/.build/{}-apple-macosx/{}", arch, profile);
    println!("cargo:rustc-link-lib=static=mac_ddc");
    println!("cargo:rerun-if-changed=mac_ddc/src/*.swift");

    // Add Swift runtime search paths
    // Parse `swift -print-target-info` JSON to get runtimeLibraryPaths
    // Then: println!("cargo:rustc-link-search=native={}", path);
}
```

Swift side: functions must use `@_cdecl("funcName")` and C-compatible types. No structs, no generics — only scalars and raw pointers.

## Approach 2: swift-rs Crate

```toml
[build-dependencies]
swift-rs = "1"
[dependencies]
swift-rs = "1"
```

```rust
// build.rs
use swift_rs::SwiftLinker;
SwiftLinker::new("10.13")
    .with_package("MySwiftPackage", "./MySwiftPackage/")
    .link();
```

- Handles Swift runtime linking automatically
- Supports: SRString, SRArray<T>, SRObject<T>, SRObjectArray
- Used by Tauri for mobile Swift plugins
- Types limited to NSObject subclasses and scalars
- WARNING: `@_cdecl` + NSObject-compatible types only — no native Swift structs

## Approach 3: Swift Calls Rust (inverted, easier)

Build Rust as `crate-type = ["staticlib"]`, generate C header with `cbindgen`, import in Swift via bridging header. Swift executable links Rust. Easier because Swift executable naturally bundles Swift runtime.

## Approach 4: Two-Binary (Rust embeds Swift binary)

Use `include_bytes!()` to embed a pre-compiled Swift binary in the Rust binary. Extract to temp dir, execute via `std::process::Command`.

Caveats:
- Binary size doubles
- Requires write access to extract
- Need pre-built binary at Rust compile time (coordinate with build.rs)
- See: zameermanji.com/blog/2021/6/17/embedding-a-rust-binary-in-another-rust-binary/ for the cargo dependency ordering pattern

## cargo install — Does It Work?
NO, not for mixed Rust+Swift projects. `cargo install` downloads source and builds — the Swift source and `swiftc` must be present on the build machine. Since crates.io doesn't ship Swift source, `cargo install` is broken for mixed projects. Options:
- Homebrew formula (build from source tarball that includes Swift code)
- Pre-built binary releases on GitHub + Homebrew bottle or binary formula

## Homebrew Distribution

Two working patterns:

### Pattern A: Build-from-source formula
```ruby
class MyTool < Formula
  desc "..."
  homepage "..."
  url "https://github.com/user/repo/archive/refs/tags/v1.0.0.tar.gz"
  sha256 "..."

  depends_on "rust" => :build
  depends_on xcode: ["14.0", :build]  # Xcode required on BUILD machine, not target

  def install
    system "cargo", "build", "--release"
    bin.install "target/release/mytool"
  end
end
```

### Pattern B: Pre-built binary formula (bottled)
Build the binary in CI (GitHub Actions), upload as release asset, formula downloads pre-built binary. User machine needs NO Xcode, NO Rust — just macOS 10.14.4+.

```ruby
class MyTool < Formula
  url "https://github.com/user/repo/releases/download/v1.0.0/mytool-macos-arm64.tar.gz"
  # ...
  def install
    bin.install "mytool"
  end
end
```

Pattern B is strongly preferred for mixed Rust+Swift — avoids requiring Xcode on user's build machine.

## Real Examples
- display-switch (github.com/haimgel/display-switch): Rust + Swift DDC control. 3.3k stars. Pure Rust now (migrated away from Swift), but the haim.dev blog post documents the original mixed approach with build.rs.
- Tauri v2: Uses swift-rs for iOS Swift plugins. macOS plugin support still in progress (issue #12137).
- mozilla/rust-components-swift: Mozilla uses Rust static libs wrapped in Swift packages for Firefox iOS.

## Build Machine Requirements
- Xcode (or at minimum Xcode Command Line Tools) required on BUILD machine
- Xcode NOT required on user/target machine (Swift runtime in base macOS)
- `swiftc` and `swift build` must be in PATH during `cargo build`

## Common Gotchas
- `swift build` path in build.rs is relative — becomes relative to manifest dir, not workspace dir. Use `env!("CARGO_MANIFEST_DIR")` to make it absolute.
- Swift's build output path includes architecture: `.build/{arch}-apple-macosx/{profile}`. Must match Rust target arch.
- Universal (fat) binaries require building both arm64 + x86_64 then `lipo`-ing. build.rs needs extra logic.
- `@_cdecl` limitation: cannot bridge async Swift, throws, or generic types without manual wrapper code.
- swift-rs 1.0.7 minimum macOS: 10.13; but for Tauri compatibility must be 10.15+.
