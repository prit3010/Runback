'use strict';

const { isValidEmail } = require('../src/email');

describe('Ticket #4 - email validation', () => {
  test('accepts plain addresses', () => {
    expect(isValidEmail('alice@example.com')).toBe(true);
    expect(isValidEmail('bob.smith@example.co.uk')).toBe(true);
  });

  test('accepts plus-tagged addresses', () => {
    expect(isValidEmail('user+tag@example.com')).toBe(true);
    expect(isValidEmail('alerts+ci@runback.dev')).toBe(true);
  });

  test('rejects malformed addresses', () => {
    expect(isValidEmail('no-at-sign')).toBe(false);
    expect(isValidEmail('two@@signs.com')).toBe(false);
    expect(isValidEmail('trailing-dot@x.')).toBe(false);
    expect(isValidEmail('')).toBe(false);
    expect(isValidEmail(null)).toBe(false);
    expect(isValidEmail(undefined)).toBe(false);
  });
});
