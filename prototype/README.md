# VisualMind Prototype 0.2.3

## VisualMind Studio GUI — Prototype 0.3

Prototype 0.3 adds a PySide6 desktop interface over the existing tested Creative Engine and Generator contracts. The CLI remains available as a diagnostic tool; GUI widgets display and edit state but do not contain creative reasoning.

The Studio window contains:

- a task field and `Анализировать` action;
- an editable Context panel with highlighted blocking gaps;
- Creative Directions, decision rationale, risks, Creative Summary and explicit confirmations;
- Production Readiness status, Generation Specification and embedded SVG preview;
- generation of a deterministic SVG, JSON decision trace and model-agnostic TXT Generation Prompt.

Supported GUI formats:

- WhatsApp 9:16 — 1080×1920;
- square 1:1 — 1080×1080;
- landscape — 1200×628.

Install the GUI into the project-local `.venv`:

```powershell
"C:\AI\AI_VisualMind\install_visualmind_gui.bat"
```

Run VisualMind Studio:

```powershell
"C:\AI\AI_VisualMind\run_visualmind_gui.bat"
```

The existing CLI remains available:

```powershell
python "C:\AI\AI_VisualMind\prototype\visualmind_prototype.py"
```

### Prototype 0.3.1 — deterministic natural-request parsing

CLI and GUI now use the same deterministic parser for explicit Russian request fields. It supports labeled Product, Audience, Topic, CTA and Action constructions with `«...»`, `"..."` and `“...”` quotes. Expected Action is normalized as intent while Display CTA preserves confirmed viewer-facing wording. Extracted product names remain user context only: verified-facts and research gaps stay open, and no product or medical property is inferred.

### Prototype 0.3.1 completion status

VisualMind Studio GUI has successfully completed the full local end-to-end route:

```text
Natural-language request → Parsed Context → Knowledge Gaps → Creative Directions
→ Creative Summary → User Confirmations → Production Readiness
→ SVG + JSON Decision Trace + TXT Generation Prompt
```

The current SVG is a deterministic technical layout used to validate architecture, content transfer, geometry and preview integration. It is not a production-quality visual asset.

Local Qwen models, ComfyUI and a CUDA-powered Generator are not connected in Prototype 0.3.1. No external or local image model participates in generation yet.

Known GUI defects retained for the next iteration:

- the selected Creative Direction indicator is not visible enough;
- vertical SVG Preview proportions are displayed incorrectly;
- typography in the technical SVG is too small;
- some English headings remain in the Russian interface.

Local console proof of an intelligent CIM decision chain:

```text
User Request → Task Understanding → Knowledge Gate
→ STOP when blocking knowledge gaps exist
→ Semantic Model → Creative Alternatives → User Direction → Creative Summary → User Confirmation
→ Confirmed Creative Specification → Generation Specification → Generator
→ SVG image + JSON decision trace
```

The prototype uses no external AI provider. It does not search websites or social networks yet. It can consume an approved research summary, refuses to invent a missing commercial product, and keeps internet Knowledge Acquisition outside the Creative Engine boundary.

Prototype 0.2 adds:

- a semantic model of brand, offer, audience, objective and expected action;
- blocking and non-blocking knowledge-gap detection;
- three contextual creative directions with a recommendation, rationale and risk;
- a meaningful audience-relevant hero instead of a generic decorative person;
- explicit trust evidence and call to action;
- a complete Generation Specification;
- a deterministic SVG preview and JSON production trace;
- local recalculation after a changed context field.
- a strict blocking gate: Creative Directions and Decisions do not exist until all blocking knowledge gaps are resolved;
- fully Russian console output when the User Request is in Russian;
- one Task Understanding output per run and complete Visual Hero descriptions.

Prototype 0.2.2 corrections:

- command-like answers such as `Сделай постер для кальция в Fohow` are not accepted as product names;
- a topic such as `кальций`, `суставы` or `профилактика остеопороза` does not close the blocking Product gap;
- when a new answer changes the topic, VisualMind asks for confirmation and recalculates the Semantic Model and dependent Decisions locally;
- a direction can be selected with Enter, a number, its name or a natural phrase such as `профилактика остеопороза`;
- an unclear direction answer produces another question instead of a traceback.

Prototype 0.2.3 production-readiness corrections:

- a Production Readiness Gate blocks generation unless Product, audience, confirmed Display CTA, channel, Asset Type, dimensions, knowledge gaps and Creative Specification are ready;
- Brand cannot be used as Product, and a topic/category still cannot replace an exact product name;
- Expected Action is kept as user intent while Display CTA is separate, professional production copy shown in Creative Summary and confirmed by the user;
- format is always explicit: WhatsApp Status 9:16 produces 1080×1920 and Landscape social image produces 1200×628;
- Generator consumes confirmed dimensions instead of silently selecting 1200×628;
- SVG key blocks are validated before saving; meta/CTA overlap and geometry outside the viewBox stop generation.

## Run interactively

```powershell
python "C:\AI\AI_VisualMind\prototype\visualmind_prototype.py"
```

The console starts from an ordinary request and prints Task Understanding once. If blocking knowledge gaps exist, it stops before Creative Reasoning and asks only for the missing blocking information. Creative Directions become available only after the gate is cleared. A confirmed direction is required before an asset can be created.

For a Russian User Request, all runtime headings, explanations, questions, validation messages and result paths are displayed in Russian. Confirmation commands are `подтвердить`, `изменить` and `направление`; their English equivalents remain accepted.

When the Product question is shown, enter the exact approved product name. A task command or a general topic is not a product and leaves the blocking gap open.

When the format is missing, select `WhatsApp Status 9:16` or `Landscape social image`. The prototype never infers production dimensions from a generic `Постер` request.

Creative Summary displays both the intended action and the final Display CTA. Production confirmation confirms the displayed wording; conversational input is not copied to the SVG automatically.

## Analyse a short request without generation

```powershell
python "C:\AI\AI_VisualMind\prototype\visualmind_prototype.py" `
  --request "Сделай постер FOHOW о профилактике суставов" `
  --analysis-only
```

This exposes the concrete product, audience and CTA gaps and exits before Creative Directions instead of silently turning the topic into an invented offer.

## Run a deterministic demonstration

```powershell
python "C:\AI\AI_VisualMind\prototype\visualmind_prototype.py" `
  --request "Сделай постер FOHOW о профилактике суставов" `
  --objective "Объяснить пользу профилактики и пригласить на консультацию" `
  --audience "Взрослые 50+" `
  --brand "FOHOW" `
  --product "Название утверждённого продукта FOHOW" `
  --asset-type "WhatsApp status 9:16" `
  --expected-action "Напишите в WhatsApp" `
  --trust-evidence "Только утверждённые сведения из каталога FOHOW" `
  --research "Утверждённая локальная сводка продукта" `
  --direction product `
  --auto-confirm
```

The generated SVG and its JSON decision trace are written to `output` by default.

## Run tests

```powershell
python -m unittest discover -s "C:\AI\AI_VisualMind\prototype" -p "test_*.py" -v
```
