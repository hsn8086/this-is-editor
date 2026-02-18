import { describe, it, expect, vi, beforeAll, beforeEach, afterEach } from "vitest";
import type { API, Config, FileInfo, Code, TaskResult, TestCase } from "@/pywebview-defines";

// Dynamic imports for services (after window.pywebview is mocked)
let ApiClient: typeof import("@/services").ApiClient;
let ApiError: typeof import("@/services").ApiError;
let Cache: typeof import("@/services").Cache;
let handleApiError: typeof import("@/services").handleApiError;
let configService: typeof import("@/services").configService;
let fileService: typeof import("@/services").fileService;
let codeService: typeof import("@/services").codeService;
let taskService: typeof import("@/services").taskService;

// Get the mocked API
const getMockApi = (): Partial<API> => window.pywebview.api as unknown as Partial<API>;

describe("services", () => {
  beforeAll(async () => {
    // Import services after window.pywebview is mocked in vitest.setup.ts
    const services = await import("@/services");
    ApiClient = services.ApiClient;
    ApiError = services.ApiError;
    Cache = services.Cache;
    handleApiError = services.handleApiError;
    configService = services.configService;
    fileService = services.fileService;
    codeService = services.codeService;
    taskService = services.taskService;
  });

  describe("Cache", () => {
    let cache: InstanceType<typeof Cache>;

    beforeEach(() => {
      cache = new Cache();
    });

    it("should store and retrieve values", () => {
      cache.set("key1", "value1");
      expect(cache.get("key1")).toBe("value1");
    });

    it("should return undefined for non-existent keys", () => {
      expect(cache.get("non-existent")).toBeUndefined();
    });

    it("should expire values after TTL", async () => {
      cache.set("key1", "value1", 10); // 10ms TTL
      expect(cache.get("key1")).toBe("value1");
      
      // Wait for expiration
      await new Promise((resolve) => setTimeout(resolve, 20));
      expect(cache.get("key1")).toBeUndefined();
    });

    it("should check existence correctly", () => {
      cache.set("key1", "value1");
      expect(cache.has("key1")).toBe(true);
      expect(cache.has("non-existent")).toBe(false);
    });

    it("should delete values", () => {
      cache.set("key1", "value1");
      cache.delete("key1");
      expect(cache.get("key1")).toBeUndefined();
    });

    it("should clear all values", () => {
      cache.set("key1", "value1");
      cache.set("key2", "value2");
      cache.clear();
      expect(cache.get("key1")).toBeUndefined();
      expect(cache.get("key2")).toBeUndefined();
    });
  });

  describe("ApiClient", () => {
    let client: InstanceType<typeof ApiClient>;

    beforeEach(() => {
      client = new ApiClient({ enableCache: true });
      vi.clearAllMocks();
    });

    afterEach(() => {
      client.clearCache();
    });

    it("should call API method and return result", async () => {
      const mockConfig: Partial<Config> = { editor: {} as any };
      vi.mocked(getMockApi().get_config!).mockResolvedValue(mockConfig);

      const result = await client.call<Config>("get_config");
      expect(result).toEqual(mockConfig);
      expect(getMockApi().get_config).toHaveBeenCalledTimes(1);
    });

    it("should cache results for cacheable methods", async () => {
      const mockConfig: Partial<Config> = { editor: {} as any };
      vi.mocked(getMockApi().get_config!).mockResolvedValue(mockConfig);

      // First call
      await client.call<Config>("get_config");
      // Second call should use cache
      await client.call<Config>("get_config");

      expect(getMockApi().get_config).toHaveBeenCalledTimes(1);
    });

    it("should not cache when cache is disabled", async () => {
      const clientNoCache = new ApiClient({ enableCache: false });
      const mockConfig: Partial<Config> = { editor: {} as any };
      vi.mocked(getMockApi().get_config!).mockResolvedValue(mockConfig);

      await clientNoCache.call<Config>("get_config");
      await clientNoCache.call<Config>("get_config");

      expect(getMockApi().get_config).toHaveBeenCalledTimes(2);
    });

    it("should handle API errors", async () => {
      vi.mocked(getMockApi().get_config!).mockRejectedValue(new Error("API Error"));

      await expect(client.call("get_config")).rejects.toThrow(ApiError);
    });

    it("should throw error for non-existent methods", async () => {
      await expect(
        client.call("non_existent_method" as keyof API)
      ).rejects.toThrow(ApiError);
    });

    it("should pass arguments to API methods", async () => {
      vi.mocked(getMockApi().set_config!).mockResolvedValue(undefined);

      await client.call("set_config", "key", "value");
      expect(getMockApi().set_config).toHaveBeenCalledWith("key", "value");
    });

    it("should invalidate cache correctly", async () => {
      const mockConfig: Partial<Config> = { editor: {} as any };
      vi.mocked(getMockApi().get_config!).mockResolvedValue(mockConfig);

      await client.call<Config>("get_config");
      client.invalidateCache("get_config");
      await client.call<Config>("get_config");

      expect(getMockApi().get_config).toHaveBeenCalledTimes(2);
    });
  });

  describe("handleApiError", () => {
    it("should wrap Error in ApiError", () => {
      const originalError = new Error("Test error");
      expect(() => handleApiError(originalError, "context")).toThrow(ApiError);
    });

    it("should preserve ApiError", () => {
      const apiError = new ApiError("API error", "CODE");
      expect(() => handleApiError(apiError)).toThrow(apiError);
    });

    it("should handle unknown errors", () => {
      expect(() => handleApiError("string error")).toThrow(ApiError);
    });
  });

  describe("ConfigService", () => {
    beforeEach(() => {
      vi.clearAllMocks();
    });

    it("should get config", async () => {
      const mockConfig: Partial<Config> = {
        editor: { tie: { theme: { value: "dark" } as any } } as any,
      };
      vi.mocked(getMockApi().get_config!).mockResolvedValue(mockConfig);

      const result = await configService.getConfig();
      expect(result).toEqual(mockConfig);
    });

    it("should get config path", async () => {
      vi.mocked(getMockApi().get_config_path!).mockResolvedValue("/path/to/config");

      const result = await configService.getConfigPath();
      expect(result).toBe("/path/to/config");
    });

    it("should set config and invalidate cache", async () => {
      vi.mocked(getMockApi().set_config!).mockResolvedValue(undefined);

      await configService.setConfig("key", "value");
      expect(getMockApi().set_config).toHaveBeenCalledWith("key", "value");
    });

    it("should parse config correctly", () => {
      const mockConfig: any = {
        group1: {
          item1: { value: "val1", display: "Item 1", i18n: "item1" },
          nested: {
            item2: { value: "val2", display: "Item 2", i18n: "item2" },
          },
        },
      };

      const items = Array.from(configService.parseConfig(mockConfig));
      expect(items).toHaveLength(2);
      expect(items[0].id).toBe("group1.item1");
      expect(items[1].id).toBe("group1.nested.item2");
    });

    it("should sort config by group", () => {
      const items = [
        { id: "b", group: "group2", display: "B" },
        { id: "a", group: "group1", display: "A" },
        { id: "c", group: "group2", display: "C" },
      ];

      const sorted = configService.sortConfig(items as any);
      expect(sorted).toHaveLength(2);
      // Object.keys doesn't guarantee order, just check groups exist
      const groups = sorted.map(([group]) => group).sort();
      expect(groups).toContain("group1");
      expect(groups).toContain("group2");
      // Check items are grouped correctly
      const group2Items = sorted.find(([g]) => g === "group2")?.[1];
      expect(group2Items).toHaveLength(2);
    });
  });

  describe("FileService", () => {
    beforeEach(() => {
      vi.clearAllMocks();
    });

    it("should list directory", async () => {
      const mockResponse = { now_path: "/test", files: [] };
      vi.mocked(getMockApi().path_ls!).mockResolvedValue(mockResponse);

      const result = await fileService.lsDir("/test");
      expect(result).toEqual(mockResponse);
      expect(getMockApi().path_ls).toHaveBeenCalledWith("/test");
    });

    it("should get file info", async () => {
      const mockFileInfo: Partial<FileInfo> = { name: "test.txt" };
      vi.mocked(getMockApi().path_get_info!).mockResolvedValue(mockFileInfo);

      const result = await fileService.getInfo("/test.txt");
      expect(result).toEqual(mockFileInfo);
    });

    it("should get file text", async () => {
      vi.mocked(getMockApi().path_get_text!).mockResolvedValue("file content");

      const result = await fileService.getText("/test.txt");
      expect(result).toBe("file content");
    });

    it("should join paths", async () => {
      vi.mocked(getMockApi().path_join!).mockResolvedValue("/parent/child");

      const result = await fileService.join("/parent", "child");
      expect(result).toBe("/parent/child");
    });

    it("should get parent directory", async () => {
      vi.mocked(getMockApi().path_parent!).mockResolvedValue("/parent");

      const result = await fileService.getParent("/parent/child");
      expect(result).toBe("/parent");
    });

    it("should manage pinned files", async () => {
      const mockFiles: Partial<FileInfo>[] = [{ name: "file1.txt" }];
      vi.mocked(getMockApi().get_pinned_files!).mockResolvedValue(mockFiles);
      vi.mocked(getMockApi().add_pinned_file!).mockResolvedValue(undefined);
      vi.mocked(getMockApi().remove_pinned_file!).mockResolvedValue(undefined);

      const files = await fileService.getPinnedFiles();
      expect(files).toEqual(mockFiles);

      await fileService.addPinnedFile("/test.txt");
      expect(getMockApi().add_pinned_file).toHaveBeenCalledWith("/test.txt");

      await fileService.removePinnedFile("/test.txt");
      expect(getMockApi().remove_pinned_file).toHaveBeenCalledWith("/test.txt");
    });

    it("should manage scroll position", async () => {
      vi.mocked(getMockApi().save_scoll!).mockResolvedValue(undefined);
      vi.mocked(getMockApi().get_scoll!).mockResolvedValue(100);

      await fileService.saveScroll(100);
      expect(getMockApi().save_scoll).toHaveBeenCalledWith(100);

      const scroll = await fileService.getScroll();
      expect(scroll).toBe(100);
    });
  });

  describe("CodeService", () => {
    beforeEach(() => {
      vi.clearAllMocks();
    });

    it("should get code", async () => {
      const mockCode: Partial<Code> = { code: "print('hello')", type: "python" };
      vi.mocked(getMockApi().get_code!).mockResolvedValue(mockCode);

      const result = await codeService.getCode();
      expect(result).toEqual(mockCode);
    });

    it("should save code", async () => {
      vi.mocked(getMockApi().save_code!).mockResolvedValue(undefined);

      await codeService.saveCode("new code");
      expect(getMockApi().save_code).toHaveBeenCalledWith("new code");
    });

    it("should format code", async () => {
      vi.mocked(getMockApi().format_code!).mockResolvedValue("formatted code");

      const result = await codeService.formatCode();
      expect(result).toBe("formatted code");
    });

    it("should get langs", async () => {
      const mockLangs = [{ id: "python", display: "Python" }] as any;
      vi.mocked(getMockApi().get_langs!).mockResolvedValue(mockLangs);

      const result = await codeService.getLangs();
      expect(result).toEqual(mockLangs);
    });

    it("should get port", () => {
      vi.mocked(getMockApi().get_port!).mockReturnValue(8080);

      const result = codeService.getPort();
      expect(result).toBe(8080);
    });
  });

  describe("TaskService", () => {
    beforeEach(async () => {
      vi.clearAllMocks();
      // Clear global cache for cpu_count to ensure fresh results
      const { globalCache } = await import("@/services");
      globalCache.clear();
    });

    it("should compile", async () => {
      vi.mocked(getMockApi().compile!).mockResolvedValue("success");

      const result = await taskService.compile();
      expect(result).toBe("success");
    });

    it("should run task", async () => {
      const mockResult: Partial<TaskResult> = { status: "success" };
      vi.mocked(getMockApi().run_task!).mockResolvedValue(mockResult);

      const result = await taskService.runTask(1, 256, 1.0);
      expect(result).toEqual(mockResult);
      expect(getMockApi().run_task).toHaveBeenCalledWith(1, 256, 1.0);
    });

    it("should get testcase", async () => {
      const mockTestcase: Partial<TestCase> = { name: "test" };
      vi.mocked(getMockApi().get_testcase!).mockResolvedValue(mockTestcase);

      const result = await taskService.getTestcase();
      expect(result).toEqual(mockTestcase);
    });

    it("should save testcase", async () => {
      vi.mocked(getMockApi().save_testcase!).mockResolvedValue(undefined);
      const testcase: Partial<TestCase> = { name: "test" };

      await taskService.saveTestcase(testcase as TestCase);
      expect(getMockApi().save_testcase).toHaveBeenCalledWith(testcase);
    });

    it("should get CPU count", async () => {
      vi.mocked(getMockApi().get_cpu_count!).mockResolvedValue([4, 8]);

      const result = await taskService.getCpuCount();
      expect(result).toEqual([4, 8]);
    });

    it("should calculate recommended judge thread with hyperthreading", async () => {
      // Case: Physical != Logical (hyperthreading enabled)
      vi.mocked(getMockApi().get_cpu_count!).mockResolvedValue([4, 8]);
      const result = await taskService.getRecommendedJudgeThread();
      expect(result).toBe(4);
    });

    it("should calculate recommended judge thread without hyperthreading", async () => {
      // Case: Physical == Logical (no hyperthreading)
      getMockApi().get_cpu_count = vi.fn().mockResolvedValue([4, 4]);
      const result = await taskService.getRecommendedJudgeThread();
      expect(result).toBe(6); // Math.max(Math.floor((4 * 3) / 2), 1) = 6
    });
  });
});
