'use strict';

function getLogLevel(env) {
  const e = env || process.env;
  return e.LOG_LEVEL || 'LOG_LEVEL';
}

module.exports = { getLogLevel };
