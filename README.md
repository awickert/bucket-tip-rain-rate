# bucket-tip-rain-rate

***Converts time stamps from tipping bucket rain gauge bucket tips into a time series of rainfall intensities based on a moving window***

### Running the code

You can run this code by typing (at the terminal window):
```
python rainfall_moving_window.py $FILENAME $WINDOW_LENGTH_MINUTES
```
Where, as one might expect, $FILENAME is the name of the file with the time-stamps of the rain gauge bucket tips, and WINDOW_LENGTH_MINUTES is the length of the moving window over which the bucket tips are smoothed into a rain rate.

### Time-stamp file configuration

*Temporarily, the code reads only files that include many other columns and also read temperature. This should be generalized/fixed -- 2016.07.05*

This program is currently configured to process ONSET Hobo rain gauge time stamps, like:
```
21.0,10/12/10 09:44:53 AM,19.0
22.0,10/12/10 09:51:25 AM,20.0
...
```

Where each row here is:<br>
```
[tip count],[date MM/DD/YY] [time HH(12):MM:SS AM/PM],[previous tip count]
````

Additional time-stamp formats can be used by changing (at the time of writing) line 31 of the code.

### Code History

This code was originally written on July 30th, 2011, in Boulder, CO, to help process rain gauge data from West Bijou Creek on the Colorado High Plins. As of 14 Feburary 2016, it still exists in its original or near-original form.
