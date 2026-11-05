/* Serveur de mise en relation de Neon Bastion.
   Chaque code de partie = un « salon » (Durable Object). Les téléphones s'y connectent en WebSocket
   avec leur identifiant ; un message { dst, ... } est remis au téléphone dst du même salon.
   Sert à la présentation des deux joueurs (comme le serveur central de TeamViewer) et de relais
   quand la connexion directe est impossible. Hibernation : rien n'est compté quand personne ne parle. */
import { DurableObject } from 'cloudflare:workers';

const HB = '{"type":"HEARTBEAT"}';

export class Room extends DurableObject {
  constructor(ctx, env) {
    super(ctx, env);
    // Les battements de cœur reçoivent une réponse sans réveiller le salon.
    this.ctx.setWebSocketAutoResponse(new WebSocketRequestResponsePair(HB, '{"type":"HB"}'));
  }
  async fetch(req) {
    const id = new URL(req.url).searchParams.get('id') || '';
    for (const old of this.ctx.getWebSockets(id)) { try { old.close(4000, 'remplacé'); } catch (e) {} }
    const pair = new WebSocketPair();
    this.ctx.acceptWebSocket(pair[1], [id]);
    pair[1].send('{"type":"OPEN"}');
    return new Response(null, { status: 101, webSocket: pair[0] });
  }
  webSocketMessage(ws, msg) {
    if (typeof msg !== 'string' || msg.length > 512 * 1024) return;
    let m; try { m = JSON.parse(msg); } catch (e) { return; }
    if (!m || typeof m.dst !== 'string') return;
    const src = this.ctx.getTags(ws)[0];
    m.src = src;
    const to = this.ctx.getWebSockets(m.dst);
    if (!to.length) {
      if (m.type === 'OFFER') { try { ws.send(JSON.stringify({ type: 'EXPIRE', src: m.dst, dst: src })); } catch (e) {} }
      return;
    }
    const s = JSON.stringify(m);
    for (const w of to) { try { w.send(s); } catch (e) {} }
  }
  webSocketClose(ws, code) { try { ws.close(code === 1005 ? 1000 : code, 'au revoir'); } catch (e) {} }
  webSocketError(ws) { try { ws.close(1011, 'erreur'); } catch (e) {} }
}

export default {
  async fetch(req, env) {
    const u = new URL(req.url);
    if (u.pathname === '/ws') {
      if (req.headers.get('Upgrade') !== 'websocket') return new Response('WebSocket attendu', { status: 426 });
      const room = u.searchParams.get('room') || '', id = u.searchParams.get('id') || '';
      if (!/^[A-Za-z0-9_-]{1,48}$/.test(room) || !/^[A-Za-z0-9_-]{1,64}$/.test(id)) return new Response('salon ou identifiant invalide', { status: 400 });
      return env.ROOM.get(env.ROOM.idFromName(room)).fetch(req);
    }
    return new Response('Neon Bastion : serveur de mise en relation en service.', { headers: { 'access-control-allow-origin': '*', 'content-type': 'text/plain; charset=utf-8' } });
  }
};
