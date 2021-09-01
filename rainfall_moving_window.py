#! /usr/bin/python3

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
parser.add_argument('-o', '--outfile', type=str, default=None,
                    help='output binned data filename')
parser.add_argument('-b', '--tipfile', type=str, default=None,
                    help='output bucket tip times (unix epoch) filename')
parser.add_argument('-p', '--outplot', type=str, default=None,
                    help='output plot filename, including extension')
parser.add_argument('-w', '--window', type=float, default=60,
                    help='smoothing window duration [minutes]')
parser.add_argument('-n', '--waitplot', type=str, default=None,
                    help='output filename for plot of waiting times between \
                          tips, including extension')
parser.add_argument('-t', '--ts', type=float,
                    default=argparse.SUPPRESS,
                    help='Time step for moving window; (defaults to window \
                          length, but can be shorter to smooth output)')
parser.add_argument('-s', '--starttime', type=int,
                    default=argparse.SUPPRESS,
                    help='Moving window start time for ALog data logger \
                          as a Unix epoch')
parser.add_argument('-e', '--endtime', type=int,
                    default=argparse.SUPPRESS,
                    help='Moving window end time for ALog data logger \
                          as a Unix epoch')
parser.add_argument('-u', '--units', type=str,
                    default=None,
                    help='Rain gauge units for ALog data logger',
                    choices=['inches', 'mm'])
parser.add_argument('-r', '--rain-per-tip', type=float,
                    default=None,
                    help='Amount of rain per bucket tip, for ALog data logger')
parser.add_argument('-d', action='store_true',
                    help='Set flag to display plot')
parser.add_argument('-g', action='store_true',
                    help='Set flag to display waiting times between tips')

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

####################
# ARGUMENT PARSING #
####################

args = vars(args)

################################
# UNASSIGNED VARS TO NONE-TYPE #
################################

"""
for key in args.keys():
  try:
    args[key]
  except:
    args[key] = None
"""
rain_amount_per_tip = None
rain_units = None

###############################
# SEND ARGUMENTS TO VARIABLES #
###############################

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
if type(args['tipfile']) != list:
  tipfile = args['tipfile']
else:
  tipfile = args['tipfile'][0]
if type(args['outplot']) != list:
  outplot = args['outplot']
else:
  outplot = args['outplot'][0]
if type(args['window']) != list:
  window = args['window']
else:
  window = args['window'][0]
if type(args['waitplot']) != list:
  waitplot = args['waitplot']
else:
  waitplot = args['waitplot'][0]
try:
  if type(args['ts']) != list:
    dt = args['ts']
  else:
    dt = args['ts'][0]
except:
  dt = window
displayPlot = args['d']
displayWaitPlot = args['g']

#halfwin=np.timedelta64(datetime.timedelta(minutes=window/2.))
#halfwin*=60
halfwin_seconds = window/2.*60
dt_scalar_minutes = dt
dt=np.timedelta64(datetime.timedelta(minutes=dt)) # minutes
#dt*=60 # convert to seconds

########################################################
# CHECK THAT THE TIME VALUES FOR THE ALOG ARE SELECTED #
########################################################

if logger == 'alog':
  try:
    start_time = args['starttime']
    end_time = args['endtime']
  except:
    sys.exit('Must define "starttime" and "endtime" for the ALog')

if logger == 'alog':
  try:
    rain_units = args['units']
    if rain_units == 'inch':
      conversion_to_mm = 25.4
    elif rain_units == 'mm':
      conversion_to_mm = 1.
  except:
    sys.exit('Must define "units" for the ALog')

if logger == 'alog':
  try:
    rain_amount_per_tip = args['rain_per_tip']
  except:
    sys.exit('Must define "rain-per-tip" for the ALog')
    
###########################################
# CHECK THAT AN OUTPUT OPTION IS SELECTED #
###########################################

if outplot or outfile or tipfile or displayPlot or waitplot or displayWaitPlot:
  pass
else:
  sys.exit("Please choose one or more output option:\n"+
            "--outplot, --waitplot, --outfile, --tipfile, -d, -g")

print( "" )

