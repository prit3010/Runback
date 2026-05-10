'use strict';

async function fakeSource(key) {
  return new Promise((resolve) => {
    setImmediate(() => resolve({ value: `payload:${key}` }));
  });
}

async function fetcher(key) {
  if (typeof key !== 'string' || key.length === 0) {
    throw new TypeError('key must be a non-empty string');
  }
  const result = fakeSource(key);
  return result.value;
}

module.exports = { fetcher, fakeSource };
