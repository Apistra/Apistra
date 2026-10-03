# CAP-01 Manual Acceptance Execution Guide

Status: READY FOR HUMAN EXECUTION
Owning workorder: [WO-CAP-01-05](../../../workorders/CAP-01/WO-CAP-01-05.md)

This guide prepares one immutable local candidate for the six published
`MT-PRC-01-*` cases. It does not mark a case as executed or accepted.

## 1. Build and start the candidate

Run from the repository root in WSL:

```bash
python3 tools/release/build_candidate.py
python3 -m tools.staging.manual_acceptance start \
  artifacts/cap00-candidate/candidate-manifest.json \
  --run-id cap01-acceptance-01
```

The command prints secret-free session identity and URLs. The generated local
credential file is named in `password_file`; it is created with owner-only
permissions below the ignored `artifacts/acceptance/CAP-01/` tree. Read it only
in the local terminal and never copy it into screenshots, notes, commits, or
Softwaretest.it evidence.

## 2. Execute the six cases

Use a fresh private browser profile for every case. Before each case, reset the
exact required fixture:

```bash
python3 -m tools.staging.manual_acceptance fixture FX-PRC-01-FRESH \
  --run-id cap01-acceptance-01
python3 -m tools.staging.manual_acceptance fixture FX-PRC-01-ADMIN-NO-PROJECT \
  --run-id cap01-acceptance-01
python3 -m tools.staging.manual_acceptance fixture FX-PRC-01-ISOLATION \
  --run-id cap01-acceptance-01
```

Execute the cases in this order and use the fixture declared by each file:

1. `MT-PRC-01-001` with `FX-PRC-01-FRESH`;
2. `MT-PRC-01-002` and `MT-PRC-01-003` with a fresh reset of
   `FX-PRC-01-ADMIN-NO-PROJECT` before each case;
3. `MT-PRC-01-004` with `FX-PRC-01-ISOLATION`;
4. `MT-PRC-01-005` with `FX-PRC-01-ADMIN-NO-PROJECT`;
5. `MT-PRC-01-006` with `FX-PRC-01-ISOLATION`.

Each reset writes a secret-free receipt into the session evidence directory.
Record every atomic step result and the required screenshots in
Softwaretest.it against the candidate commit printed by the session tool.

## 3. Check and close the session

```bash
python3 -m tools.staging.manual_acceptance status --run-id cap01-acceptance-01
python3 -m tools.staging.manual_acceptance stop --run-id cap01-acceptance-01
```

`stop` removes containers and volumes and deletes the local runtime secrets.
The secret-free session and fixture receipts remain below
`artifacts/acceptance/CAP-01/cap01-acceptance-01/` for the acceptance record.

Do not merge or promote the candidate after execution until all six cases,
candidate-bound Softwaretest.it receipts, independent implementation review,
and explicit human CAP-01 acceptance are complete.
