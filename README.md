# Offer Creator

Django-based offer creation platform.

## Architecture Standard (Mandatory)

This project uses a domain-rich Django app layout under `apps/`.
All new features must follow this structure.

### Domain apps

- `apps/accounts`
- `apps/company`
- `apps/offers`
- `apps/products`
- `apps/clients`
- `apps/pricing`
- `apps/pdf`
- `apps/core`

### Required module contract per domain app

Each domain app should include:

- `apps.py`
- `models.py`
- `views.py`
- `serializers.py`
- `urls.py`
- `admin.py`
- `tests/`

Optional modules when needed:

- `forms.py`
- `services.py`
- `filters.py`
- `signals.py`
- `tasks.py`
- `management/commands/`

### Conventions

- Use absolute imports in the form `apps.<domain>...`.
- Keep tests co-located in `apps/<domain>/tests/`.
- Keep templates co-located in `apps/<domain>/templates/<domain>/`.
- Preserve public route names when refactoring to avoid regressions.
- Keep cross-domain dependencies explicit and minimal.
