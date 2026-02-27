# Skill: Запакувати Odoo-модуль у ZIP

## Команда
> "Упакуй модуль [назва]" або "Зроби ZIP для [назва]"

## Вхідні дані
- `module_name` — назва модуля
- `output_path` — куди зберегти ZIP (за замовчуванням `dist/`)

## Кроки виконання
1. Знайти папку `18.0/<module_name>/`
2. Виключити: `__pycache__/`, `*.pyc`, `.env`, `*.log`
3. Запакувати у `dist/<module_name>_18.0.zip`
4. Вивести розмір файлу та список включених файлів

## Скрипт пакування
```bash
#!/bin/bash
MODULE=$1
VERSION="18.0"
OUTPUT="dist/${MODULE}_${VERSION}.zip"
mkdir -p dist
cd 18.0
zip -r ../$OUTPUT $MODULE \
  --exclude "*/__pycache__/*" \
  --exclude "*.pyc" \
  --exclude "*.log" \
  --exclude "*/.env"
echo "Packed: $OUTPUT"
ls -lh ../$OUTPUT
```

## Результат
Файл `dist/<module_name>_18.0.zip` готовий до завантаження через
Odoo UI: Settings → Apps → Upload Module.
