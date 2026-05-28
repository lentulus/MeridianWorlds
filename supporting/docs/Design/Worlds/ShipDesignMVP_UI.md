# Ship Design Tool — UI Skeleton

*Companion to [ShipDesignMVP_Plan.md](ShipDesignMVP_Plan.md).*
*Layout approved 2026-05-27. Interactive prototype: [ShipDesignMVP_Prototype.html](ShipDesignMVP_Prototype.html).*
*Layout: three-panel. Left = ship list + filters. Centre = slot grid + catalog. Right = stats.*

---

## 1. Main view (ship selected)

```
┌──────────────┬─────────────────────────────────────┬────────────────────┐
│ SHIPS        │ SLOT GRID          Midnight Sun      │ STATS              │
│──────────────│─────────────────────────────────────│────────────────────│
│ TL  [9 ][11]│ FRONT HULL                          │ Midnight Sun       │
│ SM  [  ]    │  [1] Steel                          │ SM +7  TL 9        │
│ Type[      ]│  [2] Control Room (3 stations)      │ Unstreamlined      │
│ ☐  Military │  [3] Habitat (8 cabins)             │                    │
│─────────────│  [4] Cargo Hold (30 t)              │ Cost    $4.2 M     │
│ > Midnight  │  [5] Cargo Hold (30 t)              │ PP       4 / 2     │
│   Sun       │  [6] ░░ empty ░░                    │ Crew    12         │
│   Star      │  [●] Fusion Reactor (4 PP)          │                    │
│   Flower    │                                     │ dDR  3 / 3 / 3    │
│   Valiant   │ CENTRAL HULL                        │ Move  1 G          │
│   ...       │  [1] Steel                          │       55 mps       │
│             │  [2] Cargo Hold (30 t)              │ HT   12            │
│             │  [3] Cargo Hold (30 t)              │                    │
│             │  [4] Fuel Tank                      │ ▸ Overrides        │
│             │  [5] ░░ empty ░░                    │                    │
│             │  [6] ░░ empty ░░                    │ Notes              │
│             │  [●] Fuel Tank                      │ [markdown field]   │
│             │                                     │                    │
│             │ REAR HULL                           │                    │
│             │  [1] Steel                          │ [Delete ship]      │
│ [+ New Ship]│  [2] Fusion Torch [!]               │                    │
│             │  [3] Fusion Torch [!]               │                    │
│             │  [4] Fusion Torch [!]               │                    │
│             │  [5] ░░ empty ░░                    │                    │
│             │  [6] Engine Room                    │                    │
│             │─────────────────────────────────────│                    │
│             │ CATALOG  [Armor▾][Power▾][Drive▾].. │                    │
│             │  ░ Steel armor           drag→slot  │                    │
│             │  ░ Light Alloy                      │                    │
│             │  ░ Metallic Laminate                │                    │
│             │  ░ Fusion Reactor                   │                    │
│             │  ░ Fusion Torch                     │                    │
│             │  ░ ── empty ──    (clears slot)     │                    │
└─────────────┴─────────────────────────────────────┴────────────────────┘
```

**Notes on main view:**

- Slot rows show `[section number] System name (key stat)`. The key stat is the
  detail text stored in `ship_system_slots.detail`.
- Empty slots show `░░ empty ░░` and are valid drop targets.
- `[!]` suffix on a slot row indicates a high-energy system.
- `[●]` is the core slot; displayed last in its section, visually distinguished.
- All stats in the right panel are derived values; the `▸ Overrides` section
  is collapsed by default (see §4).
- PP shown as `available / consumed` (e.g. `4 / 2`).

---

## 2. Slot click / drop — detail prompt

When the user drops a catalog item onto a slot (or clicks an occupied slot to edit
the detail text), an inline prompt appears over that slot row:

```
│  [2] Control Room  ┌─────────────────────────────────────────┐
│                    │  Detail text for: Control Room           │
│                    │  ┌─────────────────────────────────────┐ │
│                    │  │ 3 stations                          │ │
│                    │  └─────────────────────────────────────┘ │
│                    │  (suggested: "3 stations")               │
│                    │                         [Cancel] [Save]  │
│                    └─────────────────────────────────────────┘
```

- The input is pre-filled with a sensible default derived from `system_sm_stats`
  (e.g. cabin count, acceleration in G, cargo tons, PP output).
- Pressing Enter or clicking Save writes the slot and triggers a full stat
  recalculation.
