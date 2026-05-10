'use strict';

const { sortInventory } = require('../src/inventory');

describe('Ticket #2 - inventory sort', () => {
  test('numeric suffix order, not lexicographic', () => {
    const input = ['SKU-10', 'SKU-2', 'SKU-100', 'SKU-1'];
    expect(sortInventory(input)).toEqual(['SKU-1', 'SKU-2', 'SKU-10', 'SKU-100']);
  });

  test('case-insensitive prefix is treated equally', () => {
    const input = ['sku-3', 'SKU-1', 'Sku-2'];
    const result = sortInventory(input);
    expect(result.map((s) => Number(s.split('-')[1]))).toEqual([1, 2, 3]);
  });

  test('empty array returns empty', () => {
    expect(sortInventory([])).toEqual([]);
  });

  test('rejects non-array input', () => {
    expect(() => sortInventory('foo')).toThrow(TypeError);
  });
});
