# Архітектура модуля `vd_data_migration`

> Версія: 0.1 | Базується на: `docs/requirements.md` v0.3

---

## 1. Загальна структура файлів

```
18.0/
└── vd_data_migration/
    ├── __init__.py
    ├── __manifest__.py
    |
    ├── models/
    │   ├── __init__.py
    │   ├── migration_wizard.py        # TransientModel — головний візард
    │   └── migration_field_line.py    # TransientModel — рядок таблиці полів
    |
    ├── services/
    │   ├── __init__.py
    │   ├── rpc_client.py              # XML-RPC підключення і операції
    │   ├── field_mapper.py            # Зіставлення полів source/target
    │   └── record_importer.py         # Основна логіка імпорту
    |
    ├── controllers/
    │   ├── __init__.py
    │   └── migration_controller.py    # JSON-RPC ендпоінт для JS-віджета
    |
    ├── views/
    │   ├── migration_wizard_views.xml # Form view візарда
    │   └── menus.xml                  # Меню + action
    |
    ├── security/
    │   ├── security_groups.xml        # Група доступу
    │   └── ir.model.access.csv        # Права CRUD
    |
    └── static/
        ├── description/
        │   └── icon.png
        └── src/
            ├── js/
            │   └── migration_progress_widget.js  # Owl-компонент прогрес-бара
            ├── xml/
            │   └── migration_progress_widget.xml # OWL-шаблон віджета
            └── css/
                └── migration_progress_widget.css
```

---

## 2. Опис моделей

### 2.1 `vd.migration.wizard` — `migration_wizard.py`

`TransientModel` — головна модель візарда.

```
Поля:
┌────────────────────┬────────────────┬──────────────────────────────┐
| Назва             | Тип           | Опис                         |
├────────────────────┼────────────────┼──────────────────────────────┤
| source_url         | Char           | URL бази-джерела              |
| source_db          | Char           | Назва БД                      |
| source_login       | Char           | Логін                          |
| source_password    | Char           | Пароль (password=True)         |
| target_model_id    | Many2one       | ir.model (поточна БД)          |
| field_line_ids     | One2many       | vd.migration.field.line        |
| record_count_source| Integer        | read-only, з джерела         |
| record_count_target| Integer        | read-only, поточна БД        |
| progress           | Integer        | 0-100, для прогрес-бара     |
| progress_label     | Char           | «X / N записів»               |
| state              | Selection      | draft/analysed/loading/done    |
└────────────────────┴────────────────┴──────────────────────────────┘

Методи:
- action_analyse()     → викликає RpcClient + FieldMapper, заповнює field_line_ids
- action_import()      → викликає RecordImporter, оновлює progress
- action_delete()      → діалог підтвердження, unlink()
- action_stop()        → встановлює _stop_requested = True
- _get_rpc_client()    → створює і повертає RpcClient
```

---

### 2.2 `vd.migration.field.line` — `migration_field_line.py`

`TransientModel` — один рядок таблиці полів (One2many об’єкт wizard).

```
Поля:
┌──────────────┬───────────────┬────────────────────────────────────┐
| Назва       | Тип          | Опис                               |
├──────────────┼───────────────┼────────────────────────────────────┤
| wizard_id    | Many2one      | Зв’язок на vd.migration.wizard    |
| field_name   | Char          | Технічна назва поля             |
| field_label  | Char          | Мітка (string)                   |
| field_type   | Char          | Тип поля                        |
| source_exists| Boolean       | read-only                          |
| include      | Boolean       | Увімкнути в міграцію          |
| comodel      | Char          | Пов’язана модель (M2O/M2M)    |
└──────────────┴───────────────┴────────────────────────────────────┘
```

---

## 3. Опис сервісів (`services/`)

### 3.1 `RpcClient` — `rpc_client.py`

Інкапсулює з’єднання з Odoo через `xmlrpc.client`.

```python
class RpcClient:
    def __init__(self, url: str, db: str, login: str, password: str): ...
    def authenticate(self) -> int:               # повертає uid
    def fields_get(self, model: str) -> dict:    # поля моделі
    def search_count(self, model: str) -> int:   # кількість записів
    def model_exists(self, model: str) -> bool:  # чи існує модель
    def search_read(self, model: str, fields: list,
                    offset: int, limit: int) -> list:  # читання батча
```

