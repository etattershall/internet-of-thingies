#!/usr/bin/python

'''
Adapted from:
https://github.com/r10r/bluez/blob/master/test/simple-agent
'''
from __future__ import absolute_import, print_function, unicode_literals


# Import different dbus libraries necessary to setup and register the agent
import dbus
import dbus.service
import dbus.mainloop.glib
# Use GObject for a 'mainloop' to run in background
from gi.repository import GObject

# Set this to your HC_05_PIN, to avoid uploading to github
from secret import HC_05_PIN

# Define some globals used by bluez dbus. These haven't been changed from the
# original code (see 'Adapted from:')
BUS_NAME = 'org.bluez'
AGENT_INTERFACE = 'org.bluez.Agent1'
AGENT_PATH = "/test/agent"


class NotImplementedMethodCall(NotImplementedError):
    '''Raised when calling an Agent method which hasn't been implemented.

    From testing and the documentation, for a simple automatic pairing with
    a HC-05, Agent.RequestPinCode() is the only method that is used. The other
    methods raise this error to point out that they probably should be
    implemented.'''
    pass


class Agent(dbus.service.Object):
    '''
    A bluetooth agent object that is made avaliable to other applications over
    dbus.

    Usage:
        agent = Agent(bus, path)

    Normal Methods:
        - __init__(self, bus, object_path)
        - set_trusted(self, path)

    The following methods work with dbus.service.Object
        Implemented methods:
            - DisplayPinCode(self, device, pincode)

        Methods that raise 'NotImplementedMethodCall' in case they are used:
            - Release(self)
            - RequestPinCode(self, device)
            - DisplayPasskey(self, device, passkey, entered)
            - RequestConfirmation(self, device, passkey)
            - RequestAuthorization(self, device)
            - Cancel(self)

    see https://dbus.freedesktop.org/doc/dbus-python/doc/tutorial.html#id31
    '''
    def __init__(self, bus, object_path):
        '''
        The class setup function. This is only implemented to store the bus
        object within the class rather than a global variable

        This function takes the same arguments as the parent class
        (dbus.service.Object).

        bus:
        dbus.SystemBus() or dbus.SessionBus()

        object_path:
        An object path to export under eg "/test/Agent"
        '''
        # Defining this __init__ method overrides the parent __init__
        # method. Call the parent __init__ method here to make up for this.
        dbus.service.Object.__init__(self, bus, object_path)
        # Store the bus for use with set_trusted.
        self.stored_bus = bus

    def set_trusted(self, path):
        '''
        A function to set the device as trusted. It uses self.stored_bus which
        is set in the __init__ method.

        path:
        The 'device' parameter as passed to self.RequestPinCode
        '''
        props = dbus.Interface(self.stored_bus.get_object("org.bluez", path),
                               "org.freedesktop.DBus.Properties")
        props.Set("org.bluez.Device1", "Trusted", True)

    # In object, out string
    @dbus.service.method(AGENT_INTERFACE, in_signature="o", out_signature="s")
    def RequestPinCode(self, device):
        '''
        This method gets called when the service daemon needs to get the
        passkey for an authentication. The return value should be a string of
        1-16 characters length. The string can be alphanumeric.
        Possible errors: org.bluez.Error.Rejected
                         org.bluez.Error.Canceled
        '''
        print("RequestPinCode (%s)" % (device))
        self.set_trusted(device)
        return str(HC_05_PIN)

    # --------------- The following methods aren't implemented ----------------

    @dbus.service.method(AGENT_INTERFACE, in_signature="", out_signature="")
    def Release(self):
        '''
        This method gets called when the service daemon unregisters the agent.
        An agent can use it to do cleanup tasks. There is no need to unregister
        the agent, because when this method gets called it has already been
        unregistered.
        '''
        raise NotImplementedMethodCall("Release")

    # In object 32bituint 16bituint
    @dbus.service.method(AGENT_INTERFACE, in_signature="ouq", out_signature="")
    def DisplayPasskey(self, device, passkey, entered):
        '''
        This method gets called when the service daemon needs to display a
        passkey for an authentication. The entered parameter indicates the
        number of already typed keys on the remote side. An empty reply should
        be returned. When the passkey needs no longer to be displayed, the
        Cancel method of the agent will be called. During the pairing process
        this method might be called multiple times to update the entered value.

        Note that the passkey will always be a 6-digit number, so the display
        should be zero-padded at the start if the value contains less than 6
        digits.
        '''
        content = "DisplayPasskey(%s, %06u entered %u)" % (device, passkey,
                                                           entered)
        raise NotImplementedMethodCall(content)

    # In object string
    @dbus.service.method(AGENT_INTERFACE, in_signature="os", out_signature="")
    def DisplayPinCode(self, device, pincode):
        '''
        This method gets called when the service daemon needs to display a
        pincode for an authentication. An empty reply should be returned. When
        the pincode needs no longer to be displayed, the Cancel method of the
        agent will be called. This is used during the pairing process of
        keyboards that don't support Bluetooth 2.1 Secure Simple Pairing, in
        contrast to DisplayPasskey which is used for those that do. This
        method will only ever be called once since older keyboards do not
        support typing notification. Note that the PIN will always be a
        6-digit number, zero-padded to 6 digits. This is for harmony with the
        later specification.

        Possible errors: org.bluez.Error.Rejected
                         org.bluez.Error.Canceled
        '''
        raise NotImplementedMethodCall("DisplayPinCode(%s, %s)" %
                                       (device, pincode))

    # In object 32bituint
    @dbus.service.method(AGENT_INTERFACE, in_signature="ou", out_signature="")
    def RequestConfirmation(self, device, passkey):
        '''
        This method gets called when the service daemon needs to confirm a
        passkey for an authentication. To confirm the value it should return
        an empty reply or an error in case the passkey is invalid. Note that
        the passkey will always be a 6-digit number, so the display should be
        zero-padded at the start if the value contains less than 6 digits.

        Possible errors: org.bluez.Error.Rejected
                         org.bluez.Error.Canceled
        '''
        raise NotImplementedMethodCall("RequestConfirmation(%s, %06d)" %
                                       (device, passkey))

    # In object
    @dbus.service.method(AGENT_INTERFACE, in_signature="o", out_signature="")
    def RequestAuthorization(self, device):
        '''
        This method gets called to request the user to authorize an incoming
        pairing attempt which would in other circumstances trigger the
        just-works model.

        Possible errors: org.bluez.Error.Rejected
                         org.bluez.Error.Canceled
        '''
        raise NotImplementedMethodCall("RequestAuthorization (%s)" % (device))

    @dbus.service.method(AGENT_INTERFACE, in_signature="", out_signature="")
    def Cancel(self):
        '''
        This method gets called to indicate that the agent request failed
        before a reply was returned.
        '''
        raise NotImplementedMethodCall("Cancel")


