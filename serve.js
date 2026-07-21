// Tiny static server for DingoNav (dev/local hosting). Usage: node serve.js [port]
const http = require('http'), fs = require('fs'), path = require('path');
const root = __dirname;
const port = parseInt(process.argv[2] || process.env.PORT || '8138', 10);
const MIME = { '.html': 'text/html', '.js': 'text/javascript', '.css': 'text/css', '.json': 'application/json',
  '.png': 'image/png', '.gpx': 'application/gpx+xml', '.geojson': 'application/geo+json',
  '.pbf': 'application/x-protobuf', '.pmtiles': 'application/octet-stream' };
http.createServer((req, res) => {
  let p = decodeURIComponent(req.url.split('?')[0]);
  if (p === '/') p = '/index.html';
  const file = path.normalize(path.join(root, p));
  if (!file.startsWith(root)) { res.writeHead(403); return res.end(); }
  fs.readFile(file, (err, data) => {
    if (err) { res.writeHead(404); return res.end('not found'); }
    // Content-Length explicitly: writeHead commits the headers before end(data) can
    // infer it, so without this Node falls back to chunked and the app's download
    // progress bar has no total to count against.
    res.writeHead(200, { 'Content-Type': MIME[path.extname(file)] || 'application/octet-stream',
      'Content-Length': data.length, 'Cache-Control': 'no-cache' });
    res.end(data);
  });
}).listen(port, () => console.log('DingoNav on http://localhost:' + port));
