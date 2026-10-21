// Battery holder for two AA cells side by side, screwed to the cavity
// floor (the underside of the face) from inside the cavity. Bought AA
// contact plates slide into slots in the end walls: at one end a bridge
// contact joins the two cells in series, at the other end one spring and
// one flat contact take the leads out through the wire notch.
//
// Modeled in print orientation, base on the bed. Origin at the center
// of the footprint, so the panel library places it by its center.
//
// Its envelope is the size of battery_2aa_holder in
// catalog/components.json; regen_all.py fails if the two disagree.

include <../design_params.scad>

/* [Cells] */
// cell diameter, IEC 60086 LR6 maximum
cell_d = 14.5;
// cell length, IEC 60086 LR6 maximum
cell_len = 50.5;
// room at each end for a contact plate and its spring. MEASURE with
// the contacts you bought
contact_space = 4;
// gap between the two cells
cell_gap = 1;

/* [Body] */
// side and end wall thickness
holder_wall = 2;
// side walls rise to this fraction of the cell diameter, so the cells
// press in and stay put on a wall mounted panel
side_rise = 0.6;
// contact plate slot: thickness and width
slot_t = 0.8;
slot_w = 11;
// wire notch in the top of one end wall
notch_w = 4;

/* [Screw ears] */
// ear length beyond each end wall
ear_len = 7;
// ear width
ear_w = 9;

function holder_size() = [
    cell_len + 2 * contact_space + 2 * holder_wall + 2 * ear_len,
    2 * cell_d + cell_gap + 2 * holder_wall,
    holder_flange_t + cell_d,
];

module battery_2aa_holder() {
    inner = [cell_len + 2 * contact_space, 2 * cell_d + cell_gap];
    body = [inner[0] + 2 * holder_wall, inner[1] + 2 * holder_wall];
    h = holder_size()[2];
    cy = [-(cell_d + cell_gap) / 2, (cell_d + cell_gap) / 2];
    assert(holder_flange_t >= 1.2, "holder_flange_t too thin to clamp under a screw head");
    difference() {
        union() {
            // body: full height end walls, side walls to side_rise
            translate([-body[0] / 2, -body[1] / 2, 0])
                cube([body[0], body[1], holder_flange_t + cell_d * side_rise]);
            for (sx = [-1, 1])
                translate([sx * (body[0] - holder_wall) / 2 - holder_wall / 2, -body[1] / 2, 0])
                    cube([holder_wall, body[1], h]);
            // screw ears, flange thick, on the center line of each end
            for (sx = [-1, 1])
                translate([sx * (body[0] / 2 + ear_len / 2) - ear_len / 2, -ear_w / 2, 0])
                    cube([ear_len, ear_w, holder_flange_t]);
        }
        // cell channels, round bottomed so the cells sit centered
        for (y = cy)
            translate([-inner[0] / 2, y, holder_flange_t + cell_d / 2])
                rotate([0, 90, 0]) cylinder(d = cell_d + 0.4, h = inner[0]);
        for (y = cy)
            translate([-inner[0] / 2, y - cell_d / 2 - 0.2, holder_flange_t + cell_d / 2])
                cube([inner[0], cell_d + 0.4, cell_d]);
        // contact slots in the inner face of both end walls, open at the top
        for (sx = [-1, 1], y = cy)
            translate([sx * (inner[0] / 2 + slot_t / 2) - slot_t / 2, y - slot_w / 2, holder_flange_t])
                cube([slot_t, slot_w, h]);
        // wire notch at the +x end
        translate([inner[0] / 2 - eps, -notch_w / 2, h - notch_w])
            cube([holder_wall + 2 * eps, notch_w, notch_w + eps]);
        // screw holes through the ears
        for (sx = [-1, 1])
            translate([sx * (body[0] / 2 + ear_len / 2), 0, -eps])
                cylinder(d = holder_screw_d + 0.3, h = holder_flange_t + 2 * eps);
    }
}

// Two cells as they sit in the holder, for the panel renders.
module battery_2aa_cells() {
    for (y = [-(cell_d + cell_gap) / 2, (cell_d + cell_gap) / 2])
        translate([-cell_len / 2, y, holder_flange_t + cell_d / 2]) rotate([0, 90, 0])
            cylinder(d = cell_d - 0.3, h = cell_len);
}

battery_2aa_holder();
echo(holder_size = holder_size());
