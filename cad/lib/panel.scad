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
use <../bezels/led_segment_4d_bezel.scad>

// Material color tags. scripts/render_hero.py maps each to a material and
// fails on any other color. Keep-in-sync sweep: these, MATERIALS in
// render_hero.py and PBR() in hero_scene.py.
OAK = "#C8A165";
CHROME = "#C0C0C0";
BLACK = "#222222";
PRINTED = "#E8E4DA";
PCB = "#1E5C3A";
CELL = "#2E4A9E";
ALUMINIUM = "#A8A9AD";
BAKELITE = "#1A1210";
LED = "#E8302A";

// Component record, written by scripts/panels.py. Keep-in-sync sweep:
// these indices, COMPONENT_RECORD and FRONT_FIELDS in panels.py.
function c_id(c) = c[0];
function c_family(c) = c[1];
function c_x(c) = c[2];
function c_y(c) = c[3];
function c_hole_d(c) = c[4];
function c_bushing_d(c) = c[5];
function c_bushing_len(c) = c[6];
function c_nut_af(c) = c[7];
function c_nut_t(c) = c[8];
// the family's two front fields
function c_lever_d(c) = c[9];      // toggle
function c_lever_len(c) = c[10];
function c_knob_d(c) = c[9];       // encoder, rotary
function c_knob_h(c) = c[10];
function c_cap_d(c) = c[9];        // pushbutton head
function c_cap_h(c) = c[10];
function c_body(c) = [c[11], c[12], c[13]];

// Internal record (boards, batteries in the cavity), written by
// scripts/panels.py. Size is already turned for rot. Keep-in-sync sweep:
// these indices and wrapper() in panels.py.
function i_id(m) = m[0];
function i_finish(m) = m[1];
function i_x(m) = m[2];
function i_y(m) = m[3];
function i_size(m) = [m[4], m[5], m[6]];

// Display record (an LED segment module behind a window in the face),
// written by scripts/panels.py. Keep-in-sync sweep: these indices and
// DISPLAY_RECORD in panels.py.
function d_id(d) = d[0];
function d_x(d) = d[1];
function d_y(d) = d[2];
function d_window(d) = [d[3], d[4]];
function d_digits(d) = [d[5], d[6], d[7]];   // LED block, height above its board
function d_body(d) = [d[8], d[9], d[10]];    // behind the face underside
function d_bezel(d) = [d[11], d[12], d[13]];

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

// The board with its cavity, holes and display windows. A window is
// shown as finished: routed through, its corners chiselled square.
module board_wood(board, cavity, components, displays = []) {
    t = board[2]; face_t = cavity[0]; rim = cavity[1];
    color(OAK) difference() {
        board_blank(board);
        translate([rim, rim, -eps])
            linear_extrude(t - face_t + eps)
                rounded_rect([board[0] - 2 * rim, board[1] - 2 * rim], cavity[2]);
        for (c = components)
            translate([c_x(c), c_y(c), -eps]) cylinder(d = c_hole_d(c), h = t + 2 * eps);
        for (d = displays)
            translate([d_x(d) - d_window(d)[0] / 2, d_y(d) - d_window(d)[1] / 2, -eps])
                cube([d_window(d)[0], d_window(d)[1], t + 2 * eps]);
    }
}

// The mount every face mounted family shares, at the origin: the back
// nut and the body behind the face, and with front_nut the bushing
// standing proud and the front nut on it. A pushbutton has its head in
// front instead.
module mount_stand_in(c, t, face_t, front_nut = true) {
    nut_d = c_nut_af(c) / cos(30);
    body = c_body(c);
    color(CHROME) {
        if (front_nut) {
            translate([0, 0, t]) cylinder(d = c_bushing_d(c), h = bushing_above(c, face_t));
            translate([0, 0, t]) cylinder(d = nut_d, h = c_nut_t(c), $fn = 6);
        }
        translate([0, 0, t - face_t - c_nut_t(c)]) cylinder(d = nut_d, h = c_nut_t(c), $fn = 6);
    }
    color(BLACK)
        translate([-body[0] / 2, -body[1] / 2, t - face_t - c_nut_t(c) - body[2]])
            cube(body);
}

