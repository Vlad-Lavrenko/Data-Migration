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

- [x] `vd_data_migration/` у корені репозиторію
- [x] `__manifest__.py`, `__init__.py`
- [x] `wizard/__init__.py` + stubs
- [x] `services/__init__.py`, `controllers/__init__.py`
- [x] `security/security_groups.xml`, `ir.model.access.csv`
- [x] `views/menus.xml`
- [ ] Перевірити: `odoo-bin -i vd_data_migration`

---

## Milestone 2: Транзієнтні моделі (`wizard/`)

- [x] `vd.migration.field.line` — 7 полів
- [x] `vd.migration.wizard` — 16 полів
- [x] `wizard/__init__.py`, `security/ir.model.access.csv`

---

## Milestone 3: Сервіси (`services/`)

- [x] `JsonRpcClient` — `authenticate`, `_call_kw`, `model_exists`, `fields_get`, `search_count`, `search_read`
- [x] `FieldMapper` — `build_field_lines`
- [x] `RecordImporter` — `process_record`, `_prepare_values`, `_find_local_record`, `_resolve_many2one`, `_resolve_many2many`
- [x] `services/__init__.py`

---

## Milestone 4: Методи візарда

- [x] `action_analyse()` — validate → rpc → model_exists → counts → FieldMapper → state='analysed'
- [x] `action_import()` — reset stats → state='loading' → form reload
- [x] `action_delete()` — unlink → count=0 → display_notification
- [x] `_get_rpc_client()`, `_validate_connection_fields()`

---

## Milestone 5: Form view візарда

- [x] `<field name="state" invisible="1"/>` — домен-приховання
- [x] Блок «Підключення до джерела» — 4 поля `required="1"`, hidden при `loading`
- [x] Блок «Модель та параметри» — `target_model_id`, лічильники, `start_batch_number`, hidden при `loading`
- [x] Кнопка «Аналізувати» (`btn-primary`), hidden при `loading`
- [x] Таблиця `field_line_ids` — 6 колонок, `editable="bottom"`, `create/delete="false"`, `boolean_toggle` для boolean-полів, hidden при `draft`
- [x] `<field name="progress" widget="vd_migration_progress" .../>` — hidden поки не `loading/done/stopped`
- [x] Footer: «Завантажити», «Видалити» + `confirm="..."`, «Закрити»
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
