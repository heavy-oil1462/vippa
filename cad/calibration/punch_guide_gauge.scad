// Punch guide gauge: one bar of template bores for the center punch,
// each bore a step looser than the last. Print it flat, try the punch
// in each bore and set punch_clearance in design_params.scad to the
// tightest bore the punch slides through freely without wobble. Labels
// are the clearance in hundredths of a millimetre.

include <../design_params.scad>

/* [Steps] */
// clearance of the first bore
clearance_min = 0.0;
// clearance added per bore
clearance_step = 0.05;
// number of bores
steps = 7;

/* [Bar] */
// plastic between neighbouring bores and around the row
bar_wall = 4;

module punch_guide_gauge(clearance_min = clearance_min,
                         clearance_step = clearance_step, steps = steps,
                         bar_wall = bar_wall) {
    // the bar is as thick as a real template, so the punch sees the same
    // bore length
    t = punch_plate_t;
    pitch = punch_d + clearance_min + clearance_step * (steps - 1) + bar_wall;
    len = steps * pitch + bar_wall;
    w = punch_d + 2 * bar_wall + label_size + bar_wall;
    difference() {
        cube([len, w, t]);
        for (i = [0 : steps - 1]) {
            c = clearance_min + i * clearance_step;
            x = bar_wall + pitch * (i + 0.5);
            translate([x, bar_wall + punch_d / 2, -eps])
                cylinder(d = punch_d + c, h = t + 2 * eps);
            translate([x, w - bar_wall - label_size / 2, t - label_depth])
                linear_extrude(label_depth + eps)
                    text(str(round(c * 100)), size = label_size,
                         halign = "center", valign = "center");
        }
    }
}

punch_guide_gauge();