class RunningAgent():
    '''A class that sets up the GObject mainloop (the loop that is running)
    to provide the agent.

    It stores the mainloop as 'self.mainloop' until
    the close method is called which closes the mainloop.
    '''
    def __init__(self):
        # Arrange for the glib mainloop to be the default - for async calls
        # this must be done *before* contacting the bus
        # https://dbus.freedesktop.org/doc/dbus-python/doc/tutorial.html#id31
        dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)

        # Create a bus
        bus = dbus.SystemBus()

        # Set the device capability to DisplayYesNo - HC05 doesn't seem to take
        # this into account
        capability = "DisplayYesNo"

        # Create an agent that can be accessed at AGENT_PATH
        Agent(bus, AGENT_PATH)

        # Register the agent
        obj = bus.get_object(BUS_NAME, "/org/bluez")
        manager = dbus.Interface(obj, "org.bluez.AgentManager1")
        manager.RegisterAgent(AGENT_PATH, capability)
        print("Agent registered")
        manager.RequestDefaultAgent(AGENT_PATH)

        # Create a mainloop for aync calls
        self.mainloop = GObject.MainLoop()
        self.mainloop.run()

    def close(self):
        self.mainloop.quit()


if __name__ == '__main__':
    runningAgent = RunningAgent()
    print("got here")
    try:
        while True:
            pass
    except:
        runningAgent.quit()
        raise
