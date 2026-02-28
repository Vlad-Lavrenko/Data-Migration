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

> Мета: створити порожню структуру модуля, яка встановлюється без помилок

- [x] Створити `vd_data_migration/` у **корені репозиторію**
- [x] `__manifest__.py` — `application=True`, `depends=['base','web']`, `license='LGPL-3'`
- [x] `__init__.py` — `from . import models, wizard, services, controllers`
- [x] `models/__init__.py` — порожньо, готово до розширення
- [x] `wizard/__init__.py` + stub-файли `migration_wizard.py`, `migration_field_line.py`
- [x] `wizard/migration_wizard_views.xml` — placeholder form view (у `wizard/`, не в `views/`)
- [x] `services/__init__.py` — placeholder
- [x] `controllers/__init__.py` — placeholder
- [x] `security/security_groups.xml` — `group_migration_user` + `group_migration_admin`
- [x] `security/ir.model.access.csv` — базові права (wizard + field_line)
- [x] `views/menus.xml` — пункт меню «Міграція» + `ir.actions.act_window`
- [ ] Перевірити: модуль встановлюється без помилок (`odoo-bin -i vd_data_migration`)

---

## Milestone 2: Транзієнтні моделі (`wizard/`)

> Мета: описати структуру даних візарда

### 2.1 `vd.migration.field.line`
- [x] Поля: `wizard_id`, `field_name`, `field_label`, `field_type`, `source_exists`, `include`, `comodel`
- [x] `wizard/__init__.py` — імпорт присутній
- [x] Запис у `security/ir.model.access.csv` вже єсть

### 2.2 `vd.migration.wizard`
- [x] Поля підключення: `source_url`, `source_db`, `source_login`, `source_password`, `source_session_id`
- [x] Поля вибору: `target_model_id`, `record_count_source`, `record_count_target`
- [x] Поле початку: `start_batch_number` (Integer, default=1)
- [x] Поля прогресу: `progress`, `progress_label`, `state` (draft/analysed/loading/done/stopped)
- [x] Поля статистики: `stats_created`, `stats_updated`, `stats_errors`
- [x] One2many: `field_line_ids`
- [x] Порожні заголовки методів: `action_analyse`, `action_import`, `action_delete`, `_get_rpc_client`

---

## Milestone 3: Сервіси (`services/`)

> Мета: реалізувати бізнес-логіку без ORM-залежності

### 3.1 `JsonRpcClient` — `services/json_rpc_client.py`
- [ ] `authenticate()`, `_call_kw()`, `model_exists()`, `fields_get()`, `search_count()`, `search_read()`
- [ ] Обробка помилок: `socket.timeout`, `URLError`, JSON error → `UserError`
- [ ] `_logger.info/error` для всіх RPC-операцій

### 3.2 `FieldMapper` — `services/field_mapper.py`
- [ ] `build_field_lines()` — поля джерела + поточної БД, зіставлення, `include`

### 3.3 `RecordImporter` — `services/record_importer.py`
- [ ] `process_record()`, `_prepare_values()`, `_find_local_record()`
- [ ] `_resolve_many2one()` (FR-08), `_resolve_many2many()` (FR-09)
- [ ] `_logger.debug` для кожного запису

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

> Мета: замінити placeholder на повну форму згідно `docs/architecture.md` розділ 6

- [ ] `wizard/migration_wizard_views.xml` — замінити placeholder на повну форму:
  - [ ] Блок «Підключення до джерела» (4 поля)
  - [ ] Блок «Модель та параметри» (`target_model_id`, лічильники, `start_batch_number`)
  - [ ] Кнопка «Аналізувати» (`btn-primary`)
  - [ ] Таблиця `field_line_ids` (6 колонок, `invisible` при `state='draft'`)
  - [ ] Поле `progress` з `widget="vd_migration_progress"` (invisible по state)
  - [ ] Footer: «Завантажити», «Видалити», «Закрити»
- [ ] Перевірити view візуально в Odoo UI

---

## Milestone 6: HTTP-контролер

> Мета: надати ендпоінти для Owl-компонента

- [ ] `controllers/migration_controller.py`
- [ ] `POST /vd_migration/fetch_batch` — `{ records, total }`
- [ ] `POST /vd_migration/process_record` — `{ created, updated, errors }`
- [ ] `POST /vd_migration/finalize` — `{ ok: True }`
- [ ] `POST /vd_migration/stop/<wizard_id>` — запасний
- [ ] Всі маршрути з `auth='user'`, помилки → JSON `{ error }`

---

## Milestone 7: JS Owl-компонент (`MigrationProgressWidget`)

> Мета: реалізувати оркестратор міграції на фронтенді з per-record прогресом

- [ ] `static/src/js/migration_progress_widget.js` — Owl 2, подвійний цикл
- [ ] `static/src/xml/migration_progress_widget.xml` — шаблон
- [ ] `static/src/css/migration_progress_widget.css` — стилі
- [ ] Зареєструвати у `__manifest__.py` → `web.assets_backend`

---

## Milestone 8: Інтеграційне тестування

- [ ] Встановити модуль на Odoo 18.0 інстанс
- [ ] Повний цикл: аналіз → завантаження → зупинка → відновлення → видалення
- [ ] Хмарні сценарії: невірні credentials, недоступний сервер, модель не існує

---

## Milestone 9: Пакування і документація

- [ ] `scripts/package.sh` — збірка ZIP
- [ ] Оновити `README.md` з інструкцією встановлення
- [ ] Оновити `docs/plan.md` (позначити виконані задачі)

---

## MVP (мінімально робочий модуль)

| Milestone | Що дає |
|---|---|
| M1 | Модуль встановлюється (`vd_data_migration/` у корені репо) |
| M2 | Моделі візарда описані (включно з `start_batch_number`) |
| M3 | JSON-RPC, зіставлення полів, per-record обробка |
| M4 | Три кнопки працюють |
| M5 | UI візарда готовий (`wizard/migration_wizard_views.xml`) |
| M6 | Ендпоінти для фронтенду готові |
| M7 | Прогрес по запису + лічильник пакетів + оркестрація на фронтенді |
