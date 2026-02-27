# Git Workflow

## Гілки
- `18.0` — основна гілка (стабільна)
- `18.0-dev` — гілка розробки
- `18.0-feature/<name>` — для нових фіч
- `18.0-fix/<name>` — для виправлень

## Commit messages
Формат: `<type>(<scope>): <description>`

Типи:
- `feat` — нова функціональність
- `fix` — виправлення помилки
- `docs` — зміни у документації
- `refactor` — рефакторинг без зміни функціоналу
- `test` — додавання тестів
- `chore` — технічні зміни (залежності, конфіги)

Приклади:
```
feat(migration): add contact batch import via XML-RPC
fix(module): fix missing sudo in partner creation
docs(requirements): update functional requirements
```

## Pull Requests
- PR завжди з описом: що зроблено, як тестувати
- Один PR — одна задача
- Перед merge — перевірити що модуль встановлюється без помилок

## .gitignore обов'язково включає
```
.env
*.pyc
__pycache__/
dist/*.zip
.vscode/settings.json
```
