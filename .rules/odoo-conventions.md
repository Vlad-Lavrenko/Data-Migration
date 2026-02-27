# Odoo 18.0 — Правила розробки

## Маніфест модуля
```python
{
    'name': 'Module Name',
    'version': '18.0.1.0.0',  # major.minor.patch
    'category': 'Tools',
    'summary': 'Short description',
    'author': 'Vlad Lavrenko',
    'depends': ['base'],
    'data': [],
    'installable': True,
    'application': False,
}
```

## Моделі
- Префікс назви моделі відповідно до модуля: `dm_` (data migration)
- Завжди вказувати `_description`
- Завжди вказувати `string=` та `help=` для полів
- `sudo()` використовувати тільки з коментарем `# sudo: <reason>`
- Уникати бізнес-логіки у `_compute` — виносити у окремі методи

## View
- XML id формат: `<module>.<type>_<model>_<suffix>`
  Приклад: `dm_migration.view_partner_migration_form`
- Завжди вказувати `string=` у `<record>`
- Tree view — мінімум полів (до 6)
- Form view — групувати поля через `<group>`

## Security
- Кожна модель обов'язково має запис у `security/ir.model.access.csv`
- Групи доступу визначати у `security/security_groups.xml`
- Формат CSV: `id,name,model_id:id,group_id:id,perm_read,perm_write,perm_create,perm_unlink`

## Controllers
- Маршрут завжди з `auth='user'` або `auth='public'` (явно)
- JSON-відповідь через `http.Response` з `content_type='application/json'`
- Обробляти виключення та повертати структурований JSON з `error`

## Міграційні скрипти (RPC)
- Завжди перевіряти дублі перед `create`
- Логувати кожен створений/пропущений запис
- Використовувати батчинг: по 100 записів за раз
- Зберігати результат у log-файл поруч зі скриптом