Обробка помилок:
- `ConnectionError` — недоступність сервера
- `AuthenticationError` — невірні credentials
- `socket.timeout` — таймаут
Всі помилки логуються через `_logger` і перекидаються як `UserError`.

---

### 3.2 `FieldMapper` — `field_mapper.py`

Зіставляє поля джерела з полями поточної БД.

```python
class FieldMapper:
    def __init__(self, rpc: RpcClient, env): ...
    def build_field_lines(self, model_name: str) -> list[dict]:
        # 1. fields_get() з джерела
        # 2. fields_get() з поточної БД (через env[model]._fields)
        # 3. Зіставлення: source_exists = field в source_fields
        # 4. include = True для всіх, крім one2many → False
        # 5. Повернути list[dict] для запису у field_line_ids
```

---

### 3.3 `RecordImporter` — `record_importer.py`

Основна логіка імпорту записів.

```python
class RecordImporter:
    BATCH_SIZE = 100

    def __init__(self, rpc: RpcClient, env, wizard): ...

    def run(self, model_name: str, field_lines: list) -> dict:
        # Повертає: {'created': N, 'updated': N, 'errors': N}

    def _process_batch(self, model_name: str, records: list,
                       field_lines: list) -> None: ...

    def _prepare_values(self, record: dict, field_lines: list) -> dict:
        # Перетворює запис з source в dict для write/create

    def _resolve_many2one(self, comodel: str, source_id: int) -> int:
        # FR-08: пошук / створення запису за id

    def _resolve_many2many(self, comodel: str, source_ids: list) -> list:
        # FR-09: застосовує _resolve_many2one для кожного id

    def _find_local_record(self, model_name: str, source_id: int) -> int | None:
        # Пошук запису по id у поточній БД
```

---

## 4. Контролер (`controllers/migration_controller.py`)

Надає HTTP JSON-ендпоінт для полингу прогресу з JS-віджета:

```
GET /vd_migration/progress/<wizard_id>
    → {'progress': 42, 'label': '42 / 100 записів',
       'state': 'loading', 'created': 40, 'updated': 2, 'errors': 0}

POST /vd_migration/stop/<wizard_id>
    → {'ok': True}
```

Авторизація: `auth='user'`. Поверка по `group_system`.

---

## 5. JS Owl-віджет (`MigrationProgressWidget`)

Реалізується як **Owl-компонент** (Odoo 18 — Owl 2).

```
Стан:
- wizardId    — id запису wizard з DOM-атрибута
- progress    — 0–100
- label       — 'X / N записів'
- state       — idle | loading | done | stopped | error
- stats       — {created, updated, errors}

Методи:
- startPolling()     — setInterval 1s → GET /vd_migration/progress/<id>
- stopPolling()      — clearInterval
- onStop()           — POST /vd_migration/stop/<id>
- onImportStart()    — слухає подію 'vd_migration_start' з Form

Шаблон (XML):
<div class="vd-progress-bar">
  <div class="progress-track">
    <div class="progress-fill" style="width: {progress}%"/>
  </div>
  <span>{label}</span>
  <span class="badge">{state}</span>
  <button t-if="state === 'loading'" t-on-click="onStop">Зупинити</button>
</div>
```

Інтеграція з form view: поле `progress` огорнуте як `widget="vd_migration_progress"`.

---

## 6. Views — Структура форми

