# План розробки модуля `vd_data_migration`

> Базується на: `docs/requirements.md` v0.3 | `docs/architecture.md` v0.2

## Статуси
- `[ ]` — не розпочато
- `[~]` — в процесі
- `[x]` — виконано

---

## Milestone 0: Проектна інфраструктура

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
- [ ] `__manifest__.py` — `application=True`, `depends=['base','web']`
- [ ] `__init__.py` — `from . import models, wizard, services, controllers`
- [ ] `models/__init__.py` — порожньо, готовий до розширення
- [ ] `wizard/__init__.py`
- [ ] `services/__init__.py`
- [ ] `controllers/__init__.py`
- [ ] `security/security_groups.xml` — `group_migration_user` + `group_migration_admin`
- [ ] `security/ir.model.access.csv` — порожні права (CRUD для wizard і field_line)
- [ ] `views/menus.xml` — пункт меню «Міграція» + action для відкриття візарда
- [ ] Перевірити: модуль встановлюється без помилок (`odoo-bin -i vd_data_migration`)

---

## Milestone 2: Транзієнтні моделі (wizard/)

> Мета: описати структуру даних візарда

### 2.1 `vd.migration.field.line`
- [ ] Файл `wizard/migration_field_line.py`
- [ ] Поля: `wizard_id`, `field_name`, `field_label`, `field_type`, `source_exists`, `include`, `comodel`
- [ ] Додати до `wizard/__init__.py`

### 2.2 `vd.migration.wizard`
- [ ] Файл `wizard/migration_wizard.py`
- [ ] Поля підключення: `source_url`, `source_db`, `source_login`, `source_password`
- [ ] Поля вибору: `target_model_id`, `record_count_source`, `record_count_target`
- [ ] Поля прогресу: `progress`, `progress_label`, `state`
- [ ] Одноформне поле `field_line_ids` (One2many)
- [ ] Внутрішній атрибут `_stop_requested = False`
- [ ] Порожні заголовки методів: `action_analyse`, `action_import`, `action_delete`, `action_stop`, `_get_rpc_client`
- [ ] Додати до `wizard/__init__.py`
- [ ] Додати обидві моделі до `security/ir.model.access.csv`

---

## Milestone 3: Сервіси (services/)

> Мета: реалізувати бізнес-логіку відокремлено від Odoo ORM

### 3.1 `RpcClient`
- [ ] Файл `services/rpc_client.py`
- [ ] `__init__`: `url`, `db`, `login`, `password`, `_uid = None`, `_models = None`
- [ ] `authenticate()` — зберігає `uid`, піднімає `UserError` при невірних credentials
- [ ] `model_exists()` — перевірка через `ir.model` + `search_count`
- [ ] `fields_get()` — повертає `dict` з полями
- [ ] `search_count()` — повертає `int`
- [ ] `search_read()` — батчинг з `offset` + `limit`
- [ ] Обробка `socket.timeout`, `ConnectionRefusedError`, `Fault` (лог + `UserError`)

### 3.2 `FieldMapper`
- [ ] Файл `services/field_mapper.py`
- [ ] `build_field_lines()` — отримує поля source (через `rpc`) і target (через `env`)
- [ ] Зіставлення: `source_exists = field_name in source_fields`
- [ ] `include = True` для всіх полів; `one2many` → `include = False`
- [ ] Повертає `list[dict]` для запису через `field_line_ids`

### 3.3 `RecordImporter`
- [ ] Файл `services/record_importer.py`
- [ ] `BATCH_SIZE = 100`
- [ ] `run()` — головний цикл: офсет, батч, оновлення `progress`, перевірка `_stop_requested`
- [ ] `_process_batch()` — цикл по записах батчу
- [ ] `_prepare_values()` — розбір полів за типом (`char`/`many2one`/`many2many`/`one2many`)
- [ ] `_find_local_record()` — пошук за `id` у поточній БД
- [ ] `_resolve_many2one()` — пошук/створення за FR-08 (шаблон `"<{id}>"`)
- [ ] `_resolve_many2many()` — список → `[(6, 0, [...])]` за FR-09
- [ ] Логування: `_logger.info` по кожному батчу (created/updated/errors)

---

## Milestone 4: Методи візарда

> Мета: підключити сервіси до UI-дій

### 4.1 `action_analyse()`
- [ ] Викликати `_get_rpc_client()` і `authenticate()`
- [ ] Перевірити `model_exists()` — `UserError` якщо ні
- [ ] Заповнити `record_count_source` і `record_count_target`
- [ ] Викликати `FieldMapper.build_field_lines()`
- [ ] Очистити старі `field_line_ids` і записати нові
- [ ] Встановити `state = 'analysed'`

