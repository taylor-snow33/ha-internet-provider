# Validation report — 2026-10-30

- Python 3.14.8; Home Assistant 2026.10.4; pytest-homeassistant-custom-component 0.13.375.
- **28 tests passed**, including actual HA setup/entity registration/unload, config flow and duplicate prevention, options reload, unavailable states/recovery, missing fields, long strings and raw JSON preservation, API errors/timeouts and 429 cooldown retention.
- Coverage: **99%** (194 statements, one unexercised HTTP-date normalization line).
- Ruff lint and formatting checks passed. Python compilation and JSON parsing passed.
- HACS structure checked against current published requirements: one integration directory, manifest keys, `hacs.json`, and brand icon included. This is not a successful HACS installation or HACS remote validation claim.
- Unit/integration tests use mocked HTTP responses with synthetic/public example data. No live RV-origin request, physical WAN failover, production HA install or UI browser test was performed.
- The target public repository `taylor-snow33/ha-internet-provider` was verified on 2026-10-30. This report records local verification; GitHub publication and CI status are tracked separately. No GitHub credentials are included.
