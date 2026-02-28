# План розробки модуля `vd_data_migration`

> Базується на: `docs/requirements.md` v0.5 | `docs/architecture.md` v0.6

## Статуси
- `[ ]` — не розпочато
- `[~]` — в процесі
- `[x]` — виконано

---

## Milestone 0: Проєктна інфраструктура

- [x] Створити репозиторій та гілку `18.0`
- [x] Додати `.rules/` та `.skills/`
- [x] Сформувати `docs/requirements.md`
- [x] Сформувати `docs/architecture.md`
- [x] Сформувати `docs/plan.md`
- [x] Додати `.gitignore` для Python/Odoo
- [x] Додати `requirements.txt`

---

## Milestone 1: Scaffolding модуля

- [x] Створити `vd_data_migration/` у **корені репозиторію**
- [x] `__manifest__.py` — `application=True`, `depends=['base','web']`, `license='LGPL-3'`
- [x] `__init__.py` — `from . import models, wizard, services, controllers`
- [x] `models/__init__.py` — порожньо
- [x] `wizard/__init__.py` + stub-файли
- [x] `wizard/migration_wizard_views.xml` — placeholder
- [x] `services/__init__.py` — placeholder
- [x] `controllers/__init__.py` — placeholder
- [x] `security/security_groups.xml`
- [x] `security/ir.model.access.csv`
- [x] `views/menus.xml`
- [ ] Перевірити: `odoo-bin -i vd_data_migration`

---

## Milestone 2: Транзієнтні моделі (`wizard/`)

- [x] `vd.migration.field.line` — 7 полів
- [x] `vd.migration.wizard` — 16 полів + 4 method stubs
- [x] `wizard/__init__.py` — імпорти присутні
- [x] `security/ir.model.access.csv` — записи є

---

## Milestone 3: Сервіси (`services/`)

### 3.1 `JsonRpcClient` — `services/json_rpc_client.py`
- [x] `__init__`: url, db, login, password, `_session_id=None`, `_uid=None`
- [x] `authenticate()` — `POST /web/session/authenticate`, зберігає `_session_id`
- [x] `_call_kw()` — `POST /web/dataset/call_kw` з Cookie header
- [x] `model_exists()` — search_count на `ir.model`
- [x] `fields_get()` — атрибути `string`, `type`, `relation`
- [x] `search_count()` — повертає `int`
- [x] `search_read()` — батчинг `offset` + `limit`
- [x] Обробка: `socket.timeout`, `URLError`, JSON error → `UserError`
- [x] `_logger.info/error` для всіх RPC-операцій
- [x] `_handle_rpc_error()` — перевіряє JSON-RPC error field

### 3.2 `FieldMapper` — `services/field_mapper.py`
- [x] `build_field_lines()` — `fields_get` + `env[model]._fields`
- [x] `source_exists = field_name in source_fields`
- [x] `include=True` для всіх; `one2many` → `include=False`
- [x] Повертає `list[dict]` для `field_line_ids`

### 3.3 `RecordImporter` — `services/record_importer.py`
- [x] `process_record()` — `{created, updated, errors}`
- [x] `_prepare_values()` — many2one, many2many, one2many, інші типи
- [x] `_find_local_record()` — `search([('id','=',source_id)])`
- [x] `_resolve_many2one()` — FR-08: пошук / placeholder `name='<{id}>'`
- [x] `_resolve_many2many()` — FR-09: `[(6, 0, [...])]`
- [x] `_logger.debug` для кожного запису

- [x] `services/__init__.py` — імпорти всіх 3 сервісів

---

## Milestone 4: Методи візарда

> Мета: підключити сервіси до UI-дій

### 4.1 `action_analyse()`
- [ ] `_get_rpc_client()` → authenticate → model_exists → search_count → FieldMapper
- [ ] `state = 'analysed'`

### 4.2 `action_import()`
- [ ] Перевірка state, скидання stats, `state = 'loading'`, form reload

### 4.3 `action_delete()`
- [ ] Confirm-діалог → `unlink()` → `record_count_target = 0`

---

## Milestone 5: Form view візарда

- [ ] `wizard/migration_wizard_views.xml` — повна форма згідно `docs/architecture.md` розділ 6
- [ ] Перевірити view візуально в Odoo UI

---

## Milestone 6: HTTP-контролер

- [ ] `controllers/migration_controller.py`
- [ ] `POST /vd_migration/fetch_batch`, `process_record`, `finalize`, `stop`
- [ ] Всі маршрути з `auth='user'`, помилки → JSON `{ error }`

---

## Milestone 7: JS Owl-компонент (`MigrationProgressWidget`)

- [ ] `static/src/js/migration_progress_widget.js`
- [ ] `static/src/xml/migration_progress_widget.xml`
- [ ] `static/src/css/migration_progress_widget.css`
- [ ] Зареєструвати у `__manifest__.py` → `web.assets_backend`

---

## Milestone 8: Інтеграційне тестування

- [ ] Встановити модуль на Odoo 18.0 інстанс
- [ ] Повний цикл: аналіз → завантаження → зупинка → відновлення → видалення
- [ ] Хмарні сценарії: невірні credentials, недоступний сервер, модель не існує

---

## Milestone 9: Пакування і документація

- [ ] `scripts/package.sh`
- [ ] Оновити `README.md`
- [ ] Оновити `docs/plan.md`

---

## MVP

| Milestone | Що дає |
|---|---|
| M1 | Модуль встановлюється |
| M2 | Моделі візарда описані |
| M3 | JSON-RPC, зіставлення полів, per-record обробка |
| M4 | Три кнопки працюють |
| M5 | UI візарда готовий |
| M6 | Ендпоінти для фронтенду готові |
| M7 | Прогрес + оркестрація на фронтенді |
