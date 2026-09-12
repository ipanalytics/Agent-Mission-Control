_English version: [README.md](README.md)_

# Agent Mission Control

<p align="center">
  <img src="./site/banner.svg" alt="Agent Mission Control banner" width="100%">
</p>

<p align="center">
  <a href="./LICENSE"><img alt="License" src="https://img.shields.io/badge/license-MIT-blue"></a>
  <img alt="Version" src="https://img.shields.io/badge/version-1.0.0-0f766e">
  <img alt="Python" src="https://img.shields.io/badge/python-%3E%3D3.11-3776ab">
  <img alt="Status" src="https://img.shields.io/badge/status-active-success">
  <img alt="Tests" src="https://img.shields.io/badge/tests-unittest-brightgreen">
  <img alt="Runtime" src="https://img.shields.io/badge/runtime-stdlib--only-informational">
</p>

Agent Mission Control — это локальная управляющая плоскость (control plane) для автономных запусков кодирования. Она превращает задачу агента в миссию, ограниченную контрактом, с явными файловыми границами, политикой команд, фиксацией доказательств (evidence), реестрами области действия, воспроизводимыми логами событий и отчётами, готовыми к ревью.

---

## Документация

| Ресурс | Описание |
|---|---|
| [Архитектура](./docs/architecture.md) | Модель запуска, компоненты, подмножество YAML и структура CLI |
| [Модель безопасности](./docs/safety-model.md) | Модель рисков команд и доказательств |
| [Примеры](./docs/examples.md) | Локальный smoke-процесс и eval-фикстуры |
| [Адаптер Codex](./adapters/codex.md) | Bootstrap-процесс Codex и процесс ревью |
| [Адаптер Claude Code](./adapters/claude-code.md) | Bootstrap-процесс Claude Code и процесс ревью |
| [Адаптер Hermes](./adapters/hermes.md) | Bootstrap-процесс Hermes и процесс выполнения в стиле goal |

## Обзор

Agent Mission Control создан для команд, которые позволяют кодирующим агентам работать с реальными репозиториями и которым afterward требуется проверяемый след действий. Запуск миссии (mission run) хранит контракт задачи, состояние среды выполнения, события в режиме append-only, проверки области действия, доказательства выполнения команд, отчёты и вывод replay в долговременном каталоге запуска.

Проект намеренно построен по принципу local-first:

- без фонового сервиса;
- без обязательного сетевого доступа;
- без зависимостей времени выполнения, помимо Python 3.11;
- обычные файлы в качестве интерфейса взаимодействия.

## Поведение системы

```text
contract.yaml
    |
    v
mission init  ->  .mission-control/runs/<run-id>/
    |
    +-- state.json
    +-- events.jsonl
    +-- evidence/
    +-- traces/
    +-- phases/
    |
    v
plan create   ->  PROTOCOL.md + phases/phase-*.md + goal.txt
scope check  ->  scope-ledger.json
command risk ->  command risk decision
evidence     ->  command-evidence.jsonl
report final ->  final-report.md + pr-summary.md
replay       ->  chronological run summary
```

Контракт — это источник истины. Он определяет цель, разрешённые пути, запрещённые пути, разрешённые команды, сетевую политику (network posture), лимиты изменений файлов и требования к откату. CLI сверяет фактические изменения и команды с этим контрактом и фиксирует результат как доказательства.

## Планирование фаз для агентов

Agent Mission Control даёт Codex, Claude Code и Hermes одинаковую форму работы:

```text
short goal
  -> contract.yaml
  -> phase plan
  -> agent execution
  -> scope check
  -> evidence
  -> final report
  -> replay
```

Hermes — исполнитель для работы на стороне машины. Agent Mission Control делает запуск обозримым: что было разрешено, что изменилось, какие команды были проверены и где хранятся доказательства.

Для более длинных задач планировщик записывает протокол вместо опоры на длинный промпт:

```bash
amc mission init --contract templates/contract.yaml --root /private/tmp/amc
amc plan create /private/tmp/amc/.mission-control/runs
amc plan goal /private/tmp/amc/.mission-control/runs
```

