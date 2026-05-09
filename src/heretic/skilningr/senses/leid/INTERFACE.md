# Leið Sense — Interface Contract

**Last updated:** 2026-05-08 (v0.6.2 scaffold — Rúnhild Svartdóttir)
**Scope:** L5.3 Leið — sandboxed HTTP fetch sense
**Authority:** Architect (Rúnhild Svartdóttir)

---

## 1. Identity

| Field       | Value                                          |
|-------------|------------------------------------------------|
| True Name   | Leið ("path" / "way")                          |
| sense_id    | `leid`                                         |
| Layer       | L5.3 Skilningr sense hub                       |
| Prefix      | `leid.*`                                       |
| Config key  | `skilningr.leid.*` in `heretic.yaml`           |
| Module      | `heretic.skilningr.senses.leid`                |
| Client      | `LeidClient` (httpx GET, URL allowlist)        |

---

## 2. Purpose

Leið gives the agent a road to the outside web — strictly bounded. It fetches
HTTP resources and extracts their text within an operator-defined URL allowlist.
No URL is reachable unless the operator explicitly permits a matching pattern.
An empty allowlist means the world is closed.

Leið does NOT execute JavaScript. It does NOT follow links beyond the requested
URL. It does NOT store or send cookies. It does NOT support POST or any other
write method. v0.6.2 is GET-only.

---

## 3. Sandbox Invariants (NON-NEGOTIABLE)

| # | Invariant |
|---|-----------|
| L-1 | `sandbox.url_matches_allowlist()` is called BEFORE any `httpx` request is made. No HTTP I/O precedes this check. |
| L-2 | `url_allowlist_patterns` defaults `[]` (empty). With an empty list, no URL is fetchable regardless of `enabled=True`. |
| L-3 | `enabled: false` by default. No outbound HTTP until explicitly enabled. |
| L-4 | HTTPS-only by default (`allow_http: false`). HTTP URLs are rejected unless `allow_http: true`. Even when allowed, HTTP is logged as a warning. |
| L-5 | No cookies stored, sent, or accepted at any time. |
| L-6 | No JavaScript execution. httpx is the transport; playwright/selenium = v0.6.2.1+. |
| L-7 | Response body is capped at `max_response_bytes` (default 1 MiB). No partial read beyond this. |
| L-8 | Redirects are followed up to `max_redirects` (default 5). Beyond that the request aborts with LeidConnectionError. |
| L-9 | The wildcard pattern `"*"` is logged as a security warning at ceremony start if present in `url_allowlist_patterns`. |

---

## 4. Tools (LOCKED at v0.6.2)

| Tool name          | Action              | Required params  | Optional params |
|--------------------|---------------------|------------------|-----------------|
| `leid.fetch_url`   | Raw HTTP GET        | `url` (string)   | —               |
| `leid.extract_text`| GET + strip HTML    | `url` (string)   | —               |

---

## 5. Success Response Shapes

### leid.fetch_url
```json
{
  "url": "https://docs.python.org/3/library/os.html",
  "status_code": 200,
  "content_type": "text/html; charset=utf-8",
  "body": "<html>...",
  "body_encoding": "utf-8",
  "size_bytes": 45678,
  "truncated": false
}
```

### leid.extract_text
```json
{
  "url": "https://docs.python.org/3/library/os.html",
  "text": "os — Miscellaneous operating system interfaces...",
  "title": "os — Miscellaneous operating system interfaces — Python 3 documentation",
  "size_bytes": 45678,
  "truncated": false
}
```

---

## 6. Failure Modes

| Condition                                  | Error class                | SENSE_CONTRACTS code      |
|--------------------------------------------|----------------------------|---------------------------|
| URL not in allowlist                       | `UrlNotAllowedError`       | `PERMISSION_DENIED`       |
| HTTP URL and `allow_http: false`           | `UrlNotAllowedError`       | `PERMISSION_DENIED`       |
| Request timed out                          | `LeidTimeoutError`         | `SENSE_TIMEOUT`           |
| Response exceeds `max_response_bytes`      | `LeidResponseTooLargeError`| `INVALID_ARGUMENTS`       |
| HTTP 4xx / 5xx status                      | `LeidHttpError`            | `SENSE_INTERNAL_ERROR`    |
| Network-level error (DNS, TCP, TLS)        | `LeidConnectionError`      | `EXTERNAL_APP_UNAVAILABLE`|
| Unknown tool name in `leid.*`              | `ToolDispatchError`        | `SENSE_INTERNAL_ERROR`    |
| Sense disabled or not open                 | `SenseUnavailableError`    | `SENSE_UNAVAILABLE`       |

---

## 7. Configuration Reference

```yaml
skilningr:
  leid:
    enabled: false                        # opt-in
    url_allowlist_patterns: []            # empty = nothing fetchable; add patterns
      # - "https://docs.python.org/*"
      # - "https://en.wikipedia.org/*"
    timeout_seconds: 30
    max_redirects: 5
    max_response_bytes: 1048576           # 1 MB
    user_agent: "HERETIC/0.6.2 (heretic-summoning-circle)"
    allow_http: false                     # HTTPS-only by default
```

---

## 8. Forge Wave 2 — Implementation Contract

- `fetch_url`: call `_validate_url()` first; create `httpx.AsyncClient` with
  `follow_redirects=True, max_redirects=config.max_redirects, timeout=config.timeout_seconds,
  headers={"User-Agent": config.user_agent}`; check `Content-Length` header if present —
  reject immediately if > max_response_bytes; stream body and truncate at cap;
  handle `httpx.TimeoutException` → `LeidTimeoutError`; handle `httpx.ConnectError`
  → `LeidConnectionError`; handle 4xx/5xx → `LeidHttpError`; return dict.
- `extract_text`: call `fetch_url()` internally; if `content_type` contains `text/html`,
  use `html.parser` (stdlib) to strip tags and extract visible text; otherwise return raw
  body as text. No external HTML parser dependency in v0.6.2.
