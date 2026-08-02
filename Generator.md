# GENERATOR

## Purpose

`Generator.md` answers one question: what is the responsibility of the Generator within VisualMind?

The Generator transforms a confirmed Creative Specification into one or more Digital Assets. It performs production from approved creative decisions; it does not create, evaluate or replace those decisions.

## Architectural Role

The Generator is the production boundary of VisualMind. It receives the stable creative decision output of Creative Engine and produces the corresponding Digital Asset or assets.

The Generator is independent of any underlying image model. A model may be changed without changing this architectural responsibility or the contract with Creative Engine.

## Responsibilities

The Generator must:

- consume only a confirmed Creative Specification;
- transform the confirmed creative decisions into one or more Digital Assets;
- preserve the approved intent, constraints and required content of the Creative Specification during production;
- return the produced Digital Asset or assets as the result of production;
- maintain the association between each output and the confirmed Creative Specification from which it was produced.

## Non-Responsibilities

The Generator must not:

- perform creative reasoning, research or professional analysis;
- construct or modify the semantic model, communication strategy, emotional strategy, visual strategy or information hierarchy;
- redefine, supplement or override confirmed Decisions;
- accept an unconfirmed request, Draft Decision or Revised Decision as production input;
- make a final decision for the user;
- define user confirmation, workflow, Decision objects or Creative Engine interfaces;
- own prompt engineering, model-specific behaviour, API definitions or production technology choices.

## Inputs

The only creative input to the Generator is the **Confirmed Creative Specification**. It is carried by the Structured Result defined by `Decision_Objects.md` and contains only Confirmed Decisions.

The Generator may receive this input from any underlying production technology, but no additional creative instruction may alter the confirmed direction.

## Outputs

The Generator returns one or more **Digital Assets** produced from the Confirmed Creative Specification.

An output is a production result. It does not become a new creative decision or alter the confirmed Creative Specification.

## Boundaries with Creative Engine

Creative Engine owns professional creative reasoning, the Creative Summary, user-confirmed Decisions and the Confirmed Creative Specification. The Generator owns only the transformation of that approved specification into Digital Assets.

If a produced result requires a change to the approved creative direction, the change belongs outside the Generator boundary and must return to Creative Engine through the established decision process. The Generator must not resolve the change autonomously.
