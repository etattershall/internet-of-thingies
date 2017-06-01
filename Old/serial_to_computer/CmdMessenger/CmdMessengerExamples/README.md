# Examples from the CmdMessenger library

I attempted to get these to work with PyCmdMessenger.

Receive worked fine.

## Receive
  The 1st example will make the PC toggle the integrated led on the Arduino board.

  * On the Arduino side, it demonstrates how to:
	  - Define commands
	  - Set up a serial connection
	  - Receive a command with a parameter from the PC
  * On the PC side, it demonstrates how to:
	  - Define commands
	  - Set up a serial connection
	  - Send a command with a parameter to the Arduino

### Result

Managed to successfully convert the example. Had to change a line of the Arduino code to make it work. Either I didn't understand something or the the example is outdated.

#### Changed
```C
ledState = cmdMessenger.readBoolArg();
```
#### To
```C
ledState = cmdMessenger.readBinArg<bool>();
```
