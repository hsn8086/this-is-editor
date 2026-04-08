import { describe, expect, it, vi } from "vitest";

import { handleCreateInputKeydown } from "@/components/file-sel-create";

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
