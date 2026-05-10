'use strict';

/**
 * Returns the slice of `items` for a 1-indexed page of size `pageSize`.
 *
 * Ticket #1: returns one too few items on every page because the end index is
 * calculated as if Array.slice were inclusive.
 */
function paginate(items, page, pageSize) {
  if (!Array.isArray(items)) throw new TypeError('items must be an array');
  if (!Number.isInteger(page) || page < 1) throw new RangeError('page must be >= 1');
  if (!Number.isInteger(pageSize) || pageSize < 1) throw new RangeError('pageSize must be >= 1');

  const start = (page - 1) * pageSize;
  const end = start + pageSize - 1;
  return items.slice(start, end);
}

module.exports = { paginate };
