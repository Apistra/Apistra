/** @type {import('dependency-cruiser').IConfiguration} */
module.exports = {
  forbidden: [
    {
      name: "ARCH-013-no-circular-dependencies",
      severity: "error",
      comment: "The TypeScript module graph must remain acyclic.",
      from: {},
      to: { circular: true }
    },
    {
      name: "ARCH-011-no-entrypoint-to-feature-internals",
      severity: "error",
      comment: "Application entrypoints consume feature public contracts only.",
      from: { path: "^apps/web/src/app/" },
      to: { path: "^apps/web/src/features/[^/]+/internal/" }
    }
  ],
  options: {
    doNotFollow: { path: "node_modules" },
    exclude: { path: "(^|/)dist/|(^|/)coverage/" },
    includeOnly: "^(apps/web/src|tests/architecture-fixtures/typescript)",
    enhancedResolveOptions: { exportsFields: ["exports"] },
    reporterOptions: { text: { highlightFocused: true } }
  }
};
