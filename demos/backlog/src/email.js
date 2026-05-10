'use strict';

function isValidEmail(value) {
  if (typeof value !== 'string') return false;
  const re = /^[A-Za-z0-9._%-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$/;
  return re.test(value);
}

module.exports = { isValidEmail };
