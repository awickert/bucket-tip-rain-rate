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

filename = sys.argv[1]
window = float(sys.argv[2]) # minutes

halfwin=window/2.
halfwin*=60
dt=5 # minutes
dt*=60 # convert to seconds

rainread = csv.reader(open(filename,'rb'), delimiter=',')

# Create a vector of time stamps
tiptimes=[]
i=0
for row in rainread:
  tiptime_full = time.strptime(row[1],"%m/%d/%y %I:%M:%S %p")
  tiptimes.append(time.mktime(tiptime_full))
  i+=1
  # WORRY ABOUT DST LATER!!!!!!!!!!!!!!!
  
# Tips are in 1/100 inch
  tipsize_mm = .254
  
# Find how many tips there are in a particular window
firsttip = tiptimes[0]
lasttip = tiptimes[-1]

mwtimes = np.arange(firsttip+halfwin,lasttip-halfwin+dt,dt)

realtimes = []
for t in mwtimes:
  realtimes.append(datetime.datetime.fromtimestamp(t))

tipsInWin = []
for t in mwtimes:
  tipswhen=[i for i in tiptimes if i> t-halfwin and i< t+halfwin]
  tipsInWin.append(len(tipswhen))

rainfall_rate_in_window = np.array(tipsInWin) * tipsize_mm

#ax=plt.gca()
#xfmt = md.DateFormatter('%Y-%m-%d %H:%M:%S')
#ax.xaxis.set_major_formatter(xfmt)

plt.figure(figsize=(12,5))
plt.plot(realtimes, rainfall_rate_in_window)
plt.xticks( rotation = 45 )
plt.ylabel('Rainfal rate [mm/hr]')
plt.tight_layout()
plt.show()