### 4.2 `action_import()`
- [ ] Перевірити `state == 'analysed'`
- [ ] Скинути `_stop_requested = False`
- [ ] Встановити `state = 'loading'`, `progress = 0`
- [ ] Викликати `RecordImporter.run()`
- [ ] Після завершення: `state = 'done'` або `'stopped'`
- [ ] Показати `notification` з підсумком

### 4.3 `action_delete()`
- [ ] Перевірити `target_model_id` заповнен
- [ ] Повернути `ir.actions.act_window` з діалогом підтвердження (confirm)
- [ ] Після підтвердження: `env[model].search([]).unlink()`
- [ ] Оновити `record_count_target = 0`

### 4.4 `action_stop()`
- [ ] Встановити `_stop_requested = True`
- [ ] Залогувати `_logger.info('Stop requested by user')`

---

## Milestone 5: Form view візарда

> Мета: створити UI згідно `docs/architecture.md` розділ 6

- [ ] `views/migration_wizard_views.xml`
  - [ ] Блок «Підключення до джерела» (4 поля)
  - [ ] Блок «Модель» (`target_model_id`, лічильники read-only)
  - [ ] Кнопка «Аналізувати» (`btn-primary`)
  - [ ] Таблиця `field_line_ids` (всі 6 колонок)
  - [ ] Поле `progress` з `widget="vd_migration_progress"` (invisible по `state`)
  - [ ] Footer: «Завантажити», «Видалити», «Закрити» (з умовами `invisible`)
- [ ] `views/menus.xml` — пункт меню + `ir.actions.act_window`
- [ ] Перевірити view візуально в Odoo UI

---

## Milestone 6: HTTP-контролер

> Мета: надати ендпоінти для JS-віджета

- [ ] `controllers/migration_controller.py`
- [ ] `GET /vd_migration/progress/<wizard_id>` → JSON з `progress`, `label`, `state`, stats
- [ ] `POST /vd_migration/stop/<wizard_id>` → викликає `action_stop()`, повертає `{'ok': True}`
- [ ] Обидва маршрути з `auth='user'`
- [ ] Обробка помилок: wizard не знайдено, невірний стан

---

## Milestone 7: JS Owl-віджет (`MigrationProgressWidget`)

> Мета: відображення прогресу у реальному часі

- [ ] `static/src/js/migration_progress_widget.js`
  - [ ] Owl 2 компонент, `useState` для `progress`, `label`, `state`, `stats`
  - [ ] `startPolling()` — `setInterval(1000)` → `GET /vd_migration/progress/<id>`
  - [ ] `stopPolling()` — `clearInterval`
  - [ ] `onStop()` — `POST /vd_migration/stop/<id>`
  - [ ] Авто-запуск `startPolling` при `state = 'loading'`
  - [ ] Авто-зупинка при `state in ['done', 'stopped', 'error']`
  - [ ] Реєстрація як польовий віджет: `widget="vd_migration_progress"`
- [ ] `static/src/xml/migration_progress_widget.xml`
  - [ ] Полоска з `progress-fill` (ширина через `style`)
  - [ ] Лічильник `X / N записів`
  - [ ] Бейдж статусу
  - [ ] Кнопка «Зупинити» (видима лише при `state = 'loading'`)
  - [ ] Блок статистики (видимий після done/stopped)
- [ ] `static/src/css/migration_progress_widget.css` — стилі полоски
- [ ] Зареєструвати в `__manifest__.py` в `assets.web.assets_backend`

---

## Milestone 8: Інтеграція і ручне тестування

> Мета: перевірити повний цикл роботи з UI

- [ ] Встановити модуль на Odoo 18.0 інстанс
- [ ] Відкрити меню «Міграція» — перевірити візард
- [ ] Ввести дані підключення, обрати модель
- [ ] Натиснути «Аналізувати» — перевірити таблицю полів
- [ ] Натиснути «Завантажити» — перевірити прогрес-бар + міграцію
- [ ] Натиснути «Зупинити» — перевірити зупинку
- [ ] Натиснути «Видалити» — перевірити діалог + видалення
- [ ] Перевірити хмарні сценарії: невірні credentials, недоступний сервер, модель не існує в source

---

## Milestone 9: Пакування і документація

- [ ] `scripts/package.sh` — збірка ZIP згідно skill `Odoo_Package_Module`
- [ ] Оновити `README.md` з інструкцією встановлення
- [ ] Оновити `docs/plan.md` (позначити виконані задачі)

---

## MVP (мінімально робочий модуль)

Модуль вважається готовим після завершення Milestone 1–6:

| Milestone | Що дає |
|---|---|
| M1 | Модуль встановлюється |
| M2 | Моделі візарда описані |
| M3 | XML-RPC працює, поля зіставлені, імпорт працює |
| M4 | Три кнопки працюють |
| M5 | UI візарда готовий |
| M6 | Ендпоінти для прогресу готові |
| M7 | Прогрес-бар в реальному часі |
