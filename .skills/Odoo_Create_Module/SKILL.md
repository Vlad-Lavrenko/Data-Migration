# Skill: Створити новий Odoo-модуль

## Команда
> "Створи модуль [назва]" або "Додай новий модуль [назва]"

## Вхідні дані
- `name` — технічна назва модуля (snake_case, з префіксом `vd_`)
- `description` — короткий опис що робить модуль
- `depends` — залежності (за замовчуванням: `['base']`)
- `has_wizard` — чи містить модуль візарди (True/False)

## Кроки виконання
1. Створити папку `18.0/<name>/`
2. Згенерувати `__manifest__.py` згідно `.rules/odoo-conventions.md`
3. Створити `models/__init__.py` та `models/<name>.py` з базовою моделлю
4. Якщо `has_wizard=True`:
   - Створити `wizard/__init__.py` та `wizard/<name>_wizard.py` з TransientModel
   - `__init__.py` модуля: `from . import models, wizard`
5. Якщо `has_wizard=False`:
   - `__init__.py` модуля: `from . import models`
6. Створити `views/<name>_views.xml` з tree + form view
7. Якщо `has_wizard=True` — додати `views/<name>_wizard_views.xml` для візарда
8. Створити `security/security_groups.xml` з групою доступу
9. Створити `security/ir.model.access.csv` з базовими правами
10. Додати запис про модуль у `docs/plan.md`

## Шаблон звичайної моделі (`models/`)
```python
from odoo import models, fields, api
import logging
_logger = logging.getLogger(__name__)

class MyModel(models.Model):
    _name = 'vd_<name>'
    _description = '<description>'

    name = fields.Char(string='Name', required=True, help='Record name')
    active = fields.Boolean(string='Active', default=True)
```

## Шаблон візарда (`wizard/`)
```python
from odoo import models, fields, api
import logging
_logger = logging.getLogger(__name__)

class MyWizard(models.TransientModel):
    _name = 'vd_<name>.wizard'
    _description = '<description> Wizard'

    name = fields.Char(string='Name', help='Wizard name')

    def action_confirm(self):
        # Основна логіка візарда
        return {'type': 'ir.actions.act_window_close'}
```

## Структура при `has_wizard=True`
```
<name>/
├── __init__.py          # from . import models, wizard
├── __manifest__.py
├── models/
│   ├── __init__.py
│   └── <name>.py
├── wizard/
│   ├── __init__.py
│   └── <name>_wizard.py
├── views/
│   ├── <name>_views.xml
│   └── <name>_wizard_views.xml
├── security/
│   ├── security_groups.xml
│   └── ir.model.access.csv
└── static/
    └── description/
        └── icon.png
```

## Результат
Структура модуля готова до встановлення на Odoo 18.0 інстанс.
