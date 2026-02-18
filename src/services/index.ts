// Base services
export {
  ApiClient,
  apiClient,
  callApi,
  type ApiClientOptions,
} from "./base/api-client";

export {
  ApiError,
  handleApiError,
  withErrorHandling,
} from "./base/error-handler";

export {
  Cache,
  globalCache,
  type CacheEntry,
} from "./base/cache";

// Module services
export {
  ConfigService,
  configService,
} from "./modules/config-service";

export {
  FileService,
  fileService,
} from "./modules/file-service";

export {
  CodeService,
  codeService,
} from "./modules/code-service";

export {
  TaskService,
  taskService,
} from "./modules/task-service";
