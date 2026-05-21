# FTL Drive — Physics and Navigation

**Setting name:** Bekele–Volkova Metric Translation Drive  
**In service:** "metric drive" or "running metric"  
**GURPS stat:** Stardrive Engine (SS1; FTL-1, FTL-2 … ratings)

---

## 1. Entry condition — flat space proxy

A ship can initiate metric translation when the tidal acceleration from all nearby
massive bodies is at or below a threshold **τ = g⊕ ≈ 9.8 m/s²**. This is the
operational definition of "flat space" for jump purposes.

### Why tidal, not gravitational

Gravitational acceleration is frame-dependent; tidal acceleration (the gradient across
the ship's own length) is coordinate-independent and measurable aboard. It is the
quantity that couples to the metric field the drive manipulates.

### Reference calibration

For an Earth-mass, Earth-radius body, the jump condition is satisfied at exactly
**100 planetary diameters** from the centre. This fixes the threshold.

The jump radius scales with mass as:

> **r_jump = (M / M⊕)^(1/3) × 200 R⊕ ≈ (M / M⊕)^(1/3) × 1,274,000 km**

For bodies of the same mean density as Earth, (M/M⊕)^(1/3) = R/R⊕, so the limit
is always 100 planetary diameters regardless of size. Bodies with lower density
(gas giants, main-sequence stars) have shorter limits in diameter terms but larger
absolute distances.

### Jump limits — standard body types

| Body | M / M⊕ | R / R⊕ | r_jump (km) | r_jump (AU) | Body diameters |
|------|--------|--------|-------------|-------------|----------------|
| Dwarf world (Ceres-like) | 1.6 × 10⁻⁴ | 0.074 | 68,800 | 0.00046 | 73 |
| Mars-like | 0.107 | 0.532 | 604,000 | 0.00404 | 89 |
| **Earth (reference)** | **1.000** | **1.000** | **1,274,000** | **0.00852** | **100** |
| Super-Earth (5 M⊕) | 5.00 | ~1.50 | 2,179,000 | 0.0146 | 114 |
| Ice giant (Neptune) | 17.15 | 3.865 | 3,280,000 | 0.0219 | 67 |
| Gas giant (Jupiter) | 317.8 | 11.21 | 8,677,000 | 0.0580 | 61 |
| Red dwarf (0.1 M☉) | 33,300 | 16.4 | 41,000,000 | 0.274 | 196 |
| Sun-like star (G2V) | 333,000 | 109.2 | 88,300,000 | 0.590 | 63 |
| Blue-white giant (10 M☉) | 3,330,000 | ~437 | 190,700,000 | 1.27 | 34 |
| Neutron star (1.4 M☉) | 466,000 | 0.00157 | 98,700,000 | 0.660 | ~5 billion |

**Notes:**
- The Sun's jump limit (0.59 AU) lies between Mercury (0.39 AU) and Venus (0.72 AU).
  Ships departing the inner Solar system must first burn outward to Venusian-orbit distance.
- Gas giants have shorter limits *in diameters* than Earth because of their lower mean density.
- Neutron stars are lethal close in; the limit is enormous in diameters but only 0.66 AU
  absolute — similar to a Sun-like star, because mass is similar. The drive won't care; the
  X-ray flux will.
- Binary and trinary systems: apply the formula to each component separately. The binding
  limit is whichever body's exclusion zone is largest at any given ship position.

---

## 2. The 4-sphere of emergence

At the moment of metric insertion the ship carries a 4-position **(x, y, z, t)** and
a pointing vector into translation. The emergence point is not a geometric point — it
is drawn from a 4D probability distribution centred on the intended destination.

**Units:** position in light-seconds (ls), time in seconds (s). Since c = 1 ls s⁻¹
the two are numerically equivalent and the distribution is isotropic: equal σ in all
four dimensions. The emergence uncertainty is a true **4-sphere**, not an ellipsoid.

**4D containment geometry:** For an isotropic 4D Gaussian with standard deviation σ
per component, the 50% containment surface is a 4-sphere of radius R₄ satisfying:

> e^(−x)(1 + x) = 0.5,   x = R₄² / 2σ²

Solving numerically: x ≈ 1.678, giving

> **R₄ = 1.83 σ**

This is the 4D probable sphere — 50% of all emergences fall inside it, in position
*and* time simultaneously. A ship emerging on the surface of this sphere is displaced
R₄ light-seconds from the intended point AND R₄ seconds from the intended moment.

The 4-sphere radius grows linearly with jump distance:

> **R₄ = 1.83 · σ_θ · d**

where σ_θ is the pointing accuracy in radians and d is the jump distance in light-seconds.

---

## 3. Navigation accuracy — working assumption

**Pointing accuracy: σ_θ = 0.01 arcseconds** (assumed for current calculations).

> 0.01" = 4.848 × 10⁻⁸ rad

### Key conversion

> 1 parsec = **1.029 × 10⁸ ls** = 206,265 AU = 3.26 light-years

The per-parsec positional σ works out cleanly:

> **σ = 4.848 × 10⁻⁸ rad × 1.029 × 10⁸ ls/pc × d(pc) ≈ 5.0 × d(pc) ls**

0.01 arcsecond pointing gives **≈ 5 light-seconds of positional uncertainty per parsec
of range**, with equal temporal uncertainty in seconds.

### Sample calculations

| Range | σ (ls) | σ (AU) | R₄ = 1.83σ (ls) | R₄ (AU) | σ_t (s) |
|-------|--------|--------|-----------------|---------|---------|
| 5 pc | 25.0 | 0.050 | 45.8 | 0.092 | 25 |
| 10 pc | 50.0 | 0.100 | 91.5 | 0.183 | 50 |
| 50 pc | 250 | 0.501 | 458 | 0.917 | 250 |
| 100 pc | 500 | 1.002 | 915 | 1.83 | 500 |

At 100 pc, σ ≈ 500 ls ≈ 1 AU exactly — a convenient landmark.

### What these numbers mean in practice

Reference points:
- Habitable zone: 0.5–2 AU from star
- Jupiter-equivalent orbit: 5.2 AU (2,595 ls)
- Neptune-equivalent orbit: 30 AU (14,970 ls)
- Inner Oort cloud starts: ~1,000 AU (499,000 ls)

| Range | 4D sphere R₄ | Emergence zone |
|-------|-------------|----------------|
| 5 pc | 0.09 AU | Inside habitable zone width; near-exact arrival |
| 10 pc | 0.18 AU | Inner planetary system; excellent |
| 50 pc | 0.92 AU | Near habitable zone; inner planetary system |
| 100 pc | 1.83 AU | Inner planetary system; between Earth and Mars orbits |

At 0.01 arcsecond pointing, **all ranges out to 100 pc produce emergence well inside
the target planetary system**. This is precision navigation — the economics of beacon
infrastructure still matter (see §4) but the driver is time-of-flight after emergence,
not whether you reach the right system at all.

### Temporal error

The temporal component is equal to σ in seconds. At 100 pc: σ_t = 500 s ≈ 8.3 minutes.
A ship thrusting at 1G covers ≈ 1,200 km in that window — negligible against a 500 ls
(150 million km) positional uncertainty. Timing matters for high-precision rendezvous
with fast-moving targets, not for standard system arrival.

---

## 4. Navigation beacon geometry

A beacon at the destination broadcasts its precise 4-position continuously. The navigator
takes a fix before insertion, reducing positional uncertainty below the bare stellar-catalogue
limit. Without a beacon the navigator relies on parallax and proper-motion data whose
precision degrades with distance.

The 0.01 arcsecond assumption is the **beacon-assisted** accuracy floor. Without a beacon,
pointing accuracy degrades with catalogue quality — roughly one order of magnitude worse
at distances beyond 50 pc using current astrometric data.

A beacon at 50 pc is transmitting its position 163 years ago. The navigator corrects for
stellar proper motion; errors compound for high-proper-motion stars and binary systems.
Rapidly-moving primaries (v_t > 50 km/s, or tight binaries) require fresh ephemeris data
from a recent survey vessel or the pointing accuracy degrades.

---

## 5. Drive ratings (GURPS Spaceships cross-reference)

The Stardrive Engine in GURPS Spaceships gives a range rating (FTL-1, FTL-2, etc.).
Drive rating determines **maximum range**, not accuracy. Accuracy is a function of
pointing at insertion (§3) independent of drive power.

A short-range drive (FTL-1) pointed accurately still produces a tight 4-sphere at
its maximum range; a long-range drive pointed sloppily still produces a wide one.

---

## Open questions

- [ ] Does drive rating affect emergence accuracy, or only maximum range?
- [ ] Minimum mass for an FTL-capable body (can an asteroid provide a stable jump platform)?
- [ ] Transit duration: is time spent in metric translation negligible, fixed, or proportional to distance?
- [ ] Multiple-body systems: is the jump limit the geometric sum of all body limits, or the dominant body only?
