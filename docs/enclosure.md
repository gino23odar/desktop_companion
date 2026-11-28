# Svinka enclosure — v0.2 Baby Pig (PR-10)

## Changes from v0.1

- Flat face panel narrowed from 108 × 72 mm to nominal 80 × 58 mm. The unchanged 58.8 × 43.8 mm aperture gives a nominal flat-face margin of about 10.6 mm horizontally and 7.1 mm vertically (before the bevel); the curved shoulders still need to accommodate the 86 mm PCB.
- Display and mounting bosses tilted 12° upward; top of screen leans toward the rear. Front STL is oriented with tilted face on the build plate.
- Body width 112 mm, face-center to rear plane 85 mm (formerly 95 mm); the tilted face adds a few mm to the total bounding depth. See mesh-validation.json for exact assembled bounding dimensions including tail.
- Rounded tapered shoulders and rear, larger corner radius at the magnetic seam (23 mm), asymmetric rounded ears and two front feet. Rear support meets the same ground plane. All four main parts and four fit coupons exported again.
- Rear micro-USB opening remains below the separate curly tail; existing 6 × 3 mm magnets, four pairs, and rear removable ESP32 cradle are retained.

## Critical fit uncertainties

This is a compact prototype, not a verified final enclosure. The nominal bare TFT PCB clears the front shell in a CAD intersection test, but the glass height, hole center offsets, actual header envelope and ESP32 PCB thickness / port location were not measured. The new support plane is 6 mm behind the tilted face; test with nonconductive spacers, and never compress the touchscreen. Hole pattern is assumed centered. The 1 mm mismatch in reported right offset is resolved provisionally using the 9 mm left offset. The TFT depth allowance is 32 mm; the ESP32 cradle extends slightly across the seam into the front cavity. The 26 mm and 24 mm installed thickness measurements do not specify the exact distribution of wires and components. Check actual jumper clearance and the full assembly before powered use. If wires collide, increase body_depth or change header routing rather than force closure. Magnet fit, port engagement, load-bearing strength and thermal behavior require physical testing.

## Digital checks

All eight exported STLs are watertight, consistently wound, positive volume and one connected component. Nominal shell seam has zero volumetric overlap; the nominal bare PCB mock has no overlap with the front shell. The cradle shares a 0.02 mm nominal overlap at its two mounting pads (about 1.62 mm³ total), not a broad body collision. Physical fit and slicer toolpaths remain unverified. Preview screen artwork is illustrative only, not part of any printable STL.

## CAD

Open hardware/enclosure/svinka.scad with dimensions.scad beside it. Select part and F6, export as STL. The Windows export.ps1 helper exports all eight parts; it has not been run on Windows. The screen coupon stays flat deliberately to test aperture, mounting holes and 6 mm support height independently of the shell angle. See assembly.md and bill-of-materials.md.
