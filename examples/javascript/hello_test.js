"use strict";

const assert = require("node:assert/strict");
const { greet } = require("./greeting.js");

assert.equal(greet(), "Hello, world from JavaScript!");
assert.equal(greet("ARM"), "Hello, ARM from JavaScript!");
