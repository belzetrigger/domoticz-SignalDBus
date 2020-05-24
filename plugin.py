"""
 plugin for signal secure msg
Author: belze
0.0.1   initial version with sending support
0.0.2   receiving support via external service and update via JSON call
0.0.3   notification
"""

"""
<plugin key="SignalMessenger" name="Signal Messenger via DBus" author="belze" version="0.0.3"
externallink="https://github.com/belzetrigger/domoticz-SignalDBus" >
    <description>
        <h2>Signal Messenger</h2><br/>
        Interact with the whisper-systems-signal-messenger-client aka Signal to send send messagesself.
        <h3>Features</h3>
        <ul style="list-style-type:square">
            <li>send a message to signal for phone numbers</li>
            <li>send a message to groups</li>
            <li>add an attachment to messages</li>
            <li>commands can be send by json or switch</li>
        </ul>
        <h3>Devices</h3>
        <ul style="list-style-type:square">
            <li>Selector Switch - for testing sending messages </li>
            <li>text device for received messages</li>
            <li>text device for sent messages</li>
        </ul>
        <h3>Configuration</h3>
        Configuration options...
    </description>
    <params>
        <param field="Address" label="IP Address" width="200px" required="true" default="127.0.0.1"/>
        <param field="Port" label="Port" width="34px" required="true" default="55557"/>
        <param field="Mode1" label="recipient" width="200px"
        required="true" default="+49160......"/>
        <param field="Mode2" label="group" width="200px"
        required="false" default=""/>

        <param field="Mode3" label="testmsg" width="200px"
        required="true" default="This is a test msg"/>

        <param field="Mode4" label="Update every x minutes" width="200px"
        required="true" default="5"/>



        <param field="Mode6" label="Debug" width="75px">
            <options>
                <option label="True" value="Debug"/>
                <option label="False" value="Normal"  default="False" />
            </options>
        </param>
    </params>
</plugin>
"""

from datetime import datetime, timedelta
# domoticz crashes wit pydbus and GLib
# from pydbus import SystemBus
# from gi.repository import GObject as gobject
# import gobject
# import dbus
# Loop chrashes domotizc...
# import dbus.mainloop.glib
# from dbus.mainloop.glib import DBusGMainLoop
# from gi.repository import
# import traceback

import pathlib


try:
    import Domoticz
except ImportError:
    import fakeDomoticz as Domoticz

from signalDBusHelper import SignalHelper

# config
USE_SYSTEM_BUS = True  # if true we use SystemBus directly

# icons

# units
UNIT_TXT_RECEIVER_IDX = 1
UNIT_TXT_RECEIVER_NAME = "Receiver"
UNIT_TXT_RECEIVER_OPTIONS = ""

UNIT_SWITCH_IDX = 2
UNIT_SWITCH_NAME = "Signal Message"
UNIT_SWITCH_OPTIONS = {
    'LevelNames': '|reg?|nr msg|nr att|grp msg|grp att',
    'LevelOffHidden': 'true',
    'SelectorStyle': '0'}
UNIT_SWITCH_LVL_REGISTERED = 10
UNIT_SWITCH_LVL_MSG_NR = 20
UNIT_SWITCH_LVL_MSR_NR_ATTACH = 30
UNIT_SWITCH_LVL_MSG_GRP = 40
UNIT_SWITCH_LVL_MSR_GRP_ATTACH = 50

UNIT_TXT_SENDER_IDX = 3
UNIT_TXT_SENDER_NAME = "Sender"
UNIT_TXT_SENDER_OPTIONS = ""


