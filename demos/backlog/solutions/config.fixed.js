'use strict';

function getLogLevel(env) {
  const e = env || process.env;
  return e.LOG_LEVEL && e.LOG_LEVEL.length > 0 ? e.LOG_LEVEL : 'info';
}

module.exports = { getLogLevel };
