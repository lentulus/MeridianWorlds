import { Hono } from 'hono';
import { serve } from '@hono/node-server';
import { serveStatic } from '@hono/node-server/serve-static';
import { searchSystem } from './db.js';

const app = new Hono();
const PORT = Number(process.env.PORT ?? 3000);

app.get('/api/system', async (c) => {
  const name = c.req.query('name')?.trim();
  if (!name || name.length < 2) {
    return c.json({ error: 'Provide at least 2 characters in ?name=' }, 400);
  }

  try {
    const result = await searchSystem(name);
    if (!result) return c.json({ error: `No system matching "${name}"` }, 404);
    return c.json(result);
  } catch (err) {
    console.error(err);
    return c.json({ error: 'Query failed — check server logs' }, 500);
  }
});

// Serve the web client from public/.
// The wildcard catch-all must come after API routes.
app.use('/*', serveStatic({ root: './public' }));

serve({ fetch: app.fetch, port: PORT }, () => {
  console.log(`Worlds demo running → http://localhost:${PORT}`);
  console.log(`Meridian data: ${process.env.MERIDIAN_DATA ?? '/Volumes/Lexar/MeridianData'}`);
});
