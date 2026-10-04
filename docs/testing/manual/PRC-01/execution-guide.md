# CAP-01 Manual Acceptance Execution Guide

Status: READY FOR HUMAN EXECUTION
Owning workorder: [WO-CAP-01-05](../../../workorders/CAP-01/WO-CAP-01-05.md)

This guide prepares one immutable local candidate for the six published
`MT-PRC-01-*` cases. It does not mark a case as executed or accepted.

## 1. Build and start the candidate

Run from the repository root in WSL:

```bash
python3 tools/release/build_candidate.py
run_id="cap01-acceptance-$(date -u +%Y%m%d-%H%M%S)"
python3 -m tools.staging.manual_acceptance start \
  artifacts/cap00-candidate/candidate-manifest.json \
  --run-id "${run_id}"
```

Keep the generated `run_id` in the same shell for all commands below. Every
run ID identifies one immutable evidence directory and must never be reused,
including after a stopped or failed run. If the shell is reopened, recover the
exact ID from `artifacts/acceptance/CAP-01/`; do not create a new ID for an
already running session.

The command prints secret-free session identity and URLs. The generated local
credential file is named in `password_file`; it is created with owner-only
permissions below the ignored `artifacts/acceptance/CAP-01/` tree. Read it only
in the local terminal and never copy it into screenshots, notes, commits, or
Softwaretest.it evidence.

The same output names `test_data_file`. This local JSON file resolves every
non-secret value needed by all six cases: the active fixture, candidate, URLs,
usernames, project IDs, names, keys, and the test-case-to-fixture mapping. It
contains only a reference to the protected password file, never the password.
Display it at any time with:

```bash
python3 -m json.tool \
  "artifacts/acceptance/CAP-01/${run_id}/manual-test-data.json"
```

With the default web port, the resolved URLs are:

- sign-in and overview: `http://127.0.0.1:13000`;
- bootstrap: `http://127.0.0.1:13000/bootstrap`;
- audit: `http://127.0.0.1:13000/audit`;
- Atlas: `http://127.0.0.1:13000/projects/11111111-1111-4111-8111-111111111111`;
- Orion: `http://127.0.0.1:13000/projects/22222222-2222-4222-8222-222222222222`;
- unknown project: `http://127.0.0.1:13000/projects/99999999-9999-4999-8999-999999999999`.

The JSON derives these URLs from the actual `--web-port`, so it remains the
authoritative execution data when a non-default port is selected.

## 2. Execute the six cases

Use a fresh private browser profile for every case. Before each case, reset the
exact required fixture:

```bash
python3 -m tools.staging.manual_acceptance fixture FX-PRC-01-FRESH \
  --run-id "${run_id}"
python3 -m tools.staging.manual_acceptance fixture FX-PRC-01-ADMIN-NO-PROJECT \
  --run-id "${run_id}"
python3 -m tools.staging.manual_acceptance fixture FX-PRC-01-ISOLATION \
  --run-id "${run_id}"
```

Execute the cases in this order and use the fixture declared by each file:

1. `MT-PRC-01-001` with `FX-PRC-01-FRESH`;
2. `MT-PRC-01-002` and `MT-PRC-01-003` with a fresh reset of
   `FX-PRC-01-ADMIN-NO-PROJECT` before each case;
3. `MT-PRC-01-004` with `FX-PRC-01-ISOLATION`;
4. `MT-PRC-01-005` with `FX-PRC-01-ADMIN-NO-PROJECT`;
5. `MT-PRC-01-006` with `FX-PRC-01-ISOLATION`.

Each reset writes a secret-free receipt into the session evidence directory.
It also updates `manual-test-data.json` so that `active_fixture` always names
the fixture currently applied to the local database.
Record every atomic step result and the required screenshots in
Softwaretest.it against the candidate commit printed by the session tool.

## 3. Check and close the session

```bash
python3 -m tools.staging.manual_acceptance status --run-id "${run_id}"
python3 -m tools.staging.manual_acceptance stop --run-id "${run_id}"
```

`stop` removes containers and volumes and deletes the local runtime secrets.
The secret-free session and fixture receipts remain below
`artifacts/acceptance/CAP-01/${run_id}/` for the acceptance record. Both
`status` and repeated `stop` remain safe after the runtime secrets have been
deleted.

Do not merge or promote the candidate after execution until all six cases,
candidate-bound Softwaretest.it receipts, independent implementation review,
and explicit human CAP-01 acceptance are complete.
