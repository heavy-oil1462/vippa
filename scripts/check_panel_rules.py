#!/usr/bin/env python3
"""Cases for the layout checks in scripts/panels.py: a check has a
panel or catalog entry that fails it, so a check that stops working
fails the gate. The display and lamp checks have theirs; a new check
gets one here. Run by regen_all.py with the other gates.

Every case starts from an example panel that passes,
panels/thermostat.json for a display and panels/garage.json for a
lamp, and breaks one rule. Standard library unittest only.

Usage:
    scripts/check_panel_rules.py
"""

import copy
import io
import sys
import unittest

import panels


class PanelCase(unittest.TestCase):
    """Loads the catalog and the example panel PANEL."""

    PANEL = None

    def setUp(self):
        catalog, errors = panels.load_catalog()
        self.assertEqual(errors, [])
        self.catalog = catalog
        self.panel = panels.load_panel(self.PANEL)

    def component(self, cid):
        return next(c for c in self.panel["components"] if c["id"] == cid)

    def problems(self, panel=None, catalog=None):
        return panels.validate(panel or self.panel, catalog or self.catalog)

    def assertFails(self, needle, panel=None, catalog=None):
        problems = self.problems(panel, catalog)
        self.assertTrue(any(needle in p for p in problems),
                        f"no problem with {needle!r} in {problems}")


class DisplayChecks(PanelCase):
    """The display family: a window through the face, a bezel in front of
    it and the module behind it (ADR-0006)."""

    PANEL = "thermostat"

    def display(self, panel=None):
        panel = panel or self.panel
        return next(c for c in panel["components"]
                    if self.catalog[c["type"]]["family"] == "display")

    def test_thermostat_passes(self):
        self.assertEqual(self.problems(), [])

    def test_bezel_inside_the_cavity(self):
        # a bezel wider than the module's body, so only the bezel leaves
        catalog = copy.deepcopy(self.catalog)
        catalog["led_segment_4d"]["bezel"][0] = 160
        self.assertFails("leaves no room for its bezel", catalog=catalog)

    def test_bezel_clears_keepouts(self):
        self.display()["y"] -= 5
        self.assertFails("its keepout needs")

    def test_bezels_do_not_overlap(self):
        second = copy.deepcopy(self.display())
        second["id"] = "second"
        second["x"] += 10
        self.panel["components"].append(second)
        self.assertFails("bezel overlaps the bezel of")

    def test_digits_reach_through_the_face(self):
        self.panel["cavity"]["face_t"] = 8
        self.assertFails("reach through the face")

    def test_digits_stay_inside_the_bezel(self):
        self.panel["cavity"]["face_t"] = 3
        self.assertFails("stay inside")

    def test_body_fits_the_cavity_depth(self):
        catalog = copy.deepcopy(self.catalog)
        catalog["led_segment_4d"]["body"][2] = 30
        self.assertFails("shallower than the display body", catalog=catalog)

    def test_body_clear_of_the_cavity_wall(self):
        catalog = copy.deepcopy(self.catalog)
        catalog["led_segment_4d"]["body"][1] = 64
        self.assertFails("display body at", catalog=catalog)

    def test_body_clear_of_other_bodies(self):
        catalog = copy.deepcopy(self.catalog)
        catalog["led_segment_4d"]["body"][1] = 60
        self.assertFails("display body 0.2 mm from setpoint, needs", catalog=catalog)

    def test_internals_clear_the_body(self):
        esp = next(i for i in self.panel["internals"] if i["id"] == "esp")
        esp["x"] = 120
        self.assertFails("esp: 1.0 mm from setpoint_display, needs")

    def test_body_is_metal_for_the_antenna(self):
        esp = next(i for i in self.panel["internals"] if i["id"] == "esp")
        esp.update(rot=0, x=63, y=100)  # antenna end +x, toward the display
        self.panel["board"]["h"] = 140
        self.assertFails("setpoint_display is metal inside the antenna keepout")

    def test_shows_a_knob(self):
        self.display()["shows"] = "battery"
        self.assertFails("a display shows one of the panel's knobs")

    def test_needs_a_knob(self):
        knob = next(c for c in self.panel["components"] if c["id"] == "setpoint")
        self.panel["components"] = [self.display(),
                                    {**knob, "id": "flip", "type": "toggle_12mm"}]
        self.assertFails("a display shows one of the panel's knobs")

    def test_pins_off_the_wake_pins(self):
        pins, errors = panels.assign_pins(self.panel, self.catalog)
        self.assertEqual(errors, [])
        self.assertTrue(set(pins["setpoint_display"].values()).isdisjoint(panels.WAKE_PINS))
        self.assertEqual(pins["setpoint"], {"push": 10, "a": 11, "b": 12})

    def test_catalog_window_takes_the_digits(self):
        entry = copy.deepcopy(self.catalog["led_segment_4d"])
        entry["window"][0] = entry["digits"][0]
        self.assertTrue(any("wider and taller than the digits" in e
                            for e in panels.display_catalog_errors("x", entry)))

    def test_catalog_bezel_covers_the_window(self):
        entry = copy.deepcopy(self.catalog["led_segment_4d"])
        entry["bezel"][1] = entry["window"][1] + 1
        self.assertTrue(any("must cover the window" in e
                            for e in panels.display_catalog_errors("x", entry)))


