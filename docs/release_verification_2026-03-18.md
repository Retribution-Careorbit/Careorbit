# CareOrbit Release Verification - 2026-03-18

## Scope
Validation of recently shipped features in deployed environment:
- reminders adherence workflow
- orbit improvement plan
- pre-visit brief PDF
- SOS emergency pass payload
- test scenarios API
- browser CORS compatibility from SWA origin

## Environment
- Frontend (SWA): https://gray-field-0d037aa00.1.azurestaticapps.net
- API (App Service): https://careorbit-api-dev.azurewebsites.net
- Test identity: ramesh@careorbit.dev

## Checks Performed
1. Frontend availability
- `GET /` on SWA returned HTTP 200.
- HTML shell present.

2. CORS preflight for chat endpoint
- `OPTIONS /api/chat/query` with SWA origin returned HTTP 200.
- `Access-Control-Allow-Origin` matched SWA URL.
- `Access-Control-Allow-Credentials` was `true`.

3. Auth flow
- `POST /api/auth/login` returned valid bearer token.

4. Reminders workflow
- `GET /api/reminders/due` returned due payload with entries.
- `POST /api/reminders/rem-001/mark` with `{ "status": "taken" }` returned `status=updated`.
- Response included event and adherence recalculation hint.

5. Orbit improvement plan
- `GET /api/orbit/improvement-plan` returned HTTP 200.
- Payload keys validated: `current_score`, `projected_score_30d`, `adherence`, `actions`.

6. Test scenarios
- `GET /api/tests/scenarios` returned HTTP 200 with populated scenarios list.

7. SOS emergency pass
- `GET /api/patients/emergency-pass` returned HTTP 200.
- Payload keys validated: `dispatch_phone`, `token`, `qr_path`, `read_only_note`, `card`.

8. Pre-visit PDF
- `GET /api/summary/previsit-brief/appt-001` returned HTTP 200.
- `Content-Type` validated as `application/pdf`.

## Result
All release validation checks passed for this deployment slice.

## Notes
- Workspace artifact noise was cleaned and ignore rules were added for recurring generated log/cache files.
- Remaining untracked items (`G`, `careorbit/`) were intentionally not removed because provenance is unclear.
