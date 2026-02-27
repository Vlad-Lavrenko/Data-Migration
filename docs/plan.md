# План розробки модуля `vd_data_migration`

> Базується на: `docs/requirements.md` v0.4 | `docs/architecture.md` v0.3

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

- [ ] Створити `18.0/vd_data_migration/`
- [ ] `__manifest__.py` — `application=True`, `depends=['base','web']`, JSON-RPC summary
- [ ] `__init__.py` — `from . import models, wizard, services, controllers`
- [ ] `models/__init__.py` — порожньо, готово до розширення
- [ ] `wizard/__init__.py`
- [ ] `services/__init__.py`
- [ ] `controllers/__init__.py`
- [ ] `security/security_groups.xml` — `group_migration_user` + `group_migration_admin`
- [ ] `security/ir.model.access.csv` — базові права (wizard + field_line)
- [ ] `views/menus.xml` — пункт меню «Міграція» + `ir.actions.act_window`
- [ ] Перевірити: модуль встановлюється без помилок (`odoo-bin -i vd_data_migration`)

---

## Milestone 2: Транзієнтні моделі (`wizard/`)

> Мета: описати структуру даних візарда

### 2.1 `vd.migration.field.line`
- [ ] Файл `wizard/migration_field_line.py`
- [ ] Поля: `wizard_id`, `field_name`, `field_label`, `field_type`, `source_exists`, `include`, `comodel`
- [ ] Додати до `wizard/__init__.py`
- [ ] Додати запис у `security/ir.model.access.csv`

### 2.2 `vd.migration.wizard`
- [ ] Файл `wizard/migration_wizard.py`
- [ ] Поля підключення: `source_url`, `source_db`, `source_login`, `source_password`, `source_session_id`
- [ ] Поля вибору: `target_model_id`, `record_count_source`, `record_count_target`
- [ ] Поля прогресу: `progress`, `progress_label`, `state` (Selection: draft/analysed/loading/done/stopped)
- [ ] Поля статистики: `stats_created`, `stats_updated`, `stats_errors`
- [ ] One2many: `field_line_ids`
- [ ] Порожні заголовки методів: `action_analyse`, `action_import`, `action_delete`, `_get_rpc_client`
- [ ] Додати до `wizard/__init__.py`
- [ ] Додати запис у `security/ir.model.access.csv`

---

## Milestone 3: Сервіси (`services/`)

> Мета: реалізувати бізнес-логіку без ORM-залежності

### 3.1 `JsonRpcClient` — `services/json_rpc_client.py`
- [ ] `__init__`: `url`, `db`, `login`, `password`, `_session_id = None`, `_uid = None`
- [ ] `authenticate()` — `POST /web/session/authenticate`, зберігає `_session_id`, кидає `UserError` при невдачі
- [ ] `_call_kw()` — `POST /web/dataset/call_kw` з Cookie header, розбирає JSON-відповідь
- [ ] `model_exists()` — `search_count` на `ir.model`
- [ ] `fields_get()` — повертає `dict` з атрибутами `string`, `type`, `relation`
- [ ] `search_count()` — повертає `int`
- [ ] `search_read()` — батчинг з `offset` + `limit`
- [ ] Обробка помилок: `socket.timeout`, `URLError`, JSON error field → `UserError`
- [ ] `_logger.info/error` для всіх RPC-операцій

### 3.2 `FieldMapper` — `services/field_mapper.py`
- [ ] `build_field_lines()` — поля джерела (`rpc.fields_get`) + поточної БД (`env[model]._fields`)
- [ ] Зіставлення: `source_exists = field_name in source_fields`
- [ ] `include = True` для всіх; `one2many` → `include = False`
- [ ] Повертає `list[dict]` для запису через `field_line_ids`

### 3.3 `RecordImporter` — `services/record_importer.py`
- [ ] `process_batch(model_name, records, field_lines)` — повертає `{created, updated, errors}`
- [ ] `_prepare_values(record, field_lines)` — розбір полів за типом
- [ ] `_find_local_record(model_name, source_id)` — `env[model].search([('id','=',source_id)])`
- [ ] `_resolve_many2one(comodel, source_id)` — пошук/створення за FR-08
- [ ] `_resolve_many2many(comodel, source_ids)` — список → `[(6, 0, [...])]` за FR-09
- [ ] Логування кожного батчу: `_logger.info('Batch: +created, ~updated, !errors')`

---

## Milestone 4: Методи візарда

> Мета: підключити сервіси до UI-дій

### 4.1 `action_analyse()`
- [ ] `_get_rpc_client()` → `JsonRpcClient(url, db, login, password)`
- [ ] `rpc.authenticate()` → зберегти `source_session_id` у wizard
- [ ] `rpc.model_exists()` → `UserError` якщо ні
- [ ] `rpc.search_count()` → `record_count_source`
- [ ] `env[model].search_count([])` → `record_count_target`
- [ ] `FieldMapper.build_field_lines()` → очистити + записати `field_line_ids`
- [ ] `state = 'analysed'`

### 4.2 `action_import()`
- [ ] Перевірити `state == 'analysed'` → `UserError` якщо ні
- [ ] Скинути `stats_created = stats_updated = stats_errors = 0`
- [ ] `state = 'loading'`, `progress = 0`
- [ ] Повернути `{'type': 'ir.actions.act_window', 'res_id': self.id, ...}` (form reload)

