#
#  Developed 2021 by Boštjan Vihar (bostjan AT irnas DOT eu / bostjan DOT vihar AT um DOT si) and Jernej Vajda (jernej DOT vajda1 AT um DOT si)
#  

'''

This is a functions library for the "calvita.py" script.


'''
import re
import numpy as np
import time
import serial

data = serial.Serial('COM8',19200)
data.flushInput()
data.flushOutput()

pattern = re.compile(r'\-*\d+\.\d+') #serch for decimal numbers
# ts = time.time()
t = 0
y = 0

def scale_in(ts):
	
	try:
		line = str(data.readline()) # read line
		match = pattern.findall(line) # find pattern in line
		y = float(match[0])
		t = np.round((time.time() - ts),2) # add timestamp
		# print('t = ',t,' y =',y)
	except:
		print("interrupt")
		# break
	return t,y

def gread(d,rho,tstep,input_name): ##### READING G-CODE -> generating theoretical curves!
	file_name = input_name+'.gcode'
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

	##### SYRINGE PARAMETERS #####
	# d = 12.33 #piston diameter
	# rho = 1e-3 #material density in g/mm^3

	##### CALCULATING CURVES #####
	m = (d/2)**2*np.pi*A*rho #extruded mass in g
	tstart = 0
	# tstep = 0.0983
	tpause = P[0]
	tmax = A/Fs #time of extrusion (theoretical) - pair calculation!
	tp = np.arange(tstart,tpause,tstep)
	mp = np.ones(len(tp))
	mt = np.array([]) # po potrebi daj tu še m0 not!!!
	sumtmax = 0
	
	######### SEM DAJ FOR LOOP ZA število inkrementov! Zdaj imaš samo za 5 narejeno!
	for i in range(0,len(A)):
		sumtmax += tmax[i]
		mi = m[i]/tmax[i]*np.arange(tstart,tmax[i],tstep)
		mt = np.concatenate((mt,mi+np.sum(m[0:i]),mp*np.sum(m[0:i+1])),axis=0)
		# array i, zadnja vrednosti arraya i + array i+1, array za pavzo*vsota mi[0:], ...
	
	tt = np.arange(tstart,sumtmax+len(P)*tpause,tstep) #čas za celotni proces (teoretično)

	return tt,mt,A,F,tpause, file_name
	
def newgc(A,F,tpause,ramp):
	n_lines = np.size(A)
	extrude = "G1 A[#<_a> +{0}] F{1}\n"
	pause = "G4 P{0}\n".format(tpause-2*abs(ramp)) # POZOR SPREMEMBA: odšteje čas za ramp/ret od pavze! || 1.0 = F60/60
	ram = "G1 A[#<_a> +{0}] F60\n".format(ramp)
	ret = "G1 A[#<_a> -{0}] F60\n".format(ramp) # da malenkost več retrahira na koncu, da lahko prej teriraš (+0.014 je bilo super)
	
	startstring = ""#(pythr, C:\\Users\\leni-bosko\\OneDrive - Univerza v Mariboru\\Bostjan-UM\\Vitaprint\\vita-scale-files\\gcode-reader\\calvita.py)"
	longstring = startstring + "\n\n\nG92 A0\n\n"
	endstring = "G1 A[#<_a> +{0}] F60.0".format(ramp/15) #after the cycle is over, extrude minimum material before new iteration

	for i in range(0,n_lines):
		# longstring += ram+extrude.format((A[i]/(F[i]/60)-2*(ramp/0.5))*(F[i]/60),F[i])+ret+pause+"\n" #add new calibration extruion values, corrected for time lost due to ramp/retraction
		longstring += ram+extrude.format(A[i],F[i])+ret+pause+"\n" #add new calibration extruion values, corrected for time lost due to ramp/retraction

	longstring += endstring
	# print(longstring)
	return longstring

def CNConnect(longstring):
	planetcnc_enabled = False
	try:
		import planetcnc
		import gcode
		import gc
		planetcnc_enabled = True
		print("Running under PlanetCNC - OK")

	except:
		print("Not running under Planet CNC")

	if planetcnc_enabled:	
		if gcode.isRunning():
			print('Error - gcode running')
		else:
			pass
			
		gcode.close()

		lines = longstring.splitlines()
		for line in lines:
			gcode.lineAdd(line)