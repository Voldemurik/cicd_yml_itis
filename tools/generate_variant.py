"""Idempotent assignment generator. Run once per student repo."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from assignment.catalog import get_dynamic, get_static, select_variant


def render_task(variant: dict) -> str:
    static = get_static(variant)
    dynamic = get_dynamic(variant)
    return f"""# Персональное задание {variant["variant_id"]}

Репозиторий: `{variant["repository"]}`. Ветка: `{variant["branch"]}`. Задание выдано при **создании ветки**. Повторная выдача не меняет существующие файлы.

## Что сделать всем

1. Исправьте `.gitverse/workflows/student.yml`. Не заменяйте проверки командами `echo` или `exit 0`.
2. Настройте Ruff: `ruff check` и `ruff format --check` для `app/` и `tests/`; исправьте нарушения форматирования.
3. Настройте настоящий запуск `pytest`; исправьте ошибку вычисления в приложении (тест уже есть).
4. Свяжите jobs через `needs` так, чтобы пакет создавался только после успешных проверок.
5. В `package` передайте персональный режим через переменную окружения `REPORT_MODE`, выполните программу, создайте `dist/report.json`, загрузите artifact с именем `student-results`.
6. Дождитесь успешного `02 - Student CI + artifact audit`. Job `audit` должна скачать `student-results` и выдать `RESULT: PASS`.
7. **Отдельный этап работы с секретами:** создайте в GitVerse личный токен с правом чтения репозитория и сохраните его как секрет репозитория `READ_TOKEN` (инструкция `docs/READ_TOKEN.md`). Не вставляйте токен в YAML.
8. Вручную запустите `03 - Smartclass: verify Student CI run` на своей ветке, указав ID **успешного запуска Student CI** (число после `/cicd/`, не `job=`). Добейтесь `RESULT: PASS`.
9. При затруднениях откройте `docs/CI_CHEATSHEET.md`, а весь маршрут описан в `docs/STUDENT_GUIDE.md`.

## Персональная статическая проверка: {static['title']} ({static['code']})

{static['description']}

Проверку выполняйте в job `variant_check`. Она должна возвращать ненулевой exit code при нарушении условия.

## Персональная динамическая проверка: {dynamic['title']} ({dynamic['code']})

{dynamic['description']}

С помощью CLI приложения запустите режим `{dynamic['mode']}` на `data/sales.csv` и сохраните JSON в `dist/report.json`.

Форма запуска: `python -m app.cli --input data/sales.csv --output dist/report.json --mode "$REPORT_MODE" --variant {variant['variant_id']}`. В YAML задайте `REPORT_MODE: {dynamic['mode']}` в `env`.

JSON должен включать поля `variant`, `mode`, `rows`, `value`, `source_sha256`. Значение `value` записывается строкой. Не вставляйте ответ в YAML вручную.

## Объект оценки

Итог — успешный Student CI с артефактом `student-results` и успешный ручной запуск `smartclass.yml` с секретом `READ_TOKEN`. Сам `smartclass.yml` не нужно редактировать. Преподаватель дополнительно проверяет содержательность YAML и оставляет за собой право не засчитывать формальную или подменённую работу.
"""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--repository', required=True, help='owner/repo in GitVerse')
    parser.add_argument('--actor', required=True, help='login of the branch creator (gitverse.actor)')
    parser.add_argument('--branch', required=True, help='student/<login>')
    parser.add_argument('--static', dest='static_code', default=None, help='pilot: S3')
    parser.add_argument('--dynamic', dest='dynamic_code', default=None, help='pilot: D5')
    parser.add_argument('--root', type=Path, default=ROOT)
    args = parser.parse_args()
    root = args.root.resolve()
    if args.branch != f'student/{args.actor}':
        print(f'[ERROR] expected branch student/{args.actor}, got {args.branch}')
        return 2
    variant = select_variant(args.repository, args.actor, args.static_code, args.dynamic_code)
    expected = {'TASK.md': render_task(variant), 'variant.json': json.dumps(variant, ensure_ascii=False, indent=2) + '\n'}
    # Check all existing files before writing any of them (no partial assignment).
    conflicts = [name for name, data in expected.items()
                 if (root / name).exists()
                 and (root / name).read_text(encoding='utf-8') != data]
    if conflicts:
        print(f'[ERROR] refusing to overwrite existing assignment files: {conflicts}')
        return 2
    for relative, data in expected.items():
        path = root / relative
        if path.exists():
            print(f'[SKIP] {relative} already exists with correct contents')
        else:
            path.write_text(data, encoding='utf-8')
            print(f'[CREATED] {relative}')
    print(f'[TASK] {variant["variant_id"]} / {variant["static"]} + {variant["dynamic"]}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