- Pressing Escape or Cancel cancels the drop (slot reverts).

---

## 3. Catalog category filter

The catalog toolbar shows category buttons; clicking one filters the list below it.
Multiple categories can be active simultaneously.

```
CATALOG  [Armor ▾] [Power ▾] [Drive ▾] [Cargo ▾] [Control ▾] [Other ▾]
─────────────────────────────────────────────────────────────────────────
  ░ Steel armor
  ░ Light Alloy armor
  ░ Metallic Laminate armor
  ░ Fusion Reactor
  ░ Fusion Torch [!]
  ░ Fuel Tank
  ░ ── empty ──           ← always visible; clears the slot on drop
```

- Each category button shows a count of matching systems (e.g. `Armor (8)`).
- Systems whose TL exceeds the ship's TL are greyed out and cannot be dropped.
- The `── empty ──` entry is always shown last; dragging it onto a slot writes
  `system_id = null` and clears the detail text.

---

## 4. Description and image (below overrides)

```
│ Description                                      │
│ ┌──────────────────────────────────────────────┐ │
│ │ Orbital shuttle operated by Meridian Lines.  │ │
│ │ Three fusion torches give 3G acceleration…   │ │
│ │                                              │ │
│ └──────────────────────────────────────────────┘ │
│ (resizable; markdown accepted)                   │
│                                                  │
│ Image                                            │
│ ┌──────────────────────────────────────────────┐ │
│ │                                              │ │
│ │          [ship image or deck plan]           │ │
│ │                                              │ │
│ └──────────────────────────────────────────────┘ │
│ [Remove image]  midnight-sun.jpg                 │
```

When no image is set, the image area shows a dashed drop-zone with the text
"Drop image here or click to browse". Accepted types: any image/* (JPEG, PNG,
WebP). The file is POSTed to `/api/ships/:id/image` and stored in
`server/data/ship-images/`. The filename is recorded in `ships.image_path`.

---

## 5. Override panel (expanded — collapsed by default)

Clicking `▸ Overrides` in the stats panel expands it:

```
│ ▾ Overrides                                      │
│                                                  │
│  Move (G)   [      ]  ← derived: 1              │
│  Delta-V    [      ]  ← derived: 55 mps         │
│  dDR front  [      ]  ← derived: 3              │
│  dDR central[      ]  ← derived: 3              │
│  dDR rear   [      ]  ← derived: 3              │
│  HT         [      ]  ← derived: 12             │
│                                                  │
│  [Save overrides]   [Clear all → auto]           │
```

- Each input is blank when the column is null (auto-derive in effect).
- Placeholder text shows what the derived value would be.
- "Save overrides" PATCHes only the filled fields; blank inputs write null.
- "Clear all → auto" writes null to all override columns and closes the panel.
- The main stats panel immediately reflects any saved override (or the derived
  value if cleared).

---

## 6. New ship dialog

Triggered by `[+ New Ship]`:

```
┌──────────────────────────────────────┐
│  New Ship Design                     │
│                                      │
│  Name  [                           ] │
│  SM    [ +7 ▾ ]  (affects hull mass) │
│  TL    [ 9  ▾ ]                      │
│  ☐  Streamlined                      │
│  Type  [               ▾]            │
│  ☐  Military                         │
│                                      │
│                   [Cancel]  [Create] │
└──────────────────────────────────────┘
```

- On Create: POST to `/api/ships`, then select the new ship in the list.
- The new ship has 0 slots; all 20 positions show `░░ empty ░░`.
- All derived stats show 0 or the base HT value (13 for SM+10+; 12 for SM+5–9
  with no engine room yet).

---

## 7. Stats panel — derived vs override visual language

| State | Display |
|---|---|
| Auto-derived, no override | Value in normal weight. No decoration. |
| Override active | Value in **bold** with a small `*` suffix (e.g. `2 G*`). |
| Override differs significantly from derived | Value in **bold amber** as a caution. |

The `*` gives the user a quick signal that the value is not from slot contents,
without making it alarming.

---

## 8. Slot grid — visual conventions

| Visual | Meaning |
|---|---|
| `░░ empty ░░` | Slot has no system; valid drop target |
| `[!]` suffix | High-energy system; counts toward PP consumed |
| `[●]` label | Core slot |
| Dimmed text | System TL exceeds ship TL (display-only for imported ships) |
| Drop highlight | Slot row highlighted when a catalog item is dragged over it |
