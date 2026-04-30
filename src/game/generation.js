import { maxEnergy, maxHp } from './combat.js';
import { ARENAS } from './data.js';

export const baseStats = () => ({ strength: 6, agility: 6, vitality: 6, intellect: 6, charisma: 5, luck: 5 });

export function createPlayer(name, style) {
  const stats = baseStats();
  return { name, style, level: 1, xp: 0, xpNext: 100, arenaTier: 0, wins: 0, gold: 200, fame: 0, statPoints: 8, weaponIndex: 0, armorIndex: 0, spellIndex: 0, stats, hp: maxHp(stats), energy: maxEnergy(stats) };
}

export function createEnemy(player) {
  const tier = player.arenaTier;
  const boost = player.level + tier * 2;
  const stats = {
    strength: 5 + boost + Math.floor(Math.random() * 4),
    agility: 5 + boost + Math.floor(Math.random() * 4),
    vitality: 5 + boost + Math.floor(Math.random() * 4),
    intellect: 5 + boost + Math.floor(Math.random() * 4),
    charisma: 4 + tier,
    luck: 4 + tier + Math.floor(Math.random() * 3)
  };
  return { name: `Arena Bot ${tier + 1}-${Math.floor(Math.random() * 900)}`, arena: ARENAS[tier], stats, hp: maxHp(stats), energy: maxEnergy(stats) };
}
