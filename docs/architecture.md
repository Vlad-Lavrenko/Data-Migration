# Архітектура модуля `vd_data_migration`

> Версія: 0.3 | Базується на: `docs/requirements.md` v0.4, `.rules/odoo-conventions.md`

---

## 1. Загальна структура файлів

```
18.0/
└── vd_data_migration/
    ├── __init__.py                  # from . import models, wizard, services, controllers
    ├── __manifest__.py
    |
    ├── models/                      # Тільки models.Model / AbstractModel
    │   └── __init__.py              # (порожньо, готово до розширення)
    |
    ├── wizard/                      # Тільки models.TransientModel
    │   ├── __init__.py
    │   ├── migration_wizard.py      # TransientModel — головний візард
    │   └── migration_field_line.py  # TransientModel — рядок таблиці полів
    |
    ├── services/                    # Чиста Python-логіка, без Odoo ORM
    │   ├── __init__.py
    │   ├── json_rpc_client.py       # JSON-RPC клієнт (urllib.request + json)
    │   ├── field_mapper.py          # Зіставлення полів source/target
    │   └── record_importer.py       # Обробка батчу записів
    |
    ├── controllers/
    │   ├── __init__.py
    │   └── migration_controller.py  # HTTP JSON ендпоінти для Owl-компонента
    |
    ├── views/
    │   ├── migration_wizard_views.xml  # Form view візарда
    │   └── menus.xml                   # Меню + action
    |
    ├── security/
    │   ├── security_groups.xml         # Групи доступу
    │   └── ir.model.access.csv         # Права CRUD
    |
    └── static/
        ├── description/
        │   └── icon.png
        └── src/
            ├── js/
            │   └── migration_progress_widget.js   # Owl 2 компонент-оркестратор
            ├── xml/
            │   └── migration_progress_widget.xml  # Owl-шаблон
            └── css/
                └── migration_progress_widget.css
```

---

## 2. Опис моделей

### 2.1 `vd.migration.wizard` — `wizard/migration_wizard.py`

`TransientModel` — головна модель візарда.

```
Поля:
┌──────────────────────┬────────────────┬──────────────────────────────────────────┐
| Назва               | Тип           | Опис                                     |
├──────────────────────┼────────────────┼──────────────────────────────────────────┤
| source_url           | Char           | URL бази-джерела                          |
| source_db            | Char           | Назва БД                                  |
| source_login         | Char           | Логін                                      |
| source_password      | Char           | Пароль (password=True)                     |
| source_session_id    | Char           | JSON-RPC session_id (пам'ять, не в БД)    |
| target_model_id      | Many2one       | ir.model (поточна БД)                     |
| field_line_ids       | One2many       | vd.migration.field.line                   |
| record_count_source  | Integer        | read-only, з джерела                      |
| record_count_target  | Integer        | read-only, поточна БД                     |
| progress             | Integer        | 0-100, для прогрес-бара                   |
| progress_label       | Char           | «X / N записів»                           |
| stats_created        | Integer        | Статистика: створено                       |
| stats_updated        | Integer        | Статистика: оновлено                       |
| stats_errors         | Integer        | Статистика: помилок                        |
| state                | Selection      | draft/analysed/loading/done/stopped        |
└──────────────────────┴────────────────┴──────────────────────────────────────────┘

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
        # Повертає session_id (str)
        # Зберігає у self._session_id

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

Обробляє один батч записів (отриманий з фронтенду).
Цикл по батчах — на фронтенді, а не тут.

```python
class RecordImporter:

    def __init__(self, env, wizard): ...

    def process_batch(self, model_name: str,
                      records: list[dict],
                      field_lines: list) -> dict:
        # Повертає: {'created': N, 'updated': N, 'errors': N}
        # Для кожного запису:
        #   → _prepare_values(record, field_lines)
        #   → _find_local_record(model_name, record['id'])
        #   → write() або create()

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
  Помилки: wizard не знайдено → 404; RPC-помилка → { error: '...' }
──────────────────────────────────────────────────────────────────────
POST /vd_migration/process_batch
  Вхід:  { wizard_id, records: [...] }
  Дія:   RecordImporter.process_batch(model, records, field_lines)
  Вихід: { created: N, updated: N, errors: N }
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

Reалізується як **Owl 2 компонент** (Odoo 18.0). Є **оркестратором міграції** — виконує import-цикл на фронтенді.

### Стан компонента
```javascript
setup() {
    this.state = useState({
        progress: 0,          // 0–100
        label: '',            // 'X / N записів'
        status: 'idle',       // idle | loading | done | stopped | error
        stats: { created: 0, updated: 0, errors: 0 },
    });
    this._stopped = false;
    // Авто-старт: якщо wizard.state == 'loading' — запустити startImport()
    onWillStart(async () => {
        if (this.props.record.data.state === 'loading') {
            await this.startImport();
        }
    });
}
```

