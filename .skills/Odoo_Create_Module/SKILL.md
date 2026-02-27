# Skill: Створити новий Odoo-модуль

## Команда
> "Створи модуль [назва]" або "Додай новий модуль [назва]"

## Вхідні дані
- `name` — технічна назва модуля (snake_case, з префіксом `dm_`)
- `description` — короткий опис що робить модуль
- `depends` — залежності (за замовчуванням: `['base']`)

## Кроки виконання
1. Створити папку `18.0/<name>/`
2. Згенерувати `__manifest__.py` згідно `.rules/odoo-conventions.md`
3. Створити `__init__.py` з імпортом `models`
4. Створити `models/__init__.py` та `models/<name>.py` з базовою моделлю
5. Створити `views/<name>_views.xml` з tree + form view
6. Створити `security/security_groups.xml` з групою доступу
7. Створити `security/ir.model.access.csv` з базовими правами
8. Додати запис про модуль у `docs/plan.md`

## Шаблон моделі
```python
from odoo import models, fields, api
import logging
_logger = logging.getLogger(__name__)

class MyModel(models.Model):
    _name = 'dm_<name>'
    _description = '<description>'

    name = fields.Char(string='Name', required=True, help='Record name')
    active = fields.Boolean(string='Active', default=True)
```

## Результат
Структура модуля готова до встановлення на Odoo 18.0 інстанс.
