#
#  Developed 2021 by Boštjan Vihar (bostjan AT irnas DOT eu / bostjan DOT vihar AT um DOT si) and Jernej Vajda (jernej DOT vajda1 AT um DOT si)
#  

'''



This is the master script for calibration of mechanical extrusion using Vitaprint and Planet CNC. It is used for adjusting ramp and retraction movements for nearly linear translation of the main g-code pathway.

Usage:
1. RUN "python calvita.py" (without exclamation marks) in CMD with target g-code file in the same location
2. Type in g-code "file name" (without exclamation marks) or the default "short" file will be used

'''

import re
import numpy as np
import matplotlib.pyplot as plt
import time
import serial
import pickle
from funcalvita import *


f = open('temp.txt','r+')
var = f.read()
f.close()

r_old = float(re.findall('.*\d+\.\d+|\d+',var)[0]) #poišči numerično vrednost v var (float s predznakom ali brez, oziroma int) -> prejšnji ramp
input_name = re.findall('(?<=\n)\w+',var)[0] #poišči vse kar je za '\n' v var

print('5')
time.sleep(1)
print('4')
time.sleep(1)
print('3')
time.sleep(1)
print('2')
time.sleep(1)
print('1')
time.sleep(1)
print('START!')



# r_old = float(input('previous ramp value:') or 0)

################## STATIC SET-UP INFORMATION
d = 12.33 # piston diameter
rho = 1e-3 # material density in g/mm^3
tstep = 0.0983 # scale sampling rate in s ### re-evaluate using tstep = np.mean(tr[1:-1]-tr[0:-2])

################## READING DATA FROM g-code FILE
tt,mt,A,F,tpause,f_name = gread(d,rho,tstep,input_name)


################## READING DATA FROM SCALE
try:
	# data = serial.Serial('COM8',19200)
	# pattern = re.compile(r'\-*\d+\.\d+') #serch for decimal numbers	
	tm = 0
	tr = []
	mr = []
	ts = time.time()
	
	while tm<tt[-1]: # run until Y stopy changing
		tm,mm = scale_in(ts) # save weighing data to time measurement (tm) and mass measurement (mm)
		tr.append(tm)
		mr.append(mm)
		print('t = ',tm,' m = ',mm)

	tr = np.array(tr) # convert to numpy array
	mr = np.array(mr)
except: ################## IF THERE IS NO SCALE!
	file_name = str(input('Scale not connected. Load file name from previous measurements: ') or 'cmc40-2ext_curves_A0.1-0.5_F1.0-20.0_Nit25')+'.pckl'

	# 'cmc10-3ext_curves_A0.1-0.5_F1.0-20.0_Nit25'
	# 'cmc20-3ext_curves_A0.1-0.5_F1.0-20.0_Nit25'
	# 'cmc40-2ext_curves_A0.1-0.5_F1.0-20.0_Nit25'

	f = open(file_name,'rb')
	var = pickle.load(f)

	tr = var[2]
	mr = var[3]



################## ALIGN THEORETICAL AND REAL ARRAYS!
'''
pf = 30 # PEAK FINDING FACTOR! TA DOLOČA OBČUTLJIVOST ISKANJA LOKALNIH MAKSIMUMOV!
df = 0.001
mr_l = len(mr)
dmr = mr[1:-1]-mr[0:-2] #first  derivative of mr
ddmr = dmr[1:-1]-dmr[0:-2] #second derivative of mr
dmr_first_local = int(np.round((tpause+60*A[0]/F[0])/tstep))

dmr_max = np.where(dmr >= np.max(dmr[0:dmr_first_local])) #index array of maxima
dmr_one = dmr_max[0][0] #first maximum, za en/dva indeks/a je zamika, ker pri odvodih skrajšaš array!
t_dmr = 60*A[0]/F[0]/2 # polovični čas prvega pomika v sekundah
t_off = int(np.round(t_dmr/tstep)) # zamik t_dmr glede na frekvenco

tt = tt + tr[dmr_one-t_off] # zamakni tt do prvega peaka
mt = mt + mr[1] # POZOR: KOREKCIJE! mr[0] -> mr[1]

print('dmr_max',dmr_max)
print('A = ',A)
print('F = ',F)
print('t offset', t_off)
'''
tt = tt + 1.7 # zamakni teoretični čas za 2 sekundi (vrednosti, ki so v pufru)
mt = mt + mr[1] # POZOR: KOREKCIJE! mr[0] -> mr[1]

