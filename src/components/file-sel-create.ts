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

export interface RenameItemOptions {
  path: string;
  name: string;
  join: (path1: string, path2: string) => Promise<string>;
  getParent: (path: string) => Promise<string>;
  rename: (source: string, target: string) => Promise<unknown>;
  openFile: (path: string) => Promise<void>;
  openFolder: (path: string) => Promise<void>;
  reset: () => void;
  isDir: boolean;
}

export interface DeleteItemOptions {
  path: string;
  currentFolder: string;
  deletePath: (path: string) => Promise<unknown>;
  refreshFolder: (path: string) => Promise<void>;
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

export async function renameAndOpenItem({
  path,
  name,
  join,
  getParent,
  rename,
  openFile,
  openFolder,
  reset,
  isDir,
}: RenameItemOptions): Promise<void> {
  const parent = await getParent(path);
  const target = await join(parent, name);

  await rename(path, target);
  reset();

  if (isDir) {
    await openFolder(target);
    return;
  }

  await openFile(target);
}

export async function deleteItemAndRefresh({
  path,
  currentFolder,
  deletePath,
  refreshFolder,
}: DeleteItemOptions): Promise<void> {
  await deletePath(path);
  await refreshFolder(currentFolder);
}
