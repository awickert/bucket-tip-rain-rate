# bucket-tip-rain-rate

***Converts time stamps from tipping bucket rain gauge bucket tips into a time series of rainfall intensities based on a moving window***

### Running the code

You can run this code by typing (at the terminal window):
```bash
python rainfall_moving_window.py <arguments>
```

`-h` i the help flag, and typing `python rainfall_moving_window.py -h` yields the full instructions:
```
usage: rainfall_moving_window.py [-h] -i INFILE -l {alog,hobo} [-o OUTFILE]
                                 [-p OUTPLOT] [-w WINDOW] [-t TS] [-d]

Compute rainfall rate with time from tipping-bucket rain gauge data.

optional arguments:
  -h, --help            show this help message and exit
  -o OUTFILE, --outfile OUTFILE
                        output filename (default: None)
  -p OUTPLOT, --outplot OUTPLOT
                        output plot filename, including extension (default:
                        None)
  -w WINDOW, --window WINDOW
                        smoothing window duration [minutes] (default: 60)
  -t TS, --ts TS        Time step for moving window; (defaults to window
                        length, but can be shorter to smooth output)
  -d                    Set flag to display plot (default: False)

required arguments:
  -i INFILE, --infile INFILE
                        ASCII file containing bucket-tip time stamps
  -l {alog,hobo}, --logger {alog,hobo}
                        Which type of data logger?
```

### Time-stamp file configuration

This program is currently configured to process ONSET Hobo rain gauge time stamps, like:
```
21.0,10/12/10 09:44:53 AM
22.0,10/12/10 09:51:25 AM
...
```

### Processing and assumptions

This program finds the starting and ending time of your rainfall rate, and then truncates the time-series to the nearest whole-number interval after the start and before the end. This is to avoid artificially-low rain rates where the data does not contain the whole time interval.

### Code History

This code was originally written on July 30th, 2011, in Boulder, CO, to help process rain gauge data from West Bijou Creek on the Colorado High Plins. As of 14 Feburary 2016, it still exists in its original or near-original form.
