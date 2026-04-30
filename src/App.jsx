import React, { useMemo, useState } from 'react';
import { ARENAS, ARMOR, ATTACKS, SPELLS, STYLES, WEAPONS } from './game/data.js';
import { applyVictory, maxEnergy, maxHp, runAttack } from './game/combat.js';
import { createEnemy, createPlayer } from './game/generation.js';

const STAT_KEYS = ['strength', 'agility', 'vitality', 'intellect', 'charisma', 'luck'];

function sfx(type) {
  try {
    const ctx = new (window.AudioContext || window.webkitAudioContext)();
    const o = ctx.createOscillator();
    const g = ctx.createGain();
    o.connect(g); g.connect(ctx.destination);
    o.type = type === 'hit' ? 'square' : 'sawtooth';
    o.frequency.value = type === 'hit' ? 160 : type === 'crit' ? 320 : 120;
    g.gain.value = 0.05; o.start(); o.stop(ctx.currentTime + 0.08);
  } catch {}
}

function Fighter({ side, name, hp, max, anim, style }) {
  return <div className={`fighter ${side} ${anim} ${style.toLowerCase().replace(/\s+/g,'-')}`}>
    <div className='sprite' />
    <div className='label'>{name}</div>
    <div className='bar'><i style={{ width: `${Math.max(0, (hp / max) * 100)}%` }} /></div>
  </div>;
}

