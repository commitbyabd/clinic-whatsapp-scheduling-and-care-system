import { useCallback, useMemo, useState } from "react";

/*
  Paginates an array already in memory.

  The API returns whole lists, so this is a rendering limit rather than a
  transfer one: it stops the browser laying out hundreds of cards, but the
  payload is still fetched in full. Real pagination needs skip and limit
  parameters on the list endpoints.
*/
export function usePagination(items, pageSize = 8) {
  const [page, setPage] = useState(1);

  const total = items.length;
  const pageCount = Math.max(1, Math.ceil(total / pageSize));

  // Clamped at render rather than corrected in an effect. Deleting the last
  // row of the last page shrinks pageCount, and an effect that chased it
  // would render the empty page once before fixing itself.
  const safePage = Math.min(page, pageCount);
  const start = (safePage - 1) * pageSize;

  const pageItems = useMemo(
    () => items.slice(start, start + pageSize),
    [items, start, pageSize],
  );

  const goTo = useCallback(
    (next) => setPage(Math.min(Math.max(1, next), pageCount)),
    [pageCount],
  );

  const reset = useCallback(() => setPage(1), []);

  return {
    page: safePage,
    pageCount,
    total,
    pageItems,
    rangeStart: total === 0 ? 0 : start + 1,
    rangeEnd: Math.min(start + pageSize, total),
    setPage: goTo,
    reset,
  };
}
