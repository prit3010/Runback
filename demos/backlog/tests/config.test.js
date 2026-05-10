'use strict';

const { getLogLevel } = require('../src/config');

describe('Ticket #5 - config fallback', () => {
  test('returns the env value when set', () => {
    expect(getLogLevel({ LOG_LEVEL: 'debug' })).toBe('debug');
    expect(getLogLevel({ LOG_LEVEL: 'warn' })).toBe('warn');
  });

  test('falls back to "info" when unset', () => {
    expect(getLogLevel({})).toBe('info');
  });

  test('falls back to "info" when empty string', () => {
    expect(getLogLevel({ LOG_LEVEL: '' })).toBe('info');
  });
});
