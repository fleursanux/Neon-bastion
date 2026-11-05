// Vérifie le serveur installé : deux « téléphones » dans un salon, l'un envoie un message à l'autre.
const base = process.argv[2].replace(/^http/, 'ws');
const room = 'check' + Date.now(), open = id => new Promise((res, rej) => {
  const ws = new WebSocket(`${base}/ws?room=${room}&id=${id}`);
  const to = setTimeout(() => rej(new Error('pas de OPEN pour ' + id)), 10000);
  ws.onmessage = e => { const m = JSON.parse(e.data); if (m.type === 'OPEN') { clearTimeout(to); res(ws); } };
  ws.onerror = e => rej(new Error('erreur WebSocket ' + id));
});
const a = await open('a'), b = await open('b');
const got = new Promise((res, rej) => { const to = setTimeout(() => rej(new Error('message non reçu')), 10000); a.onmessage = e => { const m = JSON.parse(e.data); if (m.payload && m.payload.ping && m.src === 'b') { clearTimeout(to); res(); } }; });
b.send(JSON.stringify({ type: 'CANDIDATE', dst: 'a', payload: { ping: 1 } }));
await got;
const t0 = Date.now(); b.send(JSON.stringify({ type: 'CANDIDATE', dst: 'a', payload: { ping: 2 } }));
await new Promise(r => { a.onmessage = () => r(); });
console.log('Échange de messages OK, aller simple ~' + (Date.now() - t0) + ' ms');
a.close(); b.close(); process.exit(0);