if logger == 'hobo':
  rainread = csv.reader(open(filename,'r'), delimiter=',')
  print( "Reading Onset Hobo logger file..." )
  firstline = next(rainread)[0]
  secondline = next(rainread)
  Logger_name = firstline.split("Plot Title: ")[-1].split('"')[0]
  # Rain column
  # Option 1: event counter
  rain_header = [s for s in secondline if "Event" in s]
  if len(rain_header) > 0:
    _simple_event_counter = True
    if type(rain_header) == list:
      rain_header = rain_header[0]
    rain_column_number = np.ravel(np.where(
                         np.array(secondline) == rain_header))[0]
    if ' in ' in rain_header:
      rain_units = 'inches'
      rain_amount_per_tip = float(rain_header.split(',')[1].split(' ')[1])
      conversion_to_mm = 25.4
    elif ' units ' in rain_header:
      if (rain_units is None) or (rain_units is 'inches'):
        print( 'Reading units as "inches" based off of header' )
        print( '(Onset typically specifies mm but often leaves blank if inches)' )
        rain_units = 'inches'
      else:
        sys.exit('Units given by user do not match those in header\n'
                 '(Onset typically specifies mm but often leaves blank if inches)')
      if args['rain_per_tip'] is not None:
        print( "User-specified amount of rain [inches] per bucket tip" )
        print( args['rain_per_tip'], rain_units )
        rain_amount_per_tip = args['rain_per_tip']
      else:
        print( "*** WARNING ***" )
        print( "    Units not recorded in HOBO header" )
        print( "    Assuming 0.01 inches per bucket tip" )
        rain_amount_per_tip = 0.01
      conversion_to_mm = 25.4
    elif ' mm ' in rain_header:
      rain_units = 'mm'
      rain_amount_per_tip = float(rain_header.split(',')[1].split(' ')[1])
      conversion_to_mm = 1.
    elif args['units'] is not None:
      print( 'units' )
      rain_units = args['units']
      if rain_units is 'inches':
        conversion_to_mm = 25.4
      else:
        conversion_to_mm = 1.
      if args['rain_per_tip'] is not None:
        rain_amount_per_tip = args['rain_per_tip']
      else:
        sys.exit('Need to specify amount of rainfall per bucket tip')
    else:
      print( args['units'] )
      sys.exit("Unknown units")
  # Option 2: continuous precip counter with certain units
  else:
    _simple_event_counter = False
    rain_header = [s for s in secondline if "Rainfall" in s]
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
  try:
    logger_serial_number = rain_header.split('LGR S/N: ')[1].split(',')[0]
  except:
    logger_serial_number = ''
  #logger_name = secondline[-1].split(')')[0].split('S/N: ')[-1]
  print( "*** WARNING ***" )
  print( "    Hobo declares time based on GMT, but it is assumed" )
  print( "    that they mean UTC (no DST) ***" )
  # Assuming HOBO means UTC instead of GMT, as basing time off of somewhere
  # with DST would be stupid -- should double-check this
  time_offset_from_UTC = secondline[1].split(', ')[-1]
  d_hours = int(time_offset_from_UTC.split('GMT')[1].split(':')[0])
  time_correction_to_UTC = datetime.timedelta(hours=d_hours)
  time_correction_to_UTC = np.timedelta64(time_correction_to_UTC)
else:
  print( "Reading Northern Widget ALog (Arduino logger) file..." )
  tiptimesUnix = np.genfromtxt('WS01_bucket_tips.txt', delimiter=',')[:,0]

#########################################################
# BUCKET TIP TIME STAMPS AND LOGING START AND END TIMES #
#########################################################

tiptimes = []
alltimes = []
i=0
if logger == 'hobo':
  if _simple_event_counter == False:
    _precip_amount = []
  for row in rainread:
    try:
      alltimes.append(datetime.datetime.strptime(row[1],"%m/%d/%y %I:%M:%S %p"))
      if (row[rain_column_number] != '') and \
          (row[rain_column_number][0] != '0'):
        _date_time = datetime.datetime.strptime(row[1],"%m/%d/%y %I:%M:%S %p")
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
      print( "Could not read line "+str(i)+"; header?" )
      pass
    i+=1
elif logger == 'alog':
  for _ts in tiptimesUnix:
    tiptimes.append(np.datetime64(datetime.datetime.utcfromtimestamp(_ts)))
  
# START AND END TIMES -- KEEP ON GOOD HOURS, MINUTES, ETC.
# Be conservative: start on the next even dt unit after the start of the
# record, and end on the dt unit before the end of the record
if logger == 'hobo':
  start_time = alltimes[0]
  end_time = alltimes[-1]
  if dt.astype(datetime.timedelta) < datetime.timedelta(days = 1):
    _nbreaks_in_day = int(np.floor(1440. / dt_scalar_minutes))
    if _nbreaks_in_day <= 24:
      _possible_hours = np.arange(0, 24, 24/_nbreaks_in_day)
      _starting_hour = int( np.max(_possible_hours
                              [_possible_hours <= start_time.hour]) )
      _ending_hour = int (np.min(_possible_hours
                           [_possible_hours >= end_time.hour]) )
      start_time = start_time.replace(hour=_starting_hour, minute=0, second=0, 
                                      microsecond=0)
      end_time = end_time.replace(hour=_ending_hour, minute=0, second=0, 
                                  microsecond=0)
    else:
      _nbreaks_in_hour = int(np.floor(60. / dt_scalar_minutes))
      _possible_minutes = np.arange(0, 60, 60/_nbreaks_in_hour)
      _starting_minute = int( np.max(_possible_minutes
                                [_possible_minutes <= start_time.minute]) )
      _ending_minute = int( np.min(_possible_minutes
                              [_possible_minutes >= end_time.minute]) )
      start_time = start_time.replace(minute=_starting_minute, second=0, 
                                      microsecond=0)
      end_time = end_time.replace(minute=_ending_minute, second=0, 
                                  microsecond=0)
  else:
    start_time = start_time.date()
  start_time = np.datetime64(start_time)
  end_time = np.datetime64(end_time)
