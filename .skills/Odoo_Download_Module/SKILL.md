# Skill: Завантажити модуль з remote Odoo-сервера

## Команда
> "Завантаж модуль [назва] з [url]"

## Вхідні дані
- `module_name` — назва встановленого модуля на remote сервері
- `remote_url` — URL Odoo-інстансу
- `login` / `password` — облікові дані адміністратора
- `output_path` — куди зберегти ZIP (за замовчуванням `dist/`)

## Передумови
На remote сервері має бути встановлений кастомний контролер
(або модуль-downloader), який надає ендпоінт:
`GET /web/module/download/<module_name>`

## Кроки виконання
1. Авторизуватись через `/web/session/authenticate`
2. GET запит на `/web/module/download/<module_name>`
3. Зберегти відповідь як `dist/<module_name>_remote.zip`
4. Розпакувати у `18.0/<module_name>/` (якщо потрібно)

## Скрипт завантаження
```python
import requests, os

REMOTE_URL = "https://source-odoo.example.com"
DB, LOGIN, PASSWORD = "mydb", "admin", "password"
MODULE = "my_custom_module"

session = requests.Session()
session.post(f"{REMOTE_URL}/web/session/authenticate", json={
    "jsonrpc": "2.0", "method": "call",
    "params": {"db": DB, "login": LOGIN, "password": PASSWORD}
})

resp = session.get(f"{REMOTE_URL}/web/module/download/{MODULE}")
os.makedirs("dist", exist_ok=True)
with open(f"dist/{MODULE}_remote.zip", "wb") as f:
    f.write(resp.content)
print(f"Saved: dist/{MODULE}_remote.zip ({len(resp.content)} bytes)")
```
