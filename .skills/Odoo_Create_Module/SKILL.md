# Skill: Створити новий Odoo-модуль

## Команда
> "Створи модуль [назва]" або "Додай новий модуль [назва]"

## Вхідні дані
- `name` — технічна назва модуля (snake_case, з префіксом `vd_`)
- `description` — короткий опис що робить модуль
- `depends` — залежності (за замовчуванням: `['base']`)
- `has_wizard` — чи містить модуль візарди (True/False)

## Розташування модуля
- Модуль розміщується у **корені репозиторію**: `<repo-root>/<name>/`
- Підпапки версії (`18.0/`) **не використовуються** — версія фіксується гілкою (`18.0`)
- `addons_path` на Odoo-сервері вказує на корінь репозиторію

## Кроки виконання
1. Створити папку `<name>/` у корені репозиторію
2. Згенерувати `__manifest__.py` згідно `.rules/odoo-conventions.md`
3. Створити `models/__init__.py` (порожньо, готово до розширення)
4. Якщо `has_wizard=True`:
   - Створити `wizard/__init__.py` та `wizard/<name>_wizard.py` з TransientModel stub
   - `__init__.py` модуля: `from . import models, wizard, services, controllers`
5. Якщо `has_wizard=False`:
   - `__init__.py` модуля: `from . import models`
6. Створити `services/__init__.py` та `controllers/__init__.py` (порожні, з коментарями)
7. Створити `views/<name>_views.xml` — placeholder form view
8. Якщо `has_wizard=True` — замість `<name>_views.xml` використати `<name>_wizard_views.xml`
9. Створити `views/menus.xml` — menuitem + ir.actions.act_window
10. Створити `security/security_groups.xml` з групою доступу
11. Створити `security/ir.model.access.csv` з базовими правами

## Шаблон TransientModel stub (`wizard/`)
```python
from odoo import models, fields
import logging

_logger = logging.getLogger(__name__)


class MyWizard(models.TransientModel):
    """Short description. Fields added in M2."""

    _name = 'vd.<name>.wizard'
    _description = '<Description> Wizard'
```

## Структура при `has_wizard=True`
```
<name>/
├── __init__.py          # from . import models, wizard, services, controllers
├── __manifest__.py
├── models/
│   └── __init__.py      # placeholder
├── wizard/
│   ├── __init__.py
│   └── <name>_wizard.py
├── services/
│   └── __init__.py      # placeholder (filled in M3)
├── controllers/
│   └── __init__.py      # placeholder (filled in M6)
├── views/
│   ├── <name>_wizard_views.xml
│   └── menus.xml
├── security/
│   ├── security_groups.xml
│   └── ir.model.access.csv
└── static/
    └── description/
        └── icon.png
```

## Результат
Структура модуля готова до встановлення на Odoo 18.0 інстанс без помилок.
Перевірка: `odoo-bin -i <name> -d <db> --stop-after-init`
