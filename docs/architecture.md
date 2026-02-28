# Архітектура модуля `vd_data_migration`

> Версія: 0.5 | Базується на: `docs/requirements.md` v0.5, `.rules/odoo-conventions.md`

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
│   ├── wizard/                 # Тільки models.TransientModel
│   │   ├── __init__.py
│   │   ├── migration_wizard.py      # TransientModel — головний візард
│   │   └── migration_field_line.py  # TransientModel — рядок таблиці полів
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
│   ├── views/
│   │   ├── migration_wizard_views.xml  # Form view візарда
│   │   └── menus.xml                   # Меню + action
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
│           │   └── migration_progress_widget.js   # Owl 2 компонент-оркестратор
│           ├── xml/
│           │   └── migration_progress_widget.xml  # Owl-шаблон
│           └── css/
│               └── migration_progress_widget.css
└── requirements.txt
```

> **Розташування модуля:** `vd_data_migration/` знаходиться в **корені репозиторію** (не у підпапці `18.0/`).
> При розгортанні на Odoo-сервері — додати шлях до кореня репо у `addons_path`.

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
    """
    JSON-RPC 2.0 клієнт для Odoo.
    Ендпоінти джерела:
      Auth:   POST /web/session/authenticate
      Call:   POST /web/dataset/call_kw
    """
    def __init__(self, url: str, db: str, login: str, password: str):
        self.url = url.rstrip('/')
        self.db = db
        self.login = login
        self.password = password
        self._session_id: str | None = None
        self._uid: int | None = None

    def authenticate(self) -> str:
        # POST /web/session/authenticate
        # Повертає session_id (str), зберігає у self._session_id

    def _call_kw(self, model: str, method: str,
                 args: list, kwargs: dict) -> any:
        # POST /web/dataset/call_kw
        # Headers: Cookie: session_id=...
        # Повертає result або кидає UserError

    def model_exists(self, model: str) -> bool:
        # search_count на ir.model де model = model

    def fields_get(self, model: str) -> dict:
        # fields_get з attributes=['string','type','relation']

    def search_count(self, model: str) -> int:

    def search_read(self, model: str, fields: list,
                    offset: int, limit: int) -> list:
        # Повертає список записів (dict)
```

Обробка помилок: `socket.timeout`, `urllib.error.URLError`, JSON-RPC `error` поле.
Всі помилки логуються через `_logger` і перекидаються як `UserError`.

---

### 3.2 `FieldMapper` — `services/field_mapper.py`

Зіставляє поля джерела з полями поточної БД.

```python
class FieldMapper:
    def __init__(self, rpc: JsonRpcClient, env): ...

    def build_field_lines(self, model_name: str) -> list[dict]:
        # 1. fields_get() з джерела (через JsonRpcClient)
        # 2. Поля поточної БД через env[model_name]._fields
        # 3. Зіставлення: source_exists = field_name in source_fields
        # 4. include = True для всіх; one2many → include = False
        # 5. Повертає list[dict] для запису в field_line_ids
```

---

### 3.3 `RecordImporter` — `services/record_importer.py`

Обробляє **один запис** (per-record підхід).
Цикл по батчах і по записах — повністю на фронтенді.

```python
class RecordImporter:

    def __init__(self, env, wizard): ...

    def process_record(self, model_name: str,
                       record: dict,
                       field_lines: list) -> dict:
        # Повертає: {'created': 0|1, 'updated': 0|1, 'errors': 0|1}
        # → _prepare_values(record, field_lines)
        # → _find_local_record(model_name, record['id'])
        # → write() або create()
        # Логує: _logger.debug('Record %s: %s', record['id'], status)

    def _prepare_values(self, record: dict, field_lines: list) -> dict:
        # Перетворює запис з source у dict для write/create
        # Прості поля: копіює напряму
        # many2one:  _resolve_many2one(comodel, source_id)
        # many2many: _resolve_many2many(comodel, source_ids)
        # one2many / include=False: пропускає

    def _find_local_record(self, model_name: str,
                           source_id: int) -> int | None:
        # Пошук запису по id у поточній БД

    def _resolve_many2one(self, comodel: str,
                          source_id: int) -> int:
        # FR-08: пошук за id / створення з name="<{source_id}>"

    def _resolve_many2many(self, comodel: str,
                           source_ids: list) -> list:
        # FR-09: застосовує _resolve_many2one, повертає [(6, 0, [...])]
```

---

## 4. Контролер (`controllers/migration_controller.py`)

Чотири HTTP JSON-ендпоінти, всі з `auth='user'`:

