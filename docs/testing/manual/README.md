# Manual Test Definitions

Status: DRAFT

This directory contains repository-authoritative manual test definitions. Each
case has one immutable `MT-PRC-NN-NNN` identifier and one file. Softwaretest.it
is the execution and evidence system, but publication never replaces the local
definition or changes a draft into an approved test implicitly.

Rules:

- every case starts from a logged-out session at the sign-in page;
- every step names the acting role, performs one action or observation, supplies
  one concrete data item or protected reference, and has one objective expected
  result;
- credentials remain protected parameter references and never appear in the
  definition or evidence;
- definition, review, publication, read-back verification, fixture readiness,
  execution, result reporting, and capability acceptance are separate states;
- a reserved ID is never renamed or reused.

Packages:

- [MTP-PRC-01 — Administration and project lifecycle](PRC-01/README.md)
