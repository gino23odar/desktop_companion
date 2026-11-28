// OpenSCAD: set part in Customizer, F6 render, export STL.
include <dimensions.scad>
part = "assembly"; // [assembly,front_shell,rear_shell,esp_cradle,tail,screen_fit,magnet_fit,usb_fit,rail_fit,preview,exploded]
$fn = 32;
eps = 0.02;

// From the front, physical right is negative CAD x.
pcb_x = visible_w/2+visible_left-tft_w/2;
pcb_y = visible_h/2+visible_top-tft_h/2;
window_w = visible_w+2*window_clearance;
window_h = visible_h+2*window_clearance;
rear_inner = body_depth-wall;
board_front = rear_inner-esp_len-esp_rear_gap;
rail_end = rear_inner-1.5;
rail_bottom = esp_board_y-13;
rail_outer = esp_w/2+3.8;
rail_inner = esp_w/2-esp_edge_grip;
rail_slot_x = esp_w/2+esp_rail_clearance;
rail_top = esp_board_y+esp_pcb_t+esp_slot_clearance+1.2;
cradle_mount_x = 22;
cradle_mount_y = esp_board_y-2;
cradle_mount_z = rear_inner-5;

assert(face_tilt >= 0 && face_tilt <= 20, "Unsupported face tilt");
assert(board_front > 25, "Insufficient space behind TFT");
assert(magnet_depth < magnet_boss_height, "Magnet pocket cuts through boss");