class BasePlugin:
    enabled = False

    def __init__(self):
        self.debug: bool = False
        self.nextpoll = datetime.now()
        self.pollinterval = 60 * 5
        self.errorCounter = 0
        self.signalHelper: SignalHelper = None
        return

    def onStart(self):
        if Parameters["Mode6"] == 'Debug':
            self.debug = True
            Domoticz.Debugging(1)
            DumpConfigToLog()
        else:
            Domoticz.Debugging(0)

        Domoticz.Log("onStart called")

        # check polling interval parameter
        try:
            temp = int(Parameters["Mode4"])
        except:
            Domoticz.Error("Invalid polling interval parameter")
        else:
            if temp < 1:
                temp = 1  # minimum polling interval
                Domoticz.Error(
                    "Specified polling interval too short: changed to one minutes")
            elif temp > (60):
                temp = (60)  # maximum polling interval is 1 hour
                Domoticz.Error(
                    "Specified polling interval too long: changed to 1 hour")
            self.pollinterval = temp * 60
        Domoticz.Log("Using polling interval of {} seconds".format(
            str(self.pollinterval)))
        # recipient
        self.recipient = Parameters["Mode1"]
        # group
        self.groupName = Parameters["Mode2"]

        # recipient
        self.text = Parameters["Mode3"]

        self.testImage: str
        # on pi should be path: /home/domoticz/domoticz/plugins/domoticz-SignalDBus
        # pathlib.Path(__file__).parent.absolute()
        self.testImage = "{}/../../www/images/logo/180.png".format(pathlib.Path(__file__).parent.absolute())

        self.busAddress = "tcp:host={},port={}".format(Parameters["Address"], Parameters["Port"])
        # create devices
        createDevices()
        # switch them to Off state
        Devices[UNIT_SWITCH_IDX].Update(0, "Off", Name=UNIT_SWITCH_NAME)

        # test connection
        # self.tcpConn = Domoticz.Connection(Name="dbus Socket Test", Transport="TCP/IP",
        #                                   Protocol="Line",
        #                                  Protocol="None",
        #                                  Address="localhost", Port="55558")
        # self.tcpConn.Connect()
        # self.tcpConn.Listen()
        # to use async calls we need this ....
        # dbus.mainloop..DBusGMainLoop(set_as_default=True)

        try:

            self.signalHelper = SignalHelper(useSystemBus=USE_SYSTEM_BUS,
                                             busAddress=self.busAddress,
                                             defRecipient=self.recipient,
                                             defGroup=self.groupName,
                                             debug=self.debug)

            if(self.debug):
                self.signalHelper.dumpConfig()

            if self.signalHelper.init():
                Devices[UNIT_SWITCH_IDX].Update(1, "On", Name=UNIT_SWITCH_NAME)

            # TODO parameter as config
            # könnte auch unix stream sein: unix:path=/var/run/dbus/system_bus_socket"
            # self.systemBus = connectToBus("tcp:host=localhost,port=55558")

            # listen
            # signal time=1588711833.445132 sender=:1.27 -> destination=(null destination) serial=93 path=/org/asamk/Signal; interface=org.asamk.Signal; member=MessageReceived

            # self.signalObject.connect_to_signal("MessageReceived", msg_handler,
            #                                    dbus_interface="org.asamk.Signal")

            # self.systemBus.add_signal_receiver(
            #    catchall_signal_handler, interface_keyword='dbus_interface', member_keyword='member')

            # self.systemBus.add_signal_receiver(msgRcv,
            #                                   sender_keyword=None,
            #                                   destination_keyword=None,
            #                                    member_keyword='MessageReceived',
            #                                   path_keyword='/org/asamk/Signal',
            #                                   interface_keyword='org.asamk.Signal')

        except Exception as e:
            Domoticz.Error("Could not connect to socket ....{}".format(e))
            Devices[UNIT_SWITCH_IDX].Update(0, "Off", Name=UNIT_SWITCH_NAME + " << ERROR ")

    def onStop(self):
        if self.signalHelper:
            self.signalHelper.stop()
        Devices[UNIT_SWITCH_IDX].Update(0, "Off", Name=UNIT_SWITCH_NAME)
        Domoticz.Log("onStop called")

    def onConnect(self, Connection, Status, Description):
        Domoticz.Log("onConnect called")
        if (Status == 0):
            Domoticz.Log("Connected to Server: {}:{}".format(
                Connection.Address, Connection.Port)
            )
            Domoticz.Debug("connected successfully.")
            Connection.l
            # TODO try to connect to it
            # try:
            # to use async calls we need this ....
            # dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)

            # Domoticz.Debug("Try to connected to dbus.")
            # myBus = dbus.bus.BusConnection("tcp:host=localhost,port=55558")
            # bus_obj = dbus.bus.BusConnection("tcp:host={},port={}".format(
            #    Parameters["Address"], Parameters["Port"]))
            # Domoticz.Debug("Try to get signal.")

            # self.signalObject = myBus.get_object(
            #    "org.asamk.Signal",  # Bus name
            #    "/org/asamk/Signal"  # Object path
            # )
            # Domoticz.Debug("Try to send.")
            # sendMsg(self.signalObject, self.text, self.recipient)

            # Domoticz.Debug("Try to recieve.")
            # self.signalObject.connect_to_signal("MessageReceived", msg_handler,
            #                                    dbus_interface="org.asamk.Signal")
            # loop = GLib.MainLoop()
            # loop.run()
            # except Exception as e:
            #    Domoticz.Error("Could not connect to socket ....{}".format(e))

        else:
            Domoticz.Error("Failed to connect to: {}:{}, Description: {}".format(
                Connection.Address, Connection.Port, Description)
            )
            Domoticz.Log("Failed to connect (" + str(Status) + ") to: "
                         + Parameters["Address"] + ":" + Parameters["Port"] + " with error: " + Description)

    def onMessage(self, Connection, Data):
        Domoticz.Log("onMessage called")

    def onDeviceModified(self, Unit):
        Domoticz.Log("onDeviceModified called for Unit " +
                     str(Unit) )
        # TODO do some use full things ...
        if(Unit == UNIT_TXT_RECEIVER_IDX):
            Domoticz.Log("we got something on our receiver. {} ".format(Devices[UNIT_TXT_RECEIVER_IDX].sValue))

    def onCommand(self, Unit, Command, Level, Hue):
        Domoticz.Log("onCommand called for Unit " +
                     str(Unit) + ": Parameter '" + str(Command) + "', Level: " + str(Level))
        Command = Command.strip()
        action, sep, params = Command.partition(' ')
        action = action.capitalize()
        #params = params.capitalize()
        try:
            Domoticz.Debug("BLZ: onCommand called for Unit " +
                           str(Unit) + ": action '" + str(action) + "', params: " + str(params))

            if (Unit == UNIT_SWITCH_IDX):
                # Listen to sending commands
                if (action.lower() == "SendNotification".lower()):
                    Domoticz.Debug("SendNotification: {}".format(params))
                    r = self.signalHelper.sendMsg(params, self.recipient)
                    Devices[UNIT_TXT_SENDER_IDX].Update(nValue=1, sValue=str(params))
                elif (action.lower() == "SendGroupNotification".lower()):
                    Domoticz.Debug("SendGroupNotification: {}".format(params))
                    r = self.signalHelper.sendGrpMsg(params, self.groupName)
                    Devices[UNIT_TXT_SENDER_IDX].Update(nValue=1, sValue=str(params))

                # Test via button
                elif (action == "On" or Command == "On"):
                    Domoticz.Debug("On - not supported ")
                elif (action == "sendNotification"):
                    Domoticz.Debug("sendNotification: {}".format(params))
                    r = self.signalHelper.sendMsg(params, self.recipient)

                elif (action == "Set"):
                    Domoticz.Debug("Set")
                    if(Level == UNIT_SWITCH_LVL_REGISTERED):
                        Domoticz.Debug("registered?")
                        r = self.signalHelper.isRegistered()

                    elif(Level == UNIT_SWITCH_LVL_MSG_NR):
                        Domoticz.Debug("send message to number")
                        r = self.signalHelper.sendMsg(self.text, self.recipient)

                    elif(Level == UNIT_SWITCH_LVL_MSR_NR_ATTACH):
                        Domoticz.Debug("send  nr attachment")
                        r = self.signalHelper.sendMsg(self.text, self.recipient, self.testImage)

                    elif(Level == UNIT_SWITCH_LVL_MSG_GRP):
                        Domoticz.Debug("send message to group")
                        r = self.signalHelper.sendGrpMsg(self.text, self.groupName)

                    elif(Level == UNIT_SWITCH_LVL_MSR_GRP_ATTACH):
                        Domoticz.Debug("send grp attachment")
                        r = self.signalHelper.sendGrpMsg(self.text, self.groupName, self.testImage)

                    Devices[UNIT_SWITCH_IDX].Refresh()
                    Devices[UNIT_SWITCH_IDX].Update(1, "On", Name=UNIT_SWITCH_NAME + '  > ' + str(r))
                elif (action == "Off"):
                    Domoticz.Debug("Off - not supported")

        except (Exception) as e:
            Domoticz.Error("Error on deal with unit {}: msg *{}*;".format(Unit, e))

    def onNotification(self, Name, Subject, Text, Status, Priority, Sound, ImageFile):
        Domoticz.Log("BLZ Notification: " + Name + "," + Subject + "," + Text + "," +
                     Status + "," + str(Priority) + "," + Sound + "," + ImageFile)

    def onDisconnect(self, Connection):
        Domoticz.Log("onDisconnect called")

    def onHeartbeat(self):
        # Domoticz.Log("onHeartbeat called")
        myNow = datetime.now()
        if myNow >= self.nextpoll:
            Domoticz.Debug(
                "----------------------------------------------------")
            hasError = False
            self.nextpoll = myNow + timedelta(seconds=self.pollinterval)
            try:
                if (self.signalHelper.isStopped is True):
                    Domoticz.Debug("reinit signal helper")
                    self.signalHelper.init()

                Domoticz.Debug("is alive ping...")
                self.signalHelper.ping()
            except Exception as e:
                hasError = True
                Domoticz.Error("Error on ping {}".format(e))

            # we might still have an internal error
            if (hasError is False and self.signalHelper.hasError is True):
                hasError = True
                Domoticz.Error("internal error discovered ..")

            if hasError:
                if self.errorCounter > 5:
                    self.nextpoll = myNow + timedelta(minutes == 5)
                    self.signalHelper.stop()
                    Domoticz.Error("To much error happend, reset and wait 5min ")

                self.errorCounter += 1
                Domoticz.Error(
                    "Uuups. Something went wrong ... Shouldn't be here.")
                t = "Error"
                self.nextpoll = myNow

            else:
                self.errorCounter = 0

            Domoticz.Debug(
                "----------------------------------------------------")


