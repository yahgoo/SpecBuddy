# API Gateway Requirements

## Functional Requirements

- THE System SHALL enforce rate limiting as defined in the following table:

| Tier       | Requests/min | Burst limit | Retry-After header |
|------------|-------------|-------------|-------------------|
| Free       | 60          | 10          | Yes               |
| Pro        | 600         | 50          | Yes               |
| Enterprise | 6000        | 500         | No                |

- WHEN the rate limit is exceeded, THE System SHALL return HTTP 429 with the following response body:

```json
{
  "error": "rate_limit_exceeded",
  "retry_after_seconds": 30,
  "message": "THE System SHALL not process this — it is rate limited"
}
```

- THE System SHALL validate input against the following nested rules:
  - Level 1: Check authentication token
    - Level 2: Verify token signature
      - Level 3: Confirm token is not revoked
        - Level 4: Validate token claims match request scope
  - Level 1: Check request body schema
    - Level 2: Validate required fields
      - Level 3: Enforce field length constraints
        - Level 4: Apply custom business rules

- WHEN the health check endpoint `/health` is called, THE System SHALL return:

```yaml
status: healthy
version: "2.1.0"
checks:
  database: connected
  cache: connected
  queue: connected
```

- THE System SHALL log all requests using the format: `[TIMESTAMP] [METHOD] [PATH] [STATUS] [DURATION_MS]`

> **Note:** This requirement was discussed in the architecture review.
> THE System SHALL also support the legacy format for backward compatibility.

- IF the `X-Request-ID` header is present, THEN THE System SHALL propagate the value through all downstream service calls.

---

## Non-Functional Requirements

- THE System SHALL handle the following edge cases:
  1. Empty request body
  2. Request body exceeding 10MB
  3. Malformed JSON with unclosed brackets
  4. Duplicate headers
  5. Requests with no `Content-Type` header
