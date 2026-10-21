// Panel library: the finished board, its two printed templates and the
// render scenes, all built from one panel description.
//
// Never opened directly. scripts/panels.py writes a wrapper per
// panels/<name>.json (build/panels/<name>/<name>.scad) that `use`s this
// file and calls panel() with the JSON and the catalog resolved into
// plain values. Open that wrapper in OpenSCAD to look at a panel.
//
// Coordinates: the board lies front face up, the reference corner (bottom
// left seen from the front) at the origin, x right, y up the panel, the
// front face at z = board thickness. Layout positions in the JSON are
// measured in this frame. Both templates are modeled where they sit on
// the board, then turned into their print orientation, so no layout is
// ever mirrored by hand.

include <../design_params.scad>
use <../holders/battery_2aa_holder.scad>

// Material color tags. scripts/render_hero.py maps each to a material and
// fails on any other color. Keep-in-sync sweep: these, MATERIALS in
// render_hero.py and PBR() in hero_scene.py.
OAK = "#C8A165";
CHROME = "#C0C0C0";
BLACK = "#222222";
PRINTED = "#E8E4DA";
PCB = "#1E5C3A";
CELL = "#2E4A9E";

// Component record, written by scripts/panels.py. Keep-in-sync sweep:
// these indices and COMPONENT_RECORD in panels.py.
function c_id(c) = c[0];
function c_family(c) = c[1];
function c_x(c) = c[2];
function c_y(c) = c[3];
function c_hole_d(c) = c[4];
function c_bushing_d(c) = c[5];
function c_bushing_len(c) = c[6];
function c_nut_af(c) = c[7];
function c_nut_t(c) = c[8];
function c_lever_d(c) = c[9];
function c_lever_len(c) = c[10];
function c_body(c) = [c[11], c[12], c[13]];

// Internal record (boards, batteries in the cavity), written by
// scripts/panels.py. Size is already turned for rot. Keep-in-sync sweep:
// these indices and wrapper() in panels.py.
function i_id(m) = m[0];
function i_finish(m) = m[1];
function i_x(m) = m[2];
function i_y(m) = m[3];
function i_size(m) = [m[4], m[5], m[6]];

// board = [w, h, t, chamfer], cavity = [face_t, rim, r]

module rounded_rect(size, r) {
    translate([r, r]) offset(r = r) square([size[0] - 2 * r, size[1] - 2 * r]);
}

module board_blank(board) {
    w = board[0]; h = board[1]; t = board[2]; c = board[3];
    if (c > 0)
        hull() {
            cube([w, h, t - c]);
            translate([c, c, 0]) cube([w - 2 * c, h - 2 * c, t]);
        }
    else
        cube([w, h, t]);
}

module board_wood(board, cavity, components) {
    t = board[2]; face_t = cavity[0]; rim = cavity[1];
    color(OAK) difference() {
        board_blank(board);
        translate([rim, rim, -eps])
            linear_extrude(t - face_t + eps)
                rounded_rect([board[0] - 2 * rim, board[1] - 2 * rim], cavity[2]);
        for (c = components)
            translate([c_x(c), c_y(c), -eps]) cylinder(d = c_hole_d(c), h = t + 2 * eps);
    }
}

// A bat handle toggle as mounted: back nut, body behind the face, front
// nut and lever in front. throw is the lever angle from upright, + up.
module toggle_stand_in(c, t, face_t, throw = 0) {
    nut_d = c_nut_af(c) / cos(30);
    above = c_bushing_len(c) - face_t - c_nut_t(c);
    body = c_body(c);
    translate([c_x(c), c_y(c), 0]) {
        color(CHROME) {
            translate([0, 0, t]) cylinder(d = c_bushing_d(c), h = above);
            translate([0, 0, t]) cylinder(d = nut_d, h = c_nut_t(c), $fn = 6);
            translate([0, 0, t - face_t - c_nut_t(c)])
                cylinder(d = nut_d, h = c_nut_t(c), $fn = 6);
            translate([0, 0, t + above - c_lever_d(c) / 2]) rotate([-throw, 0, 0]) {
                cylinder(d1 = 0.6 * c_lever_d(c), d2 = c_lever_d(c), h = c_lever_len(c));
                translate([0, 0, c_lever_len(c)]) sphere(d = c_lever_d(c));
            }
        }
        color(BLACK)
            translate([-body[0] / 2, -body[1] / 2, t - face_t - c_nut_t(c) - body[2]])
                cube(body);
    }
}

