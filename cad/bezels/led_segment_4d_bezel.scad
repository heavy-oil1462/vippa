// Bezel for the led_segment_4d display: a printed frame glued to the
// front face around the window. The display's LED block reaches through
// the window into the bezel's opening; the frame covers the window's
// edge and its chiselled corners by at least BEZEL_LAP in
// scripts/panels.py, and stands a little above the block so the digits
// sit recessed in it. The block in the opening holds the module, its
// board against the cavity floor behind the window.
//
// Modeled in print orientation, back on the bed. Origin at the center of
// the footprint, so the panel library places it by its center.
//
// Its envelope is the bezel of led_segment_4d in
// catalog/components.json; regen_all.py fails if the two disagree. The
// panel library draws the bezel of every display with display_bezel()
// from the catalog values.

include <../design_params.scad>

/* [Display] */
// LED block of the display, catalog digits [w, h]
digits_w = 30;
digits_h = 14;

/* [Bezel] */
// outer size and height above the face, catalog bezel
bezel_w = 39;
bezel_h = 23;
bezel_t = 4;
// chamfer on the outer and inner top edge
bezel_chamfer = 1;

// outer [w, h], digits [w, h] of the LED block, t height. The opening is
// the block plus slip_fit all round.
module display_bezel(outer, digits, t, chamfer = 1) {
    opening = [digits[0] + 2 * slip_fit, digits[1] + 2 * slip_fit];
    assert(outer[0] > opening[0] + 2 * chamfer && outer[1] > opening[1] + 2 * chamfer,
           "bezel frame narrower than its chamfers");
    difference() {
        hull() {
            translate([-outer[0] / 2, -outer[1] / 2, 0]) cube([outer[0], outer[1], t - chamfer]);
            translate([-outer[0] / 2 + chamfer, -outer[1] / 2 + chamfer, 0])
                cube([outer[0] - 2 * chamfer, outer[1] - 2 * chamfer, t]);
        }
        translate([-opening[0] / 2, -opening[1] / 2, -eps]) cube([opening[0], opening[1], t + 2 * eps]);
        hull() {
            translate([-opening[0] / 2, -opening[1] / 2, t - chamfer]) cube([opening[0], opening[1], eps]);
            translate([-opening[0] / 2 - chamfer - eps, -opening[1] / 2 - chamfer - eps, t])
                cube([opening[0] + 2 * chamfer + 2 * eps, opening[1] + 2 * chamfer + 2 * eps, eps]);
        }
    }
}

display_bezel([bezel_w, bezel_h], [digits_w, digits_h], bezel_t, bezel_chamfer);
echo(bezel_size = [bezel_w, bezel_h, bezel_t]);
