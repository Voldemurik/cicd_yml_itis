"""Demo audit: status + YAML structure + independent checks + artifact content.

This local copy is educational and editable by students. For trusted grading,
run the authoritative copy outside their repository.
"""
from __future__ import annotations

import argparse
import csv
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import re
import sys

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from assignment.catalog import get_static, select_variant


def expected_metric(mode: str, data_file: Path) -> tuple[int, str, str]:
    with data_file.open('r', encoding='utf-8', newline='') as file:
        rows = list(csv.DictReader(file))
    if mode == 'row_count':
        value = len(rows)
    elif mode == 'quantity_sum':
        value = sum(int(r['quantity']) for r in rows)
    elif mode == 'revenue':
        value = sum((int(r['quantity']) * Decimal(r['price']) for r in rows), Decimal('0'))
    elif mode == 'max_price':
        value = max((Decimal(r['price']) for r in rows), default=Decimal('0'))
    elif mode == 'unique_categories':
        value = len({r['category'] for r in rows})
    elif mode == 'active_count':
        value = sum(r['status'] == 'active' for r in rows)
    else:
        raise ValueError('Unknown metric')
    return len(rows), str(value), hashlib.sha256(data_file.read_bytes()).hexdigest()


def static_ok(root: Path, spec: dict) -> tuple[bool, str]:
    file = root / spec['file']
    if not file.is_file():
        return False, f'missing {spec["file"]}'
    if spec['kind'] == 'json_bool':
        try:
            data = json.loads(file.read_text(encoding='utf-8'))
        except (json.JSONDecodeError, UnicodeError) as exc:
            return False, f'invalid JSON: {exc}'
        valid = isinstance(data, dict) and data.get(spec['key']) is spec['value']
    else:
        content = file.read_text(encoding='utf-8')
        valid = (spec['needle'] in content) if spec['kind'] == 'contains' else (spec['needle'] not in content)
    return valid, f'{spec["code"]} in {spec["file"]}'


def all_steps(job: dict) -> list[dict]:
    steps = job.get('steps', [])
    return steps if isinstance(steps, list) else []


def commands(job: dict) -> str:
    return '\n'.join(str(s.get('run', '')) for s in all_steps(job) if isinstance(s, dict))