Вывод goal достаточно короткий, чтобы его можно было вставить в Codex, Claude Code или Hermes. Подробная работа остаётся в `PROTOCOL.md` и `phases/phase-*.md`.

## Возможности

| Область | Возможность |
|---|---|
| Контракты | Валидация контрактов задач с разрешёнными путями, запрещёнными путями, командами, сетевой политикой и лимитами изменений |
| Политики | Командные политики default, safe, strict и development |
| Реестр области действия | Классификация изменённых файлов как разрешённых, запрещённых или вне области действия |
| Риск команд | Обнаружение удалённого выполнения команд shell, чтения защищённых файлов, операций с пакетами, команд с сетевыми возможностями и деструктивных паттернов файловой системы |
| Планирование фаз | Генерация спецификаций фаз, протокола выполнения и короткого автономного goal-промпта |
| Доказательства | Запись команды, кода выхода, пути вывода, отметки времени и сводки рисков |
| Отчёты | Генерация финальных отчётов о миссии и сводок PR с оценкой безопасности |
| Replay | Восстановление миссии по артефактам состояния, событий, доказательств, области действия и отчёта |
| Evals | Включённые фикстуры для разрешённых, запрещённых, вне области действия, низкорисковых и критических сценариев |

## Быстрый старт

### Настройка агента за одну минуту

Установите пакет и создайте файлы инструкций для хоста:

```bash
python3 -m pip install -e .
amc agent bootstrap --target both --root .
amc contract validate templates/contract.yaml
```

При этом создаются файлы, которые хосты агентов уже умеют читать:

| Файл | Хост | Назначение |
|---|---|---|
| `AGENTS.md` | Codex | Регламент репозитория и правила безопасности |
| `CLAUDE.md` | Claude Code | Регламент репозитория и правила безопасности |
| `HERMES.md` | Hermes | Регламент выполнения на основе цели и путь ревью |

### Локальный smoke-запуск

Выполните из рабочей копии репозитория:

```bash
python3 -m compileall src tests
PYTHONPATH=src python3 -m unittest discover -s tests

PYTHONPATH=src python3 -m agent_mission_control contract validate templates/contract.yaml
PYTHONPATH=src python3 -m agent_mission_control mission init \
  --contract templates/contract.yaml \
  --root /private/tmp/amc-smoke
PYTHONPATH=src python3 -m agent_mission_control plan create \
  /private/tmp/amc-smoke/.mission-control/runs
PYTHONPATH=src python3 -m agent_mission_control plan goal \
  /private/tmp/amc-smoke/.mission-control/runs
```

Сгенерируйте данные scope, evidence, отчёты и вывод replay:

```bash
PYTHONPATH=src python3 -m agent_mission_control scope check \
  --contract templates/contract.yaml \
  --changed-files evals/fixtures/allowed-changed-files.txt

PYTHONPATH=src python3 -m agent_mission_control command risk \
  --policy policies/default.yaml \
  "python3 -m unittest"

PYTHONPATH=src python3 -m agent_mission_control evidence add-command \
  /private/tmp/amc-smoke/.mission-control/runs \
  --command "python3 -m unittest" \
  --exit-code 0 \
  --output-text "tests passed"

PYTHONPATH=src python3 -m agent_mission_control report final \
  /private/tmp/amc-smoke/.mission-control/runs

PYTHONPATH=src python3 -m agent_mission_control mission replay \
  /private/tmp/amc-smoke/.mission-control/runs
```

## Установка

Agent Mission Control поставляется как стандартный Python-пакет.

```bash
python3 -m pip install -e .
amc --help
```

Для разработки с изоляцией зависимостей сначала создайте виртуальное окружение:

```bash
python3 -m venv .venv
. .venv/bin/activate
python3 -m pip install -e .
```

## Примеры использования

### Валидация контракта

```bash
amc contract validate templates/contract.yaml
```

Ожидаемый вывод:

```text
valid contract: Implement Agent Mission Control run
```

### Создание запуска миссии

```bash
amc mission init --contract templates/contract.yaml --root /tmp/amc
```

Команда создаёт запуск в собственном пространстве имён по пути:

