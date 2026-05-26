# AlfaCore API — v1

The companion PWA talks to AlfaCore through the `/api/v1/*` REST endpoints
defined in `alfacore-v1-openapi.yaml`. This README is the orientation map.

## What's here

| File | Purpose |
|---|---|
| `alfacore-v1-openapi.yaml` | OpenAPI 3.1 spec. The contract. |
| `README.md` | This file. |

The spec describes five endpoints behind a single bearer-auth scheme:

| Method | Path | Purpose |
|---|---|---|
| POST | `/api/v1/auth` | Issue a JWT for a portal user |
| POST | `/api/v1/scans` | Upload a scan session from the OBD-II scanner |
| GET  | `/api/v1/diagnoses/{report_id}` | Retrieve an AI diagnosis report |
| GET  | `/api/v1/vehicles/{vin}/preferences` | Vehicle service preferences |
| GET  | `/api/v1/vehicles/{vin}/recalls` | Open recall campaigns |

## Viewing the spec interactively

```bash
# Option A: Swagger UI in Docker, one liner
docker run -p 8080:8080 \
  -e SWAGGER_JSON=/spec/alfacore-v1-openapi.yaml \
  -v $(pwd):/spec \
  swaggerapi/swagger-ui
# Open http://localhost:8080

# Option B: Redocly CLI (prettier rendering)
npx @redocly/cli preview-docs alfacore-v1-openapi.yaml
```

## Generating a client

For the React Native / Capacitor companion PWA:

```bash
# TypeScript / fetch
npx openapi-typescript-codegen \
  --input alfacore-v1-openapi.yaml \
  --output src/api/alfacore \
  --client fetch

# Or with @hey-api/openapi-ts (more modern)
npx @hey-api/openapi-ts -i alfacore-v1-openapi.yaml -o src/api/alfacore
```

For a server-side Python integration test client:

```bash
pip install openapi-python-client
openapi-python-client generate --path alfacore-v1-openapi.yaml
```

## curl examples

### Authenticate

```bash
TOKEN=$(curl -sX POST https://alfacore.realpartners.tld/api/v1/auth \
  -H "Content-Type: application/json" \
  -d '{"login": "dangelo.john@gmail.com", "password": "..."}' \
  | jq -r .token)
```

### Upload a scan

```bash
curl -X POST https://alfacore.realpartners.tld/api/v1/scans \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d @- <<'JSON'
{
  "vehicle_vin": "ZASFAKBN3J7C12345",
  "started_at": "2026-05-12T13:00:00Z",
  "ended_at":   "2026-05-12T13:04:00Z",
  "modules_scanned": "ECM,TCM,ABS,BCM",
  "battery_voltage": 12.6,
  "mileage_at_scan": 89247,
  "dtcs": [
    {"code": "P0301", "status": "active", "module": "ECM",
     "freeze_frame": "RPM:2100 Coolant:92C Load:38%"}
  ],
  "pids": [
    {"pid": "010C", "name": "Engine RPM", "value": "847", "units": "rpm"}
  ]
}
JSON
```

### Check for recalls

```bash
curl -s -H "Authorization: Bearer $TOKEN" \
  https://alfacore.realpartners.tld/api/v1/vehicles/ZASFAKBN3J7C12345/recalls \
  | jq '.do_not_drive, .open_recall_count, .recalls[].campaign_name'
```

## Rate limit semantics

Three profiles. Each is a separate token bucket per request key.

| Profile | Where | Capacity (burst) | Refill | Key |
|---|---|---|---|---|
| `auth` | POST /api/v1/auth | 5 | 10/min | source IP |
| `api_read` | all authenticated endpoints | 30 | 120/min | partner_id |
| `api_ip` | all authenticated endpoints | 100 | 600/min | source IP |

On a denial:
- HTTP status: `429 Too Many Requests`
- Body: `{"error": "rate_limit_exceeded", "retry_after_seconds": <float>}`
- Header: `Retry-After: <integer-seconds>`

Honor the `Retry-After` header. Clients that don't can saturate the
bucket and get stuck in a tight retry loop while their sibling clients
proceed normally.

## JWT lifecycle

- Issued: by `/api/v1/auth`. Default TTL 30 days.
- Signed: HS256 with the server-side `alfa_core_app_api.jwt_secret`.
- Verified: on every authenticated request. During a key rotation
  window, tokens signed with the previous secret continue to verify
  (transparent to the client).
- Revoked: by deleting or marking the corresponding `alfa_core_app_api.token`
  record. Subsequent requests fail with `token_revoked_or_unknown`.
- Re-issuance: clients should treat any 401 as "re-auth and retry once."
  After the second consecutive 401, surface the credential prompt.

## Error vocabulary

| Code | Meaning |
|---|---|
| `missing_credentials` | POST /auth without login or password |
| `invalid_credentials` | Wrong login/password |
| `missing_bearer_token` | No `Authorization: Bearer ...` header |
| `token_expired` | JWT exp is in the past |
| `invalid_token` | JWT signature doesn't verify against current or previous secret |
| `token_revoked_or_unknown` | JWT valid but no matching active `token` record |
| `vehicle_not_found` | No vehicle with this VIN |
| `not_authorized` (a.k.a. `not_authorized_for_this_vehicle`) | Authenticated, but you don't own this vehicle |
| `no_paired_device_for_vehicle` | Upload attempted before scanner pairing complete |
| `rate_limit_exceeded` | Token bucket empty for this profile + key |
| `jwt_secret_not_configured` | Server misconfiguration — JWT secret param empty |

## Companion PWA implementation notes

- **Storing the token**: secure storage (Keychain on iOS, EncryptedSharedPreferences on Android). Not localStorage.
- **Refresh**: there is no refresh endpoint in v1. When the JWT expires, re-call `/auth` with stored credentials (or surface a re-login UI).
- **Offline scans**: queue scan uploads locally; replay on reconnect. The `/api/v1/scans` endpoint is idempotent at the application level only if the client deduplicates — server creates a new session per request. Track scan UUIDs client-side and avoid resending.
- **Push do_not_drive**: when the `recalls` endpoint reports `do_not_drive: true`, surface it via in-app banner and a push notification. The expected UX is "loud and immediate."
- **Diagnosis polling**: after uploading a scan, the diagnosis pipeline runs server-side. Poll `/api/v1/diagnoses/{id}` with backoff (start 2s, double up to 30s, give up after 5 minutes and treat as "still processing"). Note that the diagnosis ID is currently returned via the `scan_session.diagnosis_report_id` field once available — this needs a dedicated lookup endpoint or webhook to be wired in a future API revision.
