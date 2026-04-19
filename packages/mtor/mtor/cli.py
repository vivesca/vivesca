"""mtor CLI — local-mode dispatch for AI coding agents."""

from __future__ import annotations

import json
import secrets
import sys
from pathlib import Path
from typing import Annotated

from cyclopts import App, Parameter

from mtor import __version__
from mtor.auth import (
    OAuth2Config,
    TokenStore,
    authorization_code_flow,
    build_authorize_url,
    client_credentials_flow,
    generate_code_challenge,
    generate_code_verifier,
)
from mtor.config import MtorConfig
from mtor.dispatch import ROUTE_TO_PROVIDER, detect_task_type
from mtor.log import filter_reflections, filter_stalls, read_log, summary_stats
from mtor.worker import log_result, run_task

app = App(
    name="mtor", help="Architect-implementer dispatch for AI coding agents.", version=__version__
)


@app.command
def run(
    prompt: str,
    provider: Annotated[str, Parameter(["--provider", "-p"])] = "",
    config_file: Annotated[str | None, Parameter(["--config", "-c"])] = None,
) -> None:
    config = MtorConfig.load(Path(config_file) if config_file else None)

    # Determine task type and provider
    explicit_provider = bool(provider)
    task_type = detect_task_type(prompt)

    if explicit_provider:
        provider_name = provider
    else:
        provider_name = ROUTE_TO_PROVIDER.get(task_type, config.default_provider)
        # Fall back to default_provider if the routed provider isn't configured
        if provider_name not in config.providers:
            provider_name = config.default_provider

    if not provider_name or provider_name not in config.providers:
        available = ", ".join(config.providers.keys()) or "none configured"
        print(
            json.dumps(
                {
                    "ok": False,
                    "error": f"Unknown provider '{provider_name}'. Available: {available}",
                }
            )
        )
        sys.exit(1)

    routed_provider = provider_name
    if not explicit_provider:
        print(f"[mtor] Auto-routed to {routed_provider} for {task_type} task", file=sys.stderr)

    prov = config.providers[provider_name]
    print(f"[mtor] running on {prov.name} ({prov.model})...", file=sys.stderr)
    result = run_task(prompt, prov, config)
    log_result(result, config.log_file)
    output = {
        "ok": result.exit_code == 0,
        "provider": result.provider,
        "duration": result.duration_seconds,
        "files_created": result.files_created,
        "stall": result.stall.stall_type,
        "task_type": task_type,
        "routed_provider": routed_provider,
    }
    if result.reflection:
        output["reflection"] = result.reflection
    if result.stall.is_stalled:
        output["stall_detail"] = result.stall.detail
    print(json.dumps(output))
    sys.exit(result.exit_code)


@app.command
def log(
    count: Annotated[int, Parameter(["--count", "-n"])] = 20,
    stalls_only: Annotated[bool, Parameter(["--stalls"])] = False,
    reflections_only: Annotated[bool, Parameter(["--reflections"])] = False,
    stats: Annotated[bool, Parameter(["--stats"])] = False,
    config_file: Annotated[str | None, Parameter(["--config", "-c"])] = None,
) -> None:
    config = MtorConfig.load(Path(config_file) if config_file else None)
    entries = read_log(config.log_file, limit=count)
    if stats:
        print(json.dumps(summary_stats(entries), indent=2))
        return
    if stalls_only:
        entries = filter_stalls(entries)
    elif reflections_only:
        entries = filter_reflections(entries)
    for entry in entries:
        status = (
            "OK"
            if entry.succeeded
            else f"FAIL(stall={entry.stall})"
            if entry.is_stalled
            else "FAIL"
        )
        print(
            f"{entry.timestamp}  {entry.provider:<10}  {status:<20}  {entry.duration}s  files={entry.files_created}"
        )