global _plugin
_plugin = BasePlugin()


def onStart():
    global _plugin
    _plugin.onStart()


def onStop():
    global _plugin
    _plugin.onStop()


def onConnect(Connection, Status, Description):
    global _plugin
    _plugin.onConnect(Connection, Status, Description)


def onMessage(Connection, Data):
    global _plugin
    _plugin.onMessage(Connection, Data)


def onDeviceModified(Unit):
    global _plugin
    _plugin.onDeviceModified(Unit)


def onCommand(Unit, Command, Level, Hue):
    global _plugin
    _plugin.onCommand(Unit, Command, Level, Hue)


def onNotification(Name, Subject, Text, Status, Priority, Sound, ImageFile):
    global _plugin
    _plugin.onNotification(Name, Subject, Text, Status, Priority, Sound, ImageFile)


def onDisconnect(Connection):
    global _plugin
    _plugin.onDisconnect(Connection)


def onHeartbeat():
    global _plugin
    _plugin.onHeartbeat()

    # Generic helper functions


def DumpConfigToLog():
    for x in Parameters:
        if Parameters[x] != "":
            Domoticz.Debug("'" + x + "':'" + str(Parameters[x]) + "'")
    Domoticz.Debug("Device count: " + str(len(Devices)))
    for x in Devices:
        Domoticz.Debug("Device:           " + str(x) + " - " + str(Devices[x]))
        Domoticz.Debug("Device ID:       '" + str(Devices[x].ID) + "'")
        Domoticz.Debug("Device Name:     '" + Devices[x].Name + "'")
        Domoticz.Debug("Device nValue:    " + str(Devices[x].nValue))
        Domoticz.Debug("Device sValue:   '" + Devices[x].sValue + "'")
        Domoticz.Debug("Device LastLevel: " + str(Devices[x].LastLevel))
    return


