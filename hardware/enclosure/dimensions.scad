// All dimensions in mm. x horizontal (positive = viewer LEFT when facing screen), y up, z front -> rear.
// V0.2 prototype: verify physical fit before printing full-size parts.
body_depth = 85;
face_tilt = 12;
face_w = 80;
face_h = 58;
seam_z = 36;
wall = 3.0;
base_y = -43;

// TFT: landscape, pin header on right. Visible area centered at x=y=0.
tft_w = 86;
tft_h = 50;
visible_w = 58;
visible_h = 43;
visible_left = 9;
visible_top = 3;
window_clearance = 0.4; // each edge
hole_dx = 75;
hole_dy = 43;
// Assumed centered mounting pattern. Verify each hole against fit coupon.
hole_shift_x = 0;
hole_shift_y = 0;
tft_depth = 32; // clearance target; actual measured installed thickness 26
boss_top = 6.0; // shim upward as needed to avoid touching glass
boss_d = 6.0;
tft_pilot_d = 2.7; // M3 thread-forming screw; verify on coupon

// ESP32: slides into side channels; USB faces positive z.
esp_w = 28;
esp_len = 49;
esp_pcb_t = 1.6; // not measured; check rail coupon
esp_rail_clearance = 0.35; // each side
esp_slot_clearance = 0.4;
esp_edge_grip = 0.7;
esp_board_y = -11; // underside of board, tune after measuring connector offset
esp_usb_y = -8.5;
esp_usb_x = 0;
usb_w = 12;
usb_h = 9;
esp_rear_gap = 0.5;
cradle_screw_d = 2.7;

magnet_d = 6.3;
magnet_depth = 3.2;
magnet_boss_d = 11;
magnet_x = 46;
magnet_y = 25;
magnet_boss_height = 7;
seam_tab_clearance = 0.45;