@app.command
def doctor(config_file: Annotated[str | None, Parameter(["--config", "-c"])] = None) -> None:
    config = MtorConfig.load(Path(config_file) if config_file else None)
    checks = [
        {"provider": n, "model": p.model, "harness": p.harness, "has_key": p.api_key is not None}
        for n, p in config.providers.items()
    ]
    print(
        json.dumps(
            {
                "ok": all(c["has_key"] for c in checks),
                "coaching_file": str(config.coaching_file) if config.coaching_file else None,
                "providers": checks,
            },
            indent=2,
        )
    )


# ---------------------------------------------------------------------------
# Auth sub-commands
# ---------------------------------------------------------------------------

auth_app = App(name="auth", help="OAuth2 authentication for providers.")
app.command(auth_app)


@auth_app.command
def login(
    provider: Annotated[str, Parameter(["--provider", "-p"])],
    client_id: Annotated[str, Parameter(["--client-id"])],
    token_url: Annotated[str, Parameter(["--token-url"])],
    authorize_url: Annotated[str | None, Parameter(["--authorize-url"])] = None,
    client_secret: Annotated[str | None, Parameter(["--client-secret"])] = None,
    scopes: Annotated[str, Parameter(["--scopes"])] = "",
    redirect_port: Annotated[int, Parameter(["--redirect-port"])] = 8400,
) -> None:
    """Authenticate with a provider via OAuth2."""
    store = TokenStore()
    scope_list = [s.strip() for s in scopes.split(",") if s.strip()] if scopes else []
    config = OAuth2Config(
        client_id=client_id,
        authorize_url=authorize_url or token_url,
        token_url=token_url,
        scopes=scope_list,
        redirect_port=redirect_port,
    )

    if client_secret:
        # Machine-to-machine: Client Credentials flow
        try:
            token = client_credentials_flow(config, client_secret)
        except OSError as exc:
            print(json.dumps({"ok": False, "error": str(exc)}))
            sys.exit(1)
    elif authorize_url:
        # Interactive: Authorization Code flow with PKCE
        verifier = generate_code_verifier()
        challenge = generate_code_challenge(verifier)
        state = secrets.token_hex(16)
        url = build_authorize_url(config, challenge, "S256", state=state)
        print(f"Open this URL in your browser to authorize:\n\n  {url}\n", file=sys.stderr)
        code = input("Enter the authorization code from the redirect: ").strip()
        try:
            token = authorization_code_flow(config, code, verifier)
        except OSError as exc:
            print(json.dumps({"ok": False, "error": str(exc)}))
            sys.exit(1)
    else:
        print(
            json.dumps(
                {
                    "ok": False,
                    "error": "Provide --authorize-url for interactive flow or --client-secret for machine flow",
                }
            )
        )
        sys.exit(1)

    store.save(provider, token)
    print(json.dumps({"ok": True, "provider": provider, "expires_at": token.expires_at}))


@auth_app.command
def status(
    provider: Annotated[str | None, Parameter(["--provider", "-p"])] = None,
) -> None:
    """Show authentication status for providers."""
    store = TokenStore()
    if provider:
        token = store.load(provider)
        if token is None:
            print(json.dumps({"provider": provider, "authenticated": False}))
        else:
            print(
                json.dumps(
                    {
                        "provider": provider,
                        "authenticated": True,
                        "expired": token.is_expired,
                        "has_refresh_token": token.refresh_token is not None,
                        "scope": token.scope,
                    }
                )
            )
    else:
        providers = store.list_providers()
        if not providers:
            print(json.dumps({"authenticated_providers": []}))
        else:
            entries = []
            for name in providers:
                tok = store.load(name)
                entries.append(
                    {
                        "provider": name,
                        "expired": tok.is_expired if tok else True,
                        "has_refresh_token": (tok.refresh_token is not None) if tok else False,
                    }
                )
            print(json.dumps({"authenticated_providers": entries}, indent=2))


@auth_app.command
def logout(
    provider: Annotated[str, Parameter(["--provider", "-p"])],
) -> None:
    """Remove stored credentials for a provider."""
    store = TokenStore()
    removed = store.delete(provider)
    print(json.dumps({"ok": removed, "provider": provider}))
