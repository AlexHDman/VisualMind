# GENERATION SPECIFICATION

## Purpose

`Generation_Specification.md` answers one question: how is a Confirmed Creative Specification prepared for image generation?

A Generation Specification is the production-ready interpretation of an already confirmed Creative Specification. It makes the approved creative direction usable by the Generator without adding, changing or re-evaluating creative decisions.

## Relationship to Creative Specification

Creative Specification is the authoritative collection of confirmed creative Decisions. Generation Specification is derived exclusively from it for production.

Generation Specification does not replace Creative Specification and is not a new decision source. If required production information is absent or conflicts with the confirmed direction, the specification is incomplete; no new creative decision may be introduced to resolve the gap.

## Mandatory Contents

Every Generation Specification must contain:

| Content | Purpose |
| --- | --- |
| **Source Reference** | Identifies the Confirmed Creative Specification from which it is derived. |
| **Required Content** | States the approved message, subject, product, brand content and other required elements. |
| **Visual Direction** | States the approved visual strategy and information hierarchy. |
| **Spatial Direction** | States the approved composition direction and required relationships between key elements. |
| **Text Direction** | States the approved typography and required textual content. |
| **Colour Direction** | States the approved colour strategy and brand constraints. |
| **Emotional Direction** | States the approved emotional strategy. |
| **Production Constraints** | States the approved Digital Asset type, required format, supplied source materials and exclusions. |
| **Preservation Requirements** | States decisions and constraints that must not be changed in production. |

All contents are interpretations of Confirmed Decisions. A field may identify that no requirement applies, but it must not introduce a new creative direction.

## Responsibility Boundaries

Creative Engine owns the Confirmed Creative Specification and all creative reasoning that precedes it. The Generator owns production of Digital Assets from the confirmed direction.

Generation Specification owns neither creative reasoning nor production. Its only responsibility is to express the confirmed direction in a complete production-ready form.

It must not:

- redefine the message, audience, emotional strategy, visual strategy or information hierarchy;
- add unconfirmed content, assumptions or creative alternatives;
- select a model, API, prompt syntax or production technology;
- replace user confirmation or reopen an approved Decision.

## Output Passed to the Generator

The output is the **Generation Specification**, derived exclusively from the Confirmed Creative Specification and passed to the Generator as its production-ready interpretation.

It remains bound to its source Confirmed Creative Specification. The Generator therefore receives no new creative authority: it produces Digital Assets from the approved direction and must return any required creative change to the established decision process.
