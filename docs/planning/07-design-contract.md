# Apistra UX and UI Design Contract

Version: 0.2-draft
Status: IN_REVIEW

## 1. Scope and responsibility

This contract covers the 0.x web application, including installation bootstrap, project administration, endpoints, secrets, connectors, knowledge, workflow authoring, run inspection, human tasks, evaluation, and operational views.

The product owner approves the visual reference. An implementation agent cannot approve or invent missing visual decisions.

## 2. Confirmed brand inputs

Canonical current inputs:

- images/apistra-logo-primary.png
- images/apistra-github-avatar.png
- the dark technical workflow-editor screenshot supplied during discovery

Confirmed direction:

- dark technical interface
- high information density suitable for developers and AI engineers
- cyan-to-purple brand accent
- graph and orchestration character
- restrained, professional surfaces

Outstanding brand deliverables:

- documented ownership and usage rights
- vector master
- reversed wordmark for dark surfaces
- monochrome variants
- favicon and application icons
- minimum size, exclusion zone, and misuse rules

No logo redesign is authorised.

## 3. Design principles

1. Make execution state legible before decoration.
2. Keep workflow structure and configuration visible in context.
3. Make dangerous external effects explicit and interruptible.
4. Preserve keyboard access and non-drag alternatives.
5. Show provenance, version, project, and candidate context where decisions are made.
6. Use colour as reinforcement, never as the only status signal.
7. Prefer progressive disclosure over hiding operational detail.

## 4. Information architecture

Global shell:

- Installation status
- Project switcher
- Primary navigation
- Current project and environment
- Administrator menu
- Help and documentation

Project areas:

- Overview
- Workflows
- Agents
- Knowledge
- Connectors
- Model Endpoints
- Tools
- Runs
- Human Tasks
- Evaluations
- API Access
- Settings
- Audit

Initial page inventory:

- DSN-001 Sign in
- DSN-002 Bootstrap Administrator
- DSN-003 Project overview
- DSN-004 Project creation
- DSN-005 Endpoint catalogue and editor
- DSN-006 Secret reference manager
- DSN-007 Connector catalogue and configuration
- DSN-008 Knowledge source details and sync history
- DSN-009 Workflow list
- DSN-010 Visual workflow editor
- DSN-011 Canonical YAML or JSON editor
- DSN-012 Validation and test panel
- DSN-013 Publication review
- DSN-014 Published workflow and API contract
- DSN-015 Run list
- DSN-016 Run trace
- DSN-017 Human task inbox
- DSN-018 Human task decision
- DSN-019 Limits and policies
- DSN-020 Audit log
- DSN-021 Licence status

### 4.1 Information-architecture reference

Maintainable SVG source and generated PNG preview:

![Apistra application information architecture](../visuals/design/information-architecture.png)

## 5. Workflow editor contract

Large viewport:

- Top bar: workflow identity, draft or published state, version, save, validate, test, publish, layout, fit, canonical editor switch
- Left rail: searchable node palette grouped by flow, AI, tools, and data
- Centre: zoomable graph canvas
- Right inspector: selected node configuration, validation, policy, and version impact
- Lower or contextual panel: validation, run preview, trace, and diagnostics

Required non-drag interaction:

- Nodes can be added through keyboard-accessible commands.
- Connections can be created and inspected without pointer-only drag.
- Auto-layout does not change workflow semantics.

Canonical editor:

- Shows the same model as the visual canvas.
- Validation errors identify schema path and corresponding visual node.
- Switching representation cannot silently discard information.

### 5.1 DSN-010 workflow-editor reference

![Apistra workflow editor desktop reference](../visuals/design/workflow-editor-desktop.png)

This view defines information hierarchy and interaction placement. It does not assert implemented behaviour or final pixel identity.

### 5.2 DSN-016 run-trace reference

![Apistra run trace desktop reference](../visuals/design/run-trace-desktop.png)

### 5.3 DSN-018 human-approval references

Desktop:

![Apistra human approval desktop reference](../visuals/design/human-approval-desktop.png)

Mobile full-page view:

