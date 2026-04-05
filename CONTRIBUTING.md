# Contributing to Norway Electricity Prices

Thank you for your interest in contributing! This guide will help you get
started.

## Ways to Contribute

- 🐛 **Report bugs** — open an
  [issue](https://github.com/Kvikku/ElectricityPriceAddon/issues) with
  reproduction steps.
- 💡 **Suggest features** — open an issue describing the use case.
- 🌍 **Add translations** — contribute a new language file.
- 🔧 **Submit code** — fix a bug or implement a feature via pull request.
- 📖 **Improve docs** — fix typos, add examples, or clarify instructions.

## Development Setup

See the [Development Guide](docs/development.md) for full instructions.

Quick start:

```bash
git clone https://github.com/Kvikku/ElectricityPriceAddon.git
cd ElectricityPriceAddon
python -m venv .venv
source .venv/bin/activate
pip install pytest aiohttp ruff
```

## Pull Request Process

1. **Fork** the repository and create a feature branch from `main`.
2. Make your changes — keep them focused and minimal.
3. **Add or update tests** for any new functionality.
4. **Run the checks** before submitting:
   ```bash
   ruff check .
   ruff format --check .
   pytest tests/ -v
   ```
5. **Update documentation** if your changes affect user-facing behavior.
6. Open a **pull request** with a clear description of what and why.

## Commit Messages

Use clear, descriptive commit messages:

- `Add: new sensor for daily price range`
- `Fix: handle missing tomorrow prices gracefully`
- `Docs: update automation examples`
- `Refactor: extract price calculation to helper`

## Code Style

- Python 3.12+, with `from __future__ import annotations`.
- Type hints on all function signatures.
- Docstrings on public classes and methods.
- Constants in `const.py`, not inline.
- Linted and formatted with [Ruff](https://docs.astral.sh/ruff/).

## Adding Translations

1. Copy `custom_components/norway_electricity/translations/en.json` to a
   new file named with the
   [BCP 47 language code](https://www.iana.org/assignments/language-subtag-registry/language-subtag-registry)
   (e.g., `sv.json` for Swedish).
2. Translate all values (keep the keys unchanged).
3. Submit a pull request.

> **Note:** `strings.json` is the source of truth for English strings and
> `translations/en.json` must always be an identical copy. If you change one,
> update the other to match.

## Reporting Issues

When reporting a bug, please include:

- Home Assistant version
- Integration version (from `manifest.json`)
- Price area configured
- Relevant log entries (Settings → System → Logs)
- Steps to reproduce

## Code of Conduct

Be respectful and constructive. We're all here to build something useful for
the Home Assistant community.

## License

By contributing, you agree that your contributions will be licensed under the
same [MIT License](LICENSE) that covers the project.
