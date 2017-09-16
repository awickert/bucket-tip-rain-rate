# bucket-tip-rain-rate

***Converts time stamps from tipping bucket rain gauge bucket tips into a time series of rainfall intensities based on a moving window***

### Running the code

You can run this code by typing (at the terminal window):
```bash
python rainfall_moving_window.py <arguments>
```

#### Help contents

`-h` i the help flag, and typing `python rainfall_moving_window.py -h` yields the full instructions:
```
usage: rainfall_moving_window.py [-h] -i INFILE -l {alog,hobo} [-o OUTFILE]
                                 [-p OUTPLOT] [-w WINDOW] [-t TS]
                                 [-s STARTTIME] [-e ENDTIME] [-u {inches,mm}]
                                 [-r RAIN_PER_TIP] [-d]

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
  -s STARTTIME, --starttime STARTTIME
                        Moving window start time for ALog data logger as a
                        Unix epoch
  -e ENDTIME, --endtime ENDTIME
                        Moving window end time for ALog data logger as a Unix
                        epoch
  -u {inches,mm}, --units {inches,mm}
                        Rain gauge units for ALog data logger
  -r RAIN_PER_TIP, --rain-per-tip RAIN_PER_TIP
                        Amount of rain per bucket tip, for ALog data logger
  -d                    Set flag to display plot (default: False)

required arguments:
  -i INFILE, --infile INFILE
                        ASCII file containing bucket-tip time stamps
  -l {alog,hobo}, --logger {alog,hobo}
                        Which type of data logger?
```

#### Example 1: Basic

This is a basic example to process 15-minute rainfall intensities from an ALog data logger and create a PDF plot (other file extensions, such as PNG, are also possible). Times of deployment are specified as start and end times; these are required to ensure that the time-series does not show anomylously little rainfall at the start and/or end, and that other bucket tips that may be saved do not affect the final result. The units are specified as hundredths of an inch:
```bash
./rainfall_moving_window.py --infile "INPUT_FILE_PATH" --outfile "OUTPUT_FILE_PATH" --outplot "OUTPUT_PLOT_PATH.pdf" --logger alog --window 15 -s 1484524800 -e 1505575867 -u inches -r 0.01
```

#### Example 2: Batch processing

This is an example code to read a set of Onset Hobo CSV files inside a single directory (```$1```, passed to the program) and send them to a new (existing) directory called "hourly_reprocessed_Andy". The data are binned into 60-minute rainfall rates. It creates a PDF plot.

```bash
find $1 -maxdepth 1 -iname "*.csv" | while read fname
do
        echo $fname
        bname=$(basename "$fname")
        bname_no_ext="${bname%.*}"
        ./rainfall_moving_window.py --infile "$fname" --outfile "hourly_reprocessed_Andy/$bname" --outplot "hourly_reprocessed_Andy/$bname_no_ext.pdf" --logger hobo --window 60
done
```

### Time stamps and file configuration

This program is currently configured to process data from both:
* ONSET Hobo rain gauge data loggers (support for two standard output formats)
* ALog (Arduino-based) data loggers (see https://github.com/NorthernWidget)

The time-stamp format for the Hobo loggers is:
```
21.0,10/12/10 09:44:53 AM
22.0,10/12/10 09:51:25 AM
...
```

The format for the Northern Widget loggers is a series of UNIX time stamps (UNIX epoch), which is the number of seconds since Janurary 1, 1970. The ALog leaves trailing commas behind these at present, but this may be revised in the future. For example:
```
1469626140,
1469626605,
1469627383,
...
```

### Processing and assumptions

For Onset data loggers, this program finds the starting and ending time of your rainfall rate, and then truncates the time-series to the nearest whole-number interval after the start and before the end. This is to avoid artificially-low rain rates where the data does not contain the whole time interval.

For ALog data loggers, you supply the starting and ending time, as well as the amount of water per bucket tip and the units of that amount.

### Code History

This code was originally written on July 30th, 2011, in Boulder, CO, to help process rain gauge data from West Bijou Creek on the Colorado High Plins. As of 14 Feburary 2016, it existed in its near-original form. It was significantly revised to work with multiple raw rain gauge file outputs and with added documentation in July 2017. Some documentation was added in September 2017.
