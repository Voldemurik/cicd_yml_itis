"""Shared catalogue for the assignment generator and the demo auditor.

In production, authoritative audit code should be kept outside student repos.
"""
from __future__ import annotations

import hashlib

STATIC = [
    {
        'code': 'S1', 'title': 'Раздел в README',
        'description': 'Добавьте в README.md заголовок второго уровня «## Запуск CI». Настройте шаг проверки его наличия.',
        'kind': 'contains', 'file': 'README.md', 'needle': '## Запуск CI',
    },
    {
        'code': 'S2', 'title': 'Раздел диагностики',
        'description': 'Добавьте в docs/OPERATIONS.md строку «## Диагностика» и настройте проверку её наличия.',
        'kind': 'contains', 'file': 'docs/OPERATIONS.md', 'needle': '## Диагностика',
    },
    {
        'code': 'S3', 'title': 'Параметр конфигурации',
        'description': 'Добавьте в config/settings.json логический ключ ci_enabled со значением true. Проверяйте JSON как данные, а не просто поиск текста.',
        'kind': 'json_bool', 'file': 'config/settings.json', 'key': 'ci_enabled', 'value': True,
    },
    {
        'code': 'S4', 'title': 'История изменений',
        'description': 'Создайте docs/CHANGELOG.md с заголовком «## 1.0.0». Настройте проверку файла и его содержимого.',
        'kind': 'contains', 'file': 'docs/CHANGELOG.md', 'needle': '## 1.0.0',
    },
    {
        'code': 'S5', 'title': 'Запрет оставленных TODO',
        'description': 'Удалите маркер TODO из docs/OPERATIONS.md. Настройте проверку отсутствия такого маркера.',
        'kind': 'absent', 'file': 'docs/OPERATIONS.md', 'needle': 'TODO',
    },
    {
        'code': 'S6', 'title': 'Инструкция по CLI',
        'description': 'Добавьте в docs/USAGE.md заголовок «## Примеры CLI» и настройте проверку его наличия.',
        'kind': 'contains', 'file': 'docs/USAGE.md', 'needle': '## Примеры CLI',
    },
]

DYNAMIC = [
    {'code': 'D1', 'mode': 'row_count', 'title': 'Количество строк', 'description': 'Посчитать число записей CSV.'},
    {'code': 'D2', 'mode': 'quantity_sum', 'title': 'Сумма количества', 'description': 'Посчитать общую сумму столбца quantity.'},
    {'code': 'D3', 'mode': 'revenue', 'title': 'Выручка', 'description': 'Посчитать сумму quantity × price по всем строкам.'},
    {'code': 'D4', 'mode': 'max_price', 'title': 'Максимальная цена', 'description': 'Найти максимальную цену price.'},
    {'code': 'D5', 'mode': 'unique_categories', 'title': 'Категории', 'description': 'Посчитать число уникальных категорий.'},
    {'code': 'D6', 'mode': 'active_count', 'title': 'Активные записи', 'description': 'Посчитать записи со status=active.'},
]


def select_variant(repository: str, actor: str, static_code: str | None = None,
                   dynamic_code: str | None = None) -> dict:
    """Assign a stable variant by repository and branch creator (not commit author).

    For the pilot we deliberately force S3/D5 with explicit CLI options.
    """
    repository = repository.strip().lower()
    actor = actor.strip().lower()
    if not repository or '/' not in repository:
        raise ValueError('repository must be owner/repo')
    if not actor or '/' in actor or actor in ('.', '..'):
        raise ValueError('actor must be a GitVerse login')
    if (static_code is None) != (dynamic_code is None):
        raise ValueError('static and dynamic codes must be provided together')
    digest = hashlib.sha256(f'ci-lab-2026-v2:{repository}:{actor}'.encode()).digest()
    number = int.from_bytes(digest[:8], 'big') % (len(STATIC) * len(DYNAMIC))
    if static_code is not None:
        static = next((item for item in STATIC if item['code'] == static_code), None)
        dynamic = next((item for item in DYNAMIC if item['code'] == dynamic_code), None)
        if static is None or dynamic is None:
            raise ValueError('unknown explicit variant code')
        variant_id = f'CI-{static_code}-{dynamic_code}'
    else:
        static = STATIC[number % len(STATIC)]
        dynamic = DYNAMIC[number // len(STATIC)]
        variant_id = f'CI-{number+1:02d}'
    return {
        'schema_version': 2,
        'repository': repository,
        'actor': actor,
        'branch': f'student/{actor}',
        'variant_id': variant_id,
        'static': static['code'],
        'dynamic': dynamic['code'],
        'mode': dynamic['mode'],
        'artifact_name': 'student-results',
        'artifact_path': 'dist/report.json',
    }


def get_static(variant: dict) -> dict:
    return next(x for x in STATIC if x['code'] == variant['static'])


def get_dynamic(variant: dict) -> dict:
    return next(x for x in DYNAMIC if x['code'] == variant['dynamic'])
