# Conventions

## Code Style

- **Indentation**: 4 spaces
- **Quotes**: Double quotes (`"`) throughout
- **Line length**: ~100 characters
- **No linting/formatting config** (.flake8, pyproject.toml [tool.black], etc.)

## Naming

| Element | Convention | Example |
|---------|-----------|---------|
| Functions | snake_case | `calculate_gex()`, `black_scholes_delta()` |
| Classes | PascalCase | `SpyBot`, `DataManager`, `OptionContract` |
| Constants | SCREAMING_SNAKE | `VALID_TICKERS`, `SYSTEM_PROMPT` |
| Private | _underscore prefix | `_compute_contract_gex()`, `_cache` |
| Modules | snake_case.py | `data_manager.py`, `cog_alerts.py` |
| Dataclasses | PascalCase + "Result" suffix | `GEXResult`, `PCRResult`, `AnalysisResult` |

## Import Order

1. Standard library (`logging`, `asyncio`, `json`)
2. Third-party (`discord`, `aiohttp`, `pandas`, `numpy`)
3. Local (`from src.config import config`)

## Docstrings

- **Style**: Google-style with Args, Returns, Raises sections
- **Coverage**: All public functions and classes have docstrings
- **Inline comments**: Only for algorithm explanations

## Type Annotations

- **Coverage**: Fully typed (all functions, parameters, return types)
- **Syntax**: Modern PEP 604 (`X | None` instead of `Optional[X]`)
- **Generics**: `list[float]`, `dict[str, int]`, `tuple[float, float]`

## Logging

- **Setup**: Centralized in `main.py` with format `%(asctime)s %(name)s %(levelname)s %(message)s`
- **Per-module**: `logger = logging.getLogger(__name__)`
- **String formatting**: Percent-style with separate arguments (`logger.info("Got %d", count)`)
- **Discord noise suppressed**: `logging.getLogger("discord").setLevel(logging.WARNING)`

## Error Handling

- Specific exception types caught where possible
- Generic `Exception` caught at integration boundaries (API calls, I/O)
- Always logs with `exc_info=True` for tracebacks
- No custom exception classes — uses built-in exceptions
- `ValueError` raised for validation failures

## Data Structures

- **@dataclass** for all domain entities (`OptionContract`, `OptionsChain`, all Result types)
- **Frozen dataclass** for configuration (immutable singleton)
- **@property** for computed values on dataclasses

## Async Patterns

- `async def` for all I/O operations
- `await` consistently used (no forgotten awaits observed)
- Lifecycle hooks in bot: `setup_hook()`, `on_ready()`, `close()`
- `@tasks.loop()` for background scheduling

## Configuration

- Frozen dataclass singleton in `config.py`
- Environment variables via `os.getenv()` with defaults
- `.env` file loaded via `python-dotenv`
- Access pattern: `from src.config import config` then `config.discord_token`

---
*Generated: 2026-02-21*
