# ADR-0006: Display windows routed through the face from the back

Status: Accepted

Accepted by the supervisor in review of #24.

The window routed from the back with the router template as a deeper
second step, and a front bezel, decided by the owner on #19
(2026-10-26); the step plate and the corner marks proposed for #20.

## Context

An LED segment display (docs/CONCEPT.md, Component families) has to be
seen through the face, so the face needs a rectangular window, not a
round drilled hole. A panel is made with hand tools and exactly two
printed templates (CLAUDE.md, core ideas): a punch template on the
front and a router template on the back whose opening the guide
bushing (copy ring) rides to route the cavity. The window lies inside
the cavity, where the router template has no edge left to guide the
bushing once the cavity is routed. A router bit leaves its own radius,
`bit_d / 2`, in every inside corner, and a display window is only a
little larger than the display's LED block.

## Decision

- The router template gains a second step: a step plate, printed
  separately, that drops into the template's opening once the cavity
  is routed. Its outline is the opening less `slip_fit`
  (design_params.scad), so it registers on the same printed edge the
  bushing just rode, and it rests on the band of back face the opening
  leaves around the cavity, flush with the template, so the router
  base rides both. For each display it has an opening, the window
  grown by the bushing to bit offset with the bushing's radius in its
  corners. The bit routes the window through the face, `t` deep from
  the back.
- The window comes out with the bit radius in its corners, the
  tightest the bit can cut. The punch template bores the four corners
  of each window with punch bores, so the corners are punched on the
  front and chiselled square to the marks.
- A printed bezel (cad/bezels/) is glued on the face around the
  window. It covers the window's edge by at least `BEZEL_LAP`
  (scripts/panels.py) and frames the LED block, which reaches through
  the window from the module's board behind the face.
- The window is a catalog value of the display (`window`), the panel
  places the display by its center like a component, and
  cad/lib/panel.scad derives the board cut, the corner bores and the
  step plate from that; no panel numbers in a .scad.

## Consequences

- A panel still has two templates; a panel with a display prints the
  router template as two parts, the frame and its step plate
  (`router_step.stl`, only for such a panel).
- The step plate needs a measured `slip_fit`, a placeholder until it is
  measured on a test print, the same as the bezel's fit on the LED
  block.
- The bit has to reach `face_t` deeper than for the cavity: `t` plus
  `router_plate_t` below the router base, 32 mm on the thermostat
  panel. The step plate is engraved with the depth from the back, `t`.
- panel.scad asserts each window is at least the bit wide, and the
  step plate's rail beside a window at least `rail_min`; panels.py
  checks the bezel lies inside the cavity outline, clear of every
  other component's keepout.
- Chiselling four corners is hand work the other holes do not need; a
  window with the bit radius left in its corners also works, the bezel
  covers it.
- A brass face (an open question) would need a different way to cut
  the window.
