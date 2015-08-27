# bucket-tip-rain-rate
Converts time stamps from tipping bucket rain gauge bucket tips into a time series of rainfall intensities based on a moving window

Currently configured to use ONSET Hobo rain gauge time stamps like:

21.0,10/12/10 09:44:53 AM,19.0
22.0,10/12/10 09:51:25 AM,20.0
...

[tip count] [date MM/DD/YY] [time HH(12):MM:SS AM/PM] [tip count]
