# План розробки модуля `vd_data_migration`

> Базується на: `docs/requirements.md` v0.5 | `docs/architecture.md` v0.6

## Статуси
- `[ ]` — не розпочато
- `[~]` — в процесі
- `[x]` — виконано

---

## Milestone 0–5 — виконано [x]

---

## Milestone 6: HTTP-контролер

- [x] `controllers/migration_controller.py` — `MigrationController`
- [x] `POST /vd_migration/fetch_batch` — `{ records, total }`, тільки `include=True AND source_exists=True` поля
- [x] `POST /vd_migration/process_record` — `{ created, updated, errors }`, статистика на фронтенді
- [x] `POST /vd_migration/finalize` — зберігає `state` + `stats` з frontend
- [x] `POST /vd_migration/stop/<wizard_id>` — екстренна зупинка (запасний)
- [x] Всі маршрути `auth='user'`, `type='json'`, помилки → `{ error }`
- [x] `_build_rpc_client()` — відновлює `_session_id` з `wizard.source_session_id`
- [x] `controllers/__init__.py` — імпорт активовано

---

## Milestone 7: JS Owl-компонент (`MigrationProgressWidget`)

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
