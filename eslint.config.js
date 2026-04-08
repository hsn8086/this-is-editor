import vuetify from 'eslint-config-vuetify'

const vuetifyConfig = await vuetify()

export default [
  {
    ignores: [
      '.venv/**',
      'htmlcov/**',
      'coverage/**',
      'coverage.xml',
      '.coverage',
      'dist/**',
      'node_modules/**',
    ],
  },
  ...vuetifyConfig,
]
