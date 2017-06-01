'''
Reads data points separated by '\r\n' from a usb serial connection and plots a
live MPL graph of the data.
'''

import serial
import matplotlib.pyplot as plt
import matplotlib.animation as animation

# Constants

# After this number, they are thrown away
NUM_DATAPOINTS_IN_HISTORY = 100

AVERAGE_SIZE = 2  # Number of data points to average before recording reading


# Ask what port the arduino is on... eg: reply '5' means 'COM5'
port = serial.Serial("COM" + input("COM<what?>"))

# Create a mpl instance
fig = plt.figure()
ax1 = fig.add_subplot(1, 1, 1)

# The 'y' values of data to be plotted (initialised at 0)
# The size of this list is constant (one is removed when one is added)
dataY = list(0 for a in range(NUM_DATAPOINTS_IN_HISTORY))
# A buffer of the latest datapoints before they are averaged and recorded.
# maximum length of this is 'AVERAGE_SIZE'
latestYBuffer = []


def registerDataPoint(newPoint):
    '''Given a float, record the value either to latestYBuffer or take the
    average of latestYBuffer and record a datapoint in dataY'''
    latestYBuffer.append(newPoint)
    if len(latestYBuffer) >= AVERAGE_SIZE:
        # If there are enough readings to record the average, delete the
        # oldest reading to keep the same number
        del dataY[0]
        dataY.append(sum(latestYBuffer) / len(latestYBuffer))
        global latestYBuffer
        latestYBuffer = []


def animate(i):
    'Called at every iteration by mpl, reads the data and replots the graph'
    thisLine = ""  # a string containing the current line
    while port.inWaiting() > 0:
        # While there is Serial data avaliable
        while len(thisLine) < 2 or thisLine[-2:] != "\r\n":
            # While its not the end of a line, read the next character
            thisLine += port.read(1).decode("utf-8")
        thisLine = thisLine[:-2]  # remove the line breaks
        print(thisLine)
        registerDataPoint(float(thisLine))
        thisLine = ""  # reset for the next line
    ax1.clear()
    # Plot the Y values against Xs like [0, 1, 2, 3, 4, ...]
    ax1.plot(list(range(len(dataY))), dataY)
    ax1.set_ylim(bottom=-0.5, top=6)  # keep a constant Y axis scale


if __name__ == "__main__":
    # Set an interval to animate the graph
    ani = animation.FuncAnimation(fig, animate, interval=100)
    plt.show()  # show the graph window