elif logger == 'alog':
  start_time = np.datetime64(datetime.datetime.utcfromtimestamp(start_time))
  end_time = np.datetime64(datetime.datetime.utcfromtimestamp(end_time))
else:
  sys.exit("How did you get here??")

################
# RAIN PER TIP #
################

if logger == 'hobo':
  if _simple_event_counter == False:
    if rain_amount_per_tip is None:
      print( "Provided rain per tip will overwrite that given in table, if any" )
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

  
tiptimes_unix = (np.array(tiptimes).astype(int)/1E6).astype(int)


############################################
# STATISTICS OF WAITING TIMES BETWEEN TIPS #
############################################

# Use this to help decide what an appropriate window should be, and also to
# gain some insights into the hydroclimate

if waitplot or displayWaitPlot:
  dt_minutes = np.diff(tiptimes_unix)/60.
  hist = np.histogram(np.log(dt_minutes), 50) # 50 --> some f(n data)?
  # Linear approx... not great.
  _x_approx = (np.exp(hist[1])[1:] + np.exp(hist[1])[:-1])/2.
  _y = hist[0].astype(float)/np.sum(hist[0])
  plt.loglog(_x_approx, _y, 'o')
  plt.xlabel('Waiting time between tips [minutes]', fontsize=18)
  plt.ylabel('Fraction of tips in bin', fontsize=18)
  plt.legend()
  plt.tight_layout()
  if waitplot:
    plt.savefig(waitplot)

"""
# Hourly bins to define "events" -- Poisson or no (doesn't look like it above with just tips,
# but what if there is a mini "non-event" between "events"
t_tot = np.cumsum(dt_minutes)
t_hourly = np.arange(timestamps[0].date(), timestamps[-1].date(), dt.timedelta(hours=1))
t_events = []
timestamps = np.array(timestamps)
for i in range(len(t_hourly - 1)):
    ntips = np.sum( (timestamps < t_hourly[i+1]) * (timestamps > t_hourly[i]) )
    if ntips > 1:
        t_events.append(t_hourly[i]) # time before, but just need dt, really

dt_events = np.abs(np.diff(t_events)).astype(float)
dt_events = dt_events[dt_events > np.min(dt_events)] # remove contiguous events

hist = np.histogram(np.log(dt_events), 20)
_x_approx = (np.exp(hist[1])[1:] + np.exp(hist[1])[:-1])/2.
_y = hist[0].astype(float)/np.sum(hist[0])
plt.loglog(_x_approx, _y, 'o', label=gauge_name)
#plt.xlabel('Waiting time between tips [minutes]', fontsize=18)
#plt.ylabel('Fraction of tips in bin', fontsize=18)
#hist = np.histogram(dt_events, 1000)
#plt.loglog( (hist[1][1:] + hist[1][:-1])/2., hist[0], 'ko' )
plt.legend()
plt.tight_layout()
plt.show()
"""



#############
# WINDOWING #
#############

if outplot or outfile or displayPlot or waitplot or displayWaitPlot:

  # Find how many tips there are in a particular window
  firsttip_unix = tiptimes_unix[0]
  lasttip_unix = tiptimes_unix[-1]
  

  # Moving window times
  mwtimes = np.arange(start_time+dt/2., end_time, dt)
  mwtimes_datetime = mwtimes.astype(datetime.datetime)
  mwtimes_unix = (mwtimes.astype(int)/1E6).astype(int)
  total_time_steps = (start_time - end_time) / dt

  print( "Constructing moving window" )
  next2percent = 0
  tipsInWin = []
  i = 0 # counter
  for t in mwtimes_unix:
    tipsInWin.append( np.sum( (tiptimes_unix < (t+halfwin_seconds)) * (tiptimes_unix > (t-halfwin_seconds)) ) )
    if ((t-firsttip_unix)/(lasttip_unix-firsttip_unix))*100 > next2percent:
      print( int(next2percent), '%' )
      next2percent = np.round((t-firsttip_unix)*100/(lasttip_unix-firsttip_unix)) + 2
    i += 1
  if next2percent <= 100:
    print( 100, '%' )

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
                          
if tipfile:
  np.savetxt(tipfile, tiptimes.astype('datetime64[s]').astype('int'), fmt='%s')

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

##############
# SHOW PLOTS #
##############

# Show (or close) all at once
if displayPlot or displayWaitPlot:
  plt.show()
else:
  plt.close('all')