def createDevices():
    if UNIT_TXT_RECEIVER_IDX not in Devices:
        Domoticz.Device(Name=UNIT_TXT_RECEIVER_NAME, Unit=UNIT_TXT_RECEIVER_IDX, TypeName="Text",
                        Used=1,
                        Options=UNIT_TXT_RECEIVER_OPTIONS
                        ).Create()
        Domoticz.Log("Devices[UNIT_TXT_RECEIVER_IDX={}] created.".format(UNIT_TXT_RECEIVER_IDX))
    #   updateImageByUnit(UNIT_CMD_SWITCH_IDX, ICON_ADMIN)

    if UNIT_SWITCH_IDX not in Devices:
        Domoticz.Device(Name=UNIT_SWITCH_NAME, Unit=UNIT_SWITCH_IDX, TypeName="Selector Switch",
                        Used=1,
                        Switchtype=18, Options=UNIT_SWITCH_OPTIONS).Create()
        Domoticz.Log("Devices[UNIT_SWITCH_IDX={}] created.".format(UNIT_SWITCH_IDX))
    #    updateImageByUnit(UNIT_SWITCH_IDX, ICON_ADMIN)

    if UNIT_TXT_SENDER_IDX not in Devices:
        Domoticz.Device(Name=UNIT_TXT_SENDER_NAME, Unit=UNIT_TXT_SENDER_IDX, TypeName="Text",
                        Used=1,
                        Options=UNIT_TXT_SENDER_OPTIONS
                        ).Create()
        Domoticz.Log("Devices[UNIT_TXT_SENDER={}] created.".format(UNIT_TXT_SENDER_IDX))
