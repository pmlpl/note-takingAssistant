// ESLint flat config for Vue 3 + Vite
// 文档：https://eslint.org/docs/latest/use/configure/configuration-files
import js from '@eslint/js'
import vue from 'eslint-plugin-vue'
import browser from 'globals'

export default [
  // 基础 JS 规则
  js.configs.recommended,

  // Vue 3 推荐规则
  ...vue.configs['flat/recommended'],

  {
    files: ['**/*.{js,vue}'],
    languageOptions: {
      ecmaVersion: 2022,
      sourceType: 'module',
      globals: {
        ...browser.browser,
      },
    },
    rules: {
      // 项目实际宽松规则（避免大量改动）
      'vue/multi-word-component-names': 'off', // 允许单词组件名（如 Home.vue）
      'vue/max-attributes-per-line': 'off',    // 不强制每行一个属性
      'vue/singleline-html-element-content-newline': 'off',
      'vue/html-self-closing': 'off',
      'no-unused-vars': ['warn', { argsIgnorePattern: '^_' }],
      'no-console': 'off',                     // 允许 console（前端调试常用）
      'no-undef': 'warn',
    },
  },

  {
    // 测试文件宽松规则
    files: ['**/*.test.js', '**/*.spec.js'],
    languageOptions: {
      globals: {
        ...browser.browser,
        describe: 'readonly',
        it: 'readonly',
        test: 'readonly',
        expect: 'readonly',
        beforeEach: 'readonly',
        afterEach: 'readonly',
        beforeAll: 'readonly',
        afterAll: 'readonly',
        vi: 'readonly',
      },
    },
  },

  {
    // 配置文件忽略规则
    ignores: [
      'dist/**',
      'node_modules/**',
      '*.config.js',
      'components.d.ts',
    ],
  },
]