![Apistra human approval mobile reference](../visuals/design/human-approval-mobile.png)

## 6. Design tokens

Final values require rendered review. Required token roles:

- background.canvas
- background.application
- surface.default
- surface.elevated
- surface.interactive
- text.primary
- text.secondary
- text.disabled
- border.default
- border.strong
- accent.primary
- accent.secondary
- focus.visible
- status.information
- status.success
- status.warning
- status.error

Required scales:

- type hierarchy for page title, section, body, label, code, and metadata
- spacing
- radius
- border
- z-index
- motion duration and easing

No product state may be communicated by cyan, purple, green, amber, or red alone.

### 6.1 Design-system reference

![Apistra dark technical design-system reference](../visuals/design/design-system.png)

## 7. Component contracts

Priority components:

- Application shell
- Project switcher
- Navigation
- Data table
- Search and filter
- Form fields
- Secret input
- Endpoint selector
- Code editor
- Workflow node
- Connection and port
- Node palette
- Inspector panel
- Validation summary
- Status badge
- Limit meter
- Confirmation dialog
- Human approval card
- Run timeline
- Trace tree
- Toast and inline alert
- Empty, loading, error, offline, and permission states

Each component requires default, hover, focus, active, selected, disabled, loading, success, warning, and error states where applicable.

## 8. Responsive behaviour

Primary authoring target:

- Desktop width suitable for dense workflow design

Tablet:

- Canvas remains usable
- Palette and inspector become drawers
- No action is hover-only

Mobile:

- Supports review, run status, human tasks, and essential administration
- Full graph authoring may use a structured node list rather than reproducing the desktop canvas
- No critical approval information is truncated

Exact reference viewports are selected during the visual-reference workorder.

## 9. Accessibility

Target: WCAG 2.2 AA.

Required:

- semantic landmarks and headings
- complete keyboard path
- visible non-obscured focus
- accessible names, roles, values, and live status
- contrast measurement
- zoom and reflow
- reduced motion
- accessible graph alternatives
- error association and correction guidance
- minimum target sizes
- screen-reader smoke test for sign-in, workflow validation, publication, run inspection, and approval

## 10. Content and internationalisation

- English is the source locale.
- German is the first additional locale.
- No user-facing string is embedded in domain rules.
- Layouts allow text expansion.
- Dates and times include timezone context.
- Code, identifiers, API fields, and machine statuses remain stable English contracts.
- Errors state what happened, which input or action is affected, and a safe correction path.
- Sensitive provider or infrastructure details are not exposed.

## 11. Page states

Every relevant view defines:

- initial and loading
- empty
- populated
- success
- validation error
- technical error and retry
- conflict
- permission denied
- expired session
- disabled or archived
- offline or endpoint unavailable
- large data and pagination

The editor additionally defines:

- invalid graph
- unresolved reference
- unsaved changes
- concurrent draft modification
- published read-only version
- run in progress
- limit warning and hard stop

## 12. Visual evidence gate

The dark direction is selected, but the design gate is not yet passed.

Now present:

- maintainable repo-native generator and SVG sources;
- generated PNG review previews;
- workflow-editor, run-trace, and human-approval references;
- desktop and mobile approval views;
- information architecture;
- initial token roles and component-state reference.

Still required before the first UI workorder is READY:

- product-owner review and explicit selection of reference version 0.2;
- logo rights, vector master, reversed wordmark, monochrome and icon variants;
- measured contrast, keyboard, focus, reflow, reduced-motion, and screen-reader evidence;
- detailed references for validation, error, conflict, permission, disabled, loading, empty, and offline states;
- final light-surface or print treatment where applicable;
- manual UI and UX test definitions published through the verified Softwaretest.it API.

The research screenshot is inspiration, not implementation evidence.

## 13. Design workorder status

- Brand direction: DECIDED
- Existing logo input: DECIDED
- Logo rights and production variants: BLOCKING for public brand release
- Information architecture: IN_REVIEW
- Tokens and component details: IN_REVIEW
- Rendered reference sources: PRESENT, approval pending
- Accessibility test oracles: DRAFT
- Human design approval: PENDING
