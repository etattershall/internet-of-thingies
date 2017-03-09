# Initial Example
## Setup
### Arduino:
```C
#include "CmdMessenger.h"
enum {
    who_are_you,
    my_name_is,
    sum_two_ints,
    sum_is,
    error,
};
CmdMessenger c = CmdMessenger(Serial,',',';','/');
```

### Python:
Commands need to have their type specified
```Python
import PyCmdMessenger
arduino = PyCmdMessenger.ArduinoBoard("COM" + input("COM<what?>"),
                                      baud_rate=9600)
commands = [["who_are_you", ""],
            ["my_name_is", "s"],
            ["sum_two_ints", "ii"],
            ["sum_is", "i"],
            ["error", "s"]]
c = PyCmdMessenger.CmdMessenger(arduino, commands)
```



## Sending Commands - PC to Arduino
### Arduino:
#### In setup
Attach callback functions which grab the data from the message
```C
c.attach(who_are_you,on_who_are_you);
c.attach(sum_two_ints,on_sum_two_ints);
c.attach(on_unknown_command);
```
#### In loop
```C
c.feedinSerialData();
```

### Python:
```Python
c.send("sum_two_ints", 4, 1)
```
## Sending Commands - Arduino to PC
### Arduino
```C
// Non strings
c.sendBinCmd(sum_is,value1 + value2);
// Strings
c.sendCmd(my_name_is,"Bob");
// Multiple arguments
c.sendCmdStart(sum_two_ints);
c.sendBinArg();  // non string
c.sendCmdArg();  // string
// ...
c.sendCmdEnd();
```
### Python
```python
c.receive()
# example return ('my_name_is', ['Bob'], 1489068203.9888978)
```
