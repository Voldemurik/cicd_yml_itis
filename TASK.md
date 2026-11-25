# Персональное задание CI-33

Репозиторий: `urfu_itis_limits/cicd_yml_2026-voldemurik-b0ety`. Ветка: `student/voldemurik`. Задание выдано при **создании ветки**. Повторная выдача не меняет существующие файлы.

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

## Персональная статическая проверка: Параметр конфигурации (S3)

Добавьте в config/settings.json логический ключ ci_enabled со значением true. Проверяйте JSON как данные, а не просто поиск текста.

Проверку выполняйте в job `variant_check`. Она должна возвращать ненулевой exit code при нарушении условия.

## Персональная динамическая проверка: Активные записи (D6)

Посчитать записи со status=active.

С помощью CLI приложения запустите режим `active_count` на `data/sales.csv` и сохраните JSON в `dist/report.json`.

Форма запуска: `python -m app.cli --input data/sales.csv --output dist/report.json --mode "$REPORT_MODE" --variant CI-33`. В YAML задайте `REPORT_MODE: active_count` в `env`.

JSON должен включать поля `variant`, `mode`, `rows`, `value`, `source_sha256`. Значение `value` записывается строкой. Не вставляйте ответ в YAML вручную.

## Объект оценки

Итог — успешный Student CI с артефактом `student-results` и успешный ручной запуск `smartclass.yml` с секретом `READ_TOKEN`. Сам `smartclass.yml` не нужно редактировать. Преподаватель дополнительно проверяет содержательность YAML и оставляет за собой право не засчитывать формальную или подменённую работу.