export default function App() {
  const [screen, setScreen] = useState('title');
  const [draft, setDraft] = useState({ name: 'Cipher', style: STYLES[0] });
  const [player, setPlayer] = useState(null);
  const [enemy, setEnemy] = useState(null);
  const [log, setLog] = useState([]);
  const [anim, setAnim] = useState({ p: '', e: '' });

  const pMax = player ? maxHp(player.stats) : 1;
  const eMax = enemy ? maxHp(enemy.stats) : 1;
  const areaName = player ? ARENAS[player.arenaTier] : '';

  const beginFight = () => {
    const p = { ...player, hp: maxHp(player.stats), energy: maxEnergy(player.stats) };
    const e = createEnemy(p);
    setPlayer(p); setEnemy(e); setLog([`Welcome to ${e.arena}. Crowd wants blood.`]); setAnim({ p: '', e: '' }); setScreen('arena');
  };

  const choose = (move) => {
    if (!enemy || !player) return;
    const attack = ATTACKS[move];
    if (player.energy < attack.energy) { setLog((l) => ['Not enough energy.', ...l].slice(0, 8)); return; }

    const pRes = runAttack(player, enemy, move);
    const e1 = { ...enemy, hp: enemy.hp - pRes.dmg };
    const p1 = { ...player, energy: Math.max(0, player.energy - attack.energy) };
    setAnim({ p: pRes.hit ? 'lunge' : 'evade', e: pRes.hit ? 'hit' : 'evade' });
    sfx(pRes.crit ? 'crit' : pRes.hit ? 'hit' : 'miss');
    let nextLog = [`${player.name} ${attack.label}: ${pRes.hit ? `${pRes.dmg} dmg${pRes.crit ? ' CRIT' : ''}` : 'miss'}`, ...log].slice(0, 8);

    if (e1.hp <= 0) {
      const win = applyVictory(p1, p1.arenaTier);
      setPlayer({ ...win, hp: Math.max(12, Math.floor(maxHp(win.stats) * 0.7)), energy: maxEnergy(win.stats) });
      setEnemy(null); setScreen('city');
      setLog([`Victory. +XP +Gold +Fame +Stat points.`, ...nextLog].slice(0, 8));
      return;
    }

    const aiMoves = ['quick', 'strike', 'heavy', 'magic'];
    const aiMove = aiMoves[Math.floor(Math.random() * aiMoves.length)];
    const eRes = runAttack(e1, p1, aiMove);
    const p2 = { ...p1, hp: p1.hp - eRes.dmg };
    setAnim({ p: eRes.hit ? 'hit' : 'evade', e: 'lunge' });
    sfx(eRes.crit ? 'crit' : eRes.hit ? 'hit' : 'miss');
    nextLog = [`${e1.name} ${ATTACKS[aiMove].label}: ${eRes.hit ? `${eRes.dmg} dmg${eRes.crit ? ' CRIT' : ''}` : 'miss'}`, ...nextLog].slice(0, 8);

    if (p2.hp <= 0) {
      setPlayer({ ...p2, hp: Math.max(1, Math.floor(maxHp(p2.stats) * 0.2)), energy: maxEnergy(p2.stats) });
      setEnemy(null); setScreen('city');
      setLog([`Defeat. Street medics patched you up.`, ...nextLog].slice(0, 8));
      return;
    }

    setEnemy(e1); setPlayer(p2); setLog(nextLog);
  };

  const canAfford = player?.gold >= 100;
  const buy = (key, list) => {
    if (!canAfford) return;
    setPlayer((p) => ({ ...p, [key]: (p[key] + 1) % list.length, gold: p.gold - 100 }));
  };

  if (screen === 'title') return <main className='wrap title'><h1>NEON BLOOD // PITNET</h1><p>Cyber-gladiator career sim</p><button onClick={() => setScreen('create')}>Start Career</button></main>;
  if (screen === 'create') return <main className='wrap'><h2>Create Fighter</h2><input value={draft.name} onChange={(e) => setDraft((d) => ({ ...d, name: e.target.value }))} /><div className='row'>{STYLES.map((s) => <button className={draft.style === s ? 'active' : ''} onClick={() => setDraft((d) => ({ ...d, style: s }))} key={s}>{s}</button>)}</div><button onClick={() => { setPlayer(createPlayer(draft.name || 'Cipher', draft.style)); setScreen('city'); }}>Enter Night City</button></main>;
  if (screen === 'city') return <main className='wrap'><h2>Night City Hub // {areaName}</h2><p>{player.name} Lv{player.level} | Gold {player.gold} | XP {player.xp}/{player.xpNext} | SP {player.statPoints}</p><div className='row'><button onClick={beginFight}>Arena</button><button onClick={() => setScreen('shop')}>Shop</button><button onClick={() => setScreen('train')}>Training</button></div><div className='log'>{log.map((t, i) => <p key={i}>{t}</p>)}</div></main>;
  if (screen === 'shop') return <main className='wrap'><h2>Black Market</h2><p>Each upgrade costs 100 credits.</p><div className='row'><button disabled={!canAfford} onClick={() => buy('weaponIndex', WEAPONS)}>Weapon: {WEAPONS[player.weaponIndex]}</button><button disabled={!canAfford} onClick={() => buy('armorIndex', ARMOR)}>Armor: {ARMOR[player.armorIndex]}</button><button disabled={!canAfford} onClick={() => buy('spellIndex', SPELLS)}>Spell: {SPELLS[player.spellIndex]}</button></div><button onClick={() => setScreen('city')}>Back</button></main>;
  if (screen === 'train') return <main className='wrap'><h2>Neuro Training</h2><p>Spend stat points to build absurd power.</p><div className='grid'>{STAT_KEYS.map((k) => <button key={k} disabled={player.statPoints < 1} onClick={() => setPlayer((p) => ({ ...p, statPoints: p.statPoints - 1, stats: { ...p.stats, [k]: p.stats[k] + 1 } }))}>{k}: {player.stats[k]}</button>)}</div><button onClick={() => setScreen('city')}>Back</button></main>;

  return <main className='arena wrap'><header><h2>{player.name} vs {enemy.name}</h2><p>{ARENAS[player.arenaTier]}</p></header><section className='stage'><div className='crowd' /><Fighter side='player' name={player.name} hp={player.hp} max={pMax} anim={anim.p} style={player.style} /><Fighter side='enemy' name={enemy.name} hp={enemy.hp} max={eMax} anim={anim.e} style='Chrome Wraith' /></section><section className='row'><button onClick={() => choose('quick')}>Quick</button><button onClick={() => choose('strike')}>Strike</button><button onClick={() => choose('heavy')}>Heavy</button><button onClick={() => choose('magic')}>Magic</button></section><section className='log'>{log.map((t, i) => <p key={i}>{t}</p>)}</section></main>;
}
