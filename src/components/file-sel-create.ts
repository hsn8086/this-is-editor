export async function handleCreateInputKeydown(
  event: KeyboardEvent,
  createItem: () => void | Promise<void>,
): Promise<void> {
  if (event.key !== "Enter" || event.isComposing) return;

  event.preventDefault();
  await createItem();
}

export interface CreateAndOpenItemOptions {
  folder: string;
  createName: string;
  dialogType: "file" | "folder";
  join: (path1: string, path2: string) => Promise<string>;
  touch: (path: string) => Promise<unknown>;
  mkdir: (path: string) => Promise<unknown>;
  openFile: (path: string) => Promise<void>;
  openFolder: (path: string) => Promise<void>;
  reset: () => void;
}

export async function createAndOpenItem({
  folder,
  createName,
  dialogType,
  join,
  touch,
  mkdir,
  openFile,
  openFolder,
  reset,
}: CreateAndOpenItemOptions): Promise<void> {
  const path = await join(folder, createName);

  if (dialogType === "file") {
    await touch(path);
    reset();
    await openFile(path);
    return;
  }

  await mkdir(path);
  reset();
  await openFolder(path);
}
