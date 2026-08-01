# Creative Engine

## Purpose

Creative Engine преобразует результаты исследования в профессиональный, объяснимый набор творческих решений для рекламной коммуникации.

Он использует Creative Methodology для формирования Creative Specification. Creative Engine создаёт решения, а не визуальные материалы.

## Input

Creative Engine получает:

- Creative Context
- Structured Research Result
- Creative Methodology

## Responsibilities

Creative Engine отвечает только за:

- анализ целей клиента;
- определение коммуникационной стратегии;
- определение эмоционального направления;
- определение ключевого сообщения;
- определение психологических факторов;
- определение визуальной стратегии;
- определение информационной структуры;
- формирование понятного обоснования решения и Creative Summary для подтверждения пользователем;
- формирование Creative Specification.

Creative Engine не создаёт конечный рекламный материал, не выполняет производство и не принимает бизнес-решения за клиента.

## Output

Creative Specification и обоснование принятых творческих решений.

Creative Specification является обязательным входом Production Engine.

## Dependencies

Creative Engine использует:

- Creative Context
- Structured Research Result
- Creative Methodology

Creative Engine возвращает Structured Result, содержащий Creative Specification, обоснование, ограничения и допущения.

## Architectural Role

Creative Engine является слоем совместного профессионального рассуждения между исследованием и производством. Он применяет следующие фундаментальные свойства:

- **Creative Engine creates decisions, not visuals.** Результатом являются обоснованные творческие решения и спецификация, а не визуальный материал.
- **Collaborative Reasoning.** Engine формирует рекомендации совместно с пользователем и предоставляет понятный Creative Summary до производства.
- **User Authority.** Пользователь подтверждает направление; Engine не подменяет его окончательное решение.
- **Deterministic Workflow.** Engine следует установленной последовательности: контекст и исследование → анализ → Creative Summary → подтверждение → Creative Specification. Ни один этап не пропускается.
- **Local Recalculation.** При изменении контекста или подтверждённого направления пересчитываются только затронутые решения; не затронутые части сохраняются.
- **Decision Transparency.** Каждое решение передаётся с обоснованием, ограничениями и допущениями в Structured Result.
