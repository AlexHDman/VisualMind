# CREATIVE REASONING PIPELINE

## Purpose

`Creative_Reasoning_Pipeline.md` answers one question: how Creative Engine transforms a user request into a confirmed Creative Specification before generation.

The pipeline is the smallest complete workflow for the first VisualMind implementation. It creates explainable creative decisions, not visuals; reasoning remains collaborative, and the user retains final authority before any production begins.

## Pipeline

```text
User Request
        ↓
Context and Research
        ↓
Semantic Model
        ↓
Creative Reasoning
        ↓
Creative Summary
        ↓
User Confirmation
        ↓
Confirmed Creative Specification
        ↓
Generator
```

### 1. User Request

The user states the need, objective or desired outcome. A request starts reasoning; it is not a command to generate.

### 2. Context and Research

Creative Engine uses the available Creative Context and Structured Research Result to identify the objective, audience, message, brand context, constraints and success criteria. If information required for a justified decision is missing, the workflow returns to user clarification or research; it does not continue with an undefined assumption.

### 3. Semantic Model

Creative Engine constructs the semantic model of the brand, product, audience and objective. This model establishes the decision context for all later creative reasoning and follows **Semantic Model Before Visual Decisions** in `VISUALMIND_PRINCIPLES.md`.

### 4. Creative Reasoning

Creative Engine applies the approved knowledge sources: Foundation, Perception Model, Composition, Typography, Color Psychology and Emotional Design. It produces the minimal justified set of decisions required for the communication strategy, message, emotional strategy, visual strategy, information hierarchy and expected action.

Each decision is accompanied by its rationale, constraints, assumptions and relevant risks. The Engine does not create visuals or select production methods.

### 5. Creative Summary

Creative Engine expresses the proposed direction in a human-readable Creative Summary. It enables the user to understand what is proposed, why it is proposed and which outcome is expected without reading a prompt or implementation detail.

### 6. User Confirmation

User confirmation is mandatory before generation. The user may confirm the Creative Summary or request a change; Creative Engine provides recommendations, but never makes the final decision for the user.

### 7. Confirmed Creative Specification

After confirmation, Creative Engine completes the Creative Specification and returns it as a Structured Result with the approved decisions, rationale, constraints and assumptions. This is the stable creative decision output of the pipeline.

### 8. Generator

The Generator receives the confirmed Creative Specification. It produces the Digital Asset; it does not replace Creative Engine reasoning or reopen unconfirmed creative decisions.

## Decision Change and Local Recalculation

Each stage depends only on the decisions established before it. When the user changes a decision, Creative Engine identifies the earliest affected stage and recalculates only that stage and its downstream decisions.

```text
Changed Context or Decision
        ↓
Earliest Affected Stage
        ↓
Recalculate Downstream Decisions
        ↓
Updated Creative Summary
        ↓
User Confirmation
```

Upstream decisions that remain valid are preserved. Any changed Creative Summary requires renewed user confirmation before a new Creative Specification is passed to the Generator.

## Workflow Guarantees

- The workflow has only defined states: clarification or research, reasoning, summary for confirmation, confirmed specification, or generation.
- Generation cannot begin from an unconfirmed request, incomplete context or superseded decision.
- Every major decision is traceable through its rationale, constraints, assumptions and risks in the Structured Result.
- The pipeline applies **Professional Reasoning Before Generation** and **User Confirmation Before Production** from `VISUALMIND_PRINCIPLES.md`.
- `DECISION_FLOW.md` remains the authoritative workflow for user participation and confirmation; this document defines the Creative Engine reasoning sequence within that workflow.

## Output

The only creative output passed to the Generator is the confirmed Creative Specification. It contains the decisions required for production and their documented justification; it is not a visual asset or a production instruction set.