```
──────────────────────────────────────────────────────────────────────
POST /vd_migration/fetch_batch
  Вхід:  { wizard_id, offset, limit }   (limit завжди 100)
  Дія:   читає поля з wizard.field_line_ids (include=True)
         викликає JsonRpcClient.search_read(model, fields, offset, limit)
  Вихід: { records: [...], total: N }
  Помилки: wizard не знайдено → { error: 'not_found' }
──────────────────────────────────────────────────────────────────────
POST /vd_migration/process_record
  Вхід:  { wizard_id, record: {...} }
  Дія:   RecordImporter.process_record(model, record, field_lines)
  Вихід: { created: 0|1, updated: 0|1, errors: 0|1 }
  Помилки: виняток при write/create → errors=1, created=0, updated=0
──────────────────────────────────────────────────────────────────────
POST /vd_migration/finalize
  Вхід:  { wizard_id, state: 'done'|'stopped',
           created: N, updated: N, errors: N }
  Дія:   wizard.state = state
         wizard.stats_created/updated/errors = ...
         wizard.progress = 100 (якщо done)
  Вихід: { ok: True }
──────────────────────────────────────────────────────────────────────
POST /vd_migration/stop/<wizard_id>     (запасний, для підстраховки)
  Дія:   wizard.state = 'stopped'
  Вихід: { ok: True }
──────────────────────────────────────────────────────────────────────
```

---

## 5. JS Owl-компонент-оркестратор (`MigrationProgressWidget`)

Реалізується як **Owl 2 компонент** (Odoo 18.0). Є **оркестратором міграції** —
виконує подвійний import-цикл: зовнішній по батчах, внутрішній по записах.

### Стан компонента
```javascript
setup() {
    this.state = useState({
        progress: 0,          // 0–100
        label: '',            // 'X / N записів'
        status: 'idle',       // idle | loading | done | stopped | error
        batchesLoaded: 0,     // лічильник завантажених пакетів
        currentBatchNo: 1,    // поточний номер пакету (починається з start_batch_number)
        stats: { created: 0, updated: 0, errors: 0 },
    });
    this._stopped = false;
    onWillStart(async () => {
        if (this.props.record.data.state === 'loading') {
            await this.startImport();
        }
    });
}
```

### Import-цикл (подвійний)
```javascript
async startImport() {
    const wizardId   = this.props.record.data.id;
    const total      = this.props.record.data.record_count_source;
    const startBatch = this.props.record.data.start_batch_number || 1;

    let offset        = (startBatch - 1) * 100;
    let processed     = offset;
    let batchesLoaded = 0;
    let currentBatchNo = startBatch;

    this._stopped = false;
    this.state.status = 'loading';
    this.state.currentBatchNo = startBatch;

    outer: while (!this._stopped) {
        const { records } = await this._fetchBatch(wizardId, offset);
        if (!records.length) break;

        for (const record of records) {
            if (this._stopped) break outer;
            const r = await this._processRecord(wizardId, record);
            processed += 1;
            this._mergeStats(r);
            this.state.progress = total ? Math.round(processed / total * 100) : 100;
            this.state.label = `${processed} / ${total} записів`;
        }

        offset += records.length;
        batchesLoaded += 1;
        currentBatchNo += 1;
        this.state.batchesLoaded = batchesLoaded;
        this.state.currentBatchNo = currentBatchNo;
    }

    const finalState = this._stopped ? 'stopped' : 'done';
    await this._finalize(wizardId, finalState);
    this.state.status = finalState;
}

onStop() { this._stopped = true; }

async _fetchBatch(wizardId, offset) {
    return this.env.services.http.post(
        '/vd_migration/fetch_batch',
        { wizard_id: wizardId, offset, limit: 100 }
    );
}
async _processRecord(wizardId, record) {
    return this.env.services.http.post(
        '/vd_migration/process_record',
        { wizard_id: wizardId, record }
    );
}
async _finalize(wizardId, state) {
    return this.env.services.http.post(
        '/vd_migration/finalize',
        { wizard_id: wizardId, state, ...this.state.stats }
    );
}
_mergeStats(r) {
    this.state.stats.created += r.created || 0;
    this.state.stats.updated += r.updated || 0;
    this.state.stats.errors  += r.errors  || 0;
}
```