```xml
<!-- migration_wizard_views.xml -->
<form>
  <!-- Блок 1: Підключення -->
  <group string="Підключення до джерела">
    <field name="source_url"/>
    <field name="source_db"/>
    <field name="source_login"/>
    <field name="source_password" password="True"/>
  </group>

  <!-- Блок 2: Вибір моделі -->
  <group string="Модель">
    <field name="target_model_id"/>
    <field name="record_count_source" readonly="1"/>
    <field name="record_count_target" readonly="1"/>
  </group>

  <!-- Кнопка Аналізувати -->
  <button name="action_analyse" string="Аналізувати"
          type="object" class="btn-primary"/>

  <!-- Блок 3: Таблиця полів -->
  <field name="field_line_ids">
    <tree editable="bottom">
      <field name="field_name" readonly="1"/>
      <field name="field_label" readonly="1"/>
      <field name="field_type" readonly="1"/>
      <field name="source_exists" readonly="1"/>
      <field name="include"/>
      <field name="comodel" readonly="1"/>
    </tree>
  </field>

  <!-- Блок 4: Прогрес-бар (кастомний віджет) -->
  <field name="progress" widget="vd_migration_progress"
         invisible="state not in ['loading','done','stopped']"/>

  <!-- Футер: кнопки -->
  <footer>
    <button name="action_import" string="Завантажити"
            type="object" class="btn-primary"
            invisible="state != 'analysed'"/>
    <button name="action_delete" string="Видалити"
            type="object" class="btn-danger"
            invisible="not target_model_id"/>
    <button string="Закрити" class="btn-secondary"
            special="cancel"/>
  </footer>
</form>
```

---

## 7. Стани візарда (`state`)

```
draft ──[action_analyse OK]──→ analysed
                                  |
                         [action_import]
                                  |
                              loading ──[action_stop]─→ stopped
                                  |
                              [done]
                                  |
                               done
Любий стан + помилка → state залишається, показується UserError
```

---

## 8. Маніфест `__manifest__.py`

```python
{
    'name': 'VD Data Migration',
    'version': '18.0.1.0.0',
    'category': 'Tools',
    'summary': 'Migrate data between Odoo 18.0 instances via XML-RPC',
    'author': 'Vlad Lavrenko',
    'depends': ['base', 'web'],
    'application': True,
    'installable': True,
    'data': [
        'security/security_groups.xml',
        'security/ir.model.access.csv',
        'views/migration_wizard_views.xml',
        'views/menus.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'vd_data_migration/static/src/js/migration_progress_widget.js',
            'vd_data_migration/static/src/xml/migration_progress_widget.xml',
            'vd_data_migration/static/src/css/migration_progress_widget.css',
        ],
    },
}
```

---

## 9. Security

```
Група: vd_data_migration.group_migration_user
  → інхеритує base.group_user
  → доступ: візард (читання + запис)

Група: vd_data_migration.group_migration_admin
  → інхеритує group_migration_user
  → додатково: право видалення (unlink)

ir.model.access.csv:
  wizard      — group_migration_user: CRUD
  field_line  — group_migration_user: CRUD
```

---

## 10. Потік даних (Data Flow)

```
[Odoo UI — Form]
     |
     | натиск «Аналізувати»
     ▼
[migration_wizard.action_analyse()]
     → RpcClient.authenticate()
     → RpcClient.model_exists()
     → RpcClient.fields_get()       ←── source DB (XML-RPC)
     → FieldMapper.build_field_lines()
     → заповнює field_line_ids, counts
     → state = 'analysed'
     |
     | натиск «Завантажити»
     ▼
[migration_wizard.action_import()]
     → RecordImporter.run()
          → loop батчами по 100:
               → RpcClient.search_read()    ←── source DB
               → _prepare_values()
                    → _resolve_many2one()   → env[comodel].search/create
                    → _resolve_many2many()
               → env[model].search(id)
               → write() або create()
               → wizard.progress += batch%
               → перевірка _stop_requested
     |
[JS MigrationProgressWidget]
     → polling GET /vd_migration/progress/<id> кожну 1с
     → оновлює полоску, лічильник, статус
     → кнопка «Зупинити» → POST /vd_migration/stop/<id>
```

---

## 11. Ключові архітектурні рішення

| Задача | Рішення |
|---|---|
| Прогрес у реальному часі | Owl-віджет + polling JSON |
| Зупинка | Флаг `_stop_requested` в wizard + POST endpoint |
| Пароль не зберігається | `TransientModel` (чиститься автоматично) |
| Many2one/Many2many | `_resolve_many2one` з кешем локальних ID |
| Батчинг | `BATCH_SIZE = 100` у `RecordImporter` |
| Безпека | `auth='user'` + перевірка `group_system` в controller |
