export const RUN_SECONDS = 90;
export const SKINS = [
  { id: "mint", name: "Мятный прилив", color: "#80ead0", cost: 0 },
  { id: "sunset", name: "Закатный рейс", color: "#ffad77", cost: 80 },
  { id: "violet", name: "Ночная орхидея", color: "#bfabff", cost: 160 },
];
export function freshRun() {
  return {
    score: 0,
    combo: 0,
    bestCombo: 0,
    hits: 0,
    misses: 0,
    remaining: RUN_SECONDS,
    wave: 0,
  };
}
export function deliver(state) {
  const combo = state.combo + 1;
  return {
    ...state,
    combo,
    bestCombo: Math.max(state.bestCombo, combo),
    hits: state.hits + 1,
    score:
      state.score +
      100 * Math.min(5, 1 + Math.floor(combo / 5)) * (state.wave > 0 ? 2 : 1),
    wave: combo % 10 === 0 ? 8 : state.wave,
  };
}
export function miss(state) {
  return { ...state, combo: 0, misses: state.misses + 1 };
}
export function reward(state) {
  return Math.floor(state.score / 100);
}
export function readSave(raw) {
  try {
    const s = JSON.parse(raw);
    const owned = [
      ...new Set([
        "mint",
        ...(Array.isArray(s?.owned) ? s.owned : []).filter((id) =>
          SKINS.some((x) => x.id === id),
        ),
      ]),
    ];
    return {
      best: Number.isSafeInteger(s?.best) && s.best >= 0 ? s.best : 0,
      coins: Number.isSafeInteger(s?.coins) && s.coins >= 0 ? s.coins : 0,
      runs: Number.isSafeInteger(s?.runs) && s.runs >= 0 ? s.runs : 0,
      owned,
      skin: owned.includes(s?.skin) ? s.skin : "mint",
    };
  } catch {
    return { best: 0, coins: 0, runs: 0, owned: ["mint"], skin: "mint" };
  }
}
export function purchase(save, id) {
  const skin = SKINS.find((x) => x.id === id);
  if (!skin) return save;
  if (save.owned.includes(id)) return { ...save, skin: id };
  if (save.coins < skin.cost) return save;
  return {
    ...save,
    coins: save.coins - skin.cost,
    owned: [...save.owned, id],
    skin: id,
  };
}