### Шаблон (`migration_progress_widget.xml`)
```xml
<t t-name="vd_migration.MigrationProgressWidget">
  <div class="vd-progress-bar" t-if="state.status !== 'idle'">
    <div class="progress-track">
      <div class="progress-fill" t-attf-style="width: {{state.progress}}%"/>
    </div>
    <span class="vd-label" t-esc="state.label"/>
    <span t-attf-class="badge badge-{{state.status}}" t-esc="state.status"/>
    <button t-if="state.status === 'loading'"
            t-on-click="onStop" class="btn btn-sm btn-warning">Зупинити</button>
    <div class="vd-batch-counter" t-if="state.status === 'loading'">
      Пакетів завантажено: <b t-esc="state.batchesLoaded"/>
      (поточний пакет №<b t-esc="state.currentBatchNo"/>)
    </div>
    <div t-if="state.status in ['done','stopped']" class="vd-stats">
      Створено: <b t-esc="state.stats.created"/> |
      Оновлено: <b t-esc="state.stats.updated"/> |
      Помилок:  <b t-esc="state.stats.errors"/>
    </div>
  </div>
</t>
```

Реєстрація: `registry.category('fields').add('vd_migration_progress', MigrationProgressWidget)`

Інтеграція у form view: `<field name="progress" widget="vd_migration_progress"/>`

---

## 6. Views — Структура форми

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
  <button name="action_analyse" string="Аналізувати"
          type="object" class="btn-primary"/>
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
    <button name="action_import" string="Завантажити"
            type="object" class="btn-primary"
            invisible="state != 'analysed'"/>
    <button name="action_delete" string="Видалити"
            type="object" class="btn-danger"
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
                                    │                                │
                          [records=0 / всі записи]             [finalize]
                                    │
                               [finalize]
                                    │
                                  done

Будь-який стан + помилка → state залишається, показується UserError
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
     │
     │ натиск «Аналізувати»
     ▼
[wizard/migration_wizard.action_analyse()]
     → json_rpc_client: authenticate()         ──► source DB (JSON-RPC)
     → json_rpc_client: model_exists()
     → json_rpc_client: fields_get()           ──► source DB (JSON-RPC)
     → field_mapper: build_field_lines()
     → wizard: field_line_ids, counts, source_session_id
     → state = 'analysed'
     │
     │ натиск «Завантажити»
     ▼
[wizard.action_import()]
     → скидає stats, state = 'loading'
     → повертає form reload
     │
     │ Owl-компонент виявляє state='loading' → onWillStart()
     ▼
[JS: MigrationProgressWidget.startImport()]   ← ФРОНТЕНД ОРКЕСТРУЄ
     │  offset = (start_batch_number − 1) × 100
     │
     │  ┌─── ЗОВНІШНІЙ ЦИКЛ (по батчах) ───────────────────────────┐
     │  │  POST /vd_migration/fetch_batch → search_read → source DB  │
     │  │  if records=0 → break                                      │
     │  │  ┌─── ВНУТРІШНІЙ ЦИКЛ (по записах) ──────────────────┐    │
     │  │  │  if _stopped → break outer                         │    │
     │  │  │  POST /vd_migration/process_record                 │    │
     │  │  │    → RecordImporter → write/create                 │    │
     │  │  │  processed += 1 → оновити progress bar             │    │
     │  │  └────────────────────────────────────────────────────┘    │
     │  │  batchesLoaded += 1 → оновити лічильник пакетів           │
     │  └───────────────────────────────────────────────────────────┘
     │  POST /vd_migration/finalize
     ▼
[wizard.state = 'done'/'stopped']
```

---

## 11. Ключові архітектурні рішення

| Задача | Рішення |
|---|---|
| Розташування модуля | `vd_data_migration/` у **корені репозиторію** (не в `18.0/`) |
| Протокол зв'язку з джерелом | **JSON-RPC 2.0** через `urllib.request` (stdlib, без deps) |
| TransientModel'и окремо | Папка `wizard/` (правило `.rules/odoo-conventions.md`) |
| Прогрес у реальному часі | **Frontend-driven** — Owl 2, подвійний цикл, оновлення **по запису** |
| Зовнішній цикл | Фронтенд читає батчами 100 записів: `fetch_batch` |
| Внутрішній цикл | Фронтенд обробляє кожен запис окремо: `process_record` |
| Початковий зсув | `offset = (start_batch_number − 1) × 100` (поле `start_batch_number`, default=1) |
| Зупинка | `this._stopped = true` перевіряється в ОБОХ циклах — зупинка після поточного **запису** |
| Лічильник пакетів | `batchesLoaded` — збільшується після батчу, показується під прогрес-баром |
| CORS | Відсутній — фронтенд читає через **бекенд-проксі** (`fetch_batch`) |
| Пароль не зберігається | `TransientModel` — чиститься Odoo автоматично |
| Many2one / Many2many | `_resolve_many2one` з кешем локальних ID (бекенд) |
| Бізнес-логіка окремо | `services/` — чисті класи без ORM-залежності |
