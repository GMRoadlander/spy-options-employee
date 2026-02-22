# Testing

## Framework

- **pytest** (default configuration, no pytest.ini or conftest.py)
- No dev dependencies specified — pytest not in requirements.txt

## Test Files

| File | Tests | Module Covered |
|------|-------|---------------|
| `tests/test_greeks.py` | 45 | Black-Scholes calculations |
| `tests/test_gex.py` | 27 | Gamma exposure engine |
| `tests/test_max_pain.py` | 23 | Max pain algorithm |
| `tests/test_pcr.py` | 35 | Put/call ratio |
| **Total** | **130** | **Analysis layer only** |

## Test Organization

- Tests grouped into classes by function/concept (e.g., `TestDelta`, `TestGamma`)
- Naming: `test_<specific_behavior>` (e.g., `test_atm_call_delta_approximately_half`)
- Module-level constants for reusable parameters (`ATM_S = 600.0`, `ATM_K = 600.0`)

## Test Data

- Factory functions per test module: `make_contract()`, `make_chain()`, `make_test_chain()`
- Synthetic data with sensible defaults — no recorded API fixtures
- No shared conftest.py or fixtures

## Assertions

- Simple `assert` with `pytest.approx()` for floating-point math
- Boundary checks (`assert 0 <= delta <= 1`)
- Property checks (`assert gamma > 0` for all valid inputs)

## Mocking

- Minimal — `unittest.mock.patch` used in `test_gex.py` for patching gamma
- Factory-based test data preferred over mocking

## Coverage Gaps

- **Not tested**: Discord cogs, HTTP clients, database operations, AI commentary
- **Not tested**: Integration/E2E flows
- No coverage configuration or CI integration

## Manual Testing

- `smoke_test.py` — fetches live SPY data, runs full analysis pipeline, prints results
- `validate.py` — data quality checks (IV distribution, OI quality, volume metrics)

---
*Generated: 2026-02-21*
