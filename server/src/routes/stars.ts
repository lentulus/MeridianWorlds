import { Hono } from 'hono';
import { searchStars, getSystem, findByName, indexReady } from '../db/meridian.js';

export const stars = new Hono();

function notReady() {
  return Response.json({ error: 'Index still building, try again in a moment' }, { status: 503 });
}

stars.get('/', async (c) => {
  if (!indexReady) return notReady();

  const q = (k: string) => c.req.query(k);
  const params = {
    name:         q('name')         || undefined,
    dist_min_pc:  q('dist_min_pc')  ? Number(q('dist_min_pc'))  : undefined,
    dist_max_pc:  q('dist_max_pc')  ? Number(q('dist_max_pc'))  : undefined,
    spectral:     q('spectral')     || undefined,
    hz_eligible:  q('hz_eligible')  ? q('hz_eligible') === 'true' : undefined,
    sort:         (q('sort') || 'dist_pc') as any,
    dir:          (q('dir')  || 'asc')    as any,
    limit:        q('limit')  ? Number(q('limit'))  : 100,
    offset:       q('offset') ? Number(q('offset')) : 0,
    center_x_pc:  q('center_x_pc') ? Number(q('center_x_pc')) : undefined,
    center_y_pc:  q('center_y_pc') ? Number(q('center_y_pc')) : undefined,
    center_z_pc:  q('center_z_pc') ? Number(q('center_z_pc')) : undefined,
  };

  try {
    const result = await searchStars(params);
    return c.json(result);
  } catch (err) {
    console.error(err);
    return c.json({ error: 'Query failed' }, 500);
  }
});

stars.get('/by-name', async (c) => {
  if (!indexReady) return notReady();
  const name = c.req.query('name')?.trim();
  if (!name) return c.json({ error: 'name required' }, 400);

  const entry = findByName(name);
  if (!entry) return c.json({ error: `System not found: ${name}` }, 404);

  return c.redirect(`/api/stars/${entry.system_id}`);
});

stars.get('/:id', async (c) => {
  if (!indexReady) return notReady();
  const id = c.req.param('id');
  try {
    const result = await getSystem(id);
    if (!result) return c.json({ error: 'System not found' }, 404);
    return c.json(result);
  } catch (err) {
    console.error(err);
    return c.json({ error: 'Query failed' }, 500);
  }
});
