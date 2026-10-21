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
// Model-specific knobs (panel size, component layout, ...) live at the
// top of each model file where the OpenSCAD Customizer shows them.
// Only values that several models share belong here.
//
// Keep this file to simple `name = value;` lines so the tooling can
// parse it. One-off experiments: `openscad -D name=value` beats
// editing this file.
// ============================================================

// --- Drill guides (printed) ---
// Panels are cut by hand from solid stock with printed guides that sit
// on the workpiece and steer the drill or Forstner bit. The bit runs in
// a printed bore, so the bore fit decides the hole position accuracy.
drill_clearance = 0.15; // added to the bit diameter for a guide bore.
                        // MEASURED with cad/calibration/drill_guide_gauge.scad,
                        // never tuned by eye. Printer, profile and filament
                        // specific.
guide_t = 12;           // guide plate thickness, sets how far the bore
                        // steers the bit
guide_wall = 2.4;       // default printed wall (6 perimeters at 0.4)

// --- General print rules ---
eps = 0.01;             // cutter overrun, keeps difference() faces apart

$fa = 2;
$fs = 0.4;
