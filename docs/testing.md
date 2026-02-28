# Інтеграційне тестування `vd_data_migration`

> Milestone 8. Тестувати на **Odoo 18.0**, Python 3.10+.

---

## 1. Передумови

- [ ] Два інстанси Odoo 18.0: **джерело** (`source`) і **ціль** (`target`)
- [ ] `addons_path` на `target` містить корінь репозиторію (de лежить `vd_data_migration/`)
- [ ] На `source` є записи для тестової моделі (наприклад `res.partner` з 10+ записами)
- [ ] Користувач з групою `group_migration_user` або `group_migration_admin` на `target`

---

## 2. Встановлення

```bash
# З кореня репозиторію:
git checkout 18.0
git pull

# Встановити модуль на target:
./odoo-bin -i vd_data_migration -d <target_db> --stop-after-init

# Перевірити: встановлення без помилок
./odoo-bin -d <target_db>   # повиннен запуститись
```

---

## 3. Тестові сценарії

### TC-01: Scaffolding (візуально)
- [ ] Меню «Міграція» відображається в головному меню Odoo
- [ ] Клік на «Міграція» відкриває діалог візарда
- [ ] Відображається форма з двома блоками і footer з кнопками

---

### TC-02: Аналіз — позитивний кейс
- [ ] Заповнити `source_url`, `source_db`, `source_login`, `source_password`
- [ ] Обрати `target_model_id` = `Contact (res.partner)`
- [ ] Натиснути «Аналізувати»
- [ ] **Очікуваний результат:**
  - [ ] Таблиця `field_line_ids` заповнюється полями
  - [ ] `record_count_source` відображає кількість записів з джерела
  - [ ] `record_count_target` відображає кількість записів в поточній БД
  - [ ] `one2many` поля мають `include = False`
  - [ ] State = `analysed`, видна кнопка «Завантажити»

---

### TC-03: Аналіз — негативні кейси

| Сценарій | Очікування |
|---|---|
| Порожній `source_password` | `UserError`: невірний логін або пароль |
| Недоступний `source_url` | `UserError`: сервер недоступний |
| Модель не існує на джерелі | `UserError`: model does not exist |
| Порожні поля порожні | `UserError`: Fill in required fields |

---

### TC-04: Імпорт — повний цикл

- [ ] Після TC-02 натиснути «Завантажити»
- [ ] **Очікування:**
  - [ ] Діалог перезавантажується, відображується прогрес-бар
  - [ ] Полоска анімується, лічильник записів/пакетів зростає
  - [ ] По завершенню: state = `done`, notification із статистикою
  - [ ] Записи створені в `target`

---

### TC-05: Резюм з `start_batch_number`

- [ ] Після TC-02: встановити `start_batch_number = 2`
- [ ] Натиснути «Завантажити»
- [ ] **Очікування:**
  - [ ] `offset` стартує з 100 (перші 100 записів пропускаються)
  - [ ] Прогрес починається з `100 / N`

---

### TC-06: Зупинка імпорту (FR-10)

- [ ] Почати імпорт (достатньо записів, щоб встигнути під час)
- [ ] Натиснути «Зупинити»
- [ ] **Очікування:**
  - [ ] Імпорт зупиняється після **поточного** запису (не батчу)
  - [ ] State = `stopped`, notification «Зупинено. Оброблено: X записів.»
  - [ ] `start_batch_number` вручно виставити = послідній завантажений батч → re-analyse → імпорт продовжується

---

### TC-07: Кнопка «Видалити» (FR-07)

- [ ] Після TC-04: натиснути «Видалити»
- [ ] Відображується діалог підтвердження (`confirm=`)
- [ ] Після OK: записи видалені, `record_count_target = 0`
- [ ] Після скасування: записи не видалені

---

### TC-08: Many2one / Many2many (FR-08, FR-09)

- [ ] Обрати модель з `many2one` полем (напр. `res.partner` → `country_id`)
- [ ] Переконатись, що `country_id` розв'язується: пошук локального `id` або placeholder `<{id}>`

---

## 4. Відомі обмеження v1

| Обмеження | Поведінка |
|---|---|
| `one2many` поля | відображаються в таблиці, але `include = False` — не мігрують |
| `ir.attachment` | не мігрують (out of scope v1) |
| Батч > 100 записів | автоматично пагінація (NFR-04) |
| Налаштування між сесіями | не зберігаються (TransientModel) |

---

## 5. Потенційні ризики

> Перевірити при інсталяції:

| Ризик | Дія у разі проблеми |
|---|---|
| Import error `from ..services...` | Перенести імпорти у методи (`_get_rpc_client`, `action_analyse`) |  
| `view_vd_migration_wizard_form` not found | Перевірити `id` у `migration_wizard_views.xml` |
| Owl widget не завантажується | `odoo-bin -u vd_data_migration` + hard refresh |
| `type='json'` route 404 | Перевірити `controllers/__init__.py` імпорт |
| Session експірував під час імпорту | `fetch_batch` поверне `error` → re-analyse |
| `boolean_toggle` не відображається | Замінити на звичайний `<field widget="...">`  |

---

## 6. Логі для діагностики

```bash
# Увімкнути DEBUG-логування для модуля:
./odoo-bin --log-level=debug --log-handler=vd_data_migration:DEBUG -d <db>

# Пошук помилок у логах:
grep -i 'vd_data_migration\|MigrationController\|JsonRpcClient' odoo.log
```
