# Skill: Додати нову модель до існуючого модуля

## Команда
> "Додай модель [назва] до модуля [модуль]"

## Вхідні дані
- `model_name` — технічна назва моделі (наприклад `dm_sync_log`)
- `module` — назва існуючого модуля
- `fields` — перелік полів з типами

## Кроки виконання
1. Створити `18.0/<module>/models/<model_name>.py`
2. Додати імпорт у `18.0/<module>/models/__init__.py`
3. Створити view-файл `18.0/<module>/views/<model_name>_views.xml`
4. Зареєструвати view у `__manifest__.py` у секції `data`
5. Додати рядок у `security/ir.model.access.csv`
6. Додати action + menu item у views

## Типи полів Odoo
```python
fields.Char(string='', help='')           # текст
fields.Text(string='', help='')           # довгий текст
fields.Integer(string='', help='')        # ціле
fields.Float(string='', help='')          # дробове
fields.Boolean(string='', help='')        # чекбокс
fields.Date(string='', help='')           # дата
fields.Datetime(string='', help='')       # дата+час
fields.Selection([...], string='')        # список
fields.Many2one('model', string='')       # FK
fields.One2many('model', 'field', ...)    # зворотній зв'язок
fields.Many2many('model', string='')      # багато до багатьох
```