// How far the bushing stands proud of the face, the back nut taking up
// what the face leaves.
function bushing_above(c, face_t) = c_bushing_len(c) - face_t - c_nut_t(c);

// A bat handle toggle as mounted: the mount and the lever in front.
// throw is the lever angle from upright, + up.
module toggle_stand_in(c, t, face_t, throw = 0) {
    above = bushing_above(c, face_t);
    translate([c_x(c), c_y(c), 0]) {
        mount_stand_in(c, t, face_t);
        color(CHROME)
            translate([0, 0, t + above - c_lever_d(c) / 2]) rotate([-throw, 0, 0]) {
                cylinder(d1 = 0.6 * c_lever_d(c), d2 = c_lever_d(c), h = c_lever_len(c));
                translate([0, 0, c_lever_len(c)]) sphere(d = c_lever_d(c));
            }
    }
}

// Disc of diameter d with n rounded flutes cut around its edge, for
// knurls and fluted knob grips.
module fluted_disc(d, n, depth) {
    difference() {
        circle(d = d);
        for (i = [0 : n - 1])
            rotate(i * 360 / n) translate([d / 2 + depth / 2, 0]) circle(d = 2 * depth, $fn = 12);
    }
}

// An encoder as mounted: the mount and a machined aluminium knob on the
// shaft, sitting on the bushing, knurled below a chamfered top.
module encoder_stand_in(c, t, face_t) {
    d = c_knob_d(c); h = c_knob_h(c);
    translate([c_x(c), c_y(c), 0]) {
        mount_stand_in(c, t, face_t);
        color(ALUMINIUM) translate([0, 0, t + bushing_above(c, face_t)]) {
            linear_extrude(0.7 * h) fluted_disc(d, round(PI * d / 1.2), 0.5);
            translate([0, 0, 0.7 * h]) cylinder(d1 = d, d2 = 0.8 * d, h = 0.3 * h);
        }
    }
}

// A rotary switch as mounted: the mount and a skirted bakelite pointer
// knob, a fluted grip on a skirt with a metal pointer line toward +y.
module rotary_stand_in(c, t, face_t) {
    d = c_knob_d(c); h = c_knob_h(c);
    skirt = 0.2 * h;
    translate([c_x(c), c_y(c), 0]) {
        mount_stand_in(c, t, face_t);
        translate([0, 0, t + bushing_above(c, face_t)]) {
            color(BAKELITE) {
                cylinder(d1 = d, d2 = 0.9 * d, h = skirt);
                linear_extrude(h - 0.1 * h) fluted_disc(0.55 * d, 10, 0.06 * d);
                translate([0, 0, h - 0.1 * h]) cylinder(d1 = 0.55 * d, d2 = 0.45 * d, h = 0.1 * h);
            }
            // the pointer line, laid into the skirt's slope
            color(ALUMINIUM) translate([-0.02 * d, 0.3 * d, 0])
                cube([0.04 * d, 0.14 * d, skirt + eps]);
        }
    }
}

// A pushbutton as mounted: the back nut and body behind the face, and
// in front the head, a chamfered bezel with the button standing in it.
module pushbutton_stand_in(c, t, face_t) {
    d = c_cap_d(c); h = c_cap_h(c);
    translate([c_x(c), c_y(c), 0]) {
        mount_stand_in(c, t, face_t, front_nut = false);
        color(CHROME) translate([0, 0, t]) {
            cylinder(d1 = d, d2 = 0.9 * d, h = 0.6 * h);
            cylinder(d = 0.7 * d, h = h);
        }
    }
}

// Segments a to g of a seven segment digit, 1 lit: 0 to 9.
SEGMENTS = [[1, 1, 1, 1, 1, 1, 0], [0, 1, 1, 0, 0, 0, 0], [1, 1, 0, 1, 1, 0, 1],
            [1, 1, 1, 1, 0, 0, 1], [0, 1, 1, 0, 0, 1, 1], [1, 0, 1, 1, 0, 1, 1],
            [1, 0, 1, 1, 1, 1, 1], [1, 1, 1, 0, 0, 0, 0], [1, 1, 1, 1, 1, 1, 1],
            [1, 1, 1, 1, 0, 1, 1]];

