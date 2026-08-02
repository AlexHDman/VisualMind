# Prototype Changelog

## 0.3.2 — GUI Polish

- Added a high-visibility selected state for Creative Direction radio buttons and their cards.
- Replaced deforming SVG preview behaviour with centred aspect-ratio-preserving rendering.
- Increased technical SVG typography and spacing for vertical and landscape formats.
- Preserved the complete confirmed headline without text overlap or canvas overflow.
- Localized remaining user-facing GUI headings, messages and button labels into Russian.
- Added Qt tests for direction switching, preview resizing, aspect ratio and localization.
- Added regression tests for typography metrics, complete headline transfer and both SVG formats.
- Kept Creative Reasoning, Production Readiness and the user workflow unchanged.

## 0.3.1 — Deterministic natural-request parsing

- Added one shared parser for CLI and GUI request analysis.
- Extracted explicitly labeled Product, Audience, Topic, CTA and Action values from Russian requests.
- Added support for guillemets, straight quotes and typographic quotation marks.
- Kept normalized Expected Action separate from exact viewer-facing Display CTA.
- Preserved blocking gaps when CTA or audience is absent.
- Prevented Brand from being accepted as Product.
- Kept verified-facts and research gaps open after Product extraction.
- Added order-independent and CLI/GUI parity regression tests.
- Completed and verified the full GUI end-to-end route through SVG, JSON and TXT output.
- Confirmed that the SVG is currently a technical architecture-validation layout, not a production visual.
- Confirmed that local Qwen models, ComfyUI and a CUDA Generator are not connected yet.
- Recorded known GUI defects: an insufficiently visible selected-direction indicator, incorrect vertical preview proportions, undersized technical-SVG typography and remaining English headings.

## 0.3 — VisualMind Studio GUI

- Added a PySide6 desktop interface over the existing Creative Engine contracts.
- Kept all creative reasoning and production validation outside GUI widgets.
- Added editable Context, knowledge gaps, three Creative Directions, Creative Summary and explicit confirmations.
- Added responsive SVG preview, Generation Specification and Production Readiness panels.
- Added WhatsApp 9:16, square 1:1 and landscape format selection with explicit dimensions.
- Added model-agnostic TXT Generation Prompt alongside SVG and JSON output.
- Added dependency-aware confirmation invalidation after context changes.
- Added a testable GUI Controller with no PySide6 dependency.
- Added project-local installation and launch BAT files.

## 0.2.3 — Production Readiness Gate

- Added a mandatory pre-generation gate for Product, audience, confirmed Display CTA, explicit format, blocking gaps and confirmed Creative Specification.
- Blocked production when Product equals Brand or a topic/category is supplied instead of an exact Product.
- Separated Expected Action from professional Display CTA production copy.
- Added explicit format clarification for WhatsApp Status 9:16 (1080×1920) and Landscape social image (1200×628).
- Removed the Generator's silent 1200×628 fallback.
- Added deterministic SVG layout validation before file saving.
- Removed meta/CTA overlap and kept hero geometry inside the viewBox.
- Completed Russian hero output for Russian-language projects.
- Added production-readiness, CTA separation, format and SVG geometry regression tests.

## 0.2.2 — Product and direction input safety

- Added command-aware Product validation.
- Separated a general topic from an exact Product name.
- Kept the blocking Product gap open for commands and topic-only answers.
- Added topic-change detection and explicit user confirmation.
- Recalculated the Semantic Model and dependent Decisions after an approved topic change.
- Added natural-language direction selection using Enter, number, name or semantic wording.
- Replaced invalid-direction crashes with a safe repeated question.
- Added regression tests for Product validation, topic consistency and direction error handling.

## 0.2.1 — Real-test corrections

- Added a strict blocking gate before Creative Reasoning.
- Prevented Creative Directions, selected direction and Decisions from being created while blocking knowledge gaps remain.
- Started Creative Reasoning only after the last blocking gap is resolved.
- Localized all runtime output for Russian User Requests.
- Removed duplicate Task Understanding output.
- Replaced the incomplete `Hero` presentation with a complete localized Visual Hero description.
- Expanded unittest coverage for the blocking gate, delayed reasoning, Russian output and single Task Understanding output.

## 0.2 — Intelligent Creative Engine

- Added task understanding and a semantic model before visual decisions.
- Added blocking and non-blocking knowledge-gap detection.
- Added three explainable creative directions and explicit user selection.
- Added audience-relevant hero reasoning, trust strategy and call to action.
- Completed the Structured Result and Generation Specification contracts.
- Added 9:16-aware deterministic SVG generation and a JSON decision trace.
- Added tests for gaps, confirmation safety, semantic hero selection, local recalculation and output traceability.

## 0.1 — First end-to-end VisualMind implementation

- Proved the local request-to-SVG pipeline.
- Added Creative Summary and mandatory user confirmation.
- Added Confirmed Creative Specification and Generation Specification boundaries.
- Used a deterministic local SVG renderer with no external AI provider.