class LampChecks(PanelCase):
    """The lamp family: a pilot lamp mounted like a pushbutton, lit after
    an event of the control it follows."""

    PANEL = "garage"

    def test_garage_passes(self):
        self.assertEqual(self.problems(), [])

    def test_mount_checks(self):
        self.component("door_lamp")["y"] -= 10
        self.assertFails("door_lamp: 18.0 mm from door, keepouts need")

    def test_body_is_metal_for_the_antenna(self):
        esp = next(i for i in self.panel["internals"] if i["id"] == "esp")
        esp.update(rot=0, x=75, y=101)  # above the lamps, antenna end +x
        self.component("lights_lamp").update(x=118, y=101)  # past that end
        self.panel["board"]["h"] = 140
        self.assertFails("lights_lamp is metal inside the antenna keepout")

    def test_follows_a_component(self):
        self.component("door_lamp")["follows"] = "garage_door"
        self.assertFails("a lamp follows one of the panel's toggles")

    def test_follows_a_control(self):
        self.component("door_lamp")["follows"] = "lights_lamp"
        self.assertFails("a lamp follows one of the panel's toggles")

    def test_needs_follows(self):
        del self.component("door_lamp")["follows"]
        self.assertFails("door_lamp: follows None")

    def test_color_from_the_catalog(self):
        self.component("door_lamp")["color"] = "blue"
        self.assertFails("color 'blue' is not one of pilot_lamp_12mm's colors")

    def test_color_defaults_to_the_first(self):
        lamp = self.component("door_lamp")
        del lamp["color"]
        self.assertEqual(self.problems(), [])
        entry = self.catalog[lamp["type"]]
        self.assertEqual(panels.lamp_color(lamp, entry), entry["colors"][0])

    def test_pins_off_the_wake_pins(self):
        pins, errors = panels.assign_pins(self.panel, self.catalog)
        self.assertEqual(errors, [])
        for lamp in ("door_lamp", "lights_lamp"):
            self.assertNotIn(pins[lamp]["pin"], panels.WAKE_PINS)
        self.assertEqual([pins[c]["pin"] for c in ("door", "lights", "vent")], [10, 11, 12])

    def test_catalog_colors_known(self):
        entry = copy.deepcopy(self.catalog["pilot_lamp_12mm"])
        entry["colors"].append("violet")
        self.assertTrue(any("colors must be a list" in e
                            for e in panels.lamp_catalog_errors("x", entry)))

    def test_catalog_led_current(self):
        entry = copy.deepcopy(self.catalog["pilot_lamp_12mm"])
        entry["led_ma"] = panels.LED_MAX_MA + 5
        self.assertTrue(any("what an ESP32-H2 pin drives" in e
                            for e in panels.lamp_catalog_errors("x", entry)))


if __name__ == "__main__":
    out = io.StringIO()
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    result = unittest.TextTestRunner(stream=out, verbosity=0).run(suite)
    if result.wasSuccessful():
        print(f"ok: {result.testsRun} panel rule cases, each check fails its case")
    else:
        print(f"[FAIL] panel rule cases\n{out.getvalue()}")
    sys.exit(0 if result.wasSuccessful() else 1)