### 4.3 `action_delete()`
- [ ] Перевірити `target_model_id` заповнено
- [ ] Повернути confirm-діалог
- [ ] `env[model].search([]).unlink()`
- [ ] `record_count_target = 0`

---

## Milestone 5: Form view візарда

> Мета: створити UI згідно `docs/architecture.md` розділ 6

- [ ] `views/migration_wizard_views.xml`
  - [ ] Блок «Підключення до джерела» (4 поля)
  - [ ] Блок «Модель» (`target_model_id`, read-only лічильники)
  - [ ] Кнопка «Аналізувати» (`btn-primary`)
  - [ ] Таблиця `field_line_ids` (6 колонок, `invisible` при `state='draft'`)
  - [ ] Поле `progress` з `widget="vd_migration_progress"` (invisible по state)
  - [ ] Footer: «Завантажити» (invisible якщо не analysed), «Видалити», «Закрити»
- [ ] `views/menus.xml` — пункт меню + `ir.actions.act_window`
- [ ] Перевірити view візуально в Odoo UI

---

## Milestone 6: HTTP-контролер

> Мета: надати ендпоінти для Owl-компонента

- [ ] `controllers/migration_controller.py`
- [ ] `POST /vd_migration/fetch_batch`
  - [ ] Читає `wizard.source_session_id`, `field_line_ids` (include=True)
  - [ ] Викликає `JsonRpcClient.search_read(offset, 100)`
  - [ ] Повертає `{ records: [...], total: N }`
- [ ] `POST /vd_migration/process_batch`
  - [ ] Читає wizard, field_lines
  - [ ] Викликає `RecordImporter.process_batch()`
  - [ ] Повертає `{ created, updated, errors }`
- [ ] `POST /vd_migration/finalize`
  - [ ] Оновлює `wizard.state`, `stats_*`, `progress`
  - [ ] Повертає `{ ok: True }`
- [ ] `POST /vd_migration/stop/<wizard_id>` — запасний
- [ ] Всі маршрути з `auth='user'`
- [ ] Обробка помилок: wizard не знайдено → `{ error: 'not_found' }`

---

## Milestone 7: JS Owl-компонент (`MigrationProgressWidget`)

> Мета: реалізувати оркестратор міграції на фронтенді

- [ ] `static/src/js/migration_progress_widget.js`
  - [ ] Owl 2 компонент, `useState` для `progress`, `label`, `status`, `stats`
  - [ ] `onWillStart()` — авто-старт якщо `state == 'loading'`
  - [ ] `startImport()` — головний import-цикл (fetch → process → repeat)
  - [ ] Завершення циклу при `records.length == 0`
  - [ ] `onStop()` — `this._stopped = true`
  - [ ] `_fetchBatch()` — `POST /vd_migration/fetch_batch`
  - [ ] `_processBatch()` — `POST /vd_migration/process_batch`
  - [ ] `_finalize()` — `POST /vd_migration/finalize`
  - [ ] `_mergeStats()` — накопичення статистики
  - [ ] Реєстрація: `registry.category('fields').add('vd_migration_progress', ...)`
- [ ] `static/src/xml/migration_progress_widget.xml`
  - [ ] Полоска з `progress-fill` (ширина через `t-attf-style`)
  - [ ] Лічильник `X / N записів`
  - [ ] Бейдж статусу
  - [ ] Кнопка «Зупинити» (тільки при `status='loading'`)
  - [ ] Блок фінальної статистики (при `done`/`stopped`)
- [ ] `static/src/css/migration_progress_widget.css` — стилі полоски
- [ ] Зареєструвати у `__manifest__.py` → `web.assets_backend`
- [ ] Перевірити: прогрес оновлюється після кожного батчу без перезавантаження

---

## Milestone 8: Інтеграційне тестування

> Мета: перевірити повний цикл з UI

- [ ] Встановити модуль на Odoo 18.0 інстанс
- [ ] Відкрити меню «Міграція» — перевірити візард
- [ ] Ввести дані підключення, обрати модель → «Аналізувати»
  - [ ] Таблиця полів заповнена, `source_exists` правильно
- [ ] «Завантажити» → прогрес-бар оновлюється в реальному часі
- [ ] «Зупинити» → цикл зупиняється після поточного батчу
- [ ] Перезапустити «Завантажити» → продовжує (або з нуля)
- [ ] «Видалити» → діалог підтвердження + unlink
- [ ] Хмарні сценарії:
  - [ ] Невірні credentials → UserError «Невірний логін/пароль»
  - [ ] Недоступний сервер → UserError «Сервер недоступний»
  - [ ] Модель не існує в source → UserError
  - [ ] Many2one запис відсутній в target → створюється з `name="<{id}>"`

---

## Milestone 9: Пакування і документація

- [ ] `scripts/package.sh` — збірка ZIP
- [ ] Оновити `README.md` з інструкцією встановлення
- [ ] Оновити `docs/plan.md` (позначити виконані задачі)

---

## MVP (мінімально робочий модуль)

Модуль вважається готовим після завершення Milestone 1–6:

| Milestone | Що дає |
|---|---|
| M1 | Модуль встановлюється |
| M2 | Моделі візарда описані |
| M3 | JSON-RPC, зіставлення полів, обробка батчів |
| M4 | Три кнопки працюють |
| M5 | UI візарда готовий |
| M6 | Ендпоінти для фронтенду готові |
| M7 | Прогрес-бар + оркестрація на фронтенді |
