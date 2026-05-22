// Lightweight pub/sub signal — no framework dependency.

type Listener<T> = (value: T) => void;

export function signal<T>(initial: T) {
  let value = initial;
  const listeners = new Set<Listener<T>>();
  return {
    get(): T { return value; },
    set(next: T) {
      value = next;
      for (const fn of listeners) fn(next);
    },
    subscribe(fn: Listener<T>) {
      listeners.add(fn);
      return () => listeners.delete(fn);
    },
  };
}

export type Signal<T> = ReturnType<typeof signal<T>>;

// ── App-level selections ─────────────────────────────────────────────────────

export const selectedSystemId = signal<string | null>(null);
export const selectedShipId   = signal<number | null>(null);
