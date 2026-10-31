"""Target allow-list, SSRF protection, header redaction and hard experiment limits."""
import asyncio
from types import SimpleNamespace as NS

from app.core.security import check_target_url, classify_address, redact_headers

HOSTS = {"localhost": ["127.0.0.1", "::1"], "shop.example.com": ["93.184.216.34"], "internal.example.com": ["10.0.0.7"],
         "meta.example.com": ["169.254.169.254"]}


async def resolver(host, port):
    if host not in HOSTS:
        raise OSError("unresolvable")
    return HOSTS[host]


def check(url, owned=False, env="staging", allow=()):
    return asyncio.run(check_target_url(url, ownership_confirmed=owned, environment_type=env,
                                        settings=NS(allowed_remote_hosts=list(allow)), resolver=resolver))


def test_loopback_allowed_by_default():
    assert check("http://localhost:9001/").ok
    assert check("http://localhost:9001/shop/").normalized_url == "http://localhost:9001/shop"


def test_rejects_bad_schemes_credentials_and_unresolvable():
    assert not check("ftp://localhost").ok
    assert not check("http://user:pw@localhost").ok
    assert not check("http://nope.invalid").ok
    assert not check("not a url").ok


def test_remote_needs_ownership_allowlist_and_staging_env():
    assert not check("http://shop.example.com").ok
    assert not check("http://shop.example.com", owned=True).ok  # not on the allow-list
    assert check("http://shop.example.com", owned=True, allow=["shop.example.com"]).ok
    assert not check("http://shop.example.com", owned=True, env="local", allow=["shop.example.com"]).ok


def test_private_and_metadata_ranges_rejected_even_when_allow_listed():
    assert not check("http://internal.example.com", owned=True, allow=["internal.example.com"]).ok
    assert not check("http://meta.example.com", owned=True, allow=["meta.example.com"]).ok
    assert classify_address("169.254.169.254") == "link_local" and classify_address("8.8.8.8") == "global"


def test_sensitive_headers_are_redacted():
    out = redact_headers({"Authorization": "Bearer x", "Cookie": "s=1", "Accept": "*/*"})
    assert out["Authorization"] == "[REDACTED]" and out["Cookie"] == "[REDACTED]" and out["Accept"] == "*/*"
