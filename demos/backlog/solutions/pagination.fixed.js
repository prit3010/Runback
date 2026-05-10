'use strict';

function paginate(items, page, pageSize) {
  if (!Array.isArray(items)) throw new TypeError('items must be an array');
  if (!Number.isInteger(page) || page < 1) throw new RangeError('page must be >= 1');
  if (!Number.isInteger(pageSize) || pageSize < 1) throw new RangeError('pageSize must be >= 1');

  const start = (page - 1) * pageSize;
  const end = start + pageSize;
  return items.slice(start, end);
}

module.exports = { paginate };
