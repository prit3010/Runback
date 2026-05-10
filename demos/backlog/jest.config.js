/** @type {import('jest').Config} */
module.exports = {
  testEnvironment: 'node',
  testMatch: ['**/tests/**/*.test.js'],
  verbose: true,
  collectCoverage: false,
  // Tests in this fixture must be deterministic: no network and no fs writes outside tmp.
  testTimeout: 5000,
};
