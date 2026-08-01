# ENGINE INTERFACES

## Purpose

`Engine_Interfaces.md` answers one question: what information enters Creative Engine, and what information leaves it.

It defines the smallest interface contract required for the first VisualMind implementation. It does not define workflow, reasoning logic, object structure, APIs or implementation.

## Required Inputs

| Input | Provider / Owner | Contract purpose |
| --- | --- | --- |
| **User Request** | User | States the requested need, objective or desired outcome. |
| **Creative Context** | Project context | Provides the available goal, audience, message, constraints and success criteria. |
| **Structured Research Result** | Research function | Provides relevant researched facts, findings, gaps and confidence. |
| **User Confirmation** | User | Confirms or rejects the Creative Summary; confirmation is required before a Confirmed Creative Specification can be emitted. |

Creative Engine receives these inputs; it does not change their source records or invent missing facts. Missing information is represented as a gap, assumption or clarification need in its output.

## Knowledge Sources

Creative Engine uses the following approved knowledge sources as governing and professional inputs:

| Knowledge source | Interface role |
| --- | --- |
| `VISUALMIND_PRINCIPLES.md` | Permanent constraints on Creative Engine responsibility and decision-making. |
| `FOUNDATION.md` | Identifies the stable Foundation knowledge scope. |
| `HUMAN_PERCEPTION.md` | Knowledge of human perception. |
| `GESTALT.md` | Knowledge of automatic visual organisation. |
| `PERCEPTION_MODEL.md` | Contract for evaluating a creative direction through perception. |
| `COMPOSITION.md` | Knowledge of visual-space organisation. |
| `TYPOGRAPHY.md` | Knowledge of effective textual information transfer. |
| `COLOR_PSYCHOLOGY.md` | Knowledge of colour strategy. |
| `EMOTIONAL_DESIGN.md` | Knowledge of emotional strategy. |

These documents remain their own Source of Truth. Creative Engine applies their knowledge but does not modify or redefine it.

## Required Outputs

| Output | Consumer | Contract purpose |
| --- | --- | --- |
| **Creative Summary** | User | Human-readable proposed direction for review and confirmation. |
| **Confirmed Creative Specification** | Generator | Final collection of confirmed creative decisions required for production. |
| **Structured Result** | Generator and other authorised VisualMind components | Transport container carrying the Confirmed Creative Specification with its rationale, constraints, assumptions and risks. |

Creative Engine must not emit a Confirmed Creative Specification or a Generator-ready Structured Result until user confirmation is available.

## External Dependencies

- **User:** owns the request, clarification and final confirmation of the proposed direction.
- **Research function:** owns the Structured Research Result; Creative Engine consumes rather than performs research.
- **Generator:** consumes the confirmed Creative Specification and produces the Digital Asset; it does not own creative reasoning.

No other dependency is required by this interface contract.

## Interface Boundaries

- `DECISION_FLOW.md` owns the user participation and confirmation sequence; Creative Engine provides the Summary required by that sequence.
- `Creative_Reasoning_Pipeline.md` owns the reasoning sequence and local recalculation rule; this document only names the information crossing the Engine boundary.
- `Decision_Objects.md` owns the definition and states of Decision objects; this document does not redefine them.
- Creative Engine owns the creation of creative decisions, the Creative Summary and the Creative Specification.
- User authority remains outside Creative Engine: the Engine records confirmation but cannot create it.
- Generator receives confirmed decisions only; it does not receive authority to alter them.
