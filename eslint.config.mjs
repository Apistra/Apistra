import parser from "@typescript-eslint/parser";

export default [
  {
    files: [
      "apps/web/src/**/*.{ts,tsx}",
      "tools/**/*.mjs",
      "tests/complexity-fixtures/typescript/**/*.ts",
    ],
    languageOptions: {
      parser,
      parserOptions: {
        ecmaVersion: "latest",
        sourceType: "module",
      },
    },
    rules: {
      complexity: ["error", { max: 10, variant: "classic" }],
    },
  },
];
