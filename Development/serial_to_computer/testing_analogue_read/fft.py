'''Computes the fft from data to give values that are ready to plot
Usage:
    python3.5 fft.py - plot an FFT of the file 'output.csv' (produced by
                         test_analogue_read.py)
OR
    from fft import calculateFFT
    frequencies, amplitudes = calculateFFT(samples,
                                           time between samples (micros))
'''

import numpy as np
import matplotlib.pyplot as plt


def getDataFromCSV():
    '''1) Reads data [0, 1023] from 'output.csv'
    2) converts to volts [0, 5]
    3) parses to remove initial readings that are unusually frequent
    4) returns (volts, average time between readings)'''
    # list of (difference, value) tuples for every line in the file
    with open("output.csv", "r") as fHandle:
        fullData = [tuple(int(val) for val in line.split(","))
                    for line in fHandle]

    # calculate the average time difference between readings
    averageTdifferenceAllData = sum(t for t, v in fullData) / len(fullData)

    # a list to store the data with similar time intervals
    dataToUse = []

    # go through the data and only return the ones with a time difference
    # close to the average (remove anomolies - tend to be large time gaps at
    # the begining
    for index, data in enumerate(fullData):
        if abs(data[0] - averageTdifferenceAllData) > 100:
            print(("Skipping all entries before {}. The time difference {} "
                   "is greater than the average {}."
                   ).format(index, data[0], averageTdifferenceAllData))
            dataToUse = []
        else:
            dataToUse.append(data)

    # convert data [0, 1023] to volts [0, 5]
    valuesWithSameTimeDifference = [v * 5 / 1023 for t, v in dataToUse]
    averageTimeDifference = sum(t for t, v in dataToUse) / len(dataToUse)
    return valuesWithSameTimeDifference, averageTimeDifference


def calculateFFT(vals, deltaT):
    '''Calculates the Xs (Hz) and Ys (input units) for the fft plot of a list
    of samples (vals) at a regular interval (deltaT) (microseconds)'''
    # convert to numpy array
    signal = np.array(vals, dtype=float)
    # Calculate the FFT
    fourier = np.fft.fft(signal)
    # Calculate the corresponding freqencies
    N = signal.size
    freq = np.fft.fftfreq(N, d=deltaT / (10 ** 6))
    # Use fftshift to move
    # from [ 0,  1,  2,  3, 4, -1, -2, -3, -4]
    # to   [-4, -3, -2, -1, 0,  1,  2,  3,  4]
    # which matters for the line graph (order)
    # Use 2 * the absolute because the amplitude is shared between reflected
    # positive and negative freqency components.
    # eg for 50Hz @ 120 amplitude:
    # the fft shares that 120 into 60 for +50Hz and 60 for -50Hz
    # Only return the second half of the data (don't include negative
    # frequencies which are just reflections)
    return (np.fft.fftshift(freq)[int(N / 2):],
            2 * np.fft.fftshift(np.absolute(fourier) / N)[int(N / 2):])


def showFFT(units="V"):
    'Plots the fft data from the csv file onto a graph'
    values, timeBetweenValues = getDataFromCSV()

    plt.figure(1, figsize=(18, 18))

    # time graph
    plt.subplot(211)
    Xs = [i * timeBetweenValues / (10 ** 6) for i in range(len(values))]
    plt.plot(Xs, values)
    plt.ylabel("Amplitude / {}".format(units))
    plt.xlabel("Time / s")
    plt.title("Time Domain")

    # freqency graph
    plt.subplot(212)
    Xs, Ys = calculateFFT(values, timeBetweenValues)
    plt.plot(Xs, Ys)
    plt.ylabel("Amplitude / {}".format(units))
    plt.xlabel("Frequency / Hz")
    plt.title("Frequency Domain")

    plt.show()


if __name__ == "__main__":
    # if not importing, show the graph
    showFFT()
