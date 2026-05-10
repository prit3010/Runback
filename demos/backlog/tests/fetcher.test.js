'use strict';

const { fetcher } = require('../src/fetcher');

describe('Ticket #3 - fetcher missing await', () => {
  test('returns the resolved value, not a Promise', async () => {
    const v = await fetcher('alpha');
    expect(v).toBe('payload:alpha');
  });

  test('different keys yield different payloads', async () => {
    expect(await fetcher('a')).toBe('payload:a');
    expect(await fetcher('b')).toBe('payload:b');
  });

  test('rejects empty key', async () => {
    await expect(fetcher('')).rejects.toThrow(TypeError);
  });
});
