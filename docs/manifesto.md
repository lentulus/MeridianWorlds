# Worlds — Project Manifesto

*Founded: 2026-05-07*

---

## What Worlds Is

Worlds is a way to keep notes about the actors and events in a novel or rpg campaign.  

---

## What Worlds Is Not

- **It is not a repository of large scale system data.** Meridian will provide that fixed data, but Worlds may reference it by key and may be called on. to display it


---

## Core Principles

**There might be many worlds** even though there is only one Meridian.  However, one Worlds might be tracked through a long period of time.  

**Mutability is complex.**
There will be frequent adds and implicit updates.  BUT it most be possible to observe the state of data at any given point in time -- at least on timestamp will be required on every row.  Some rows will might be inserted in the "middle" of a time line.  Note that INT64 timestamps are prefered but that would be a problem for Javascript.

**Generation in limited ares.**
Most of what will be in these data will be used provided.  Possible exception for some user data.  Viewers now in the Starscape project will probably move here.  Editors and viewers are essential

**Only for defined space.**
If an ungenerated sector is required, Meridian will have to be used to provide it

**The contract is stable; the backend is replaceable.**
Consumers talk to a `StarscapeProvider` Protocol; Meridian will provide the initial implementation.  This product may talk to it's own database directly but only through the Provider for background data

---

## Relationship to Other Projects

| Project | Role |
|---|---|
| **meridian** | The output: immutable Parquet files + manifest + DuckDB query layer |

