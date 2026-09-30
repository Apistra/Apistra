import { readFileSync, readdirSync } from "node:fs";
import { dirname, join, relative, resolve, sep } from "node:path";
import { spawnSync } from "node:child_process";

const repositoryRoot = resolve(import.meta.dirname, "../..");
const sourceRoot = join(repositoryRoot, "apps/web/src");

function collectTypeScriptFiles(directory) {
  return readdirSync(directory, { withFileTypes: true }).flatMap((entry) => {
    const path = join(directory, entry.name);
    if (entry.isDirectory()) return collectTypeScriptFiles(path);
    return entry.isFile() && /\.tsx?$/.test(entry.name) ? [path] : [];
  });
}

const sourceFiles = collectTypeScriptFiles(sourceRoot);
if (sourceFiles.length === 0) {
  console.error("Architecture scope is empty: apps/web/src contains no TypeScript files.");
  process.exit(2);
}

const importPattern = /(?:from\s+|import\s*\(\s*|import\s*)["']([^"']+)["']/g;
const boundaryViolations = [];
for (const sourceFile of sourceFiles) {
  const sourceRelative = relative(sourceRoot, sourceFile).split(sep).join("/");
  const sourceFeature = sourceRelative.match(/^features\/([^/]+)\//)?.[1];
  const text = readFileSync(sourceFile, "utf8");
  for (const match of text.matchAll(importPattern)) {
    if (!match[1].startsWith(".")) continue;
    const target = relative(sourceRoot, resolve(dirname(sourceFile), match[1])).split(sep).join("/");
    const internalFeature = target.match(/^features\/([^/]+)\/internal(?:\/|$)/)?.[1];
    if (internalFeature && sourceFeature !== internalFeature) {
      boundaryViolations.push(`${sourceRelative} imports ${target}`);
    }
  }
}

if (boundaryViolations.length > 0) {
  console.error("ARCH-012 public feature contract violations:");
  for (const violation of boundaryViolations) console.error(`- ${violation}`);
  process.exit(1);
}

const cruiser = join(repositoryRoot, "node_modules/dependency-cruiser/bin/dependency-cruiser.mjs");
const result = spawnSync(
  process.execPath,
  [cruiser, "--config", ".dependency-cruiser.cjs", "apps/web/src"],
  { cwd: repositoryRoot, encoding: "utf8" }
);

process.stdout.write(result.stdout ?? "");
process.stderr.write(result.stderr ?? "");
process.exit(result.status ?? 1);
