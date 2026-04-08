export async function handleCreateInputKeydown(
  event: KeyboardEvent,
  createItem: () => void | Promise<void>,
): Promise<void> {
  if (event.key !== "Enter" || event.isComposing) return;

  event.preventDefault();
  await createItem();
}
