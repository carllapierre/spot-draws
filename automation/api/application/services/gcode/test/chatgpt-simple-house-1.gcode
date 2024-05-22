G00 Z5.0

; Build the square building
G1 X0 Y0 Z0
G1 X1 Y0
G1 X1 Y1
G1 X0 Y1
G1 X0 Y0

; Build the rectangular door
G1 X0.4 Y0.1 Z0.5
G1 X0.6 Y0.1 Z0
G1 X0.6 Y0.6
G1 X0.4 Y0.6
G1 X0.4 Y0.1

; Build the triangular roof
G1 X0 Y1 Z0.5
G1 X0.5 Y1.5 Z-0.5
G1 X1 Y1