# 🏛️ DESIGN.md — XPLOIT SOVEREIGN SILK AESTHETIC CONTRACT

> **Anti-Slop Craftsmanship Standard // Human-Centered Design Protocol**  
> *"Dials: ENERGY 2 / RHYTHM 2 / MOTION 1"*

---

## 1. Identity & Visual Language

- **Design Philosophy:** Luxury Monochrome Monolith (Linear, Vercel, Apple, and Raycast inspired).
- **Character:** Precision engineering, high contrast, pure obsidian canvases, restrained typography, and intentional micro-surfaces.
- **Atmosphere:** Deep, focused, professional, and razor-sharp.

---

## 2. The Color System (Zero-Slop Palette)

| Token | Hex / Value | Usage & Intent |
| :--- | :--- | :--- |
| **`--bg-canvas`** | `#000000` | True Pitch Black. The definitive anchor ground plane. |
| **`--bg-surface`** | `#09090b` | Primary card and container surface. Solid, non-distracting. |
| **`--bg-elevated`** | `#121216` | Popovers, active dropdowns, and focused items. |
| **`--border-hairline`** | `rgba(255, 255, 255, 0.08)` | Ultra-fine 1px edge delineation. Flat and crisp. |
| **`--border-active`** | `rgba(255, 255, 255, 0.22)` | Hover, active, or focused boundary marker. |
| **`--text-primary`** | `#ffffff` | Pure Silk White. Highest hierarchical contrast. |
| **`--text-secondary`** | `#a1a1aa` | Silver Ash. Descriptions, secondary labels, and subtitles. |
| **`--text-muted`** | `#71717a` | Muted Zinc. Timestamps, metadata, and shortcuts. |
| **`--accent-pure`** | `#ffffff` | Platinum White CTA and active state indicator. |

### 🚫 Anti-Slop Color Directives:
- **FORBIDDEN (R-01):** Generic blue-purple, blue-cyan, or rainbow gradients. Full-page background glows and blurry ambient orbs are strictly banned.
- **FORBIDDEN (R-07):** Meaningless stock grid patterns, blueprint lines, and decorative dot-matrix backgrounds.

---

## 3. Typography & Hierarchy

- **Primary Sans:** `'Inter', -apple-system, BlinkMacSystemFont, sans-serif`
- **Monospace Primitives:** `'Geist Mono', 'Fira Code', monospace`
- **Scale:**
  - Page Titles: `1.25rem - 1.5rem` (Weight: `700 - 800`, Letter-Spacing: `-0.02em`)
  - Section Eyebrows: `0.7rem` (Weight: `600`, Uppercase, Letter-Spacing: `0.08em`, Color: `--text-muted`)
  - Body Text: `0.85rem - 0.9rem` (Weight: `400`, Line-Height: `1.5`)
  - Monospace Data / Tags: `0.75rem` (Weight: `500`)

---

## 4. Surfaces, Depth & Geometry

- **Glassmorphism Dose Cap (R-10):** Maximum **ONE** element on a page may use `backdrop-filter: blur()`. When everything is frosted glass, depth communicates nothing.
- **Radius Standard (R-11):**
  - Interactive Buttons / Inputs: `8px`
  - Cards & Containers: `12px`
  - Status Badges / Pills: `4px - 6px`
  - **FORBIDDEN:** Pill-shaped (`border-radius: 9999px`) buttons and cards everywhere.
- **Elevation vs Flat (R-12):** Default to flat surfaces separated by hairline borders. Reserve drop shadows for floating modals or context menus only.
- **Glow Restriction (R-13):** Glow is an emergency focus amplifier. Do not place glows on badges, borders, icons, and cards simultaneously.

---

## 5. Three Dials Execution Standard

| Dial | Value | Exact Behavioral Rule |
| :--- | :---: | :--- |
| **ENERGY** | **2 (Balanced)** | High functional clarity, zero cartoonish elements, clear visual hierarchy. |
| **RHYTHM** | **2 (Varied)** | Layout adapts to actual data needs. Avoids identical 3-column card grid templates. |
| **MOTION** | **1 (Crisp)** | Transitions strictly between `100ms - 150ms` ease-out. No sluggish, floaty animations. |

---

## 6. Anti-Slop Code & Content Gate

- **Zero Over-Engineering:** Deliver minimal, idiomatic, and robust code. Avoid unnecessary helper abstractions.
- **Clean Documentation:** Explain the *why*, never the obvious *what*.
- **Human-Authored Voice:** No AI conversational clichés ("In this comprehensive guide...", "Dive deep into...", "Let's explore..."). Deliver punchy, direct technical output.