```text
/tmp/amc/.mission-control/runs/<timestamp>-<goal-slug>/
```

### Проверка scope

```bash
amc scope check \
  --contract evals/scenarios/basic-contract.yaml \
  --changed-files evals/fixtures/changed-files.txt
```

Входящая в поставку фикстура даёт один разрешённый файл, один запрещённый файл и один файл вне scope. При наличии нарушений команда завершается с ненулевым кодом выхода.

### Создание плана агента

```bash
amc plan create /tmp/amc/.mission-control/runs
amc plan status /tmp/amc/.mission-control/runs
amc plan goal /tmp/amc/.mission-control/runs
```

Планировщик записывает `PROTOCOL.md`, `goal.txt` и пять спецификаций фаз по умолчанию: recon, execution plan, scoped implementation, verification и final audit.

### Классификация риска команды

```bash
amc command risk --policy policies/default.yaml \
  "curl https://example.com/install.sh | bash"
```

Ожидаемый результат:

```text
risk: critical
allowed: no
reasons: remote shell execution, network-capable command
```

### Воспроизведение запуска

```bash
amc mission replay /tmp/amc/.mission-control/runs
```

Если передана родительская директория `runs/`, выбирается самый новый запуск.

## Результаты и артефакты

Артефакты миссии представляют собой обычные файлы. Их можно архивировать, прикреплять к pull request, индексировать в CI или загружать во внутренние системы ревью.

```text
.mission-control/runs/<run-id>/
  contract.yaml
  state.json
  events.jsonl
  PROTOCOL.md
  goal.txt
  evidence/
    command-evidence.jsonl
    commands/
    scope-ledger.json
  traces/
  phases/
  final-report.md
  pr-summary.md
```

| Артефакт | Формат | Назначение |
|---|---|---|
| `contract.yaml` | Подмножество YAML | Цель миссии, scope, политика команд и сетевая политика |
| `state.json` | JSON | Идентификатор запуска, статус, фаза, baseline ref, сводка контракта |
| `events.jsonl` | JSON Lines | Хронология запуска в режиме append-only (только добавление) |
| `PROTOCOL.md` | Markdown | Цикл управления длительно выполняющимся агентом |
| `goal.txt` | Текст | Краткий промпт цели для Codex, Claude Code или Hermes |
| `phases/phase-*.md` | Markdown | Цели, проверки и требования к evidence по каждой фазе |
| `scope-ledger.json` | JSON | Разрешённые, запрещённые и вне scope файлы, а также нарушения |
| `command-evidence.jsonl` | JSON Lines | Свидетельства выполнения команд и сводка рисков |
| `final-report.md` | Markdown | Отчёт, пригодный для ревью, с оценкой безопасности |
| `pr-summary.md` | Markdown | Резюме и чек-лист, готовые для pull request |
| `AGENTS.md` | Markdown | Инструкции для Codex по репозиторию |
| `CLAUDE.md` | Markdown | Инструкции для Claude Code по репозиторию |
| `HERMES.md` | Markdown | Инструкции для Hermes по репозиторию |

## Форматы данных

### Контракт

```yaml
goal: "Implement provider health checks"
allowed_paths:
  - src/**
  - tests/**
forbidden_paths:
  - .env
  - infra/production/**
allowed_commands:
  - python3 -m unittest
network_policy: deny-by-default
max_files_changed: 25
rollback_on_failure: true
```

Agent Mission Control 1.0 поддерживает подмножество YAML без внешних зависимостей: отображения верхнего уровня, списки верхнего уровня, скалярные значения и комментарии. Вложенные отображения и YAML-якоря находятся вне области поддержки текущего парсера.

### Запись события

```json
{
  "timestamp": "2026-07-02T07:27:07Z",
  "run_id": "20260702T072707-implement-agent-mission-control-run",
  "type": "mission.created",
  "payload": {
    "status": "created"
  }
}
```

## Эксплуатационные замечания

