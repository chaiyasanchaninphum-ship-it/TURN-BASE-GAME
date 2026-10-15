// Headless balance sim: drives full runs with the in-game auto-play AI.
// usage: node sim.js <html> <runs> <squad-json|starter> [asc] [stars]
const { chromium } = require(process.env.PLAYWRIGHT || '/opt/node22/lib/node_modules/playwright');
const path = require('path');
(async () => {
  const file = path.resolve(process.argv[2]);
  const runs = +process.argv[3] || 3;
  const squadArg = process.argv[4] || 'starter';
  const asc = +process.argv[5] || 0;
  const stars = +process.argv[6] || 1;
  const browser = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium-1194/chrome-linux/chrome' }).catch(() => chromium.launch());
  const page = await browser.newPage({ viewport: { width: 420, height: 760 } });
  const errors = [];
  page.on('pageerror', e => errors.push(String(e && e.stack || e)));
  page.on('console', m => { if (m.type() === 'error' && !/Failed to load|ERR_|net::/.test(m.text())) errors.push('console: ' + m.text()); });
  await page.route(/^https?:/, r => r.abort());
  await page.goto('file://' + file);
  await page.waitForTimeout(300);
  if (process.env.MODE) await page.evaluate(m => window.__MODE = m, process.env.MODE);
  if (process.env.THRONE) await page.evaluate(() => window.__THRONE = true);
  const results = [];
  for (let i = 0; i < runs; i++) {
    await page.evaluate(i => window.__DAY = '2026-10-' + String(10 + i).padStart(2, '0'), i);
    const res = await page.evaluate(async ({ squadArg, asc, stars }) => {
      SKIP = true; closeModal();
      if (squadArg !== 'starter') {
        const sq = JSON.parse(squadArg);
        sq.forEach(id => META.owned[id] = { star: stars, sh: 0 });
        META.squad = sq;
      } else { Object.values(META.owned).forEach(o => o.star = stars) }
      META.auto = true; META.ascMax = 20; META.startRelic = null;
      RUN = null;
      const FL=[];window.__FL=FL;
      if(!window.__wrapped){window.__wrapped=1;
        const sc=startCombat;window.startCombat=function(k,ids){window.__FL.push({k,act:RUN.act,ids:ids.join(','),turns:0,hpIn:Math.round(aliveHeroes().reduce((a,h)=>a+h.hp/h.maxHp,0)/Math.max(1,aliveHeroes().length)*100)});return sc(k,ids)};
        const st=startTurn;window.startTurn=function(){const f=window.__FL[window.__FL.length-1];if(f)f.turns++;return st()};
      }
      if(window.__MODE==='rush') newRun(0,{mode:'rush'});
      else if(window.__MODE==='daily'){const cfg=dailyConfig(window.__DAY);newRun(5,{mode:'daily',squad:cfg.squad,rent:Object.fromEntries(cfg.squad.map(id=>[id,3])),mods:cfg.mods,relics:[{id:cfg.relic,ed:null}],seed:cfg.seed,dayKey:cfg.key})}
      else newRun(asc);
      const log = { acts: {}, deaths: [], nodes: [] };
      const sleep = ms => new Promise(r => setTimeout(r, ms));
      const fake = d => ({ dataset: d, disabled: false });
      let guard = 0, lastAct = 1, combatTurns = 0;
      while (guard++ < 4000) {
        await sleep(5);
        if (!$('#cut').hidden) { $('#cut').click(); continue }
        if (!RUN) break;
        if (!$('#modal').hidden) {
          const sw = document.querySelector('#sheet [data-act="relic-swap"]');
          if (sw) { sw.click(); continue }
          const thr0 = document.querySelector('#sheet [data-act="go-throne"]');
          if (thr0 && window.__THRONE) { log.victory3 = true; thr0.click(); continue }
          const fin = document.querySelector('#sheet [data-act="finish-run"]');
          if (fin) { log.victory = true; if (window.__ENDLESS) { document.querySelector('#sheet [data-act="go-endless"]').click() } else fin.click(); continue }
          const thr = document.querySelector('#sheet [data-act="go-throne"]');
          if (thr && window.__THRONE) { thr.click(); continue }
          const dp = document.querySelector('#sheet [data-act="deck-pick"]');
          if (dp) { dp.click(); continue }
          closeModal(); continue;
        }
        if (RUN.act !== lastAct) { lastAct = RUN.act }
        if (CUR === 'map') {
          const av = nextNodes();
          if (!av.length) { closeModal(); continue }
          if (av[0] === 'boss') { ACT.node(fake({ boss: 1 })); continue }
          const hpLow = aliveHeroes().reduce((a, h) => a + h.hp / h.maxHp, 0) / aliveHeroes().length < .55;
          const pr = { camp: hpLow ? 0 : 4, shop: RUN.gold > 150 ? 1 : 5, elite: hpLow ? 6 : 2, combat: 3, event: 3 };
          const n = av.slice().sort((a, b) => pr[a.t] - pr[b.t])[0];
          log.nodes.push(n.t);
          ACT.node(fake({ r: n.r, c: n.c })); continue;
        }
        if (CUR === 'combat') {
          if (C && !C.busy && !C.over && META.auto) { await autoPlay() }
          if (C) { const k = 'a' + RUN.act; log.acts[k] = log.acts[k] || { fights: 0, turns: 0, bestHit: 0 }; }
          continue;
        }
        if (CUR === 'reward') {
          const rw = RUN.reward; const k = 'a' + RUN.act; log.acts[k] = log.acts[k] || { fights: 0, turns: 0, bestHit: 0 }; log.acts[k].fights++;
          if (rw.hand && !rw.taken.hand) { ACT['rw-hand'](); continue }
          if (rw.relics.length && !rw.taken.relic) { ACT['rw-relic'](fake({ i: 0 })); continue }
          if (!rw.taken.card) { const b = document.querySelector('[data-act="rw-card"]'); if (b) ACT['rw-card'](b); else ACT['rw-skip'](); continue }
          ACT['rw-done'](); continue;
        }
        if (CUR === 'shop') {
          const S = RUN.shop; let bought = false;
          S.relics.forEach((x, i) => { if (!bought && !S.sold['r' + i] && RUN.gold >= x.p && RUN.relics.length < relicSlots()) { ACT.buy(fake({ k: 'r' + i })); bought = true } });
          if (!bought) S.hands.forEach((x, i) => { if (!bought && !S.sold['h' + i] && RUN.gold >= x.p) { ACT.buy(fake({ k: 'h' + i })); bought = true } });
          if (bought) continue;
          ACT['leave-node'](); continue;
        }
        if (CUR === 'camp') {
          const hp = aliveHeroes().reduce((a, h) => a + h.hp / h.maxHp, 0) / aliveHeroes().length;
          const st = aliveHeroes().reduce((a, h) => a + h.stress, 0) / aliveHeroes().length;
          ACT.camp(fake({ k: hp < .7 ? 'rest' : st > 55 ? 'pray' : 'smith' })); await sleep(700); continue;
        }
        if (CUR === 'event') {
          if (RUN.ev && RUN.ev.res) { const c = document.querySelector('[data-act="ev-card"]'); if (c && !RUN.ev.took) { ACT['ev-card'](c); continue } ACT['leave-node'](); continue }
          const btns = [...document.querySelectorAll('[data-act="ev-choice"]')].filter(b => !b.disabled);
          await ACT['ev-choice'](btns[btns.length > 1 ? 1 : 0]); continue;
        }
        if (CUR === 'runend') break;
        if (CUR === 'home') break;
        if (typeof RENDER.rushpick === 'function' && CUR === 'rushpick') { const b = document.querySelector('[data-act="rush-boon"]'); if (b) b.click(); continue }
      }
      const R = RUNEND || {};
      const per={};FL.forEach(f=>{const k='a'+f.act+(f.k==='boss'?'B':f.k==='elite'?'E':'');per[k]=per[k]||{n:0,t:0};per[k].n++;per[k].t+=f.turns});
      Object.values(per).forEach(v=>v.t=+(v.t/v.n).toFixed(1));
      const last=FL[FL.length-1];
      return { per, died: R.win||log.victory?null:last, win: !!R.win, act: R.act, kills: R.kills, releases: R.releases, best: META.best.hit, guard, cur: CUR, victory: !!log.victory, rush: RUN===null&&R.stage, score: R.score, mods: R.mode, v3: !!log.victory3, ults: R.ults, throne: R.throne, deadHeroes: (R.heroes || []).filter(h => h.dead).length };
    }, { squadArg, asc, stars });
    results.push(res);
    console.log(JSON.stringify(res));
  }
  if (errors.length) { console.log('ERRORS:'); console.log([...new Set(errors)].slice(0, 15).join('\n')) }
  const wins = results.filter(r => r.victory).length;
  console.log(`SUMMARY wins ${wins}/${results.length} avgAct ${(results.reduce((a, r) => a + (r.act || 0), 0) / results.length).toFixed(2)}`);
  await browser.close();
})();
