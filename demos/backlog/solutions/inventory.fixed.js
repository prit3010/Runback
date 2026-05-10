'use strict';

function sortInventory(skus) {
  if (!Array.isArray(skus)) throw new TypeError('skus must be an array');
  return [...skus].sort((a, b) => {
    const an = Number(a.split('-')[1]);
    const bn = Number(b.split('-')[1]);
    return an - bn;
  });
}

module.exports = { sortInventory };
