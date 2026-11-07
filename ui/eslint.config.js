import js from '@eslint/js'
import prettier from 'eslint-config-prettier/flat'
import pluginVue from 'eslint-plugin-vue'
import { defineConfig, globalIgnores } from 'eslint/config'
import globals from 'globals'
import tseslint from 'typescript-eslint'

/**
 * ESLint flat config for the rdx UI.
 *
 * Encodes the CLAUDE.md conventions that a linter can check: `<script setup lang="ts">` only,
 * no `any`, no `v-html` (DOMPurify arrives in Phase 1 with a dedicated directive), no bare
 * user-visible strings in templates (i18n keys only), cyclomatic complexity <= 25 as upstream.
 */
export default defineConfig(
  globalIgnores([
    'dist/',
    'node_modules/',
    'coverage/',
    'test-results/',
    'playwright-report/',
    'blob-report/',
  ]),
  js.configs.recommended,
  tseslint.configs.recommended,
  pluginVue.configs['flat/recommended'],
  {
    files: ['**/*.vue'],
    languageOptions: {
      parserOptions: {
        parser: tseslint.parser,
        extraFileExtensions: ['.vue'],
        sourceType: 'module',
      },
    },
  },
  {
    files: ['**/*.{js,ts,vue}'],
    languageOptions: {
      ecmaVersion: 'latest',
      sourceType: 'module',
      globals: { ...globals.browser, ...globals.node },
    },
    rules: {
      complexity: ['error', 25],
      'no-console': ['error', { allow: ['warn', 'error'] }],
      '@typescript-eslint/no-explicit-any': 'error',
      '@typescript-eslint/consistent-type-imports': ['error', { fixStyle: 'inline-type-imports' }],
      '@typescript-eslint/no-unused-vars': ['error', { argsIgnorePattern: '^_' }],
      'vue/block-lang': ['error', { script: { lang: 'ts' } }],
      'vue/component-api-style': ['error', ['script-setup']],
      'vue/define-macros-order': 'error',
      'vue/no-v-html': 'error',
      'vue/no-bare-strings-in-template': 'error',
      'vue/no-unused-refs': 'error',
      'vue/require-typed-ref': 'error',
      'vue/no-useless-v-bind': 'error',
      'vue/prefer-true-attribute-shorthand': 'error',
    },
  },
  prettier,
)