trn = tr[tr>=tt[0]] # the new tr begins at tt0
mrn = mr[len(tr)-len(trn)::] # the new mr starts at the same point

if len(mt)<len(mrn):
	tt = tt[0:len(mt)]
	trn = trn[0:len(mt)]
	mrn = mrn[0:len(mt)]
else:
	tt = tt[0:len(mrn)]
	trn = trn[0:len(mrn)]
	mt = mt[0:len(mrn)]


################# CALCULATE DIFFERENCE BETWEEN REAL AND THEORETICAL
####	align grahps at first pause
print("A =",A[0],"F =",F[0],"tpause =",tpause)
tp_one = A[0]/(F[0]/60) + tpause# time when reaching the end of first pause
print("tp_one =",tp_one)
tp_one_i = int(tp_one/tstep) #index of mt at tp_one 
print("tp_one_i =",tp_one_i)
mrn = mrn+(mt[tp_one_i]-mrn[tp_one_i]) #shift mrn at tp_one to mt

dm = mt-mrn # TRENUTNO ODŠTEJE realno od teoretične mase
# dm[dm<0]=0 # poišče vrednosti, ki so manjše od 0 in jih postavi na 0 POZOR: KOREKCIJE -> IZKOMENTIRANO

t_arr = np.int_(np.round(np.cumsum((A/F/60 + tpause)/tstep))) #make array with time measurements at the end of each sequence
t_arr = np.append(0,t_arr)
dm_a = np.split(np.arange(0,len(A),1),len(A)) #make place holder array with len(A) sub-arrays
a_i = np.array([])

osf_arr = np.array([])

for i in range(0,len(A)):
	dm_i = dm[t_arr[i]:t_arr[i+1]]
	a_i = np.append(a_i,np.max(np.absolute(dm_i))-dm_i[0]) # calculate individual differences of theoretical to real curves
	osf = 0
	print(osf)
	for j in range(0,len(dm_i)):
		osf += dm_i[j]
	osf_arr = np.append(osf_arr,osf)
	# vse teoretične - vse realne, če je vsota negativna -> je overshootal? //rešeno spodaj
	# če je overshootal naj bo ramp negativen // rešeno spodaj
	# npr. razmerje vsota/absolutnih?
	dm_a[i]=dm_i #save individual dm arrays into subarrays - ONLY NEEDED FOR PLOTTING

os = 1 #če je overshootal, je -1
osf_sum = 0
for k in range(0,len(osf_arr)):
	osf_sum += osf_arr[k]
print(osf_sum)
if osf_sum >= 0:
	os = 1
else:
	os = -0.8 # da ne gre spet prenizko
print(os)

################ DETERMINE RAMP/RETRACTION VALUE
print(a_i)
cf = 3 # correction factor
mai = np.mean(a_i)
ramp = mai/((d/2)**2*np.pi*rho)*cf*os # RAMP/RETRACTION IN MM!
ramp = abs(ramp + r_old) # NEW CALCULATED RAMP + OLD -> absolute, cannot be negative


################ BUILD NEW G-CODE AND RUN IN Planet CNC
longstring = newgc(A,F,tpause,ramp)

CNConnect(longstring)

################ SAVE NEW G-CODE TO FILE
g = open('new'+f_name,'w')
g.write(longstring)
g.close()

print('old ramp equals '+str(r_old))
print('new ramp equals '+str(ramp))

h = open('temp.txt','w')
h.write(str(ramp)+'\n'+input_name)
h.close()

################ PLOT theoretical and real curves

#uniform length)
mt = mt[0:len(tt)]
trn = trn[0:len(tt)]
mrn = mrn[0:len(tt)]

# first derivative
dmt = mt[1:-1]-mt[0:-2]
dmrn = mrn[1:-1]-mrn[0:-2]



# plt.plot(tt,mt[0:len(tt)],trn[0:len(tt)],mrn[0:len(tt)])
plt.plot(tt,mt,trn,mrn)#,tt[1:-1],dmt,trn[1:-1],dmrn)
plt.legend(["ramp value = {0}".format(r_old)])
plt.savefig("sample_F{0}_R{1}.png".format(F[1],np.round(r_old,2)))
plt.show()