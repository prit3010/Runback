'use strict';

const { greet } = require('../src/greet');

describe('baseline', () => {
  test('greet returns a default message for empty input', () => {
    expect(greet('')).toBe('Hello, friend!');
    expect(greet(undefined)).toBe('Hello, friend!');
  });

  test('greet personalizes when given a name', () => {
    expect(greet('Ada')).toBe('Hello, Ada!');
  });

  test('the project source tree imports without errors', () => {
    expect(() => require('../src/index')).not.toThrow();
  });
});
