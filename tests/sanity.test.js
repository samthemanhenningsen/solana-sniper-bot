import assert from 'node:assert/strict';
import { attackChance, maxEnergy, maxHp, runAttack, applyVictory } from '../src/game/combat.js';
import { createEnemy, createPlayer } from '../src/game/generation.js';

const stats = { strength: 10, agility: 10, vitality: 10, intellect: 10, charisma: 5, luck: 5 };
assert.equal(maxHp(stats), 330);
assert.equal(maxEnergy(stats), 215);

const p = { stats }, d = { stats: { ...stats, agility: 1 } };
const c = attackChance(p, d, 'quick');
assert.ok(c >= 0.12 && c <= 0.97);

const hit = runAttack({ stats }, { stats }, 'heavy', () => 0);
assert.ok(hit.dmg >= 1);

const player = createPlayer('Test', 'Neon Ronin');
const enemy = createEnemy(player);
assert.ok(enemy.hp > 0 && enemy.energy > 0);

const won = applyVictory(player, 2);
assert.ok(won.gold > player.gold && won.xp >= 0 && won.statPoints > player.statPoints);

console.log('sanity tests passed');
