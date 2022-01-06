# How to use this code
This code is designed to optimise extrusion parameters in piston driven systems with elastic elements (e.g. 3D bioprinting).

## Files and requirements
- calvita.py - Reads data from the weighing scale, compares the results to a theoretical mass progression based on the input g-code from file, generates ramp/retraction value and new g-code file.
- funcalvity.py - Function library file for calvita.py.
- temp.txt - A temporary file containing the calculated value of the ramp/retraction value in mm (initial = "0") and the name of the g-code file (default = "calibrate.gcode")
- calibrate.gcode - Default calibration file used for testing.

To run the algorithm the user requires:
- Piston drive extruder and controller
- Analytical weighing scale with support for data output through RS232 cable
- Data cable with RS232 to USB conversion
- A PC with CNC control software and support for Python 3

## Running the algorithm
1. set temp file to initial ramp/retraction value (default 0) \n gcode-filename
2. load gcode-file to CNC control software (e.g., PlanetCNC)
3. run calvita3.py in cmd, when countdown reaches 0, execute g-code in PlanetCNC
4. after the cycle is completed, the python script generates new gcode file and modifies the temp file
5. Wait for the weighing scale values to settle (approx 5 min). 
6. Tare weighing scale
7. load new_gcode-file to PlanetCNC and repeat the cycle until ramp/retraction value stops changing

## Additional tools
This repository also contains tune-code.py which allows generating modified g-code files with user-defined ramp/retraction values.
