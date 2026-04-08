// Base services
export {
  ApiClient,
  apiClient,
  type ApiClientOptions,
  callApi,
} from './base/api-client'

export {
  Cache,
  type CacheEntry,
  globalCache,
} from './base/cache'

export {
  ApiError,
  handleApiError,
  withErrorHandling,
} from './base/error-handler'

export {
  CodeService,
  codeService,
} from './modules/code-service'

// Module services
export {
  ConfigService,
  configService,
} from './modules/config-service'

export {
  FileService,
  fileService,
} from './modules/file-service'

export {
  TaskService,
  taskService,
} from './modules/task-service'
