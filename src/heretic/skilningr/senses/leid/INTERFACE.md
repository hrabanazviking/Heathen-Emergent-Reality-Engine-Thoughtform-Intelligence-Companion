# Leið Sense — Interface Contract

**Last updated:** 2026-05-09 (v0.7.1 *Straumr á Leið* streaming addendum — Rúnhild Svartdóttir) | 2026-05-08 (v0.6.2 scaffold — Rúnhild Svartdóttir)
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
| L-6 | No JavaScript execution. httpx is the transport; playwright/selenium = v0.8 Opið Vef. |
| L-7 | Response body is capped at `max_response_bytes` (default 1 MiB). **As of v0.7.1 the cap is enforced via streaming abort:** `httpx.AsyncClient.stream("GET", url)` + `aiter_bytes`; the `LeidResponseTooLargeError` is raised **mid-stream** as soon as the accumulator exceeds the cap. The connection is closed during stack unwind; remaining bytes never travel. Memory at moment of raise is bounded by `max_response_bytes + chunk_size` (default ~1.06 MiB). The agent receives a structured error, never partial content. |
| L-7a | When `Content-Length` header is present and already exceeds `max_response_bytes`, `LeidResponseTooLargeError` is raised before any chunk is read. Malformed `Content-Length` values are ignored (fall through to chunk loop). |
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
  "size_bytes": 45678
}
```

> **Drift correction (v0.7.1):** Earlier sketches of this section showed `body_encoding`
> and `truncated` keys. The shipped v0.6.2 client returned neither (UTF-8 decode with
> `errors="replace"` is implicit; oversized bodies raise instead of truncating). The
> table above now matches the live `LeidClient.fetch_url` return shape. v0.7.1 does not
> change these keys.

### leid.extract_text
```json
{
  "url": "https://docs.python.org/3/library/os.html",
  "text": "os — Miscellaneous operating system interfaces...",
  "title": "os — Miscellaneous operating system interfaces — Python 3 documentation",
  "source_size_bytes": 45678
}
```

> **Drift correction (v0.7.1):** Earlier sketches showed `size_bytes` and `truncated`.
> The shipped client returns `source_size_bytes` (the bytes of the original HTML before
> tag-stripping) and no `truncated` key. v0.7.1 does not change these keys.

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

## 8. Forge Implementation Contract

### v0.7.1 (current — *Straumr á Leið* streaming)

- `fetch_url`:
  1. Call `_validate_url()` first (allowlist + HTTPS-only gate). No httpx call before this.
  2. Open `httpx.AsyncClient(follow_redirects=True, max_redirects=config.max_redirects, timeout=config.timeout_seconds, headers={"User-Agent": config.user_agent})`.
  3. Open `client.stream("GET", url)` as the response context.
  4. **Pre-cap on `Content-Length`**: if header is present and parses as `int` greater than `max_response_bytes`, raise `LeidResponseTooLargeError` immediately. Malformed values are ignored.
  5. **Status check**: if `response.status_code >= 400`, peek up to 500 bytes via a bounded `aiter_bytes` loop for the error-message tail, then raise `LeidHttpError`.
  6. **Streaming accumulator**: `acc = bytearray()`. Iterate `async for chunk in response.aiter_bytes(65536)`. Extend `acc`. After each extend, if `len(acc) > max_response_bytes`, raise `LeidResponseTooLargeError`.
  7. Decode `bytes(acc)` as UTF-8 with `errors="replace"`. Return dict with the five keys in §5.
  8. Map `httpx.TimeoutException` → `LeidTimeoutError`; `httpx.TooManyRedirects` → `LeidConnectionError`; `httpx.ConnectError` → `LeidConnectionError`; other `httpx.HTTPError` → `LeidConnectionError`.

- `extract_text`: call `fetch_url()` internally; if `content_type` contains `text/html` or `application/xhtml`, use `_TextExtractor` (stdlib `html.parser` subclass) to strip tags and capture title; otherwise return raw decoded body as text. No external HTML parser dependency.

### v0.6.2 (historical — buffer-then-check)

The v0.6.2 implementation read `response.content` (full materialisation) then checked
`len > max_response_bytes`. The exception class and surface contract were the same; the
mechanism was the difference. v0.7.1 replaces this in place; the v0.6.2 code path is
gone. The audit-deferred N-2 finding from `AUDIT_v0.6.2_MORE_SENSES.md` is closed by
v0.7.1.

### Method shape policy

The public surface (`fetch_url`, `extract_text`) is **unchanged** between v0.6.2 and
v0.7.1. No new methods, no new private helpers, no new config keys. The streaming
behaviour is hidden behind the same agent-facing contract. This was an explicit
Architect decision: a one-path replacement is cleaner than parallel buffer/streaming
modes when the v0.6.2 path was authored as a known-temporary placeholder.
