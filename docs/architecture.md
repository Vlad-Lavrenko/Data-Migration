# Архітектура модуля `vd_data_migration`

> Версія: 0.6 | Базується на: `docs/requirements.md` v0.5, `.rules/odoo-conventions.md`

---

## 1. Загальна структура файлів

```
<repo-root>/
├── .rules/
├── .skills/
├── docs/
├── vd_data_migration/          ← модуль у корені репозиторію
│   ├── __init__.py             # from . import models, wizard, services, controllers
│   ├── __manifest__.py
│   |
│   ├── models/                 # Тільки models.Model / AbstractModel
│   │   └── __init__.py         # (порожньо, готово до розширення)
│   |
│   ├── wizard/                 # ВСЕ що стосується wizard: TransientModel + XML views
│   │   ├── __init__.py
│   │   ├── migration_wizard.py         # TransientModel — головний візард
│   │   ├── migration_field_line.py     # TransientModel — рядок таблиці полів
│   │   └── migration_wizard_views.xml  # Form view візарда
│   |
│   ├── services/               # Чиста Python-логіка, без Odoo ORM
│   │   ├── __init__.py
│   │   ├── json_rpc_client.py  # JSON-RPC клієнт (urllib.request + json)
│   │   ├── field_mapper.py     # Зіставлення полів source/target
│   │   └── record_importer.py  # Обробка одного запису (per-record)
│   |
│   ├── controllers/
│   │   ├── __init__.py
│   │   └── migration_controller.py  # HTTP JSON ендпоінти для Owl-компонента
│   |
│   ├── views/                  # Тільки menus.xml
│   │   └── menus.xml
│   |
│   ├── security/
│   │   ├── security_groups.xml         # Групи доступу
│   │   └── ir.model.access.csv         # Права CRUD
│   |
│   └── static/
│       ├── description/
│       │   └── icon.png
│       └── src/
│           ├── js/
│           │   └── migration_progress_widget.js
│           ├── xml/
│           │   └── migration_progress_widget.xml
│           └── css/
│               └── migration_progress_widget.css
└── requirements.txt
```

> **Правило `wizard/`:** містить **все що стосується візарда** — Python-моделі (`TransientModel`) та XML views для них. `views/` містить тільки `menus.xml`.

---

## 2. Опис моделей

### 2.1 `vd.migration.wizard` — `wizard/migration_wizard.py`

`TransientModel` — головна модель візарда.

```
Поля:
┌──────────────────────┬────────────────┬──────────────────────────────────────────────────┐
| Назва               | Тип           | Опис                                             |
├──────────────────────┼────────────────┼──────────────────────────────────────────────────┤
| source_url           | Char           | URL бази-джерела                                  |
| source_db            | Char           | Назва БД                                          |
| source_login         | Char           | Логін                                              |
| source_password      | Char           | Пароль (password=True)                             |
| source_session_id    | Char           | JSON-RPC session_id (пам'ять, не в БД)            |
| target_model_id      | Many2one       | ir.model (поточна БД)                             |
| field_line_ids       | One2many       | vd.migration.field.line                           |
| record_count_source  | Integer        | read-only, з джерела                              |
| record_count_target  | Integer        | read-only, поточна БД                             |
| start_batch_number   | Integer        | Початковий номер пакету (default=1, мін=1)        |
| progress             | Integer        | 0-100, для прогрес-бара                           |
| progress_label       | Char           | «X / N записів»                                   |
| stats_created        | Integer        | Статистика: створено                               |
| stats_updated        | Integer        | Статистика: оновлено                               |
| stats_errors         | Integer        | Статистика: помилок                                |
| state                | Selection      | draft/analysed/loading/done/stopped               |
└──────────────────────┴────────────────┴──────────────────────────────────────────────────┘

Методи:
- action_analyse()       → JsonRpcClient + FieldMapper, заповнює field_line_ids, state='analysed'
- action_import()        → валідація, скидання stats, state='loading', повертає form reload
- action_delete()        → діалог підтвердження, unlink(), record_count_target=0
- _get_rpc_client()      → створює і повертає JsonRpcClient з полів wizard
```

---

