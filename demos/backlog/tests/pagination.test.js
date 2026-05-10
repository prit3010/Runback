'use strict';

const { paginate } = require('../src/pagination');

describe('Ticket #1 - pagination', () => {
  const items = ['a', 'b', 'c', 'd', 'e', 'f', 'g'];

  test('first page returns exactly pageSize items', () => {
    expect(paginate(items, 1, 3)).toEqual(['a', 'b', 'c']);
  });

  test('middle page returns exactly pageSize items', () => {
    expect(paginate(items, 2, 3)).toEqual(['d', 'e', 'f']);
  });

  test('last partial page returns the remaining items', () => {
    expect(paginate(items, 3, 3)).toEqual(['g']);
  });

  test('full final page returns exactly pageSize items', () => {
    expect(paginate(['a', 'b', 'c', 'd'], 2, 2)).toEqual(['c', 'd']);
  });

  test('rejects bad inputs', () => {
    expect(() => paginate(items, 0, 3)).toThrow(RangeError);
    expect(() => paginate(items, 1, 0)).toThrow(RangeError);
    expect(() => paginate('not-an-array', 1, 3)).toThrow(TypeError);
  });
});
