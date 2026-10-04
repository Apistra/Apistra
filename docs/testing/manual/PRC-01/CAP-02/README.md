# MTP-PRC-01/CAP-02 — Safe AI configuration

Version: 0.1
Status: REVIEWED LOCALLY; NOT PUBLISHED; NOT EXECUTED
Capability: CAP-02
Definition owner: WO-CAP-02-06
Execution owner: WO-CAP-02-07

This package extends PRC-01 with eight independently executable manual cases.
Every case starts logged out, resolves its own sign-in and navigation steps,
uses only deterministic synthetic fixture data, and keeps credentials behind
protected runtime references. The fixture descriptors are generated with:

```text
python -m tools.fixtures.cap_02.generator setup --run-id <safe-run-id>
python -m tools.fixtures.cap_02.generator verify --run-id <safe-run-id>
```

Descriptor generation does not apply product state and is not execution
evidence. The future guarded CAP-02 fixture applicator must verify candidate,
environment, project ownership, credential references, and reset scope before
WO-CAP-02-07 may execute these cases.

Cases:

- MT-PRC-01-007 — write-only secret creation and replacement
- MT-PRC-01-008 — foreign, revoked, tampered, and unresolved secret denial
- MT-PRC-01-009 — offline endpoint save and bounded safe probe
- MT-PRC-01-010 — immutable agent reference retention
- MT-PRC-01-011 — tool effect and approval-policy enforcement
- MT-PRC-01-012 — exact resource/cost limit boundaries
- MT-PRC-01-013 — optimistic policy conflict and input retention
- MT-PRC-01-014 — responsive, keyboard, focus, permission, and session states
