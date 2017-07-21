#! /usr/bin/python

"""
Started by Andrew Wickert 30 JUL 11, working with Francis Rengers
For finding rain intensities over a given window
"""

from __future__ import division

import time
import csv
import datetime
import numpy as np
import sys
from matplotlib import pyplot as plt
import os
import argparse

##########
# PARSER #
##########

parser = argparse.ArgumentParser(description= \
        'Compute rainfall rate with time from tipping-bucket rain gauge data.',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)

requiredArgs = parser.add_argument_group('required arguments')

window = 60. # default

# REQUIRED
requiredArgs.add_argument('-i', '--infile', type=str, default=argparse.SUPPRESS,
                    help='ASCII file containing bucket-tip time stamps',
                    required = True)
requiredArgs.add_argument('-l', '--logger', type=str, nargs=1, default=argparse.SUPPRESS,
                    help='Which type of data logger?',
                    choices=['alog', 'hobo'],
                    required = True)

# OPTIONAL
parser.add_argument('-o', '--outfile', type=str, nargs=1, default=None,
                    help='output filename')
parser.add_argument('-p', '--outplot', type=str, nargs=1, default=None,
                    help='output plot filename, including extension')
parser.add_argument('-w', '--window', type=float, nargs=1, default=60,
                    help='smoothing window duration [minutes]')
parser.add_argument('-t', '--ts', type=float, nargs=1,default=window/2,
                    help='Time step for moving window; \
                    defaults to (window/2)')
parser.add_argument('-d', action='store_true',
                    help='Set flag to display plot')


###############################
# SEND ARGUMENTS TO VARIABLES #
###############################

args = parser.parse_args()
args = vars(args)

# REQUIRED
if type(args['infile']) != list:
  filename = args['infile']
else:
  filename = args['infile'][0]

if type(args['logger']) != list:
  logger = args['logger']
else:
  logger = args['logger'][0]

# OPTIONAL
if type(args['outfile']) != list:
  outfile = args['outfile']
else:
  outfile = args['outfile'][0]
if type(args['outplot']) != list:
  outplot = args['outplot']
else:
  outplot = args['outplot'][0]
if type(args['window']) != list:
  window = args['window']
else:
  window = args['window'][0]
if type(args['ts']) != list:
  dt = args['ts']
else:
  dt = args['ts'][0]
displayPlot = args['d']

halfwin=np.timedelta64(datetime.timedelta(minutes=window/2.))
#halfwin*=60
dt=np.timedelta64(datetime.timedelta(minutes=dt)) # minutes
#dt*=60 # convert to seconds

rainread = csv.reader(open(filename,'rb'), delimiter=',')

if logger == 'hobo':
  print "Reading Onset Hobo logger file..."
  firstline = rainread.next()[0]
  secondline = rainread.next()
  #site_name = firstline.split("Plot Title: ")[-1]
  # Rain column
  rain_header = [s for s in secondline if "Event" in s]
  rain_header = rain_header[0]
  rain_column_number = np.ravel(np.where(
                       np.array(secondline) == rain_header))[0]
  if ' in ' in rain_header:
    rain_units = 'inches'
    rain_amount_per_tip = float(rain_header.split(',')[1].split(' ')[1])
    conversion_to_mm = 25.4
    mm_per_tip = rain_amount_per_tip * conversion_to_mm
  elif ' units ' in rain_header:
    rain_units = 'inches'
    print "*** WARNING ***"
    print "Units not recorded in HOBO header"
    print "Assuming 0.01 inches per bucket tip"
    rain_amount_per_tip = 0.01
    conversion_to_mm = 25.4
    mm_per_tip = rain_amount_per_tip * conversion_to_mm
  else:
    sys.exit("Unknown units")
  logger_serial_number = rain_header.split(',')[2].split(' ')[-1]
  logger_name = secondline[-1].split(')')[0].split('S/N: ')[-1]
  # Assuming HOBO means UTC instead of GMT, as basing time off of somewhere
  # with DST would be stupid -- should double-check this
  time_offset_from_UTC = secondline[1].split(', ')[-1]
  d_hours = int(time_offset_from_UTC.split('GMT')[1].split(':')[0])
  time_correction_to_UTC = datetime.timedelta(hours=d_hours)
  time_correction_to_UTC = np.timedelta64(time_correction_to_UTC)
else:
  print "Reading Northern Widget ALog (Arduino logger) file..."
  sys.exit("ALog not written yet")
tipsize_mm = rain_amount_per_tip * conversion_to_mm

# Create a vector of time stamps
tiptimes=[]
i=0
if logger == 'hobo':
  for row in rainread:
    try:
      if row[rain_column_number] != '':
        tiptime_full = time.strptime(row[1],"%m/%d/%y %I:%M:%S %p")
        _date_time = datetime.datetime.fromtimestamp(time.mktime(tiptime_full))
        _date_time = np.datetime64(_date_time)
        tiptimes.append(_date_time - time_correction_to_UTC)
    except:
      # Probably, you're in the header
      print "Could not read line "+str(i)+"; header?"
      pass
    i+=1
else:
  sys.exit()
  
tiptimes = np.array(tiptimes).astype(np.datetime64)
  
  
# Find how many tips there are in a particular window
firsttip = tiptimes[0]
lasttip = tiptimes[-1]

# Moving window times
mwtimes = np.arange(firsttip + halfwin, \
                    lasttip - (halfwin + dt), \
                    dt)
totaltime = lasttip - \
            halfwin + dt - \
            ( firsttip + halfwin )
total_time_steps = totaltime / dt

print "Constructing moving window"
next2percent = 0
tipsInWin = []
i = 0 # counter
for t in mwtimes:
  tipswhen=[i for i in tiptimes if i> t-halfwin and i< t+halfwin]
  tipsInWin.append(len(tipswhen))
  if ((t-firsttip)/(lasttip-firsttip))*100 > next2percent:
    print next2percent, '%'
    next2percent = np.round((t-firsttip)*100/(lasttip-firsttip)) + 2
  i += 1
if next2percent <= 100:
  print 100, '%'

rainfall_rate_in_window = np.array(tipsInWin) * tipsize_mm

##########
# OUTPUT #
##########

localname = os.path.split(filename)[-1]
basename = os.path.splitext(localname)[0]
outname = basename + '__'+str(window)+'_minute_moving_window'
outdata = np.vstack(rainfall_rate_in_window).transpose()
#np.savetxt(outname+'.txt', outdata)

########
# PLOT #
########

plt.figure(figsize=(12,5))
plt.plot(mwtimes, rainfall_rate_in_window)
plt.xticks( rotation = 45 )
plt.ylabel('Rainfal rate [mm/hr]\n'+str(window)+'-minute moving window')
plt.tight_layout()
#plt.savefig(outname+'.png')
plt.show()

