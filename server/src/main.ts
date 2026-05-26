import { serve } from '@hono/node-server';
import { buildIndex } from './db/meridian.js';
import { Config } from './config.js';
import { app } from './app.js';

buildIndex().then(() => {
  serve({ fetch: app.fetch, port: Config.port }, () => {
    console.log(`Server listening on http://localhost:${Config.port}`);
  });
}).catch((err) => {
  console.error('Failed to build index:', err);
  process.exit(1);
});
