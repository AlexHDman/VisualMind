# DECISION OBJECTS

## Purpose

`Decision_Objects.md` answers one question: what decision objects are created, confirmed, modified and transferred during the Creative Reasoning Pipeline.

It defines the smallest complete object model required for Creative Engine to express explainable creative decisions. It does not define their implementation, storage, interface or processing sequence.

## Decision Object

A Decision is one explicit, justified creative choice made by Creative Engine within an approved decision area. It records what has been decided, why it is justified, which conditions apply and whether the user has confirmed it.

A Decision represents a decision, not a visual asset, prompt, production instruction or business decision made on behalf of the user.

## Mandatory Fields

| Field | Purpose |
| --- | --- |
| **Decision ID** | Identifies the Decision within its Creative Specification. |
| **Decision Area** | Identifies the professional area of the decision, such as communication, message, emotional strategy, visual strategy or information hierarchy. |
| **Decision Statement** | States the selected direction in human-readable form. |
| **Rationale** | Explains why the direction supports the objective, audience and context. |
| **Source References** | Identifies the relevant context, research and professional knowledge used to justify the Decision. |
| **Constraints** | States conditions that limit or qualify the Decision. |
| **Assumptions** | States information treated as true because it has not been established as fact. |
| **Risks** | States conditions that may weaken the intended result or require clarification. |
| **State** | Records whether the Decision is Draft, Confirmed or Revised. |
| **User Confirmation** | Records whether the user has confirmed the Decision and the confirmed Creative Summary that establishes shared understanding. |

The mandatory fields make each Decision transparent and reviewable. A field may state that no known constraint, assumption or risk applies; it must not be omitted.

## Decision States

### Draft

A Draft is a proposed Decision that has not received user confirmation. It may inform a Creative Summary but cannot be transferred to the Generator.

### Confirmed

A Confirmed Decision has explicit user confirmation through the agreed Creative Summary. Only Confirmed Decisions may form the Creative Specification passed to the Generator.

### Revised

A Revised Decision replaces or updates a previously proposed or confirmed direction. It records the current proposed change and requires user confirmation before it becomes Confirmed.

## User Confirmation

User Confirmation is represented by the mandatory **User Confirmation** field and the **Confirmed** state.

The field must identify the confirmed Creative Summary and state whether the user has accepted the Decision. A Decision is not confirmed merely because Creative Engine considers it justified. User Authority remains external to the Decision object: the object records the user’s confirmation; it does not create it.

## Creative Specification

Creative Specification is the final collection of Confirmed Decision objects for one approved creative direction. It contains no Draft or Revised Decisions.

The collection preserves the rationale, constraints, assumptions and risks required to understand the approved direction. It is the creative decision output of Creative Engine, not a visual asset or a production method.

## Structured Result

Structured Result is the transport container that carries the confirmed Creative Specification to the Generator. It preserves the Creative Specification and the metadata required to identify its purpose, source and confidence.

Structured Result does not redefine Decisions or add unconfirmed creative directions. The Generator receives the confirmed Creative Specification through this container.

## Boundaries

`Creative_Reasoning_Pipeline.md` defines the reasoning sequence, confirmation point and local recalculation rule. `Creative_Engine.md` defines the Engine’s responsibility for forming decisions. `Decision_Objects.md` defines only the objects exchanged within those established boundaries.
