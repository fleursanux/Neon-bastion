#!/usr/bin/env python3
"""Construit l'application installable (PWA) à partir de neon-bastion.html.
Usage : python3 build.py <source.html> <url publique de l'application> <dossier de sortie>"""
import hashlib, json, re, sys, pathlib
src, url = sys.argv[1], sys.argv[2]
out = pathlib.Path(sys.argv[3] if len(sys.argv) > 3 else '.')
out.mkdir(parents=True, exist_ok=True)
game = open(src, encoding='utf-8').read()
version = re.search(r"const APP_VERSION = '([^']+)'", game).group(1)
# Les balises de tête du jeu (titre, polices) passent dans <head>
head_bits = re.findall(r'^(<title>.*?</title>|<link [^>]*>)\s*$', game, re.M)
body = re.sub(r'^(<title>.*?</title>|<meta name="claude:[^>]*>|<link [^>]*>)\s*\n', '', game, flags=re.M)

UPDATE_UI = r"""
<div id="updBar" hidden style="position:fixed;z-index:60;left:50%;transform:translateX(-50%);top:calc(env(safe-area-inset-top,0px) + 10px);display:flex;gap:10px;align-items:center;background:#111829;border:1px solid #3ef2c8;color:#e4ecfb;border-radius:999px;padding:6px 8px 6px 14px;font:600 .85rem 'Chakra Petch',system-ui,sans-serif;box-shadow:0 8px 24px rgba(0,0,0,.5)">
  <span>Nouvelle version disponible</span>
  <button id="updBtn" type="button" style="all:unset;cursor:pointer;background:#3ef2c8;color:#062019;border-radius:999px;padding:6px 12px;font-weight:700">Mettre à jour</button>
</div>
<script>
/* Service worker : jeu disponible hors ligne et mises à jour automatiques */
if ('serviceWorker' in navigator) {
  let reloading = false, hadController = !!navigator.serviceWorker.controller;
  navigator.serviceWorker.register('sw.js').then(reg => {
    const check = () => reg.update().catch(() => {});
    document.addEventListener('visibilitychange', () => { if (!document.hidden) check(); });
    setInterval(check, 30 * 60 * 1000);
  }).catch(() => {});
  navigator.serviceWorker.addEventListener('controllerchange', () => {
    if (!hadController) { hadController = true; return; }      // première installation : rien à recharger
    const bar = document.getElementById('updBar');
    bar.hidden = false;
    document.getElementById('updBtn').onclick = () => { if (!reloading) { reloading = true; location.reload(); } };
  });
}
</script>
"""
html = f"""<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="theme-color" content="#0a0e18">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="apple-mobile-web-app-title" content="Neon Bastion">
<meta name="description" content="Tower defense néon à niveaux infinis.">
<link rel="manifest" href="manifest.webmanifest">
<link rel="icon" type="image/png" href="icons/icon-192.png">
<link rel="apple-touch-icon" href="icons/apple-touch-icon.png">
{chr(10).join(head_bits)}
<style>:root{{padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}}body{{margin:0;font:14px system-ui,sans-serif}}img{{max-width:100%}}</style>
<script>window.NB_APP = {json.dumps({'url': url, 'version': version})};</script>
</head>
<body>
{body}
{UPDATE_UI}
</body>
</html>
"""
(out / 'index.html').write_text(html, encoding='utf-8')
build = hashlib.sha256(html.encode()).hexdigest()[:10]
manifest = {
  "name": "Neon Bastion", "short_name": "Neon Bastion", "lang": "fr",
  "description": "Tower defense néon à niveaux infinis.",
  "start_url": "./", "scope": "./", "display": "standalone", "orientation": "any",
  "background_color": "#0a0e18", "theme_color": "#0a0e18",
  "icons": [
    {"src": "icons/icon-192.png", "sizes": "192x192", "type": "image/png"},
    {"src": "icons/icon-512.png", "sizes": "512x512", "type": "image/png"},
    {"src": "icons/maskable-512.png", "sizes": "512x512", "type": "image/png", "purpose": "maskable"}
  ]
}
(out / 'manifest.webmanifest').write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
sw = f"""/* Neon Bastion {version} · build {build} */
const CACHE = 'neon-bastion-{version}-{build}';
const CORE = ['./', './index.html', './manifest.webmanifest', './icons/icon-192.png', './icons/icon-512.png', './icons/apple-touch-icon.png'];
self.addEventListener('install', e => {{
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(CORE)).then(() => self.skipWaiting()));
}});
self.addEventListener('activate', e => {{
  e.waitUntil(caches.keys().then(keys => Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k)))).then(() => self.clients.claim()));
}});
self.addEventListener('fetch', e => {{
  const req = e.request;
  if (req.method !== 'GET') return;
  // La page du jeu : toujours la dernière version en ligne, la copie locale hors connexion
  if (req.mode === 'navigate') {{
    e.respondWith(fetch(req).then(res => {{ const copy = res.clone(); caches.open(CACHE).then(c => c.put('./index.html', copy)); return res; }})
      .catch(() => caches.match('./index.html')));
    return;
  }}
  // Le reste (icônes, polices) : depuis le cache, sinon le réseau
  e.respondWith(caches.match(req).then(hit => hit || fetch(req).then(res => {{
    if (res.ok || res.type === 'opaque') {{ const copy = res.clone(); caches.open(CACHE).then(c => c.put(req, copy)); }}
    return res;
  }})));
}});
"""
(out / 'sw.js').write_text(sw, encoding='utf-8')
(out / '.nojekyll').write_text('')
print(f'Construit : version {version}, build {build}')
