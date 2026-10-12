import test from "node:test";
import assert from "node:assert/strict";
import {
  freshRun,
  deliver,
  miss,
  reward,
  readSave,
  purchase,
} from "../src/game.js";
test("90 second run starts empty", () => {
  assert.equal(freshRun().remaining, 90);
  assert.equal(freshRun().score, 0);
});
test("ten deliveries trigger hot wave and preserve best combo after miss", () => {
  let s = freshRun();
  for (let i = 0; i < 10; i++) s = deliver(s);
  assert.equal(s.wave, 8);
  assert.equal(s.combo, 10);
  assert.equal(s.bestCombo, 10);
  assert.equal(miss(s).combo, 0);
  assert.equal(miss(s).bestCombo, 10);
  assert.equal(deliver(s).score - s.score, 600);
});
test("rewards are whole soft currency", () =>
  assert.equal(reward({ ...freshRun(), score: 1234 }), 12));
test("save recovers invalid input and rejects invalid fields", () => {
  assert.deepEqual(readSave("broken"), readSave(null));
  assert.equal(
    readSave('{"coins":-99,"best":"a","owned":["unknown"],"skin":"unknown"}')
      .skin,
    "mint",
  );
  assert.equal(readSave('{"coins":-99}').coins, 0);
});
test("cosmetic purchase debits once and cannot overspend", () => {
  let s = readSave(null);
  assert.deepEqual(purchase(s, "violet"), s);
  s = { ...s, coins: 100 };
  s = purchase(s, "sunset");
  assert.equal(s.coins, 20);
  assert.equal(s.skin, "sunset");
  assert.equal(purchase(s, "sunset").coins, 20);
  assert.equal(purchase(s, "violet").skin, "sunset");
  assert.deepEqual(purchase(s, "fake"), s);
});
