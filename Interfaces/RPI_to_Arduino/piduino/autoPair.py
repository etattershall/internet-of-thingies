#!/usr/bin/python

from __future__ import absolute_import, print_function, unicode_literals

import dbus
import dbus.service
import dbus.mainloop.glib
from gi.repository import GObject

BUS_NAME = 'org.bluez'
AGENT_INTERFACE = 'org.bluez.Agent1'
AGENT_PATH = "/test/agent"

bus = None
device_obj = None
dev_path = None


def set_trusted(path):
    props = dbus.Interface(bus.get_object("org.bluez", path),
                           "org.freedesktop.DBus.Properties")
    props.Set("org.bluez.Device1", "Trusted", True)


class Rejected(dbus.DBusException):
    _dbus_error_name = "org.bluez.Error.Rejected"


class NotImplementedMethodCall(NotImplementedError):
    '''Raised when calling an Agent method which hasn't been implemented.

    From testing and the documentation, for a simple automatic pairing with
    a HC-05, Agent.RequestPinCode() is the only method that is used. The other
    methods raise this error to point out that they probably should be
    implemented.'''
    pass


class Agent(dbus.service.Object):
    @dbus.service.method(AGENT_INTERFACE, in_signature="", out_signature="")
    def Release(self):
        '''
        This method gets called when the service daemon unregisters the agent.
        An agent can use it to do cleanup tasks. There is no need to unregister
        the agent, because when this method gets called it has already been
        unregistered.
        '''
        raise NotImplementedMethodCall("Release")

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
        set_trusted(device)
        return raw_input("PIN")

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
        raise Rejected("Not Implemented")

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
        raise Rejected("Not Implemented")

    @dbus.service.method(AGENT_INTERFACE, in_signature="", out_signature="")
    def Cancel(self):
        '''
        This method gets called to indicate that the agent request failed
        before a reply was returned.
        '''
        raise NotImplementedMethodCall("Cancel")


if __name__ == '__main__':
    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
    bus = dbus.SystemBus()
    capability = "DisplayYesNo"
    agent = Agent(bus, AGENT_PATH)
    mainloop = GObject.MainLoop()
    obj = bus.get_object(BUS_NAME, "/org/bluez")
    manager = dbus.Interface(obj, "org.bluez.AgentManager1")
    manager.RegisterAgent(AGENT_PATH, capability)

    print("Agent registered")

    manager.RequestDefaultAgent(AGENT_PATH)

    mainloop.run()
