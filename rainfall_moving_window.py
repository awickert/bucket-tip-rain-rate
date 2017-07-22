#! /usr/bin/python

"""
Started by Andrew Wickert 30 JUL 11, working with Francis Rengers
For finding rain intensities over a given window
"""

##########
# PARSER #
##########

import argparse

parser = argparse.ArgumentParser(description= \
        'Compute rainfall rate with time from tipping-bucket rain gauge data.',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)

requiredArgs = parser.add_argument_group('required arguments')

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
parser.add_argument('-t', '--ts', type=float, nargs=1,default=argparse.SUPPRESS,
                    help='Time step for moving window; (defaults to window \
                          length, but can be shorter to smooth output)')
parser.add_argument('-d', action='store_true',
                    help='Set flag to display plot')

args = parser.parse_args()

##################
# IMPORT MODULES #
##################

import time
import csv
import datetime
import numpy as np
import sys
from matplotlib import pyplot as plt
import os
import pandas as pd

###############################
# SEND ARGUMENTS TO VARIABLES #
###############################

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
try:
  if type(args['ts']) != list:
    dt = args['ts']
  else:
    dt = args['ts'][0]
except:
  dt = window
displayPlot = args['d']

halfwin=np.timedelta64(datetime.timedelta(minutes=window/2.))
#halfwin*=60
dt_scalar_minutes = dt
dt=np.timedelta64(datetime.timedelta(minutes=dt)) # minutes
#dt*=60 # convert to seconds

###########################################
# CHECK THAT AN OUTPUT OPTION IS SELECTED #
###########################################

if outplot or outfile or displayPlot:
  pass
else:
  sys.exit("Please choose one or more output option: --outplot, --outfile, -d")

rainread = csv.reader(open(filename,'rb'), delimiter=',')

print ""

if logger == 'hobo':
  print "Reading Onset Hobo logger file..."
  firstline = rainread.next()[0]
  secondline = rainread.next()
  Logger_name = firstline.split("Plot Title: ")[-1].split('"')[0]
  # Rain column
  # Option 1: event counter
  rain_header = [s for s in secondline if "Event" in s]
  if len(rain_header) > 0:
    _simple_event_counter = True
    print rain_header
    if type(rain_header) == list:
      rain_header = rain_header[0]
    rain_column_number = np.ravel(np.where(
                         np.array(secondline) == rain_header))[0]
    if ' in ' in rain_header:
      rain_units = 'inches'
      rain_amount_per_tip = float(rain_header.split(',')[1].split(' ')[1])
      conversion_to_mm = 25.4
    elif ' units ' in rain_header:
      rain_units = 'inches'
      print "*** WARNING ***"
      print "    Units not recorded in HOBO header"
      print "    Assuming 0.01 inches per bucket tip"
      rain_amount_per_tip = 0.01
      conversion_to_mm = 25.4
    elif ' mm ' in rain_header:
      rain_units = 'mm'
      rain_amount_per_tip = float(rain_header.split(',')[1].split(' ')[1])
      conversion_to_mm = 1.
    else:
      sys.exit("Unknown units")
  # Option 2: continuous precip counter with certain units
  else:
    _simple_event_counter = False
    rain_header = [s for s in secondline if "Rainfall" in s]
    print rain_header
    if type(rain_header) == list:
      rain_header = rain_header[0]
    rain_column_number = np.ravel(np.where(
                         np.array(secondline) == rain_header))[0]
    if ' in ' in rain_header:
      rain_units = 'inches'
      conversion_to_mm = 25.4
    elif ' mm ' in rain_header:
      rain_units = 'mm'
      conversion_to_mm = 1.
  # Add code sections in the future to use these for concatenation of
  # files and/or file naming?
  logger_serial_number = rain_header.split('LGR S/N: ')[1].split(',')[0]
  #logger_name = secondline[-1].split(')')[0].split('S/N: ')[-1]
  print "*** WARNING ***"
  print "    Hobo declares time based on GMT, but it is assumed"
  print "    that they mean UTC (no DST) ***"
  # Assuming HOBO means UTC instead of GMT, as basing time off of somewhere
  # with DST would be stupid -- should double-check this
  time_offset_from_UTC = secondline[1].split(', ')[-1]
  d_hours = int(time_offset_from_UTC.split('GMT')[1].split(':')[0])
  time_correction_to_UTC = datetime.timedelta(hours=d_hours)
  time_correction_to_UTC = np.timedelta64(time_correction_to_UTC)
else:
  print "Reading Northern Widget ALog (Arduino logger) file..."
  sys.exit("ALog not written yet")

#########################################################
# BUCKET TIP TIME STAMPS AND LOGING START AND END TIMES #
#########################################################

