// All runtime paths live in .env at the project root.
// Change them there — no recompile needed.

function require_env(key: string, fallback?: string): string {
  const val = process.env[key] ?? fallback;
  if (!val) throw new Error(`Missing required env var: ${key}`);
  return val;
}

export const Config = {
  port:         Number(process.env.PORT ?? 3000),
  meridianData: require_env('MERIDIAN_DATA', '/Volumes/Lexar/MeridianData'),
  worldsDb:     require_env('WORLDS_DB',     '/Users/lentulus/databases/world.db'),
} as const;
