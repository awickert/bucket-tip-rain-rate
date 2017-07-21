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

parser = argparse.ArgumentParser(description= \
        'Compute rainfall rate with time from tipping-bucket rain gauge data.',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)

window = 60. # default
parser.add_argument('--filename', type=str, nargs=1, default=argparse.SUPPRESS,
                    help='ASCII file containing bucket-tip time stamps')
parser.add_argument('--logger', type=str, nargs=1, default=argparse.SUPPRESS,
                    help='Which type of data logger?',
                    choices=['alog', 'hobo'])
parser.add_argument('--window', type=float, nargs=1, default=60,
                    help='smoothing window duration [minutes]')

args = parser.parse_args()
args = vars(args)
if type(args['window']) != float:
  window = args['window'][0]

parser.add_argument('--ts', type=float, nargs=1,default=window/2,
                    help='Time step for moving window; \
                    defaults to (window/2)')
                    
args = parser.parse_args()
args = vars(args)

filename = args['filename'][0]
logger = args['logger'][0]
if type(args['ts']) != float:
  dt = args['ts'][0]


halfwin=window/2.
halfwin*=60
dt=window/2. # minutes
dt*=60 # convert to seconds

rainread = csv.reader(open(filename,'rb'), delimiter=',')

if logger == 'hobo':
  firstline = rainread.next()[0]
  secondline = rainread.next()
  site_name = firstline.split("Plot Title: ")[-1]
  # Rain column
  rain_header = [s for s in secondline if "Event" in s]
  rain_column_number = np.ravel(np.where(
                       np.array(secondline) == rain_header))[0]
  if ' in ' in rain_header[0]:
    rain_units = 'inches'
    conversion_to_mm = 25.4
  else
    sys.exit()

  logger_serial_number
  

# Create a vector of time stamps
tiptimes=[]
i=0
for row in rainread:
  try:
    tiptime_full = time.strptime(row[1],"%m/%d/%y %I:%M:%S %p")
    if row[3] != '':
      # Check if it isn't a temperature measurement
      # This may have to be changed for purely rain-mesuring Hobo loggers
      # THE REAL WAY is to look for the column with "event"
      tiptimes.append(time.mktime(tiptime_full))
  except:
    # Probably, you're in the header
    print "Could not read line "+str(i)+"; header?"
    pass
  i+=1
  
  # WORRY ABOUT DST LATER!!!!!!!!!!!!!!!
  
# Tips are in 1/100 inch
tipsize_mm = .254
  
# Find how many tips there are in a particular window
firsttip = tiptimes[0]
lasttip = tiptimes[-1]

mwtimes = np.arange(firsttip+halfwin,lasttip-halfwin+dt,dt)

totaltime = lasttip-halfwin+dt - (firsttip+halfwin)
total_time_steps = totaltime / dt

realtimes = []
for t in mwtimes:
  realtimes.append(datetime.datetime.fromtimestamp(t))

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
plt.plot(realtimes, rainfall_rate_in_window)
plt.xticks( rotation = 45 )
plt.ylabel('Rainfal rate [mm/hr]\n'+str(window)+'-minute moving window')
plt.tight_layout()
#plt.savefig(outname+'.png')
plt.show()