// The lit segments of one digit n (0 to 9) of height h, centered, slanted
// like a real display.
module seven_segment(n, h) {
    w = 0.5 * h; s = 0.13 * h; g = 0.03 * h;
    on = SEGMENTS[n];
    multmatrix([[1, tan(8), 0, 0], [0, 1, 0, 0], [0, 0, 1, 0]]) {
        for (i = [0, 3, 6]) if (on[i] == 1)  // a, d, g
            translate([-w / 2 + s / 2 + g, (i == 0 ? h / 2 : i == 3 ? -h / 2 : 0) - s / 2])
                square([w - s - 2 * g, s]);
        for (i = [1, 2, 4, 5]) if (on[i] == 1) {  // b, c, e, f
            sx = (i == 1 || i == 2) ? 1 : -1;
            top = (i == 1 || i == 5);
            translate([sx * (w / 2 - s / 2) - s / 2, top ? g : -h / 2 + g])
                square([s, h / 2 - 2 * g]);
        }
    }
}

// A display as mounted: the module's board against the cavity floor
// behind the window, its LED block reaching through the window, the
// printed bezel on the face around it. The stand-in reads 50, the knob
// at half, lit as it is for display_time after an event.
module display_stand_in(d, t, face_t) {
    floor_z = t - face_t;
    digits = d_digits(d); body = d_body(d); bezel = d_bezel(d);
    reading = [-1, -1, 5, 0];  // -1 dark
    translate([d_x(d), d_y(d), 0]) {
        color(PCB) translate([-body[0] / 2, -body[1] / 2, floor_z - 1.6]) cube([body[0], body[1], 1.6]);
        // the driver chip, and the right angle header and its plug at one end
        color(BLACK) {
            translate([-4, -4, floor_z - 3]) cube([8, 8, 1.4 + eps]);
            translate([-body[0] / 2 + 1, -5, floor_z - body[2]]) cube([4, 10, body[2] - 1.6 + eps]);
        }
        color(BAKELITE) translate([-digits[0] / 2, -digits[1] / 2, floor_z]) cube(digits);
        color(LED) for (i = [0 : 3]) if (reading[i] >= 0)
            translate([(i - 1.5) * digits[0] / 4, 0, floor_z + digits[2] - 0.1])
                linear_extrude(0.15) seven_segment(reading[i], 0.65 * digits[1]);
        color(BLACK) translate([0, 0, t]) display_bezel([bezel[0], bezel[1]], digits, bezel[2]);
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
// both lever positions. Keep-in-sync sweep for families: FRONT_FIELDS in
// panels.py.
module finished_panel(board, cavity, components, internals, displays = []) {
    board_wood(board, cavity, components, displays);
    for (i = [0 : len(components) - 1]) {
        c = components[i]; t = board[2]; face_t = cavity[0];
        if (c_family(c) == "toggle")
            toggle_stand_in(c, t, face_t, i % 2 == 0 ? 14 : -14);
        else if (c_family(c) == "encoder")
            encoder_stand_in(c, t, face_t);
        else if (c_family(c) == "rotary")
            rotary_stand_in(c, t, face_t);
        else if (c_family(c) == "pushbutton")
            pushbutton_stand_in(c, t, face_t);
        else
            assert(false, str("no stand-in for family ", c_family(c)));
    }
    assert(len(internals) == 0 || holder_screw_len - holder_flange_t <= cavity[0] - face_skin,
           str("holder screws reach ", holder_screw_len - holder_flange_t, " mm into a ",
               cavity[0], " mm face, more than face_t - face_skin"));
    for (m = internals)
        internal_stand_in(m, board[2] - cavity[0]);
    for (d = displays)
        display_stand_in(d, board[2], cavity[0]);
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
// A display window's corners get a punch bore each: the window is routed
// with round corners (the bit radius) and squared to the four marks
// with a chisel. Its size is engraved between them.
module punch_template_in_place(name, board, cavity, components, displays = []) {
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
        for (d = displays) {
            win = d_window(d);
            for (sx = [-1, 1], sy = [-1, 1])
                translate([d_x(d) + sx * win[0] / 2, d_y(d) + sy * win[1] / 2, t - eps])
                    cylinder(d = punch_d + punch_clearance, h = punch_plate_t + 2 * eps);
            translate([d_x(d), d_y(d), top - label_depth]) label(str(win[0], " x ", win[1]));
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

// The router template's second step, for the display windows (ADR-0006):
// a plate that drops into the router template's opening once the cavity
// is routed, resting on the band of back face the opening leaves around
// the cavity, flush with the template so the router base rides both.
// The guide bushing runs inside a window opening, the window grown by
// the bushing to bit offset, and the bit goes on through the face. The
// window comes out with the bit radius in its corners; the punch marks
// show where to chisel them square.
module router_step_in_place(name, board, cavity, displays) {
    w = board[0]; h = board[1]; t = board[2];
    rim = cavity[1]; r = cavity[2];
    off = (copy_ring_od - bit_d) / 2;
    plate = [w - 2 * rim + 2 * off - 2 * slip_fit, h - 2 * rim + 2 * off - 2 * slip_fit];
    // the window's corner radius is the bit's, the tightest it can cut, so
    // the opening's is the guide bushing's
    win_r = bit_d / 2;
    assert(len(displays) > 0, "router_step: the panel has no display");
    for (d = displays) {
        win = d_window(d);
        rail = min(d_x(d) - win[0] / 2 - rim, w - rim - d_x(d) - win[0] / 2,
                   d_y(d) - win[1] / 2 - rim, h - rim - d_y(d) - win[1] / 2);
        assert(min(win) >= bit_d, str(d_id(d), ": window ", win[0], " x ", win[1],
                                      " is narrower than the bit ", bit_d));
        assert(rail >= rail_min, str(d_id(d), ": step plate rail ", rail,
                                     " beside the window is narrower than rail_min"));
    }
    color(PRINTED) difference() {
        translate([rim - off + slip_fit, rim - off + slip_fit, -router_plate_t])
            linear_extrude(router_plate_t) rounded_rect(plate, r + off - slip_fit);
        for (d = displays) {
            win = d_window(d);
            translate([d_x(d) - win[0] / 2 - off, d_y(d) - win[1] / 2 - off, -router_plate_t - eps])
                linear_extrude(router_plate_t + 2 * eps)
                    rounded_rect([win[0] + 2 * off, win[1] + 2 * off], win_r + off);
        }
        translate([w / 2, rim - off / 2, -router_plate_t - eps])
            label(str(name, "  STEP  through  depth ", t), flip = true);
    }
}

module punch_template_print(name, board, cavity, components, displays = []) {
    translate([0, 0, board[2] + punch_plate_t]) rotate([180, 0, 0])
        punch_template_in_place(name, board, cavity, components, displays);
}

module router_step_print(name, board, cavity, displays) {
    translate([0, 0, router_plate_t]) router_step_in_place(name, board, cavity, displays);
}

module router_template_print(name, board, cavity) {
    translate([0, 0, router_plate_t]) router_template_in_place(name, board, cavity);
}

// part: panel (finished board), punch, router, router_step (templates in
// print orientation; router_step only for a panel with a display), hero
// (the panel standing, front toward -y), build (the board with its punch
// template seated, the router template beside it, its step plate in it)
module panel(part, name, board, cavity, components, internals = [], displays = []) {
    if (part == "panel")
        finished_panel(board, cavity, components, internals, displays);
    else if (part == "punch")
        punch_template_print(name, board, cavity, components, displays);
    else if (part == "router")
        router_template_print(name, board, cavity);
    else if (part == "router_step")
        router_step_print(name, board, cavity, displays);
    else if (part == "hero")
        rotate([90, 0, 0]) translate([0, 0, -board[2]])
            finished_panel(board, cavity, components, internals, displays);
    else if (part == "build") {
        board_wood(board, cavity, components, displays);
        punch_template_in_place(name, board, cavity, components, displays);
        translate([board[0] + fence_t + router_margin + 40, 0, 0]) {
            router_template_print(name, board, cavity);
            if (len(displays) > 0) router_step_print(name, board, cavity, displays);
        }
    } else
        assert(false, str("unknown part ", part));
}
