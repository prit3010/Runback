'use strict';

/**
 * Returns a friendly greeting. Used by the entrypoint as a smoke test.
 * @param {string} name
 * @returns {string}
 */
function greet(name) {
  if (typeof name !== 'string' || name.length === 0) {
    return 'Hello, friend!';
  }
  return `Hello, ${name}!`;
}

module.exports = { greet };
