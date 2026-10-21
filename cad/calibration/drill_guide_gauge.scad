// Drill guide gauge: one bar of guide bores for one bit, each bore a
// step looser than the last. Print it flat, try the bit in each bore
// and set drill_clearance in design_params.scad to the tightest bore
// the bit turns in freely without wobble. Labels are the clearance in
// hundredths of a millimetre.

include <../design_params.scad>

/* [Bit] */
// diameter of the bit being gauged
bit_d = 6;

/* [Steps] */
// clearance of the first bore
clearance_min = 0.0;
// clearance added per bore
clearance_step = 0.05;
// number of bores
steps = 7;

/* [Bar] */
// bar thickness, same as a real guide so the bit sees the same bore length
bar_t = 12;
// plastic between neighbouring bores and around the row
bar_wall = 4;
// label depth cut into the top face
label_depth = 0.6;
// label text size
label_size = 3.5;

module drill_guide_gauge(bit_d = bit_d, clearance_min = clearance_min,
                         clearance_step = clearance_step, steps = steps,
                         bar_t = bar_t, bar_wall = bar_wall,
                         label_depth = label_depth, label_size = label_size) {
    pitch = bit_d + clearance_min + clearance_step * (steps - 1) + bar_wall;
    len = steps * pitch + bar_wall;
    w = bit_d + 2 * bar_wall + label_size + bar_wall;
    difference() {
        cube([len, w, bar_t]);
        for (i = [0 : steps - 1]) {
            c = clearance_min + i * clearance_step;
            x = bar_wall + pitch * (i + 0.5);
            translate([x, bar_wall + bit_d / 2, -eps])
                cylinder(d = bit_d + c, h = bar_t + 2 * eps);
            translate([x, w - bar_wall - label_size / 2, bar_t - label_depth])
                linear_extrude(label_depth + eps)
                    text(str(round(c * 100)), size = label_size,
                         halign = "center", valign = "center");
        }
    }
}

drill_guide_gauge();