### 2.2 `vd.migration.field.line` — `wizard/migration_field_line.py`

`TransientModel` — один рядок таблиці полів.

```
Поля:
┌──────────────┬───────────────┬────────────────────────────────────────┐
| Назва       | Тип          | Опис                                   |
├──────────────┼───────────────┼────────────────────────────────────────┤
| wizard_id    | Many2one      | Зв'язок на vd.migration.wizard        |
| field_name   | Char          | Технічна назва поля                   |
| field_label  | Char          | Мітка (string)                         |
| field_type   | Char          | Тип поля                               |
| source_exists| Boolean       | read-only                              |
| include      | Boolean       | Увімкнути в міграцію                   |
| comodel      | Char          | Пов'язана модель (M2O/M2M/O2M)        |
└──────────────┴───────────────┴────────────────────────────────────────┘
```

---

## 3. Опис сервісів (`services/`)

> Сервіси — чисті Python-класи без ORM-залежності. Приймають `env` як аргумент.

### 3.1 `JsonRpcClient` — `services/json_rpc_client.py`

Інкапсулює JSON-RPC 2.0 комунікацію з Odoo через `urllib.request` + `json` (тільки stdlib).

```python
class JsonRpcClient:
    def __init__(self, url: str, db: str, login: str, password: str): ...
    def authenticate(self) -> str: ...
    def _call_kw(self, model: str, method: str, args: list, kwargs: dict) -> any: ...
    def model_exists(self, model: str) -> bool: ...
    def fields_get(self, model: str) -> dict: ...
    def search_count(self, model: str) -> int: ...
    def search_read(self, model: str, fields: list, offset: int, limit: int) -> list: ...
```

Обробка помилок: `socket.timeout`, `urllib.error.URLError`, JSON-RPC `error` поле → `UserError`.

---

### 3.2 `FieldMapper` — `services/field_mapper.py`

```python
class FieldMapper:
    def __init__(self, rpc: JsonRpcClient, env): ...
    def build_field_lines(self, model_name: str) -> list[dict]: ...
```

---

### 3.3 `RecordImporter` — `services/record_importer.py`

```python
class RecordImporter:
    def __init__(self, env, wizard): ...
    def process_record(self, model_name: str, record: dict, field_lines: list) -> dict: ...
    def _prepare_values(self, record: dict, field_lines: list) -> dict: ...
    def _find_local_record(self, model_name: str, source_id: int) -> int | None: ...
    def _resolve_many2one(self, comodel: str, source_id: int) -> int: ...
    def _resolve_many2many(self, comodel: str, source_ids: list) -> list: ...
```

---

## 4. Контролер (`controllers/migration_controller.py`)

Чотири HTTP JSON-ендпоінти, всі з `auth='user'`:

```
POST /vd_migration/fetch_batch    → { records: [...], total: N }
POST /vd_migration/process_record → { created: 0|1, updated: 0|1, errors: 0|1 }
POST /vd_migration/finalize       → { ok: True }
POST /vd_migration/stop/<id>      → { ok: True }
```

---

## 5. JS Owl-компонент-оркестратор (`MigrationProgressWidget`)

Реалізується як **Owl 2 компонент** (Odoo 18.0). Подвійний цикл: зовнішній по батчах, внутрішній по записах.

```javascript
setup() {
    this.state = useState({
        progress: 0, label: '', status: 'idle',
        batchesLoaded: 0, currentBatchNo: 1,
        stats: { created: 0, updated: 0, errors: 0 },
    });
    this._stopped = false;
    onWillStart(async () => {
        if (this.props.record.data.state === 'loading') await this.startImport();
    });
}
```

Реєстрація: `registry.category('fields').add('vd_migration_progress', MigrationProgressWidget)`

---

## 6. Views — Структура форми

> Файл: `wizard/migration_wizard_views.xml`

