import { ATTACKS } from './data.js';

export const clamp = (n, min, max) => Math.max(min, Math.min(max, n));
export const maxHp = (s) => 90 + s.vitality * 20 + s.strength * 4;
export const maxEnergy = (s) => 45 + s.intellect * 12 + s.agility * 5;
export const attackChance = (attacker, defender, move) => clamp(ATTACKS[move].hit + (attacker.stats.agility - defender.stats.agility) * 0.015 + attacker.stats.luck * 0.003, 0.12, 0.97);

export function runAttack(attacker, defender, move, rng = Math.random) {
  const chance = attackChance(attacker, defender, move);
  const hit = rng() < chance;
  if (!hit) return { hit: false, dmg: 0, crit: false, chance };
  const cfg = ATTACKS[move];
  const stat = move === 'magic' ? attacker.stats.intellect : attacker.stats.strength;
  const mitigation = defender.stats.vitality * 1.3;
  const crit = rng() < clamp(0.08 + attacker.stats.luck * 0.01, 0.08, 0.45);
  const raw = cfg.base + stat * cfg.scale + rng() * 8 - mitigation;
  const dmg = Math.max(1, Math.round(crit ? raw * 1.7 : raw));
  return { hit: true, dmg, crit, chance };
}

export function applyVictory(player, tier) {
  const gold = 120 + tier * 70;
  const xp = 95 + tier * 55;
  const fame = 8 + tier * 3;
  const statGain = 4 + tier * 2;
  const next = { ...player, gold: player.gold + gold, xp: player.xp + xp, fame: player.fame + fame, wins: player.wins + 1, statPoints: player.statPoints + statGain };
  while (next.xp >= next.xpNext) {
    next.xp -= next.xpNext;
    next.level += 1;
    next.xpNext = Math.floor(next.xpNext * 1.33);
    next.statPoints += 6;
    next.arenaTier = Math.min(4, next.arenaTier + 1);
  }
  return next;
}
