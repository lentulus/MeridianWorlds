import { Hono } from 'hono';
import {
  getHullSizes, getCatalog, getCatalogSystemStats,
  listShips, getShip, createShip, updateShip, updateSlots, deleteShip,
} from '../db/ships.js';
import type { CreateShipBody, UpdateSlotsBody } from '@worlds/shared';

export const ships = new Hono();

ships.get('/hull-sizes', (c) => {
  return c.json(getHullSizes());
});

ships.get('/catalog', (c) => {
  const tl = Number(c.req.query('tl') ?? 10);
  const sm = Number(c.req.query('sm') ?? 4);
  return c.json(getCatalog(tl, sm));
});

ships.get('/catalog/:id', (c) => {
  const systemId = Number(c.req.param('id'));
  const sm = Number(c.req.query('sm') ?? 4);
  const entry = getCatalogSystemStats(systemId, sm);
  if (!entry) return c.json({ error: 'System not found in catalogue' }, 404);
  return c.json(entry);
});

ships.get('/', (c) => {
  const q = (k: string) => c.req.query(k);
  const params = {
    tl:           q('tl')      ? Number(q('tl'))      : undefined,
    tl_max:       q('tl_max')  ? Number(q('tl_max'))  : undefined,
    sm:           q('sm')      ? Number(q('sm'))      : undefined,
    type:         q('type')    || undefined,
    military:     q('military')     ? q('military')     === 'true' : undefined,
    superscience: q('superscience') ? q('superscience') === 'true' : undefined,
    sort:         q('sort')    || undefined,
    dir:          q('dir')     || undefined,
  };
  return c.json(listShips(params));
});

ships.get('/:id', (c) => {
  const id = Number(c.req.param('id'));
  const ship = getShip(id);
  if (!ship) return c.json({ error: 'Ship not found' }, 404);
  return c.json(ship);
});

ships.post('/', async (c) => {
  const body = await c.req.json<CreateShipBody>();
  const shipId = createShip(body);
  return c.json({ ship_id: shipId }, 201);
});

ships.patch('/:id', async (c) => {
  const id = Number(c.req.param('id'));
  const body = await c.req.json<Partial<CreateShipBody>>();
  updateShip(id, body);
  return c.json({ ok: true });
});

ships.put('/:id/slots', async (c) => {
  const id = Number(c.req.param('id'));
  const body = await c.req.json<UpdateSlotsBody>();
  updateSlots(id, body);
  return c.json({ ok: true });
});

ships.delete('/:id', (c) => {
  const id = Number(c.req.param('id'));
  deleteShip(id);
  return c.json({ ok: true });
});
