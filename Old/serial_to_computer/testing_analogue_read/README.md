# Testing Analog Read
Looking at the signal recorded when a wire is plugged into an analog pin like an arial.

## Files
* **test_analogue_read.ino** - Arduino sketch to read the pin and send up the time difference over serial
* **test_analogue_read.py** - Python script to read this data to csv
* **fft.py** - Python script to plot this csv data to graph / compute FFT
* **output.csv** - The output from test_analogue_read.py
