import { Hono } from 'hono';
import { cors } from 'hono/cors';
import { stars } from './routes/stars.js';
import { ships } from './routes/ships.js';

export const app = new Hono();

app.use('*', cors());
app.route('/api/stars', stars);
app.route('/api/ships', ships);
app.get('/health', (c) => c.json({ ok: true }));
