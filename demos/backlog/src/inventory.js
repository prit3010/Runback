'use strict';

/**
 * Sorts inventory SKUs ascending. SKUs are alphanumeric like "SKU-100", "sku-99".
 *
 * Ticket #2: sort is lexicographic, so "SKU-10" sorts before "SKU-2".
 */
function sortInventory(skus) {
  if (!Array.isArray(skus)) throw new TypeError('skus must be an array');
  return [...skus].sort();
}

module.exports = { sortInventory };
