# Contributing to intent-drift

We welcome contributions to the intent-drift skill! This document describes how to
get started.

## Development Setup

1. **Fork and clone the repository**:
   ```bash
   git clone https://github.com/your-username/intent-drift-skill
   cd intent-drift-skill
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Link to your Claude Code skills directory**:
   ```bash
   ln -s "$PWD" ~/.claude/skills/intent-drift
   ```

## Code Style

- Follow PEP 8 with a line length of 100 characters
- Use type hints for all function signatures
- Write docstrings for all public functions and classes
- Use Black for formatting and isort for import sorting

## Testing

Run the test suite:
```bash
pytest tests/
```

For coverage:
```bash
pytest --cov=intent_drift tests/
```

## Adding a New Provider

1. Create a new file in `providers/` named `<provider_name>_provider.py`
2. Subclass `EvidenceProvider` from `providers/base.py`
3. Implement the `collect()` method returning `List[Evidence]`
4. Add your provider to `providers/__init__.py`
5. Register it in `src/intent_alignment/engine.py` (in `_register_default_providers()`)
6. Add tests in `tests/unit/test_providers.py`

## Adding a New Exporter

1. Create a new exporter class in `exporters/`
2. Subclass `BaseExporter`
3. Implement the `export()` method
4. Add it to the exporter registry in `analyzer.py`

## Documentation

- Update `docs/` for any user-facing changes
- Update `README.md` for new features
- Update `metadata.json` if parameters change

## Pull Request Process

1. Create a feature branch: `git checkout -b feature/my-feature`
2. Make your changes with tests
3. Run the full test suite
4. Update documentation
5. Submit a PR with a clear description

## Code of Conduct

Please be respectful and constructive in all interactions. See `CODE_OF_CONDUCT.md`
for details.
