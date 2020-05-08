from typing import List
from typing import Any, Dict
from datetime import datetime, timedelta
try:
    import Domoticz
except ImportError:
    import fakeDomoticz as Domoticz
import dbus
import dbus.mainloop.glib


class SignalHelper:

    def __init__(self,
                 useSystemBus: bool = True, busAddress: str = None,
                 defRecipient: str = None, defGroup: str = None, debug: bool = False):

        self.useSystemBus = useSystemBus
        self.busAddress = busAddress
        self.defRecipient = defRecipient
        self.defGroup = defGroup

        self.debug = debug
        self.lastUpdate: datetime
        self.hasError = False
        self.nextpoll = datetime.now()
        self.reset()

    def dumpConfig(self):
        Domoticz.Debug(
            "useSystemBus:{}\t"
            "busAddress:{}\t"
            "default recipient:{}\t"
            "default group:{}\t"
            .format(self.useSystemBus, self.busAddress, self.defRecipient, self.defGroup)
        )

    def reset(self):
        self.isStopped = True  # goes to false on init
        self.bus = None
        self.signalObject = None
        self.groups: dict
        self.resetError()

    def init(self):
        try:
            # 1. connect
            self.connect()

            # 2. check registered
            if self.signalObject:
                r = self.isRegistered()
                if not r:
                    raise Exception("Signal Cli not set up correctly. Number is not registered.")

            # 3. fetch groups
            self.groups = self.getGroups()
            self.isStopped = False
            return True
        except Exception as e:
            self.isStopped = True
            self.setMyError(e)
            raise e

    def connect(self):
        Domoticz.Debug("Try to connect")
        if self.useSystemBus is True:
            Domoticz.Debug("on system bus")
            self.bus = self.connectToSystemBus()
        else:
            Domoticz.Debug("on {}".format(self.busAddress))
            self.bus = self. connectToBus(address=self.busAddress)

        if self.bus:
            # TODO deeper checks on connection
            self.bus.get_is_authenticated()
            self.bus.get_is_connected()

            Domoticz.Debug("get signal bus object")
            self.signalObject = self.getSignalProxy()

    def connectToSystemBus(self, enableLoop: bool = False):
        if enableLoop:
            dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
        return dbus.SystemBus()

    def connectToBus(self, enableLoop: bool = False, address: str = "tcp:host=localhost,port=55558"):
        if enableLoop:
            dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
        b = dbus.bus.BusConnection(address)
        return b

    def closeConnection(self):
        if self.bus:
            Domoticz.Debug("close connection")
            self.bus.close()

    def setMyError(self, error):
        self.hasError = True
        self.errorMsg = error

    def resetError(self):
        self.hasError = False
        self.errorMsg = None

    def stop(self):
        self.isStopped = True
        closeConnection()

    def getSignalProxy(self):
        o = self.bus.get_object(
            "org.asamk.Signal",  # Bus name
            "/org/asamk/Signal"  # Object path
        )
        return o

    def introspect(self):
        #  Introspection returns an XML document containing information
        # about the methods supported by an interface.
        r = self.signalObject.Introspect()
        # TODO print it
        return r

    def ping(self):
        Domoticz.Debug("Ping the bus")
        self.signalObject.Ping()
        return

    def isRegistered(self):
        Domoticz.Debug("Check if number isRegistered")
        isRegistered = self.signalObject.isRegistered()
        b: bool = (isRegistered == dbus.Boolean(1))
        Domoticz.Debug("isRegistered {}".format(b))
        return b

    def getGroups(self):
        groups = dict()
        gIds: dbus.Array = self.signalObject.getGroupIds()
        for g in gIds:
            gName = self.signalObject.getGroupName(g)
            groups[gName] = g
            Domoticz.Debug(" group name: {}  id: {}".format(gName, g))
        return groups

    def sendGrpMsg(self, text: str, groupName: str, attachment: str = None):
        # get group id based on name
        Domoticz.Debug(" grp msg: {} to: {} ".format(text, groupName))
        dbMsg = dbus.String(text)
        att = None
        if not attachment:
            att = dbus.Array([], signature='s')
        else:
            da = dbus.String(attachment)
            att = dbus.Array([da], signature='s')
        grpId = self.groups[groupName]
        # grpId = groups[0]
        if not grpId:
            raise Exception("GroupNotFoundExcpetion")
        try:
            r = self.signalObject.sendGroupMessage(dbMsg, att, grpId)
            Domoticz.Debug(" send result: {} ".format(r))
        except Exception as e:
            Domoticz.Error("error  {} ".format(e))
        return r

    def sendMsg(self, text: str, nr: str, attachment: str = None):
        dbMsg = dbus.String(text)
        dbNr = dbus.String(nr)
        att = None
        if not attachment:
            att = dbus.Array([], signature='s')
        else:
            da = dbus.String(attachment)
            att = dbus.Array([da], signature='s')
        Domoticz.Debug(" msg: {} to: {} ".format(text, nr))
        # send to group
        # r = self.signalObject.sendGroupMessage(msg, att, dbGroups[0])
        # Domoticz.Debug(" grp send result: {} ".format(r))
        # send to number
        try:
            r = self.signalObject.sendMessage(dbMsg, att, dbNr)
            Domoticz.Debug(" nr send result: {} ".format(r))
        except Exception as e:
            Domoticz.Error("error  {} ".format(e))
        return r

# util stuff
# https://stackoverflow.com/questions/11486443/dbus-python-how-to-get-response-with-native-types


def python_to_dbus(data):
    '''
        convert python data types to dbus data types
    '''
    if isinstance(data, str):
        data = dbus.String(data)
    elif isinstance(data, bool):
        # python bools are also ints, order is important !
        data = dbus.Boolean(data)
    elif isinstance(data, int):
        data = dbus.Int64(data)
    elif isinstance(data, float):
        data = dbus.Double(data)
    elif isinstance(data, list):
        data = dbus.Array([python_to_dbus(value) for value in data], signature='v')
    elif isinstance(data, dict):
        data = dbus.Dictionary(data, signature='sv')
        for key in data.keys():
            data[key] = python_to_dbus(data[key])
    return data


def dbus_to_python(data):
    '''
        convert dbus data types to python native data types
    '''
    if isinstance(data, dbus.String):
        data = str(data)
    elif isinstance(data, dbus.Boolean):
        data = bool(data)
    elif isinstance(data, dbus.Int64):
        data = int(data)
    elif isinstance(data, dbus.Double):
        data = float(data)
    elif isinstance(data, dbus.Array):
        data = [dbus_to_python(value) for value in data]
    elif isinstance(data, dbus.Dictionary):
        new_data = dict()
        for key in data.keys():
            new_data[key] = dbus_to_python(data[key])
        data = new_data
    return data