tiptimes = []
alltimes = []
if logger == 'hobo':
  if _simple_event_counter == False:
    _precip_amount = []
  i=0
  for row in rainread:
    try:
      alltimes.append(time.strptime(row[1],"%m/%d/%y %I:%M:%S %p"))
      if (row[rain_column_number] != '') and \
          (row[rain_column_number][0] != '0'):
        tiptime_full = time.strptime(row[1],"%m/%d/%y %I:%M:%S %p")
        _date_time = datetime.datetime.fromtimestamp(time.mktime(tiptime_full))
        _date_time = np.datetime64(_date_time)
        if _simple_event_counter == True:
          tiptimes.append(_date_time - time_correction_to_UTC)
        else:
          # Only append data if it is recording a new value,
          # not if it is recording a total value while being read
          # they make it so complicated!
          if row[rain_column_number + 1] == '':
            tiptimes.append(_date_time - time_correction_to_UTC)
            _precip_amount.append(row[rain_column_number])
    except:
      # Probably, you're in the header
      print "Could not read line "+str(i)+"; header?"
      pass
    i+=1
  
  # START AND END TIMES -- KEEP ON GOOD HOURS, MINUTES, ETC.
  # Be conservative: start on the next even dt unit after the start of the
  # record, and end on the dt unit before the end of the record
  start_time = datetime.datetime.fromtimestamp(time.mktime(alltimes[0]))
  end_time = datetime.datetime.fromtimestamp(time.mktime(alltimes[-1]))
  if dt.astype(datetime.timedelta) < datetime.timedelta(days = 1):
    _nbreaks_in_day = int(np.floor(1440. / dt_scalar_minutes))
    if _nbreaks_in_day <= 24:
      _possible_hours = np.arange(0, 24, 24/_nbreaks_in_day)
      _starting_hour = np.max(_possible_hours
                              [_possible_hours <= start_time.hour])
      _ending_hour = np.min(_possible_hours
                           [_possible_hours >= end_time.hour])
      start_time = start_time.replace(hour=_starting_hour, minute=0, second=0, 
                                      microsecond=0)
      end_time = end_time.replace(hour=_ending_hour, minute=0, second=0, 
                                  microsecond=0)
    else:
      _nbreaks_in_hour = int(np.floor(60. / dt_scalar_minutes))
      _possible_minutes = np.arange(0, 60, 60/_nbreaks_in_hour)
      _starting_minute = np.max(_possible_minutes
                                [_possible_minutes <= start_time.minute])
      _ending_minute = np.min(_possible_minutes
                              [_possible_minutes >= end_time.minute])
      start_time = start_time.replace(minute=_starting_minute, second=0, 
                                      microsecond=0)
      end_time = end_time.replace(minute=_ending_minute, second=0, 
                                  microsecond=0)
  else:
    start_time = start_time.date()
  start_time = np.datetime64(start_time)
  end_time = np.datetime64(end_time)
  
else:
  sys.exit()

if _simple_event_counter == False:
  rain_amount_per_tip = np.diff(np.array(_precip_amount).astype(float))
  # crudely deal with floating point issues
  rain_amount_per_tip = np.round(rain_amount_per_tip, 9)
  # Check that they are all equal, and if so, convert to a scalar
  if len(set(rain_amount_per_tip)) == 1:
    rain_amount_per_tip = rain_amount_per_tip[0]
  else:
    sys.exit("Unequal rainfall amounts in tips: check header / contact developer")

mm_per_tip = rain_amount_per_tip * conversion_to_mm

##############
############## PLACEHOLDER HERE FOR PROBABILITY / STATS ON RAINFALL
############## DISTRIBUTION AND EVALUATION OF MINIMUM AVERAGING WINDOW LENGTH
##############
  
tiptimes = np.array(tiptimes).astype(np.datetime64)
  
# Find how many tips there are in a particular window
firsttip = tiptimes[0]
lasttip = tiptimes[-1]

# Moving window times
mwtimes = np.arange(firsttip + halfwin, \
                    lasttip - (halfwin + dt), \
                    dt)
mwtimes_datetime = mwtimes.astype(datetime.datetime)
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

# Rain rate in mm/hr
dt_hours = dt_scalar_minutes/60.
rainfall_rate_in_window = np.array(tipsInWin) * mm_per_tip / dt_hours

##########
# OUTPUT #
##########

#localname = os.path.split(filename)[-1]
#basename = os.path.splitext(localname)[0]
#outname = basename + '__'+str(window)+'_minute_moving_window'
#outdata = np.vstack(rainfall_rate_in_window).transpose()
#np.savetxt(outname+'.txt', outdata)
if outfile:
  outUnixtime = []
  for _t in mwtimes_datetime:
    outUnixtime.append(int(time.mktime(datetime.datetime.timetuple(_t))))
  outUnixtime = np.array(outUnixtime)
  outdict = {'Time [UTC]' : mwtimes_datetime,
             'Time [Unix timestamp]' : outUnixtime,
             'Rainfall rate [mm/hr]' : rainfall_rate_in_window}
  outdata = pd.DataFrame(outdict)
  outdata.to_csv(outfile, header=True, index=False, encoding='ascii',
                 columns=['Time [Unix timestamp]', 'Time [UTC]', 
                          'Rainfall rate [mm/hr]'])

########
# PLOT #
########

if outplot or displayPlot:
  plt.figure(figsize=(12,5))
  plt.plot(mwtimes_datetime, rainfall_rate_in_window)
  plt.xticks( rotation = 45 )
  if window < 60:
    ylabel_str = 'Rainfal rate [mm/hr]\n'+str(window)+'-minute window'
  elif window < 1440:
    ylabel_str = 'Rainfal rate [mm/hr]\n'+str(window/60)+'-hour '
    if window % 60 == 0:
      ylabel_str += 'window'
    else:
      ylabel_str += str(window%60)+'-minute window'
  else:
    ylabel_str = 'Rainfal rate [mm/hr]\n'+str(window/1440)+'-day '
    if window % 1440 == 0:
      ylabel_str += 'window'
    else:
      ylabel_str += str((window%1440)/60)+'-hour '
      if window % 60 == 0:
        ylabel_str += 'window'
      else:
        ylabel_str += str(window%60)+'-minute window'
  if dt_scalar_minutes != window:
    ylabel_str += '\n'+str(int(dt_scalar_minutes))+'-minute moving window steps'
  plt.ylabel(ylabel_str, fontsize=16)
  plt.tight_layout()
  if outplot:
    plt.savefig(outplot)
  if displayPlot:
    plt.show()

