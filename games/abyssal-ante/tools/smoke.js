// Functional smoke test + screenshots for every screen / new feature.
const { chromium } = require(process.env.PLAYWRIGHT || '/opt/node22/lib/node_modules/playwright');
const path = require('path');
const OUT = path.resolve(__dirname, 'shots');
require('fs').mkdirSync(OUT, { recursive: true });
(async () => {
  const file = path.resolve(process.argv[2]);
  const browser = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium-1194/chrome-linux/chrome' });
  const page = await browser.newPage({ viewport: { width: +(process.env.W||400), height: +(process.env.H||720) }, deviceScaleFactor: 2 });
  const errors = [];
  page.on('pageerror', e => errors.push(String(e && e.stack || e)));
  page.on('console', m => { if (m.type() === 'error' && !/Failed to load|ERR_|net::/.test(m.text())) errors.push('console: ' + m.text()) });
  await page.route(/^https?:/, r => r.abort());
  await page.goto('file://' + file);
  await page.waitForTimeout(400);
  const shot = async n => { await page.screenshot({ path: `${OUT}/${n}.png` }); console.log('shot', n) };
  const ev = (fn, arg) => page.evaluate(fn, arg);
  const step = async (name, fn, arg) => { try { const r = await ev(fn, arg); console.log('OK', name, r === undefined ? '' : JSON.stringify(r).slice(0, 200)) } catch (e) { console.log('FAIL', name, String(e).slice(0, 300)); errors.push(name + ': ' + e) } };

  await shot('01-intro');
  await step('intro mentions new code', () => document.querySelector('#sheet').textContent.includes('ABYSSTHRONE'));
  await step('codes', () => { closeModal(); Object.keys(CODES).forEach(k => redeem(k)); closeModal(); return { gems: META.gems, tickets: META.tickets, owned: Object.keys(META.owned).length } });
  await step('patch modal', () => { ACT.patch(); return document.querySelector('.patch').textContent });
  await shot('02-patch');
  await step('home', () => { closeModal(); go('home'); return !!document.querySelector('[data-s="modes"]') });
  await shot('03-home');
  await step('gacha hero x10', async () => { SKIP = true; GTAB = 'hero'; go('gacha'); await ACT.pull({ dataset: { n: '10' } }); closeModal(); GTAB = 'relic'; await ACT.pull({ dataset: { n: '10' } }); closeModal(); go('gacha'); return META.stats.pulls });
  await shot('04-gacha-relic');
  await step('own all heroes 6*', () => { HEROES.forEach(h => META.owned[h.id] = { star: 6, sh: 0 }); go('heroes'); HEROES.forEach(h => { openHero(h.id); closeModal() }); return Object.keys(META.owned).length });
  await step('open new hero', () => { openHero('nyx'); return document.querySelector('#sheet').textContent.includes('ท่าไม้ตาย') });
  await shot('05-hero-nyx');
  await step('vault tabs', () => { closeModal(); go('vault'); ['mine', 'all', 'hands'].forEach(t => { VTAB = t; RENDER.vault() }); return document.querySelectorAll('#scr-vault .item').length });
  await step('modes screen', () => { go('modes'); return document.querySelectorAll('#scr-modes .mod').length });
  await shot('06-modes');
  await page.evaluate(() => document.querySelector('#scr-modes .scroll').scrollTop = 9999);
  await shot('07-modes-hall');
  await step('pvp w/ ult', async () => {
    SKIP = false; META.squad = ['aurelia', 'nyx', 'lilac', 'seraphine']; go('arena');
    ACT['pvp-go']({ dataset: { i: '0' } }); return PV && PV.a.heroes.map(h => h.id);
  });
  await page.waitForTimeout(6500);
  await shot('08-pvp');
  await step('pvp finish', async () => { ACT['pvp-skip'](); for (let i = 0; i < 400 && PV && !PV.over; i++) await new Promise(r => setTimeout(r, 20)); const r = PV && PV.res; ACT['pvp-leave'](); SKIP = false; return r });

  // tower combat: ultbar + cut-in screenshots
  await step('start run', () => { SKIP = false; META.auto = false; RUN = null; newRun(0); const n = nextNodes()[0]; ACT.node({ dataset: { r: n.r, c: n.c } }); return RUN.heroes.map(h => h.id) });
  await page.waitForTimeout(1200);
  await step('fill ults', () => { RUN.heroes.forEach(h => h.ult = 100); renderCombat(); return document.querySelectorAll('#ultbar .ultbtn').length });
  await shot('09-combat-ultbar');
  await step('hero modal ult', () => { heroRunInfo(RUN.heroes[0]); return document.querySelector('#sheet').textContent.includes('ใช้!') });
  await shot('10-hero-ult-modal');
  await step('use ult (nyx)', () => { closeModal(); const h = RUN.heroes.find(x => x.id === 'nyx'); useUlt(h); return true });
  await page.waitForTimeout(700);
  await shot('11-ult-cutin');
  await page.waitForTimeout(2600);
  await step('after ult', () => ({ busy: C && C.busy, ub: C && C.ub, foes: C && C.enemies.map(e => Math.round(e.hp / e.maxHp * 100)) }));
  await step('play a card + release', async () => { if (!C) return 'combat over'; const c = C.hand.find(x => !whyNot(x)); if (c) await playCard(c.uid); SKIP = true; await release(); SKIP = false; return { over: !C || C.over } });
  await page.waitForTimeout(600);

  // throne boss: intro + phase 2
  await step('throne setup', () => { closeModal(); C = null; RUN.act = 4; RUN.throne = true; RUN.map = genMap(); RUN.pos = { r: ROWS, c: 0, boss: true }; startCombat('boss', ['b_king', 'ashknight', 'choir']); return C.blinds });
  await page.waitForTimeout(1300);
  await shot('12-boss-intro');
  await page.waitForTimeout(2200);
  await step('phase 2', async () => {
    for (let i = 0; i < 100 && C.busy; i++) await new Promise(r => setTimeout(r, 30));
    const k = C.enemies.find(e => e.id === 'b_king'); k.hp = 5; k.block = 0;
    const c = C.hand.find(x => !whyNot(x) && CARDS[x.id].t === 'atk') || C.hand.find(x => !whyNot(x));
    C.target = k.uid; if (c) await playCard(c.uid);
    const p = release(); await new Promise(r => setTimeout(r, 2600)); return { p2: k.p2, pend: k.p2pend, name: k.name, blinds: C && C.blinds, hp: k.hp, max: k.maxHp };
  });
  await shot('13-phase2');
  await page.waitForTimeout(4000);
  await step('after phase2', () => ({ cur: CUR, blinds: C && C.blinds, king: C && C.enemies.filter(e => e.boss).map(e => [e.name, e.p2, Math.round(e.hp)]) }));
  await shot('14-combat-p2');

  // daily + rush start
  await step('daily start', () => { closeModal(); C = null; RUN = null; go('modes'); const b = document.querySelector('[data-act="mode-go"][data-m="daily"]'); b.click(); return { mode: RUN.mode, mods: RUN.mods, squad: RUN.heroes.map(h => h.id + ':' + starOf(h.id)), relics: RUN.relics.map(r => r.id), cur: CUR } });
  await shot('15-daily-map');
  await step('daily same map twice', () => { const a = JSON.stringify(RUN.map.rows.map(r => r.map(n => n && n.t))); const b = JSON.stringify(withSeed((RUN.seed || 1) + RUN.act * 7919, genMap0).rows.map(r => r.map(n => n && n.t))); return a === b });
  await step('daily end scoring', () => { RUN.kills = 12; RUN.bestHit = 5000; runEnd(false); return { score: RUNEND.score, bonus: RUNEND.bonus, hist: META.daily.hist } });
  await shot('16-runend-daily');
  await step('rush start', () => { go('modes'); document.querySelector('[data-act="mode-go"][data-m="rush"]').click(); return { mode: RUN.mode, deck: RUN.deck.length, relics: RUN.relics.length } });
  await page.waitForTimeout(2200);
  await step('rush in combat', () => ({ cur: CUR, boss: C && C.enemies[0].id, label: document.querySelector('#cAnte').textContent }));
  await page.waitForTimeout(2000);
  await shot('17-rush-combat');
  await step('rush continue after home', () => { C = null; go('home'); continueRun(); return CUR });
  await page.waitForTimeout(300);
  await step('settings + bgm toggle', () => { closeModal(); ACT.settings(); ACT['toggle-bgm'](); ACT['toggle-bgm'](); return document.querySelector('#sheet').textContent.includes('เพลง') });
  await step('save roundtrip', () => { const code = btoa(unescape(encodeURIComponent(JSON.stringify({ meta: META, run: RUN })))); const o = JSON.parse(decodeURIComponent(escape(atob(code)))); return !!mergeMeta(o.meta).daily });
  console.log(errors.length ? 'ERRORS:\n' + [...new Set(errors)].join('\n') : 'NO ERRORS');
  await browser.close();
})();
