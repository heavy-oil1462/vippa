// ============================================================
// VIPPA SHARED DESIGN PARAMETERS: single source of truth for
// every dimension two or more models must agree on.
//
// Consumers:
//   - models in cad/<category>/ do   include <../design_params.scad>
//   - libraries in cad/lib/ do       include <../design_params.scad>
//   - scripts/check_params.py FAILS the build if any of these names
//     is re-declared anywhere else. Change values HERE only.
//
// What lives where:
//   - here: workshop tools, printer and print fits, the same for every
//     panel
//   - catalog/components.json: panel hardware dimensions
//   - panels/<name>.json: one panel's board, cavity and layout
//
// Keep this file to simple `name = value;` lines so the tooling can
// parse it. One-off experiments: `openscad -D name=value` beats
// editing this file.
// ============================================================

// --- Center punch template (front face) ---
// The template sits on the front face, registers on the two reference
// edges with its fences, and guides a center punch to every hole
// center. Holes are then drilled by hand from the punch marks.
punch_d = 8;            // nose diameter of your center punch, the part the
                        // template bore guides. MEASURE yours.
punch_clearance = 0.15; // added to punch_d for a template bore. MEASURED
                        // with cad/calibration/punch_guide_gauge.scad,
                        // never tuned by eye. Printer, profile and
                        // filament specific.
punch_plate_t = 4;      // punch template plate thickness; the punch nose
                        // must be longer than this

// --- Fences (both templates) ---
// Two fences meet at the reference corner, the bottom left corner seen
// from the front. Every layout position is measured from those two
// edges, so the board's other two edges may be off size.
fence_t = 5;            // fence thickness
fence_h = 12;           // how far a fence reaches down the board edge,
                        // capped at the board thickness
fence_relief = 1;       // groove along the fence root, so an eased board
                        // arris or a speck of dust cannot lift the template

// --- Router template (back face) ---
// The back cavity is routed by hand: a router with a guide bushing
// (copy ring) runs along the inside of a printed template.
copy_ring_od = 30;      // guide bushing outer diameter. MEASURE yours.
copy_ring_h = 6;        // how far the guide bushing stands below the base
bit_d = 12;             // straight bit diameter
router_base_d = 150;    // router base diameter, must span the opening
router_base_overlap = 15; // base on the template either side of the opening
router_plate_t = 10;    // router template plate thickness
router_margin = 30;     // template beyond the free board edges, for the
                        // router base to ride on
rail_min = 15;          // narrowest template rail allowed

// --- Holders screwed to the cavity floor ---
// Internals (battery holder, later a board tray) screw to the underside
// of the face from inside the cavity. The face is thin, so the screw
// must stop face_skin short of the front: panel.scad asserts
// holder_screw_len - holder_flange_t <= face_t - face_skin.
holder_flange_t = 2;    // printed flange under the screw head
holder_screw_d = 2.2;   // small self tapping screw, e.g. 2.2 x 4.5
holder_screw_len = 4.5;
face_skin = 1.5;        // wood left in front of a screw tip

// --- Printed parts fitted to each other or to bought parts ---
slip_fit = 0.2;         // gap per side for a printed part to slide over a
                        // bought one or into another print without play:
                        // a bezel over the display's LED block, the
                        // router step plate into the router template.
                        // PLACEHOLDER: MEASURE with a test print of both,
                        // never tune by eye. Printer, profile and
                        // filament specific.

// --- Template labels ---
label_depth = 0.6;      // text engraved into the exposed face
label_size = 4;         // text size

// --- Printer ---
bed_x = 256;            // usable print bed
bed_y = 256;

// --- General print rules ---
eps = 0.01;             // cutter overrun, keeps difference() faces apart

$fa = 2;
$fs = 0.4;
