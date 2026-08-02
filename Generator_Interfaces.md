# GENERATOR INTERFACES

## Purpose

`Generator_Interfaces.md` answers one question: what information enters the Generator, and what information leaves it?

It defines the smallest interface contract required for the first VisualMind prototype. It does not define workflow, prompting, model selection, APIs, object structure or creative reasoning.

## Required Inputs

| Input | Provider / Owner | Contract requirement |
| --- | --- | --- |
| **Generation Specification** | Production preparation boundary | Must be derived exclusively from a Confirmed Creative Specification and identify that source. |

The Generator accepts no unconfirmed request, Draft or Revised Decision, alternative creative direction or additional creative instruction. Source materials and production constraints, when required, are contained in the Generation Specification.

## Required Outputs

| Output | Consumer | Contract requirement |
| --- | --- | --- |
| **Digital Asset or Assets** | Authorised VisualMind consumer | Produced from the received Generation Specification. |
| **Source Association** | Authorised VisualMind consumer | Identifies the Generation Specification and Confirmed Creative Specification from which the output was produced. |

The output association preserves traceability. It does not alter the Confirmed Creative Specification or create a new creative Decision.

## External Dependencies

- **Generation Specification:** the required production-ready input from the established preparation boundary.
- **Underlying image model or production technology:** may perform the transformation into Digital Assets without changing the Generator interface contract.
- **Supplied source materials:** may be used only when identified by the received Generation Specification.

No other external dependency is required by this contract.

## Interface Boundaries

- `Creative_Engine.md` owns creative reasoning and confirmed creative decisions; Generator does not perform or change them.
- `Generation_Specification.md` owns the production-ready interpretation of the confirmed direction; Generator consumes it without supplementing it.
- `Decision_Objects.md` owns Decision definitions and states; Generator accepts only their confirmed final collection through the Generation Specification.
- Generator owns only the transformation of the received direction into Digital Assets and preservation of the source association.
- If a production result requires a creative change, the Generator returns no substitute decision; the change belongs to the established Creative Engine decision boundary.
