import { serve } from '@hono/node-server';
import { Hono } from 'hono';
import { cors } from 'hono/cors';
import { buildIndex } from './db/meridian.js';
import { stars } from './routes/stars.js';
import { ships } from './routes/ships.js';
import { Config } from './config.js';

const app = new Hono();

app.use('*', cors());

app.route('/api/stars', stars);
app.route('/api/ships', ships);

app.get('/health', (c) => c.json({ ok: true }));

buildIndex().then(() => {
  serve({ fetch: app.fetch, port: Config.port }, () => {
    console.log(`Server listening on http://localhost:${Config.port}`);
  });
}).catch((err) => {
  console.error('Failed to build index:', err);
  process.exit(1);
});
