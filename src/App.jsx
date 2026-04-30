import React, { useMemo, useState } from 'react';
import { STYLES } from './game/data.js';
import { applyVictory, maxEnergy, maxHp, runAttack } from './game/combat.js';
import { createEnemy, createPlayer } from './game/generation.js';
import { WEAPONS, ARMOR, SPELLS } from './game/data.js';

const statsList = ['strength','agility','vitality','intellect','charisma','luck'];

const beep=(f,d=0.06)=>{try{const c=new (window.AudioContext||window.webkitAudioContext)();const o=c.createOscillator();const g=c.createGain();o.frequency.value=f;o.connect(g);g.connect(c.destination);g.gain.value=0.04;o.start();o.stop(c.currentTime+d);}catch{}};

export default function App() {
  const [screen, setScreen] = useState('title');
  const [name, setName] = useState('');
  const [style, setStyle] = useState(STYLES[0]);
  const [player, setPlayer] = useState(null);
  const [enemy, setEnemy] = useState(null);
  const [log, setLog] = useState([]);
  const [anim, setAnim] = useState({ p: '', e: '' });

  const startFight = () => { const p = { ...player, hp: maxHp(player.stats), energy: maxEnergy(player.stats) }; const e = createEnemy(player); setPlayer(p); setEnemy(e); setLog([`Entering ${e.arena}`]); setScreen('arena'); };
  const act = (move) => {
    if (!enemy || player.energy <= 0) return;
    const pRes = runAttack(player, enemy, move); beep(pRes.hit?220:130); setAnim({ p: pRes.hit ? 'lunge' : 'miss', e: pRes.hit ? 'hit' : 'evade' });
    const newEnemy = { ...enemy, hp: enemy.hp - pRes.dmg, energy: enemy.energy - 6 };
    let nextLog = [`${player.name} uses ${move.toUpperCase()} ${pRes.hit ? `for ${pRes.dmg}` : 'and misses'}`,...log].slice(0,6);
    if (newEnemy.hp <= 0) { const rewarded = applyVictory(player, player.arenaTier); setPlayer(rewarded); setEnemy(null); setLog(['Victory! Rewards claimed.', ...nextLog]); setScreen('city'); return; }
    const eRes = runAttack(newEnemy, player, ['quick','strike','heavy','magic'][Math.floor(Math.random()*4)]); beep(eRes.hit?160:110); setAnim((a)=>({ ...a, p: eRes.hit ? 'hit' : 'evade', e: 'lunge' }));
    const newPlayer = { ...player, hp: player.hp - eRes.dmg, energy: player.energy - 10 };
    nextLog = [`${newEnemy.name} ${eRes.hit ? `hits for ${eRes.dmg}` : 'misses'}`,...nextLog].slice(0,6);
    if (newPlayer.hp <= 0) { setPlayer({ ...newPlayer, hp: 1 }); setScreen('city'); setLog(['Defeated. Med-bay restored you with 1 HP.',...nextLog]); setEnemy(null); return; }
    setPlayer(newPlayer); setEnemy(newEnemy); setLog(nextLog);
  };

  if (screen === 'title') return <div className='wrap'><h1>NEON BLOOD ARENA</h1><button onClick={()=>setScreen('create')}>Start Career</button></div>;
  if (screen === 'create') return <div className='wrap'><h2>Create Fighter</h2><input value={name} onChange={(e)=>setName(e.target.value)} placeholder='Name'/><div>{STYLES.map(s=><button key={s} onClick={()=>setStyle(s)} className={style===s?'active':''}>{s}</button>)}</div><button onClick={()=>{setPlayer(createPlayer(name||'Cipher', style)); setScreen('city');}}>Enter City</button></div>;
  if (screen === 'city') return <div className='wrap'><h2>Night City Hub</h2><p>{player.name} Lv{player.level} | Gold {player.gold} | SP {player.statPoints}</p><div className='panel'><button onClick={startFight}>Arena</button><button onClick={()=>setScreen('shop')}>Shop</button><button onClick={()=>setScreen('train')}>Training</button></div><div>{log.map((l,i)=><div key={i}>{l}</div>)}</div></div>;
  if (screen === 'shop') return <div className='wrap'><h2>Black Market</h2>{[['weaponIndex',WEAPONS],['armorIndex',ARMOR],['spellIndex',SPELLS]].map(([k,arr])=><button key={k} onClick={()=>setPlayer(p=>({...p,[k]:(p[k]+1)%arr.length,gold:Math.max(0,p.gold-100)}))}>{k}: {arr[player[k]]}</button>)}<button onClick={()=>setScreen('city')}>Back</button></div>;
  if (screen === 'train') return <div className='wrap'><h2>Neuro Training</h2>{statsList.map(s=><button key={s} disabled={player.statPoints<1} onClick={()=>setPlayer(p=>({...p,statPoints:p.statPoints-1,stats:{...p.stats,[s]:p.stats[s]+1}}))}>{s}: {player.stats[s]}</button>)}<button onClick={()=>setScreen('city')}>Back</button></div>;

  return <div className='arena'><div className='hud'><h3>{player.name} vs {enemy.name}</h3><p>HP {player.hp} / EN {player.energy}</p><p>Enemy HP {enemy.hp} / EN {enemy.energy}</p></div><div className='stage'><div className={`fighter player ${anim.p}`}></div><div className={`fighter enemy ${anim.e}`}></div></div><div className='panel'><button onClick={()=>act('quick')}>Quick</button><button onClick={()=>act('strike')}>Strike</button><button onClick={()=>act('heavy')}>Heavy</button><button onClick={()=>act('magic')}>Magic</button></div><div>{log.map((l,i)=><div key={i}>{l}</div>)}</div></div>;
}