```xml
<form string="Міграція даних">
  <group string="Підключення до джерела">
    <field name="source_url"/>
    <field name="source_db"/>
    <field name="source_login"/>
    <field name="source_password" password="True"/>
  </group>
  <group string="Модель та параметри">
    <field name="target_model_id"/>
    <field name="record_count_source" readonly="1"/>
    <field name="record_count_target" readonly="1"/>
    <field name="start_batch_number"/>
  </group>
  <button name="action_analyse" string="Аналізувати" type="object" class="btn-primary"/>
  <field name="field_line_ids" invisible="state == 'draft'">
    <tree editable="bottom">
      <field name="field_name"    readonly="1"/>
      <field name="field_label"   readonly="1"/>
      <field name="field_type"    readonly="1"/>
      <field name="source_exists" readonly="1"/>
      <field name="include"/>
      <field name="comodel"       readonly="1"/>
    </tree>
  </field>
  <field name="progress" widget="vd_migration_progress"
         invisible="state not in ['loading','done','stopped']"/>
  <footer>
    <button name="action_import" string="Завантажити" type="object" class="btn-primary"
            invisible="state != 'analysed'"/>
    <button name="action_delete" string="Видалити" type="object" class="btn-danger"
            invisible="not target_model_id"/>
    <button string="Закрити" special="cancel" class="btn-secondary"/>
  </footer>
</form>
```

---

## 7. Стани візарда (`state`)

```
draft ──[action_analyse OK]──► analysed
                                    │
                           [action_import]
                                    │
                                loading ──[this._stopped=true]──► stopped
                                    │
                          [records=0 / всі записи]
                                    │
                               [finalize]
                                    │
                                  done
```

---

## 8. Маніфест `__manifest__.py`

```python
{
    'name': 'VD Data Migration',
    'version': '18.0.1.0.0',
    'category': 'Tools',
    'summary': 'Migrate data between Odoo 18.0 instances via JSON-RPC',
    'author': 'Vlad Lavrenko',
    'depends': ['base', 'web'],
    'application': True,
    'installable': True,
    'license': 'LGPL-3',
    'data': [
        'security/security_groups.xml',
        'security/ir.model.access.csv',
        'wizard/migration_wizard_views.xml',
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
  → доступ: wizard + field_line (CRUD)

Група: vd_data_migration.group_migration_admin
  → інхеритує group_migration_user
  → додатково: право unlink на цільових моделях

ir.model.access.csv:
  vd_migration_wizard_user      — group_migration_user:  1,1,1,0
  vd_migration_wizard_admin     — group_migration_admin: 1,1,1,1
  vd_migration_field_line_user  — group_migration_user:  1,1,1,0
```

---

## 10. Потік даних (Data Flow)

```
[Odoo UI — Form]
     │ «Аналізувати»
     ▼
[wizard.action_analyse()] → JsonRpcClient → source DB
     → FieldMapper.build_field_lines() → field_line_ids
     → state = 'analysed'
     │ «Завантажити»
     ▼
[wizard.action_import()] → state = 'loading' → form reload
     │ Owl виявляє state='loading' → startImport()
     ▼
[JS: MigrationProgressWidget]
     │  offset = (start_batch_number − 1) × 100
     │  ЗОВНІШНІЙ ЦИКЛ: POST /fetch_batch → search_read → source DB
     │    ВНУТРІШНІЙ ЦИКЛ: POST /process_record → RecordImporter → write/create
     │      processed += 1 → оновити progress bar після кожного запису
     │  POST /finalize → wizard.state = 'done'/'stopped'
```

---

## 11. Ключові архітектурні рішення

| Задача | Рішення |
|---|---|
| Розташування модуля | `vd_data_migration/` у **корені репозиторію** (не в `18.0/`) |
| Wizard-файли | `wizard/` містить **і Python, і XML views** для wizard |
| `views/` | Містить **тільки** `menus.xml` |
| Протокол зв'язку з джерелом | **JSON-RPC 2.0** через `urllib.request` (stdlib, без deps) |
| Прогрес у реальному часі | **Frontend-driven** — Owl 2, подвійний цикл, по запису |
| Зупинка | `this._stopped = true` в обох циклах — після поточного запису |
| CORS | Відсутній — фронтенд через **бекенд-проксі** (`fetch_batch`) |
| Пароль | `TransientModel` — чиститься Odoo автоматично |
| Бізнес-логіка | `services/` — чисті класи без ORM-залежності |
