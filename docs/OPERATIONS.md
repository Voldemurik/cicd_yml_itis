# Эксплуатация приложения

## Исходные данные

Приложение читает `data/sales.csv` с колонками `item`, `category`, `quantity`, `price` и `status`. Исходный файл не изменяется. Для варианта CI-33 используется режим `active_count`: программа считает строки со значением `active` в колонке `status`.

Результат сохраняется в `dist/report.json` и содержит идентификатор варианта, режим, общее число строк, вычисленное значение и SHA-256 исходного CSV.

## Запуск

```bash
python -m app.cli --input data/sales.csv --output dist/report.json --mode active_count --variant CI-33
```

В CI режим передаётся через переменную окружения `REPORT_MODE`, а готовый файл загружается как артефакт `student-results`.

## Диагностика

Перед запуском CI проверьте проект локально:

```bash
python -m ruff check app tests
python -m ruff format --check app tests
python -m pytest -q
python -m json.tool config/settings.json
```

Если job `quality` падает, исправьте первую ошибку Ruff или pytest, не отключая проверки. Ошибка `variant_check` означает, что `config/settings.json` некорректен или логический ключ `ci_enabled` не равен `true`. Если `package` не создаёт артефакт, проверьте команду CLI, наличие `dist/report.json` и параметры `actions/upload-artifact@v4`. В `audit` итоговым признаком успеха является строка `RESULT: PASS`.
