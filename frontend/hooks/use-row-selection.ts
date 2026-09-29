import { useCallback, useEffect, useState } from 'react';

export function useRowSelection(availableIds: string[]) {
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());

  // Prune stale IDs when the underlying data changes (e.g., after a refetch)
  useEffect(() => {
    setSelectedIds((prev) => {
      const next = new Set<string>();
      let changed = false;
      prev.forEach((id) => {
        if (availableIds.includes(id)) {
          next.add(id);
        } else {
          changed = true;
        }
      });
      return changed ? next : prev;
    });
  }, [availableIds]);

  const toggle = useCallback((id: string) => {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }, []);

  const toggleAll = useCallback(() => {
    setSelectedIds((prev) => {
      if (prev.size === availableIds.length && availableIds.length > 0) {
        return new Set();
      }
      return new Set(availableIds);
    });
  }, [availableIds]);

  const clear = useCallback(() => {
    setSelectedIds(new Set());
  }, []);

  const isSelected = useCallback((id: string) => selectedIds.has(id), [selectedIds]);
  
  const isAllSelected = availableIds.length > 0 && selectedIds.size === availableIds.length;

  return {
    selectedIds,
    toggle,
    toggleAll,
    clear,
    isSelected,
    isAllSelected,
  };
}