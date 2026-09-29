# Apistra Visual Planning Artefacts

Version: 0.2-draft
Status: IN_REVIEW

This package supplies the maintainable visual sources that complement the textual BuildBySpec planning baseline.

It contains:

- architecture and runtime diagrams under architecture;
- canonical BPMN 2.0 process definitions and readable SVG previews under processes;
- information architecture, UI references, and design-system views under design.

All artefacts are planning references. They are not implementation, test, deployment, or approval evidence.

## Reproduction

Run:

    python docs/visuals/generate_visuals.py

SVG and BPMN generation uses the Python standard library. PNG previews for architecture, processes, and design are produced when Pillow is installed. The generator reads the existing canonical logo from images/apistra-logo-primary.png; it does not redesign the logo.

## Architecture references

- ARC-CTX-01 — system context and trust boundaries
- ARC-CNT-01 — runtime containers
- ARC-MOD-01 — planned module dependencies
- ARC-DEP-01 — delivery and local staging deployment
- ARC-DOM-01 — core domain model
- ARC-SEQ-01 — durable run sequence
- ARC-SEQ-02 — human approval sequence
- ARC-SEQ-03 — knowledge synchronisation sequence

## Business-process references

- PRC-01 — configure installation and project
- PRC-02 — connect and index knowledge
- PRC-03 — author and publish a workflow
- PRC-04 — execute a published process through the API
- PRC-05 — complete a human approval
- PRC-06 — evaluate workflow quality
- PRC-07 — operate and recover Apistra

The BPMN files are the canonical process definitions. The adjacent SVG and PNG files are review-oriented previews generated from the same source specification.

## Design references

- DSN-IA-01 — application information architecture
- DSN-SYS-01 — design-system reference
- DSN-010 — workflow editor desktop
- DSN-016 — run trace desktop
- DSN-018 — human approval desktop and mobile

The dark technical direction reuses the product-owner-selected research reference and existing logo. It is not a new logo or unrelated visual direction.

## Approval state

Sources and previews are present. Product-owner design approval, logo-rights documentation, accessibility measurement, manual UI/UX test publication, and implementation evidence remain pending. The Design Gate is therefore still PENDING.