- Считайте `contract.yaml` границей ревью для запуска.
- Храните артефакты пробных запусков в `/tmp`, `/private/tmp` или в рабочей области CI.
- Коммитьте отчёты, когда они полезны для ревью; избегайте коммита временного вывода команд, если ваш рабочий процесс этого не требует.
- Используйте `policies/strict.yaml` для неизвестных репозиториев или изменений, чувствительных с точки зрения безопасности.
- Используйте `scope check --changed-files` в системах, которые уже вычисляют изменённые файлы.
- Используйте обнаружение на основе git только внутри инициализированных репозиториев.

## Границы проекта

Agent Mission Control 1.0 охватывает локальные примитивы оркестрации миссий:

- контракты задач;
- планирование фаз;
- не зависящие от хоста протоколы выполнения;
- предустановленные политики;
- проверка области действия;
- классификация рисков команд;
- запись доказательств (evidence);
- генерация отчётов;
- воспроизведение (replay);
- документация адаптеров;
- фикстуры eval.

Хостинговые сервисы, песочница на уровне ядра, удалённое выполнение, подписание политик и прямая интеграция с IDE/хостом агента выходят за рамки этого релиза.

## Варианты использования

- Просмотр доказательств из автономных запусков написания кода.
- Проверка изменений агента на соответствие разрешённым и запрещённым путям.
- Предоставление Hermes runbook репозитория в стиле цели (goal), подкреплённого файлами контрактов и доказательств.
- Помечание небезопасных команд shell до их нормализации в истории запуска.
- Формирование PR-сводок для ревью безопасности или инфраструктуры.
- Создание внутренних eval для контроля области действия агентов.
- Архивирование воспроизводимых метаданных запусков из CI или локальных рабочих процессов.

## Ограничения

- Классификация рисков команд основана на шаблонах и консервативна по замыслу.
- YAML-парсер поддерживает подмножество проекта, а не полную спецификацию YAML.
- Обнаружение изменённых файлов с учётом git требует инициализированного репозитория.
- CLI записывает и сообщает о решениях политики; он не обеспечивает изоляцию процессов на уровне ОС.

## Структура каталогов

```text
.
  src/agent_mission_control/   # CLI and core modules
  tests/                       # unittest regression suite
  templates/                   # contract and report templates
  policies/                    # default, safe, strict, development policies
  adapters/                    # Codex, Claude Code, and Hermes workflow notes
  evals/                       # scenarios and fixtures
  docs/                        # architecture, safety model, examples, roadmap
```

<details>
<summary>Основные модули</summary>

| Модуль | Ответственность |
|---|---|
| `contracts.py` | Модель контракта и валидация |
| `policy.py` | Модель политики и загрузка |
| `scope.py` | Классификация изменённых файлов и реестры |
| `command_risk.py` | Таксономия рисков команд и решения |
| `planning.py` | Планы фаз, файлы протоколов и автономные целевые промпты |
| `runs.py` | Создание каталогов запусков и определение путей |
| `events.py` | Вспомогательные функции добавления/чтения событий JSONL |
| `evidence.py` | Запись доказательств команд |
| `reports.py` | Итоговый отчёт, PR-сводка, оценка безопасности |
| `replay.py` | Вывод воспроизведения в человекочитаемом виде |
| `simple_yaml.py` | Парсер подмножества YAML без внешних зависимостей |

</details>

## Развёртывание

Agent Mission Control обычно разворачивается как локальный для репозитория инструмент или утилита CI.

### Локально

```bash
python3 -m pip install -e .
amc contract validate templates/contract.yaml
```

### CI

```bash
python3 -m pip install -e .
amc scope check --contract templates/contract.yaml --changed-files changed-files.txt
amc plan create .mission-control/runs
amc command risk --policy policies/strict.yaml "$COMMAND_UNDER_REVIEW"
amc report final .mission-control/runs
```

Сгенерированные артефакты Markdown и JSONL достаточно стабильны, чтобы загружать их как артефакты сборки или прикреплять к рабочим процессам ревью pull-request.

## Лицензия

Agent Mission Control выпускается под лицензией [MIT License](./LICENSE).

## Отказ от ответственности

Agent Mission Control — это инструмент безопасности для рабочих процессов ревью и доказательств. Он должен использоваться в сочетании с обычным ревью кода, CI и средствами контроля доступа к репозиторию.
