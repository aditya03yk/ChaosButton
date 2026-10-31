"""Target safety checks: URL validation, SSRF protection and header redaction.

Kept free of third-party imports so the rules are easy to unit test.
"""
import asyncio
import ipaddress
import socket
from dataclasses import dataclass, field
from typing import Any, Mapping
from urllib.parse import urlsplit

SENSITIVE_HEADERS = {"authorization", "cookie", "set-cookie", "proxy-authorization",
                     "x-api-key", "x-auth-token"}


def redact_headers(headers: Mapping[str, str]) -> dict[str, str]:
    """Return a copy of headers that is safe to log."""
    return {k: ("[REDACTED]" if k.lower() in SENSITIVE_HEADERS else v) for k, v in headers.items()}


def classify_address(ip: str) -> str:
    """Classify an IP as loopback, private, link_local, reserved or global."""
    addr = ipaddress.ip_address(ip)
    if addr.is_loopback:
        return "loopback"
    if addr.is_link_local:
        return "link_local"
    if addr.is_private:
        return "private"
    if addr.is_global:
        return "global"
    return "reserved"


async def resolve_host(host: str, port: int) -> list[str]:
    """Resolve a hostname to unique IP strings without blocking the loop."""
    loop = asyncio.get_running_loop()
    infos = await loop.getaddrinfo(host, port, type=socket.SOCK_STREAM)
    return sorted({info[4][0] for info in infos})


@dataclass
class UrlCheck:
    ok: bool
    normalized_url: str = ""
    host: str = ""
    loopback: bool = False
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


async def check_target_url(url: str, *, ownership_confirmed: bool, environment_type: str,
                           settings: Any, resolver=resolve_host) -> UrlCheck:
    """Validate a target URL against the allow-list rules.

    Loopback targets are always allowed. Remote targets need an explicit ownership
    confirmation, a non-local environment type, presence in ALLOWED_REMOTE_HOSTS and
    public-only resolved addresses (no private, link-local or reserved ranges).
    """
    result = UrlCheck(ok=False)
    try:
        parts = urlsplit(url.strip())
        port = parts.port
    except ValueError:
        result.errors.append("The URL is malformed.")
        return result
    if parts.scheme not in ("http", "https"):
        result.errors.append("Only http and https URLs are supported.")
    if not parts.hostname:
        result.errors.append("The URL must include a host name.")
    if parts.username or parts.password:
        result.errors.append("Credentials inside the URL are not allowed.")
    if result.errors:
        return result

    host = parts.hostname or ""
    port = port or (443 if parts.scheme == "https" else 80)
    try:
        addresses = await resolver(host, port)
    except OSError:
        result.errors.append(f"The host '{host}' could not be resolved.")
        return result

    kinds = {classify_address(ip) for ip in addresses}
    result.host = host
    result.loopback = kinds == {"loopback"}
    if not result.loopback:
        _check_remote(result, host, kinds, ownership_confirmed, environment_type, settings)
    result.normalized_url = f"{parts.scheme}://{parts.netloc}{parts.path.rstrip('/')}"
    result.ok = not result.errors
    return result


def _check_remote(result: UrlCheck, host: str, kinds: set[str], ownership_confirmed: bool,
                  environment_type: str, settings: Any) -> None:
    if not ownership_confirmed:
        result.errors.append("Remote targets require explicit ownership confirmation.")
    if environment_type == "local":
        result.errors.append("A remote host cannot use the 'local' environment type.")
    if host.lower() not in {h.lower() for h in settings.allowed_remote_hosts}:
        result.errors.append(f"'{host}' is not in the ALLOWED_REMOTE_HOSTS allow-list.")
    if kinds != {"global"}:
        result.errors.append("The host resolves to a private, link-local, loopback or reserved "
                             "address, which is not permitted for remote targets.")
    result.warnings.append("Remote target: only test systems you own or are authorised to test.")
