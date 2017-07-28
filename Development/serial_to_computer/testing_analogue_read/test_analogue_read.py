'''Reads data from serial to csv'''

import serial
import serial.tools.list_ports


def getFirstArduinoPort():
    "Returns the port (eg COM5) of the first arduino"
    ports = serial.tools.list_ports.comports()
    for p in ports:
        # Check to see if the serial port is connected to an Arduino
        if 'Arduino' in p.description:
            # Return this port
            return p.device
    raise IOError("No Arduino found!")


def writeLines(numberToRead, filename="output.csv", baudRate=115200):
    "writes a number of lines from the serial port to the file"
    linesToReturn = []
    with serial.Serial(getFirstArduinoPort(), baudRate) as ser:
        with open(filename, "wb") as fHandle:
            started = False  # dont record until after "Starting up!"
            while len(linesToReturn) < numberToRead:
                line = ser.readline()
                if not started:
                    print("Skipping line:", line)
                else:
                    fHandle.write(line)
                    linesToReturn.append(line)
                if b"Starting up!" in line:
                    started = True
    return linesToReturn


if __name__ == "__main__":
    data = [tuple(int(el) for el in line.decode().strip().split(","))
            for line in writeLines(3000)]

    def average(start, end):
        return(sum(el[1] for el in data[start:end]) / (end - start))

    print("average first 1000", average(0, 1000))
    print("average middle 1000", average(4500, 5500))
    print("average end 1000", average(9000, 10000))
