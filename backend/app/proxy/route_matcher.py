"""Explicit route and method matching for fault rules."""


def normalize_path(path: str) -> str:
    """Strip query strings and trailing slashes; always return a leading slash."""
    path = path.split("?", 1)[0]
    if not path.startswith("/"):
        path = "/" + path
    return path.rstrip("/") or "/"


def prefix_matches(pattern: str, path: str) -> bool:
    return path == pattern or path.startswith(pattern.rstrip("/") + "/")


def matches(pattern: str, path: str) -> bool:
    """Public entry point: supports exact routes and trailing '/*' wildcards."""
    if pattern.endswith("/*"):
        return prefix_matches(normalize_path(pattern[:-2]), normalize_path(path))
    return normalize_path(pattern) == normalize_path(path)


def method_matches(rule_method: str, method: str) -> bool:
    return rule_method.upper() in ("*", "ANY") or rule_method.upper() == method.upper()
