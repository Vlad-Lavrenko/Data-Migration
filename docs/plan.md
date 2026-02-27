# План розробки

## Статуси
- `[ ]` — не розпочато
- `[~]` — в процесі
- `[x]` — виконано

---

## Milestone 1: Базова інфраструктура
- [x] Створити репозиторій та гілку `18.0`
- [x] Додати `.rules/` та `.skills/`
- [x] Сформувати `docs/requirements.md`
- [ ] Додати `.gitignore` для Python/Odoo
- [ ] Додати `requirements.txt`

## Milestone 2: Скрипти міграції (RPC)
- [ ] Скрипт міграції `res.partner` (`scripts/migrate_partners.py`)
- [ ] Параметризований скрипт для довільної моделі (`scripts/migrate_model.py`)
- [ ] Конфіг через `.env` файл
- [ ] Логування у файл

## Milestone 3: Кастомний Odoo-модуль (downloader)
- [ ] Модуль `dm_module_downloader` — HTTP-контролер для завантаження ZIP
- [ ] Security: тільки для групи `base.group_system`
- [ ] Клієнтський скрипт завантаження

## Milestone 4: Тести
- [ ] Unit-тести для скриптів міграції
- [ ] Інтеграційний тест (mock Odoo RPC)
