"use strict";

function greet(name = "world") {
  return `Hello, ${name} from JavaScript!`;
}

module.exports = { greet };
