import { describe, expect, it, vi } from "vitest";

import {
  createAndOpenItem,
  deleteItemAndRefresh,
  handleCreateInputKeydown,
  renameAndOpenItem,
} from "@/components/file-sel-create";

describe("handleCreateInputKeydown", () => {
  it("should create item when Enter is pressed", async () => {
    const createItem = vi.fn().mockResolvedValue(undefined);
    const preventDefault = vi.fn();
    const event = {
      key: "Enter",
      isComposing: false,
      preventDefault,
    } as unknown as KeyboardEvent;

    await handleCreateInputKeydown(event, createItem);

    expect(preventDefault).toHaveBeenCalledTimes(1);
    expect(createItem).toHaveBeenCalledTimes(1);
  });

  it("should ignore non-Enter keys", async () => {
    const createItem = vi.fn().mockResolvedValue(undefined);
    const preventDefault = vi.fn();
    const event = {
      key: "Escape",
      isComposing: false,
      preventDefault,
    } as unknown as KeyboardEvent;

    await handleCreateInputKeydown(event, createItem);

    expect(preventDefault).not.toHaveBeenCalled();
    expect(createItem).not.toHaveBeenCalled();
  });

  it("should ignore Enter during IME composition", async () => {
    const createItem = vi.fn().mockResolvedValue(undefined);
    const preventDefault = vi.fn();
    const event = {
      key: "Enter",
      isComposing: true,
      preventDefault,
    } as unknown as KeyboardEvent;

    await handleCreateInputKeydown(event, createItem);

    expect(preventDefault).not.toHaveBeenCalled();
    expect(createItem).not.toHaveBeenCalled();
  });
});

describe("createAndOpenItem", () => {
  it("should create file and open editor immediately", async () => {
    const join = vi.fn().mockResolvedValue("/workspace/new.py");
    const touch = vi.fn().mockResolvedValue(undefined);
    const mkdir = vi.fn().mockResolvedValue(undefined);
    const openFile = vi.fn().mockResolvedValue(undefined);
    const openFolder = vi.fn().mockResolvedValue(undefined);
    const reset = vi.fn();

    await createAndOpenItem({
      folder: "/workspace",
      createName: "new.py",
      dialogType: "file",
      join,
      touch,
      mkdir,
      openFile,
      openFolder,
      reset,
    });

    expect(join).toHaveBeenCalledWith("/workspace", "new.py");
    expect(touch).toHaveBeenCalledWith("/workspace/new.py");
    expect(reset).toHaveBeenCalledTimes(1);
    expect(openFile).toHaveBeenCalledWith("/workspace/new.py");
    expect(mkdir).not.toHaveBeenCalled();
    expect(openFolder).not.toHaveBeenCalled();
  });

  it("should create folder and enter it immediately", async () => {
    const join = vi.fn().mockResolvedValue("/workspace/new-folder");
    const touch = vi.fn().mockResolvedValue(undefined);
    const mkdir = vi.fn().mockResolvedValue(undefined);
    const openFile = vi.fn().mockResolvedValue(undefined);
    const openFolder = vi.fn().mockResolvedValue(undefined);
    const reset = vi.fn();

    await createAndOpenItem({
      folder: "/workspace",
      createName: "new-folder",
      dialogType: "folder",
      join,
      touch,
      mkdir,
      openFile,
      openFolder,
      reset,
    });

    expect(join).toHaveBeenCalledWith("/workspace", "new-folder");
    expect(mkdir).toHaveBeenCalledWith("/workspace/new-folder");
    expect(reset).toHaveBeenCalledTimes(1);
    expect(openFolder).toHaveBeenCalledWith("/workspace/new-folder");
    expect(touch).not.toHaveBeenCalled();
    expect(openFile).not.toHaveBeenCalled();
  });
});

describe("renameAndOpenItem", () => {
  it("should rename file and reopen it", async () => {
    const join = vi.fn().mockResolvedValue("/workspace/new.py");
    const getParent = vi.fn().mockResolvedValue("/workspace");
    const rename = vi.fn().mockResolvedValue(undefined);
    const openFile = vi.fn().mockResolvedValue(undefined);
    const openFolder = vi.fn().mockResolvedValue(undefined);
    const reset = vi.fn();

    await renameAndOpenItem({
      path: "/workspace/old.py",
      name: "new.py",
      join,
      getParent,
      rename,
      openFile,
      openFolder,
      reset,
      isDir: false,
    });

    expect(getParent).toHaveBeenCalledWith("/workspace/old.py");
    expect(join).toHaveBeenCalledWith("/workspace", "new.py");
    expect(rename).toHaveBeenCalledWith("/workspace/old.py", "/workspace/new.py");
    expect(reset).toHaveBeenCalledTimes(1);
    expect(openFile).toHaveBeenCalledWith("/workspace/new.py");
    expect(openFolder).not.toHaveBeenCalled();
  });

  it("should rename folder and open it", async () => {
    const join = vi.fn().mockResolvedValue("/workspace/new-folder");
    const getParent = vi.fn().mockResolvedValue("/workspace");
    const rename = vi.fn().mockResolvedValue(undefined);
    const openFile = vi.fn().mockResolvedValue(undefined);
    const openFolder = vi.fn().mockResolvedValue(undefined);
    const reset = vi.fn();

    await renameAndOpenItem({
      path: "/workspace/old-folder",
      name: "new-folder",
      join,
      getParent,
      rename,
      openFile,
      openFolder,
      reset,
      isDir: true,
    });

    expect(rename).toHaveBeenCalledWith(
      "/workspace/old-folder",
      "/workspace/new-folder",
    );
    expect(reset).toHaveBeenCalledTimes(1);
    expect(openFolder).toHaveBeenCalledWith("/workspace/new-folder");
    expect(openFile).not.toHaveBeenCalled();
  });
});

describe("deleteItemAndRefresh", () => {
  it("should delete item and refresh current folder", async () => {
    const deletePath = vi.fn().mockResolvedValue(undefined);
    const refreshFolder = vi.fn().mockResolvedValue(undefined);

    await deleteItemAndRefresh({
      path: "/workspace/remove.py",
      currentFolder: "/workspace",
      deletePath,
      refreshFolder,
    });

    expect(deletePath).toHaveBeenCalledWith("/workspace/remove.py");
    expect(refreshFolder).toHaveBeenCalledWith("/workspace");
  });
});
