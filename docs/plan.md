# План розробки модуля `vd_data_migration`

> Базується на: `docs/requirements.md` v0.5 | `docs/architecture.md` v0.4

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
- [ ] Поле початку: `start_batch_number` (Integer, default=1, string='Початковий номер пакету')
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
- [ ] `process_record(model_name, record, field_lines)` — повертає `{created: 0|1, updated: 0|1, errors: 0|1}`
- [ ] `_prepare_values(record, field_lines)` — розбір полів за типом
- [ ] `_find_local_record(model_name, source_id)` — `env[model].search([('id','=',source_id)])`
- [ ] `_resolve_many2one(comodel, source_id)` — пошук/створення за FR-08
- [ ] `_resolve_many2many(comodel, source_ids)` — список → `[(6, 0, [...])]` за FR-09
- [ ] Логування кожного запису: `_logger.debug('Record %s: %s', record_id, status)`

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
  - [ ] Блок «Модель та параметри» (`target_model_id`, read-only лічильники, `start_batch_number`)
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
- [ ] `POST /vd_migration/process_record`
  - [ ] Читає wizard + field_line_ids
  - [ ] Викликає `RecordImporter.process_record(model, record, field_lines)`
  - [ ] Повертає `{ created: 0|1, updated: 0|1, errors: 0|1 }`
  - [ ] При винятку: повертає `{ created: 0, updated: 0, errors: 1 }` (не кидає 500)
- [ ] `POST /vd_migration/finalize`
  - [ ] Оновлює `wizard.state`, `stats_*`, `progress`
  - [ ] Повертає `{ ok: True }`
- [ ] `POST /vd_migration/stop/<wizard_id>` — запасний
- [ ] Всі маршрути з `auth='user'`
- [ ] Обробка помилок: wizard не знайдено → `{ error: 'not_found' }`

---

## Milestone 7: JS Owl-компонент (`MigrationProgressWidget`)

> Мета: реалізувати оркестратор міграції на фронтенді з per-record прогресом

- [ ] `static/src/js/migration_progress_widget.js`
  - [ ] Owl 2 компонент, `useState` для `progress`, `label`, `status`, `batchesLoaded`, `currentBatchNo`, `stats`
  - [ ] `onWillStart()` — авто-старт якщо `state == 'loading'`
  - [ ] `startImport()` — ініціалізація: `offset = (start_batch_number − 1) × 100`
  - [ ] Зовнішній цикл `while (!this._stopped)` — по батчах
  - [ ] `_fetchBatch()` → `POST /vd_migration/fetch_batch`
  - [ ] Внутрішній цикл `for (const record of records)` — по записах
  - [ ] Перевірка `this._stopped` на початку внутрішнього циклу (`break outer`)
  - [ ] `_processRecord()` → `POST /vd_migration/process_record`
  - [ ] Оновлення `state.progress` та `state.label` **після кожного запису**
  - [ ] Після завершення батчу: `state.batchesLoaded += 1`, `state.currentBatchNo += 1`
  - [ ] `onStop()` — `this._stopped = true`
  - [ ] `_finalize()` → `POST /vd_migration/finalize`
  - [ ] `_mergeStats()` — накопичення created/updated/errors
  - [ ] Реєстрація: `registry.category('fields').add('vd_migration_progress', ...)`
- [ ] `static/src/xml/migration_progress_widget.xml`
  - [ ] Полоска з `progress-fill` (ширина через `t-attf-style`)
  - [ ] Лічильник записів `X / N записів`
  - [ ] Бейдж статусу
  - [ ] Кнопка «Зупинити» (тільки при `status='loading'`)
  - [ ] **Лічильник пакетів** під прогрес-баром: `Пакетів завантажено: X (поточний №Y)`
  - [ ] Блок фінальної статистики (при `done`/`stopped`)
- [ ] `static/src/css/migration_progress_widget.css` — стилі полоски та лічильника
- [ ] Зареєструвати у `__manifest__.py` → `web.assets_backend`
- [ ] Перевірити: прогрес оновлюється **після кожного запису** без перезавантаження
- [ ] Перевірити: «Зупинити» зупиняє після **поточного запису** (не батчу)

---

## Milestone 8: Інтеграційне тестування

> Мета: перевірити повний цикл з UI

- [ ] Встановити модуль на Odoo 18.0 інстанс
- [ ] Відкрити меню «Міграція» — перевірити візард
- [ ] Ввести дані підключення, обрати модель → «Аналізувати»
  - [ ] Таблиця полів заповнена, `source_exists` правильно
- [ ] «Завантажити» (start_batch_number=1) → прогрес-бар оновлюється після кожного запису
- [ ] Перевірити лічильник пакетів під прогрес-баром
- [ ] «Зупинити» → зупиняється після поточного **запису**
- [ ] Перезапустити з start_batch_number=3 → offset починається з 200
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

Модуль вважається готовим після завершення Milestone 1–7:

| Milestone | Що дає |
|---|---|
| M1 | Модуль встановлюється |
| M2 | Моделі візарда описані (включно з `start_batch_number`) |
| M3 | JSON-RPC, зіставлення полів, per-record обробка |
| M4 | Три кнопки працюють |
| M5 | UI візарда готовий |
| M6 | Ендпоінти для фронтенду готові |
| M7 | Прогрес по запису + лічильник пакетів + оркестрація на фронтенді |