// An internal module lying on the cavity floor (the underside of the
// face), reaching toward the open back. Only the envelope is a catalog
// value; the detail inside it is for the renders. Keep-in-sync sweep for
// finishes: FINISHES in panels.py.
module internal_stand_in(m, floor_z) {
    s = i_size(m);
    long_x = s[0] >= s[1];
    len_ = max(s[0], s[1]);
    wid = min(s[0], s[1]);
    translate([i_x(m), i_y(m), floor_z]) rotate([0, 0, long_x ? 0 : 90]) mirror([0, 0, 1]) {
        if (i_finish(m) == "pcb") {
            color(PCB) translate([-len_ / 2, -wid / 2, 0]) cube([len_, wid, 1.6]);
            // radio module can toward the +x (antenna) end, USB at the other
            color(CHROME) translate([len_ / 2 - 25, -9, 1.6]) cube([18, 18, 3.2]);
            color(CHROME) translate([-len_ / 2, -4.5, 1.6]) cube([7.5, 9, 3.2]);
            color(BLACK) for (sy = [-1, 1])
                translate([-len_ / 2 + 10, sy * (wid / 2 - 2.5) - 1.25, 1.6])
                    cube([len_ - 30, 2.5, s[2] - 1.6]);
        } else if (i_finish(m) == "aa_holder") {
            // the real printed holder, with two cells in it
            color(PRINTED) battery_2aa_holder();
            color(CELL) battery_2aa_cells();
        } else
            assert(false, str("no stand-in for finish ", i_finish(m)));
    }
}

// The finished panel. Toggles alternate up and down so a render shows
// both lever positions.
module finished_panel(board, cavity, components, internals) {
    board_wood(board, cavity, components);
    for (i = [0 : len(components) - 1])
        if (c_family(components[i]) == "toggle")
            toggle_stand_in(components[i], board[2], cavity[0], i % 2 == 0 ? 14 : -14);
    assert(len(internals) == 0 || holder_screw_len - holder_flange_t <= cavity[0] - face_skin,
           str("holder screws reach ", holder_screw_len - holder_flange_t, " mm into a ",
               cavity[0], " mm face, more than face_t - face_skin"));
    for (m = internals)
        internal_stand_in(m, board[2] - cavity[0]);
}

// Fence groove along the fence root, a diamond centered on the corner
// line so it relieves plate and fence alike and prints without support.
module root_grooves(board, z) {
    s = fence_relief * sqrt(2);
    translate([0, -fence_t - eps, z]) rotate([-90, 0, 0])
        linear_extrude(board[1] + fence_t + 2 * eps) rotate(45) square(s, center = true);
    translate([-fence_t - eps, 0, z]) rotate([0, 90, 0])
        linear_extrude(board[0] + fence_t + 2 * eps) rotate(45) square(s, center = true);
}

// Fences down the two reference edges, from z0 to z1.
module fences(board, z0, z1) {
    translate([-fence_t, -fence_t, z0]) cube([fence_t, board[1] + fence_t, z1 - z0]);
    translate([-fence_t, -fence_t, z0]) cube([board[0] + fence_t, fence_t, z1 - z0]);
}

// Engraved text, reading correctly from +z, or with flip from -z after
// the board is turned over its long (x) edge, the natural way to turn a
// long board.
module label(txt, flip = false) {
    mirror([0, flip ? 1 : 0, 0])
        linear_extrude(label_depth + eps)
            text(txt, size = label_size, halign = "center", valign = "center");
}

