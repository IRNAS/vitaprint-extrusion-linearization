#
#  Developed 2021 by Boštjan Vihar (bostjan AT irnas DOT eu / bostjan DOT vihar AT um DOT si) and Jernej Vajda (jernej DOT vajda1 AT um DOT si)
#  

'''


Creating a new g-code, adjusted for custom ramp/retraction

Usage:
1. RUN "python tune-code.py" (without exclamation marks) in CMD with target g-code file in the same location
2. Type in g-code "file name" (without exclamation marks) or the default "short" file will be used

'''

import re
import numpy as np
# import matplotlib.pyplot as plt
# import time
# import serial
# import pickle
# from funcalvita3 import gread,newgc

name_i = input("Input name of existing g-code file (default calibrate): ") or "calibrate"
ramp_i = float(input("Input ramp/retraction value (default 0.5): ") or "0.5")

# tt,mt,A,F,tpause,f_name = gread(d,rho,tstep,name_i)

# longstring = newgc(A,F,tpause,ramp_i)

#### READ EXISTING G-CODE
file_name = name_i+'.gcode'
file = open(file_name,"r")
file_text = file.read()

a_var = re.findall("(?<=\+)\d+\.*\d*",file_text) # find all values of A (positive lookbehind assertion)
A = list(map(float,a_var)) #convert list of strings to list of floats
A = np.array(A)

f_var = re.findall("(?<=F)\d+\.*\d*",file_text)
F = list(map(float,f_var))
F = np.array(F)
Fs = F/60 # feedrate in mm/s

p_var = re.findall("(?<=P)\d+\.*\d*",file_text)
P = list(map(float,p_var))
P = np.array(P)

tpause = P[0]


### BUILD NEW G-CODE
n_lines = np.size(A)
extrude = "G1 A[#<_a> +{0}] F{1}\n"
pause = "G4 P{0}\n".format(tpause-2*abs(ramp_i)) # POZOR SPREMEMBA: odšteje čas za ramp/ret od pavze! || 1.0 = F60/60
ram = "G1 A[#<_a> +{0}] F60\n".format(ramp_i)
ret = "G1 A[#<_a> -{0}] F60\n".format(ramp_i) # da malenkost več retrahira na koncu, da lahko prej teriraš (+0.014 je bilo super)

startstring = ""#(pythr, C:\\Users\\leni-bosko\\OneDrive - Univerza v Mariboru\\Bostjan-UM\\Vitaprint\\vita-scale-files\\gcode-reader\\calvita.py)"
longstring = startstring + "\n\n\nG92 A0\n\n"
endstring = "G1 A[#<_a> +{0}] F60.0".format(ramp_i/15) #after the cycle is over, extrude minimum material before new iteration

for i in range(0,n_lines):
	# longstring += ram+extrude.format((A[i]/(F[i]/60)-2*(ramp/0.5))*(F[i]/60),F[i])+ret+pause+"\n" #add new calibration extruion values, corrected for time lost due to ramp/retraction
	longstring += ram+extrude.format(A[i],F[i])+ret+pause+"\n" #add new calibration extruion values, corrected for time lost due to ramp/retraction

longstring += endstring
# print(longstring)



################ SAVE NEW G-CODE TO FILE
g = open(name_i+"_r_"+str(ramp_i)+".gcode",'w')
g.write(longstring)
g.close()

h = open('temp.txt','w')
h.write(str(ramp_i)+'\n'+name_i)
h.close()