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
    'license': 'LGPL-3',
    'application': False,
}
```

## Розташування модуля у репозиторії

- Модуль розміщується у **корені репозиторію**: `<repo-root>/vd_data_migration/`
- Підпапки версії (`18.0/`) **не використовуються** — гілка `18.0` є версійним маркером
- `addons_path` на сервері Odoo вказує на **корінь репозиторію**

## Структура папок модуля

Стандартна структура:
```
vd_data_migration/
├── __init__.py
├── __manifest__.py
├── models/          # Звичайні моделі (Model, AbstractModel)
│   └── __init__.py
├── wizard/          # Все що стосується візарда: TransientModel + XML views
│   ├── __init__.py
│   ├── <name>_wizard.py
│   └── <name>_wizard_views.xml
├── views/           # Тільки menus.xml та views незалежних від wizard моделей
│   └── menus.xml
├── controllers/
├── security/
└── static/
```

### Правило розподілу файлів:
- `models/` — містить **тільки** `models.Model` та `models.AbstractModel`
- `wizard/` — містить **все що стосується візарда**: `TransientModel`-класи **та** XML views для них
- `views/` — містить `menus.xml` та views моделей **не-wizard** (якщо є `models/`)
- Якщо модуль містить лише wizard — `views/` містить тільки `menus.xml`
- `__init__.py` модуля імпортує: `from . import models, wizard, services, controllers`

## Моделі
- Префікс назви моделі відповідно до модуля: `vd_` (data migration)
- Завжди вказувати `_description`
- Завжди вказувати `string=` та `help=` для полів
- `sudo()` використовувати тільки з коментарем `# sudo: <reason>`
- Уникати бізнес-логіки у `_compute` — виносити у окремі методи

## View
- XML id формат: `<module>.<type>_<model>_<suffix>`
  Приклад: `vd_data_migration.view_migration_wizard_form`
- Завжди вказувати `string=` у `<record>`
- Tree view — мінімум полів (до 6)
- Form view — групувати поля через `<group>`
- **View для wizard** зберігати в `wizard/` (не в `views/`)
- `menus.xml` завжди в `views/`

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
- Якщо потрібен прогрес **по-штучно** (per-record) — бекенд має endpoint `process_record`;
  батч використовується лише для читання з джерела (`fetch_batch`)
- Зупинка циклу — через локальний JS-прапор (`this._stopped`), перевіряється в **обох** циклах
- Після завершення — notify бекенд через `POST /finalize`
