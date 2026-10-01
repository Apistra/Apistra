import { join, resolve } from "node:path";
import { spawnSync } from "node:child_process";

const repositoryRoot = resolve(import.meta.dirname, "../..");
const cruiser = join(repositoryRoot, "node_modules/dependency-cruiser/bin/dependency-cruiser.mjs");

function runFixture(name) {
  return spawnSync(
    process.execPath,
    [
      cruiser,
      "--config",
      ".dependency-cruiser.cjs",
      `tests/architecture-fixtures/typescript/${name}`
    ],
    { cwd: repositoryRoot, encoding: "utf8" }
  );
}

const allowed = runFixture("allowed");
if (allowed.status !== 0) {
  process.stderr.write(allowed.stdout ?? "");
  process.stderr.write(allowed.stderr ?? "");
  console.error("The allowed TypeScript architecture fixture must pass.");
  process.exit(1);
}

const forbidden = runFixture("forbidden");
if (forbidden.status === 0) {
  console.error("The forbidden TypeScript architecture fixture must fail.");
  process.exit(1);
}

console.log("TypeScript architecture fixtures behaved as expected.");
