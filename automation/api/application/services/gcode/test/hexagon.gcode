G00 Z5.0

; Generate circle
G1 X0 Y1 Z-0.1;
G1 X0 Y1 Z-0.1; Move to the top of the circle
G1 X0.707 Y0.707 ; Approximate quarter circle
G1 X1 Y0 ; Approximate quarter circle
G1 X0.707 Y-0.707 ; Approximate quarter circle
G1 X0 Y-1 ; Approximate quarter circle
G1 X-0.707 Y-0.707 ; Approximate quarter circle
G1 X-1 Y0 ; Approximate quarter circle
G1 X-0.707 Y0.707 ; Approximate quarter circle
G1 X0 Y1 ; Return to the top of the circle

M30 ; End of program