### Import-цикл
```javascript
async startImport() {
    this._stopped = false;
    this.state.status = 'loading';
    const wizardId = this.props.record.data.id;
    const total    = this.props.record.data.record_count_source;
    let offset = 0;

    while (!this._stopped) {
        // 1. Отримати батч з джерела (через бекенд-проксі)
        const { records } = await this._fetchBatch(wizardId, offset);

        // 2. Якщо 0 записів — всі дані отримані
        if (!records.length) break;

        // 3. Обробити батч на бекенді
        const result = await this._processBatch(wizardId, records);

        // 4. Оновити стан UI
        offset += records.length;
        this._mergeStats(result);
        this.state.progress = total ? Math.round(offset / total * 100) : 100;
        this.state.label = `${offset} / ${total} записів`;
    }

    // 5. Завершення
    const finalState = this._stopped ? 'stopped' : 'done';
    await this._finalize(wizardId, finalState);
    this.state.status = finalState;
}

onStop() {
    this._stopped = true;  // зупинить цикл після поточного батчу
}

async _fetchBatch(wizardId, offset) {
    return this.env.services.http.post(
        '/vd_migration/fetch_batch',
        { wizard_id: wizardId, offset, limit: 100 }
    );
}

async _processBatch(wizardId, records) {
    return this.env.services.http.post(
        '/vd_migration/process_batch',
        { wizard_id: wizardId, records }
    );
}

async _finalize(wizardId, state) {
    return this.env.services.http.post(
        '/vd_migration/finalize',
        { wizard_id: wizardId, state, ...this.state.stats }
    );
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
            t-on-click="onStop" class="btn btn-sm btn-warning">
      Зупинити
    </button>
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
<!-- views/migration_wizard_views.xml -->
<form string="Міграція даних">
  <group string="Підключення до джерела">
    <field name="source_url"/>
    <field name="source_db"/>
    <field name="source_login"/>
    <field name="source_password" password="True"/>
  </group>

  <group string="Модель">
    <field name="target_model_id"/>
    <field name="record_count_source" readonly="1"/>
    <field name="record_count_target" readonly="1"/>
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

  <!-- Прогрес-бар / оркестратор — Owl 2 компонент -->
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
                              [records=0]                      [finalize]
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
     → services/json_rpc_client.py: authenticate()     ──► source DB (JSON-RPC)
     → services/json_rpc_client.py: model_exists()
     → services/json_rpc_client.py: fields_get()       ──► source DB (JSON-RPC)
     → services/field_mapper.py: build_field_lines()
     → wizard: field_line_ids, counts, source_session_id
     → state = 'analysed'
     │
     │ натиск «Завантажити»
     ▼
[wizard/migration_wizard.action_import()]
     → скидає stats, state = 'loading'
     → повертає form reload
     │
     │ Owl-компонент виявляє state='loading' → onWillStart()
     ▼
[JS: MigrationProgressWidget.startImport()]   ← ФРОНТЕНД ОРКЕСТРУЄ
     │
     │  ┌─────────────────── цикл (offset=0) ─────────────────────┐
     │  │                                                           │
     │  │  POST /vd_migration/fetch_batch                          │
     │  │    → controllers/migration_controller.py                 │
     │  │    → services/json_rpc_client.search_read(offset, 100)  │
     │  │    ←── source DB (JSON-RPC)                             │
     │  │    → { records: [...] }                                  │
     │  │                                                           │
     │  │  if records.length == 0 → break ─────────────────────► │
     │  │                                                           │
     │  │  POST /vd_migration/process_batch                        │
     │  │    → services/record_importer.process_batch()            │
     │  │         → _prepare_values() per record                   │
     │  │              → _resolve_many2one/many2many               │
     │  │         → env[model].search(id) → write/create           │
     │  │    → { created, updated, errors }                        │
     │  │                                                           │
     │  │  offset += records.length                                │
     │  │  Оновити progress bar (без polling!)                     │
     │  │  Перевірити this._stopped                                │
     │  └────────────────────────────────────────────────────────┘
     │
     │  POST /vd_migration/finalize { state, stats }
     ▼
[wizard.state = 'done'/'stopped', stats збережено]
```

---

## 11. Ключові архітектурні рішення

| Задача | Рішення |
|---|---|
| Протокол зв'язку з джерелом | **JSON-RPC 2.0** через `urllib.request` (stdlib, без deps) |
| TransientModel'и окремо | Папка `wizard/` (правило `.rules/odoo-conventions.md`) |
| Прогрес у реальному часі | **Frontend-driven** — Owl 2 компонент оркеструє цикл, без polling |
| Цикл по батчах | На **фронтенді**: читати до `records.length == 0` |
| Зупинка | `this._stopped = true` у JS + `POST /finalize` з state='stopped' |
| CORS | Відсутній — фронтенд читає через **бекенд-проксі** (`fetch_batch`) |
| Пароль не зберігається | `TransientModel` — чиститься Odoo автоматично |
| Many2one / Many2many | `_resolve_many2one` з кешем локальних ID (бекенд) |
| Батчинг | Рівно 100 записів за один `fetch_batch` запит |
| Бізнес-логіка окремо | `services/` — чисті класи без ORM-залежності |