// Punch template where it sits: on the front face.
module punch_template_in_place(name, board, cavity, components) {
    w = board[0]; h = board[1]; t = board[2];
    fh = min(fence_h, t);
    top = t + punch_plate_t;
    assert(w + fence_t <= max(bed_x, bed_y) && h + fence_t <= min(bed_x, bed_y),
           str("punch template ", w + fence_t, " x ", h + fence_t, " does not fit the bed"));
    color(PRINTED) difference() {
        union() {
            translate([-fence_t, -fence_t, t]) cube([w + fence_t, h + fence_t, punch_plate_t]);
            fences(board, t - fh, top);
        }
        for (c = components) {
            translate([c_x(c), c_y(c), t - eps])
                cylinder(d = punch_d + punch_clearance, h = punch_plate_t + 2 * eps);
            // drill size for this hole, under the bore
            translate([c_x(c), c_y(c) - punch_d / 2 - 1.5 - label_size / 2, top - label_depth])
                label(str(c_hole_d(c)));
        }
        translate([w / 2, cavity[1] / 2, top - label_depth]) label(str(name, "  FRONT"));
        root_grooves(board, t);
    }
}

// Router template where it sits: on the back face (below the board in
// this frame). The guide bushing rides the inside of the opening, so the
// opening is the cavity grown by the bushing to bit offset.
module router_template_in_place(name, board, cavity) {
    w = board[0]; h = board[1]; t = board[2];
    face_t = cavity[0]; rim = cavity[1]; r = cavity[2];
    off = (copy_ring_od - bit_d) / 2;
    fh = min(fence_h, t);
    lo = -fence_t - router_margin;
    size = [w + fence_t + 2 * router_margin, h + fence_t + 2 * router_margin];
    opening = [w - 2 * rim + 2 * off, h - 2 * rim + 2 * off];
    assert(off > 0, "copy_ring_od must exceed bit_d");
    assert(r >= bit_d / 2, str("cavity corner r ", r, " is tighter than the bit radius ", bit_d / 2));
    assert(rim > off, str("cavity rim ", rim, " must exceed the bushing offset ", off,
                          " or the opening cuts into the fences"));
    assert(rim - off + router_margin >= rail_min, "router template rail narrower than rail_min");
    assert(router_plate_t >= copy_ring_h, "router_plate_t is thinner than the guide bushing");
    assert(min(opening) + 2 * router_base_overlap <= router_base_d,
           str("opening ", min(opening), " mm is too wide for the router base to span"));
    assert(size[0] <= max(bed_x, bed_y) && size[1] <= min(bed_x, bed_y),
           str("router template ", size[0], " x ", size[1], " does not fit the bed"));
    color(PRINTED) difference() {
        union() {
            translate([lo, lo, -router_plate_t]) cube([size[0], size[1], router_plate_t]);
            fences(board, -router_plate_t, fh);
        }
        translate([rim - off, rim - off, -router_plate_t - eps])
            linear_extrude(router_plate_t + 2 * eps) rounded_rect(opening, r + off);
        translate([w / 2, h + router_margin / 2, -router_plate_t - eps])
            label(str(name, "  BACK  ring ", copy_ring_od, "  bit ", bit_d,
                      "  depth ", t - face_t), flip = true);
        root_grooves(board, 0);
    }
}

module punch_template_print(name, board, cavity, components) {
    translate([0, 0, board[2] + punch_plate_t]) rotate([180, 0, 0])
        punch_template_in_place(name, board, cavity, components);
}

module router_template_print(name, board, cavity) {
    translate([0, 0, router_plate_t]) router_template_in_place(name, board, cavity);
}

// part: panel (finished board), punch, router (templates in print
// orientation), hero (the panel standing, front toward -y), build (the
// board with its punch template seated, the router template beside it)
module panel(part, name, board, cavity, components, internals = []) {
    if (part == "panel")
        finished_panel(board, cavity, components, internals);
    else if (part == "punch")
        punch_template_print(name, board, cavity, components);
    else if (part == "router")
        router_template_print(name, board, cavity);
    else if (part == "hero")
        rotate([90, 0, 0]) translate([0, 0, -board[2]])
            finished_panel(board, cavity, components, internals);
    else if (part == "build") {
        board_wood(board, cavity, components);
        punch_template_in_place(name, board, cavity, components);
        translate([board[0] + fence_t + router_margin + 40, 0, 0])
            router_template_print(name, board, cavity);
    } else
        assert(false, str("unknown part ", part));
}