def inspect_workflow(path: Path) -> list[tuple[bool, str]]:
    results = []
    try:
        # BaseLoader is intentional: PyYAML's YAML 1.1 SafeLoader treats "on" as True.
        data = yaml.load(path.read_text(encoding='utf-8'), Loader=yaml.BaseLoader)
        assert isinstance(data, dict)
        assert isinstance(data.get('on'), dict) and 'push' in data['on'] and 'workflow_dispatch' in data['on']
        jobs = data['jobs']
        assert isinstance(jobs, dict)
        for name in ('quality', 'variant_check', 'package'):
            assert isinstance(jobs.get(name), dict), f'missing job: {name}'
        results.append((True, 'direct push/dispatch triggers and required jobs'))
    except Exception as exc:
        return [(False, f'workflow structure: {exc}')]

    def effective_lines(text: str) -> str:
        # Strip comments and obvious logging lines before inspecting commands.
        return '\n'.join(
            line.strip() for line in text.splitlines()
            if line.strip()
            and not line.lstrip().startswith('#')
            and not re.match(r'^(echo|printf)\b', line.strip())
        )

    quality = effective_lines(commands(jobs['quality']))
    variant = effective_lines(commands(jobs['variant_check']))
    package = effective_lines(commands(jobs['package']))
    results.append((bool(re.search(r'^(?:(?:[./\w-]*/)?python(?:3)?\s+-m\s+)?ruff\s+check\b', quality, re.M)) and
                    bool(re.search(r'^(?:(?:[./\w-]*/)?python(?:3)?\s+-m\s+)?ruff\s+format\s+--check\b', quality, re.M)),
                    'Ruff lint and formatting commands'))
    results.append((bool(re.search(r'^(?:(?:[./\w-]*/)?python(?:3)?\s+-m\s+)?pytest\b', quality, re.M)), 'real pytest command'))
    results.append((bool(re.search(r'^(?:python(?:3)?|grep|rg|test|jq)\b', variant, re.M)) and
                    'TODO' not in variant and 'exit 0' not in variant,
                    'non-trivial personal static check'))
    results.append((bool(re.search(r'^(?:[./\w-]*/)?python(?:3)?\s+-m\s+app\.cli\b', package, re.M)) and
                    'TODO' not in package and 'exit 0' not in package,
                    'real application run in package job'))
    env_step = any(isinstance(s, dict) and isinstance(s.get('env'), dict) and
                   'REPORT_MODE' in s['env'] for s in all_steps(jobs['package']))
    env_job = isinstance(jobs['package'].get('env'), dict) and 'REPORT_MODE' in jobs['package']['env']
    results.append((env_step or env_job, 'REPORT_MODE environment variable in package job'))
    unsafe = any(isinstance(s, dict) and s.get('continue-on-error') == 'true'
                 for job in (jobs[n] for n in ('quality', 'variant_check', 'package')) for s in all_steps(job))
    unsafe |= any(isinstance(job, dict) and job.get('continue-on-error') == 'true'
                  for job in (jobs[n] for n in ('quality', 'variant_check', 'package')))
    unsafe |= '|| true' in quality or '|| true' in variant or '|| true' in package
    results.append((not unsafe, 'no obvious masking of command failures'))
    dep_static = jobs['variant_check'].get('needs')
    dep_pack = jobs['package'].get('needs')
    dep_list = dep_pack if isinstance(dep_pack, list) else [dep_pack]
    results.append((dep_static == 'quality' and 'quality' in dep_list and 'variant_check' in dep_list,
                    'needs graph: quality -> variant_check -> package'))
    uploads = [s for s in all_steps(jobs['package']) if isinstance(s, dict) and
               'upload-artifact' in str(s.get('uses', ''))]
    has_upload = any(s.get('with', {}).get('name') == 'student-results' and
                     'dist/report.json' in str(s.get('with', {}).get('path', ''))
                     for s in uploads if isinstance(s.get('with'), dict))
    results.append((has_upload, 'upload-artifact name/path contract'))
    return results


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--repository', required=True)
    ap.add_argument('--student-status', required=True)
    ap.add_argument('--branch', required=True, help='student/<login>')
    ap.add_argument('--static', dest='static_code', default=None)
    ap.add_argument('--dynamic', dest='dynamic_code', default=None)
    ap.add_argument('--artifact-dir', type=Path, default=Path('collected'))
    ap.add_argument('--json-out', type=Path, default=Path('audit-report.json'))
    ap.add_argument('--root', type=Path, default=ROOT)
    args = ap.parse_args()
    root = args.root.resolve()
    results: list[tuple[bool, str]] = []

    def check(condition: bool, msg: str) -> None:
        results.append((bool(condition), msg))

    check(args.student_status == 'success', f'student workflow status = {args.student_status}')
    try:
        if not args.branch.startswith('student/') or args.branch.count('/') != 1:
            raise ValueError('audit must run on a student/<login> branch')
        branch_actor = args.branch.split('/', 1)[1]
        expected = select_variant(args.repository, branch_actor, args.static_code, args.dynamic_code)
        supplied = json.loads((root / 'variant.json').read_text(encoding='utf-8'))
        check(supplied == expected, 'variant.json matches repository-derived assignment')
    except Exception as exc:
        expected = None
        check(False, f'personal task unavailable or invalid: {exc}')

    results.extend(inspect_workflow(root / '.gitverse/workflows/student.yml'))

    if expected:
        is_valid, detail = static_ok(root, get_static(expected))
        check(is_valid, f'personal static requirement: {detail}')
        report_path = args.artifact_dir.resolve() / 'report.json'
        if report_path.is_file():
            try:
                report = json.loads(report_path.read_text(encoding='utf-8'))
                count, value, digest = expected_metric(expected['mode'], root / 'data/sales.csv')
                check(report.get('variant') == expected['variant_id'], 'artifact variant id')
                check(report.get('mode') == expected['mode'], 'artifact dynamic mode')
                check(type(report.get('rows')) is int and report['rows'] == count, 'artifact row count')
                check(isinstance(report.get('value'), str) and Decimal(report['value']) == Decimal(value),
                      'artifact computed metric')
                check(report.get('source_sha256') == digest, 'artifact input SHA256')
            except Exception as exc:
                check(False, f'artifact unreadable/invalid: {exc}')
        else:
            check(False, f'no downloaded artifact: {report_path}')

    for is_pass, description in results:
        print(f'[{"PASS" if is_pass else "FAIL"}] {description}')
    passed = all(ok for ok, _ in results)
    summary = {'result': 'PASS' if passed else 'FAIL', 'repository': args.repository,
               'checks': [{'pass': ok, 'description': name} for ok, name in results]}
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'RESULT: {summary["result"]}')
    return 0 if passed else 1


if __name__ == '__main__':
    raise SystemExit(main())
