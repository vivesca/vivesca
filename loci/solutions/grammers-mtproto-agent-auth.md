# Telegram MTProto agent auth with grammers 0.7.0

**grammers version:** `grammers-client = "0.7.0"` (crates.io, released ~2023). This is the last published version as of Mar 2026 — no 0.8 exists yet. The TL schema baked in is from Telegram layer ~158.

**Context:** Building graphis — a Rust CLI for agent use that authenticates as a Telegram user and drives BotFather. Session: Mar 2026.

---

## DC Migration (PHONE_MIGRATE)

Terry's phone is on DC5. Any `auth.sendCode` call to the default DC returns:
```
rpc error 303: PHONE_MIGRATE caused by auth.sendCode (value: 5)
```

**grammers 0.7 does NOT handle this automatically** — neither `client.invoke()` nor the high-level `client.request_login_code()` retries on the correct DC. You must handle it manually.

**Fix:** catch the error, parse the DC number, reconnect via `InitParams::server_addr`:

```rust
use grammers_client::InitParams;

const DC_ADDRS: &[&str] = &[
    "",                    // DC0 unused
    "149.154.175.53:443",  // DC1
    "149.154.167.51:443",  // DC2
    "149.154.175.100:443", // DC3
    "149.154.167.91:443",  // DC4
    "91.108.56.130:443",   // DC5
];

fn parse_phone_migrate(err: &str) -> Option<usize> {
    let re = Regex::new(r"PHONE_MIGRATE.*\(value: (\d+)\)").ok()?;
    re.captures(err)?.get(1)?.as_str().parse().ok()
}

async fn connect_to_dc(dc: usize) -> Result<Client, ...> {
    let addr: SocketAddr = DC_ADDRS[dc].parse()?;
    Client::connect(Config {
        session: Session::load_file_or_create(&session_path)?,
        api_id, api_hash,
        params: InitParams {
            server_addr: Some(addr),
            ..Default::default()
        },
    }).await
}

// In auth-start:
let result = match client.invoke(&send_code_req).await {
    Ok(r) => r,
    Err(e) => {
        if let Some(dc) = parse_phone_migrate(&e.to_string()) {
            save_dc(dc)?;                          // persist for future runs
            client = connect_to_dc(dc).await?;
            client.invoke(&send_code_req).await?   // retry on correct DC
        } else {
            return Err(e.into());
        }
    }
};
```

**Critical:** save the DC number to a file (`dc.txt`) and read it in every subsequent `Client::connect` call. The session file does NOT encode which DC address to use — grammers ignores the DC on reconnect and always uses the default.

---

## LoginToken is opaque (`pub(crate)` fields)

`grammers_client::types::LoginToken` wraps the auth code response but its fields (`phone`, `phone_code_hash`) are `pub(crate)`. You cannot access them from outside the crate.

**Also:** `LoginToken` does NOT implement `Debug` or `Serialize` — the Debug repr extraction trick doesn't compile.

**Fix:** bypass `request_login_code` entirely, call raw TL `auth.SendCode` directly:

```rust
use grammers_tl_types as tl;

let result = client.invoke(&tl::functions::auth::SendCode {
    phone_number: phone.to_string(),
    api_id,
    api_hash,
    settings: tl::enums::CodeSettings::Settings(tl::types::CodeSettings {
        allow_flashcall: false,
        current_number: false,
        allow_app_hash: false,
        allow_missed_call: false,
        allow_firebase: false,
        unknown_number: false,   // field exists in 0.7 schema
        logout_tokens: None,
        token: None,
        app_sandbox: None,
    }),
}).await?;

let phone_code_hash = match result {
    tl::enums::auth::SentCode::Code(sent) => sent.phone_code_hash,
    tl::enums::auth::SentCode::Success(_) => { /* already authed */ return Ok(()); }
};
```

Note: the enum variant is `SentCode::Code` not `SentCode::SentCode` in grammers 0.7.

---

## Two-step auth state: what to persist

```rust
#[derive(Serialize, Deserialize)]
struct PendingAuth {
    phone: String,
    phone_code_hash: String,
    dc: Option<usize>,   // DC number if PHONE_MIGRATE occurred
}
```

Save to `~/.local/share/graphis/pending-auth.json` after step 1.
Save DC to `~/.local/share/graphis/dc.txt` for all future connections.
Save session (`client.session().save_to_file()`) after connecting to the migrated DC — this stores the MTProto auth key for that DC.

---

## Completing sign-in with raw TL

```rust
// auth-complete reads pending-auth.json, connects to saved DC, calls:
client.invoke(&tl::functions::auth::SignIn {
    phone_number: pending.phone.clone(),
    phone_code_hash: pending.phone_code_hash.clone(),
    phone_code: Some(code.to_string()),
    email_verification: None,
}).await?
```

If the account has 2FA, you get error `SESSION_PASSWORD_NEEDED`. Handle by:
1. Prompt for password (spawn_blocking + /dev/tty, since user is present)
2. Call `account.GetPassword` → get SRP params (`g`, `p`, `salt1`, `salt2`, `srp_b`, `srp_id`)
3. Compute SRP-2048-SHA512 (see `compute_srp` in `~/code/graphis/src/main.rs`)
4. Call `auth.CheckPassword` with `InputCheckPasswordSrp`

The algo variant name in grammers 0.7 TL types:
```rust
tl::enums::PasswordKdfAlgo::Sha256Sha256Pbkdf2Hmacsha512iter100000Sha256ModPow(algo)
```

---

## API credentials

Use Telegram Desktop's public credentials — avoids needing to create an app on my.telegram.org (which blocks headless browsers):

```
TELEGRAM_API_ID=2040
TELEGRAM_API_HASH=b18441a1ff607e10a989891a5462e627
```

These are embedded in the open-source Telegram Desktop binary. Standard workaround for personal MTProto clients.

---

## Library choice: grammers vs Telethon

| | grammers (Rust) | Telethon (Python) |
|---|---|---|
| DC migration | Manual — must handle PHONE_MIGRATE yourself | Automatic |
| Auth flow | LoginToken opaque, raw TL needed | High-level, 10 lines |
| Maturity | 0.7.0, slow development | Active, well-documented |
| Use when | Rust is a hard requirement | Default choice for MTProto work |

**If speed matters, use Telethon.** grammers costs significant debugging time on edge cases that Telethon handles transparently.

## Cargo.toml for this setup

```toml
[dependencies]
grammers-client = "0.7"
grammers-session = "0.7"
grammers-tl-types = "0.7"
tokio = { version = "1", features = ["full"] }
serde = { version = "1", features = ["derive"] }
serde_json = "1"
sha2 = "0.10"          # for SRP
num-bigint = "0.4"     # for SRP
num-traits = "0.2"     # for SRP
rand = "0.8"           # for SRP random a
regex = "1"
dirs = "5"
```

---

## Recovery

If any step breaks with transport errors:
```bash
rm ~/.local/share/graphis/session.bin ~/.local/share/graphis/pending-auth.json
echo "5" > ~/.local/share/graphis/dc.txt
graphis auth +85261872354
# give code
graphis auth-complete <CODE>
```
