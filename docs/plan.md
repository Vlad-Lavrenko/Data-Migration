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
- [x] `__manifest__.py`
- [x] `__init__.py`
- [x] `models/__init__.py`
- [x] `wizard/__init__.py` + stub-файли
- [x] `wizard/migration_wizard_views.xml` — placeholder
- [x] `services/__init__.py`
- [x] `controllers/__init__.py`
- [x] `security/security_groups.xml`
- [x] `security/ir.model.access.csv`
- [x] `views/menus.xml`
- [ ] Перевірити: `odoo-bin -i vd_data_migration`

---

## Milestone 2: Транзієнтні моделі (`wizard/`)

- [x] `vd.migration.field.line` — 7 полів
- [x] `vd.migration.wizard` — 16 полів
- [x] `wizard/__init__.py`
- [x] `security/ir.model.access.csv`

---

## Milestone 3: Сервіси (`services/`)

- [x] `JsonRpcClient` — `authenticate`, `_call_kw`, `model_exists`, `fields_get`, `search_count`, `search_read`, `_handle_rpc_error`
- [x] `FieldMapper` — `build_field_lines`
- [x] `RecordImporter` — `process_record`, `_prepare_values`, `_find_local_record`, `_resolve_many2one`, `_resolve_many2many`
- [x] `services/__init__.py` — імпорти

---

## Milestone 4: Методи візарда

### 4.1 `action_analyse()`
- [x] `_validate_connection_fields()` — окремий helper, перевіряє 5 обов'язкових полів
- [x] `_get_rpc_client()` → authenticate → зберігає `source_session_id`
- [x] `model_exists()` → `UserError` якщо модель не існує на джерелі
- [x] `search_count` джерела + `search_count` поточної БД
- [x] `FieldMapper.build_field_lines()` → `(5,0,0)` + `(0,0,line)` записи
- [x] `state = 'analysed'`

### 4.2 `action_import()`
- [x] Перевірка `state == 'analysed'` → `UserError`
- [x] Скидання `stats_*`, `progress`, `progress_label`
- [x] `state = 'loading'`
- [x] Повертає `ir.actions.act_window` (form reload, `target='new'`)

### 4.3 `action_delete()`
- [x] Перевірка `target_model_id`
- [x] `search([]).unlink()` + `record_count_target = 0`
- [x] Повертає `display_notification` з підсумком
- [x] Confirm-діалог — через `confirm=""` на кнопці у view (M5)

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
