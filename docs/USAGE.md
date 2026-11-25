# Использование учебного Python-приложения

Приложение читает CSV, вычисляет одну метрику и сохраняет JSON-отчёт. На старте в `app/core.py` есть намеренная ошибка, которая выявляется тестом.

Общий интерфейс:

```bash
python -m app.cli --input data/sales.csv --output dist/example.json --mode row_count --variant DEMO
```

Вы можете посмотреть список параметров через `python -m app.cli --help`. Для персонального задания замените демонстрационные `--mode` и `--variant` на значения из **своего** `TASK.md`. В CI режим нужно передать через `REPORT_MODE` в YAML, а не просто вписать его в команду запуска. Выходной файл для CI: `dist/report.json`.

## Проверка качества локально

```bash
python -m venv .venv
# Linux/macOS: .venv/bin/python -m pip install -r requirements-dev.txt
# Windows: .venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.venv/bin/python -m ruff check app tests          # Linux/macOS
.venv/bin/python -m ruff format --check app tests # Linux/macOS
.venv/bin/python -m pytest -q                      # Linux/macOS
```

На Windows вместо `.venv/bin/python` используйте `.venv\Scripts\python.exe`. Форматирование можно исправить через `python -m ruff format app tests` в активном venv и затем изучить `git diff`.
