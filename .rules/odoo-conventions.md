# Odoo 18.0 — Правила розробки

## Маніфест модуля
```python
{
    'name': 'Module Name',
    'version': '18.0.1.0.0',  # major.minor.patch
    'category': 'Tools',
    'summary': 'Short description',
    'author': 'Vlad Lavrenko',
    'depends': ['base'],
    'data': [],
    'installable': True,
    'application': False,
}
```

## Структура папок модуля

Стандартна структура:
```
<module_name>/
├── __init__.py
├── __manifest__.py
├── models/          # Звичайні моделі (Model, AbstractModel)
│   └── __init__.py
├── wizard/          # Тільки TransientModel-класи
│   └── __init__.py
├── views/
├── controllers/
├── security/
└── static/
```

### Правило розподілу моделей:
- `models/` — містить **тільки** `models.Model` та `models.AbstractModel`
- `wizard/` — містить **тільки** `models.TransientModel`
- Якщо модуль містить візарди — папка `wizard/` є обов'язковою
- `__init__.py` модуля імпортує обидва: `from . import models, wizard`

## Моделі
- Префікс назви моделі відповідно до модуля: `vd_` (data migration)
- Завжди вказувати `_description`
- Завжди вказувати `string=` та `help=` для полів
- `sudo()` використовувати тільки з коментарем `# sudo: <reason>`
- Уникати бізнес-логіки у `_compute` — виносити у окремі методи

## View
- XML id формат: `<module>.<type>_<model>_<suffix>`
  Приклад: `vd_migration.view_partner_migration_form`
- Завжди вказувати `string=` у `<record>`
- Tree view — мінімум полів (до 6)
- Form view — групувати поля через `<group>`
- View для візарда зберігати в `views/` (не в `wizard/`)

## Security
- Кожна модель обов'язково має запис у `security/ir.model.access.csv`
- Групи доступу визначати у `security/security_groups.xml`
- Формат CSV: `id,name,model_id:id,group_id:id,perm_read,perm_write,perm_create,perm_unlink`

## Controllers
- Маршрут завжди з `auth='user'` або `auth='public'` (явно)
- JSON-відповідь через `http.Response` з `content_type='application/json'`
- Обробляти виключення та повертати структурований JSON з `error`

## Зв'язок з зовнішнім Odoo (JSON-RPC)
- Використовувати **JSON-RPC 2.0** через `urllib.request` + `json` (тільки stdlib, без зовнішніх залежностей)
- Аутентифікація: `POST /web/session/authenticate` → зберігати `session_id`
- Виклики моделей: `POST /web/dataset/call_kw` з Cookie `session_id`
- Читання даних — батчами по **100 записів** (`search_read` з `offset` + `limit`)
- Цикл по батчах завершується коли `len(records) == 0`
- Логувати кожну RPC-операцію через `_logger`
- Обробляти: `socket.timeout`, `URLError`, JSON `error` поле → `UserError`
- Зберігати `session_id` тільки в `TransientModel` (пам'ять, не в БД)

## Frontend-driven процеси
- Якщо процес потребує прогресу в реальному часі — виконувати цикл на **фронтенді** (Owl 2)
- Фронтенд читає батчи через бекенд-**проксі** (уникати прямих CORS-запитів)
- Зупинка циклу — через локальний JS-прапор (`this._stopped`), без polling
- Після завершення — notify бекенд через `POST /finalize`