module rr(w,h,r){
    hull() for(x=[-w/2+r,w/2-r],y=[-h/2+r,h/2-r]) translate([x,y]) circle(r=r);
}
module section(z,w,h,r){ translate([0,0,z]) linear_extrude(height=eps) rr(w,h,r); }
module loft(sections){
    for(i=[0:len(sections)-2]) hull(){
        section(sections[i][0],sections[i][1],sections[i][2],sections[i][3]);
        section(sections[i+1][0],sections[i+1][1],sections[i+1][2],sections[i+1][3]);
    }
}
module prism(w,h,r,z0,z1){translate([0,0,z0]) linear_extrude(height=z1-z0) rr(w,h,r);}
module face_transform(){rotate([face_tilt,0,0]) children();}
module tilted_section(z,w,h,r){face_transform() section(z,w,h,r);}
module front_profile(inner=false){
    if(!inner){
        hull(){ for(a=[[0,face_w,face_h,8],[2,94,64,10],[7,110,74,12],[15,112,80,22]]) tilted_section(a[0],a[1],a[2],a[3]); section(seam_z-eps,112,82,23); }
    }else{
        hull(){ for(a=[[3,91,56,3],[5.8,100,59,3],[9,103,67,7],[15,105,73,18]]) tilted_section(a[0],a[1],a[2],a[3]); section(seam_z+eps,106,76,20); }
    }
}
module soft_ear(x,y,z,wide,tall,lean){
    hull(){
        translate([x,y,z]) scale([wide,8,8]) sphere(r=1);
        translate([x+lean,y+tall,z+1]) scale([4.8,5.4,5.5]) sphere(r=1);
        translate([x-lean*.45,y+3,z+1]) scale([wide*.75,6,7]) sphere(r=1);
    }
}
module front_outer(){
    intersection(){
        union(){
            front_profile();
            soft_ear(34,34,13,11,18,7);
            soft_ear(-34,34,14,9,12,-4);
            for(x=[-30,30]) hull(){
                translate([x,-35,9]) scale([12,9,9]) sphere(r=1);
                translate([x,-37,19]) scale([10,8,10]) sphere(r=1);
            }
        }
        translate([-100,base_y,-40]) cube([200,150,150]);
        face_transform() translate([-100,-100,0.05]) cube([200,200,200]);
        translate([-100,-100,-40]) cube([200,200,seam_z+40]);
    }
}
module front_void(){front_profile(true);}
module rear_outer(){
    loft([[seam_z,112,82,23],[seam_z+5,112,82,23],[50,108,80,24],[65,98,74,25],[76,86,66,25],[body_depth-2,72,57,23],[body_depth-eps,68,54,22]]);
    intersection(){
        hull(){translate([0,-34,64]) scale([21,11,11]) sphere(r=1);translate([0,-36,75]) scale([20,9,8]) sphere(r=1);}
        translate([-100,base_y,0]) cube([200,100,body_depth]);
    }
}
module rear_void(){
    loft([[seam_z-eps,106,76,20],[seam_z+5,106,76,20],[50,102,74,21],[65,92,68,22],[76,80,60,22],[rear_inner-eps,67,51,20]]);
}
module screen_cut(){
    // square-ish corners preserve the screen corners, bevel outward for touch access.
    loft([[-1,window_w+2.4,window_h+2.4,1.4],[1.25,window_w,window_h,0.2],[wall+0.5,window_w,window_h,0.2]]);
}
module tft_holes(){for(sx=[-1,1],sy=[-1,1]) translate([pcb_x+hole_shift_x+sx*hole_dx/2,pcb_y+hole_shift_y+sy*hole_dy/2,0]) children();}
module tft_bosses(){tft_holes() translate([0,0,2.8]) cylinder(h=boss_top-2.8,d=boss_d);}
module tft_pilots(){tft_holes() translate([0,0,2.1]) cylinder(h=boss_top,d=tft_pilot_d);}
module magnet_positions(){for(x=[-magnet_x,magnet_x],y=[-magnet_y,magnet_y]) translate([x,y,0]) children();}
module front_magnet_bosses(){magnet_positions() translate([0,0,seam_z-magnet_boss_height]) cylinder(h=magnet_boss_height,d=magnet_boss_d);}
module rear_magnet_bosses(){magnet_positions() translate([0,0,seam_z]) cylinder(h=magnet_boss_height,d=magnet_boss_d);}
module front_magnet_cuts(){magnet_positions() translate([0,0,seam_z-magnet_depth]) cylinder(h=magnet_depth+eps,d=magnet_d);}
module rear_magnet_cuts(){magnet_positions() translate([0,0,seam_z-eps]) cylinder(h=magnet_depth+eps,d=magnet_d);}
module alignment_tabs(){
    for(s=[-1,1]){
        translate([-10,s>0?36:-41,seam_z-2]) cube([20,5,2]);
        translate([-10,s>0?35.3:-38+seam_tab_clearance,seam_z-eps]) cube([20,2.2,2.5+eps]);
        translate([s>0?51:-56,-8,seam_z-2]) cube([5,16,2]);
        translate([s>0?50.3:-53+seam_tab_clearance,-8,seam_z-eps]) cube([2.2,16,2.5+eps]);
    }
}
module front_shell(){
    difference(){
        union(){
            difference(){front_outer();front_void();}
            intersection(){front_outer();face_transform() tft_bosses();}
            front_magnet_bosses();alignment_tabs();
        }
        face_transform(){screen_cut();tft_pilots();} front_magnet_cuts();
    }
}
module usb_cut(z0,z1){translate([esp_usb_x,esp_usb_y,0]) prism(usb_w,usb_h,1.1,z0,z1);}
module butt_recess(){translate([esp_usb_x,esp_usb_y,body_depth-0.65]) scale([1,0.75,1]) cylinder(h=1.5,r=8.5);}
module rear_vents(){
    // Through the flat rear face, below the electronics and USB port.
    for(x=[-17,0,17],y=[-20,-24]) translate([x,y,0]) prism(10,2.2,1.0,rear_inner-7,body_depth+1);
}
module cradle_bosses(){for(s=[-1,1]) translate([s*cradle_mount_x,cradle_mount_y,cradle_mount_z+2-eps]) cylinder(h=wall+3,d=8);}
module cradle_pilots(){for(s=[-1,1]) translate([s*cradle_mount_x,cradle_mount_y,cradle_mount_z+2-eps]) cylinder(h=4.7,d=cradle_screw_d);}
module rear_shell(){
    difference(){
        union(){difference(){rear_outer();rear_void();}rear_magnet_bosses();cradle_bosses();}
        rear_magnet_cuts();usb_cut(rear_inner-1,body_depth+1);butt_recess();rear_vents();cradle_pilots();
        // trim bosses flush with exterior rear face if parameter changes
        translate([-100,-100,body_depth]) cube([200,200,10]);
    }
}
module rail(s,front=board_front,end=rail_end){
    scale([s,1,1]) difference(){
        translate([rail_inner,rail_bottom,front]) cube([rail_outer-rail_inner,rail_top-rail_bottom,end-front]);
        translate([rail_inner-eps,esp_board_y-esp_slot_clearance/2,front-eps]) cube([rail_slot_x-rail_inner+eps,esp_pcb_t+esp_slot_clearance,end-front+2*eps]);
    }
}
module esp_cradle(){
    difference(){
        union(){
            for(s=[-1,1]){
                rail(s);
                // Front PCB stop; contacts board edges only.
                scale([s,1,1]) translate([rail_inner,esp_board_y-0.2,board_front-1.4]) cube([rail_outer-rail_inner,esp_pcb_t+0.4,1.6]);
                // Rear mounting ears with axial screw holes.
                scale([s,1,1]) hull(){
                    translate([rail_outer-1,cradle_mount_y-3,cradle_mount_z]) cube([1.5,6,2]);
                    translate([cradle_mount_x,cradle_mount_y,cradle_mount_z]) cylinder(h=2,d=8);
                }
            }
            // Crossbar is well below PCB and pin headers; verify wire clearance.
            translate([-rail_outer,rail_bottom,board_front+2]) cube([2*rail_outer,2.4,5]);
        }
        for(s=[-1,1]) translate([s*cradle_mount_x,cradle_mount_y,cradle_mount_z-1]) cylinder(h=4,d=3.5);
    }
}
module tail_shape(){
    // Printed flat as a raised spiral relief; attach to rear plastic only.
    pts=concat([[0,0],[0,3]], [for(i=[0:29]) let(a=-115+i*13,r=9.5-i*0.23) [4+r*cos(a),14+r*sin(a)]]);
    for(i=[0:len(pts)-2]) hull(){translate(pts[i]) circle(r=2.1);translate(pts[i+1]) circle(r=2.1);}
    translate([0,0]) circle(r=3.8);
}
module tail(){linear_extrude(height=5) tail_shape();}
module screen_fit(){
    // Exact hole and bezel coordinates; thin sacrificial full-size fit template.
    difference(){
        union(){translate([pcb_x,pcb_y,0]) prism(tft_w+3,tft_h+3,2,0,wall);tft_bosses();}
        screen_cut();tft_pilots();
    }
}
module magnet_fit(){
    // Three pockets left to right: 6.1 / 6.3 / 6.5 mm, depth 3.2.
    difference(){translate([-17,-6,0]) cube([34,12,5]);for(i=[0:2])translate([-11+i*11,0,5-magnet_depth]) cylinder(h=magnet_depth+eps,d=6.1+i*.2);}
}
module usb_fit(){
    // Rear wall geometry, use actual cable and board to check reach.
    difference(){translate([esp_usb_x-13,esp_usb_y-10,0]) cube([26,20,wall]);usb_cut(-1,wall+1);}
}
module rail_fit(){
    difference(){union(){for(s=[-1,1]) rail(s,0,12);translate([-rail_outer,rail_bottom,0]) cube([2*rail_outer,2.4,12]);}}
}
// Visualization only. No electronic mock-ups are included in printable STLs.
module face_mock(){
    color("#372B37") translate([0,0,wall-0.1]) linear_extrude(height=0.2) rr(window_w,window_h,0.2);
    color("#FFD1DE") translate([0,0,wall-0.22]) linear_extrude(height=0.12) square([visible_w,visible_h],center=true);
    for(s=[-1,1]){
        color("#F491AA") translate([s*12,6,wall-0.35]) linear_extrude(height=0.1) scale([1.35,0.65]) circle(r=3);
        color("#382B37") translate([s*9,9,wall-0.36]) linear_extrude(height=0.1) hull(){translate([-2,-1]) circle(r=.35); translate([0,1]) circle(r=.35);} 
        color("#382B37") translate([s*9,9,wall-0.36]) linear_extrude(height=0.1) hull(){translate([0,1]) circle(r=.35); translate([2,-1]) circle(r=.35);}
    }
    color("#F491AA") translate([0,0,wall-0.4]) linear_extrude(height=.1) rr(15,9,4);
    color("#382B37") for(s=[-1,1]) translate([s*3.4,0,wall-0.52]) cylinder(h=.1,r=1.1);
    color("#382B37") translate([0,-9,wall-.4]) linear_extrude(height=.1) mirror([1,0,0]) text("Te quiero!",size=3.4,halign="center",valign="center");
}
module assembly(){
    color("lightpink") front_shell();
    color("pink") rear_shell();
    color("gray") esp_cradle();
    color("hotpink") translate([-3,12,body_depth]) tail();
}
if(part=="front_shell") translate([0,0,-0.05]) rotate([-face_tilt,0,0]) front_shell();
else if(part=="rear_shell") translate([0,0,body_depth]) rotate([0,180,0]) rear_shell();
else if(part=="esp_cradle") rotate([90,0,0]) translate([0,-rail_bottom,-board_front]) esp_cradle();
else if(part=="tail") tail();
else if(part=="screen_fit") screen_fit();
else if(part=="magnet_fit") magnet_fit();
else if(part=="usb_fit") usb_fit();
else if(part=="rail_fit") rotate([90,0,0]) translate([0,-rail_bottom,0]) rail_fit();
else if(part=="preview") rotate([90,0,0]) {assembly();face_transform() face_mock();}
else if(part=="exploded") rotate([90,0,0]) {
    color("lightpink") front_shell();face_transform() face_mock();
    color("pink") translate([0,0,30]) rear_shell();
    color("gray") translate([0,22,10]) esp_cradle();
    color("hotpink") translate([-3,12,body_depth+40]) tail();
}
else if(part=="check_seam") intersection(){front_shell();rear_shell();}
else if(part!="check_pcb" && part!="check_cradle") assembly();
// Nominal digital fit checks. A zero-volume intersection is expected.
if(part=="check_pcb") intersection(){front_shell();face_transform() translate([pcb_x-tft_w/2,pcb_y-tft_h/2,boss_top+0.05]) cube([tft_w,tft_h,1.6]);}
if(part=="check_cradle") intersection(){union(){front_shell();rear_shell();}esp_cradle();}
