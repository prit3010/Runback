'use strict';

const { greet } = require('./greet');

function main() {
  // eslint-disable-next-line no-console
  console.log(greet(process.argv[2]));
}

if (require.main === module) {
  main();
}

module.exports = { main };
