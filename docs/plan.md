# План розробки модуля `vd_data_migration`

> Базується на: `docs/requirements.md` v0.5 | `docs/architecture.md` v0.6

## Статуси
- `[ ]` — не розпочато
- `[~]` — в процесі
- `[x]` — виконано

---

## Milestone 0–6 — виконано [x]

---

## Milestone 7: JS Owl-компонент (`MigrationProgressWidget`)

- [x] `static/src/js/migration_progress_widget.js`
  - [x] Owl 2 `Component`, `useState`, `onMounted`
  - [x] `startImport()` — подвійний цикл `outerLoop` (batch) / inner (per-record)
  - [x] `stopImport()` — `this._stopped = true`, перевірка на початку обох циклів (FR-10)
  - [x] `_updateProgress()` — оновлення після кожного запису (FR-11)
  - [x] Resume з `start_batch_number`: `offset = (startBatch - 1) * 100`
  - [x] Ініціалізація `state` з полів wizard (для відображення попереднього результату)
  - [x] Getters `statusLabel`, `statusClass`
  - [x] `registry.category("fields").add("vd_migration_progress", ...)`
- [x] `static/src/xml/migration_progress_widget.xml`
  - [x] Progress bar (анімована при `running`)
  - [x] Лічильник записів і пакетів
  - [x] Кнопка «Зупинити» (visible при `running`)
  - [x] Фінальна статистика badges (visible при `done`/`stopped`)
  - [x] Alert при `error`
- [x] `static/src/css/migration_progress_widget.css` — стилі
- [x] `__manifest__.py` — assets розкоментовано

---

## Milestone 8: Інтеграційне тестування

- [ ] Встановити модуль: `odoo-bin -i vd_data_migration -d <db>`
- [ ] Перевірити scaffolding: модуль з’являється в Apps без помилок
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
