# !/usr/bin/python3 -u

# Python script for the signalDomoticzService
# Author: belze
# this is an example how a signal message receiver might work running outside of domoticz
# If dealing with attachments, make sure user that run script has access to the folder
# if dbus is used with signal-cli attachments are stored in:
#  /home/signal-cli/.local/share/signal-cli/attachments/
# based on https://github.com/AsamK/signal-cli/wiki/DBus-service over dbus


# $ sudo mkdir /usr/local/lib/signalDomoticzService
# $ sudo mv /home/domoticz/domoticz/plugins/domoticz-SignalDBus/signalDomoticzService.py /usr/local/lib/signalDomoticzService/
# $ sudo chown root:root /usr/local/lib/signalDomoticzService/signalDomoticzService.py
# $ sudo chmod 644 /usr/local/lib/signalDomoticzService/signalDomoticzService.py

import json
from pydbus import SystemBus  # here we use pydbus, it is more convenient
from gi.repository import GLib
import requests
import urllib.parse
import filetype
import time
import systemd.daemon
from systemd.daemon import notify, Notification
import pidfile

# settings for domoticz
DOM_BASE_URL = "http://localhost:8080"  # base url for domoticz
DOM_DEV_IDX = 68  # id of receiver text device
# http://dom-pi:8080/json.htm?type=command&param=udevice&idx=68&nvalue=0&&svalue=%27Message%27,%20%27Tes%27,%20%27received%20in%20group%27,%20%27%27
# http://dom-pi:8080/json.htm?type=command&param=udevice&idx=IDX&nvalue=0&svalue=TEXT
DOM_JSN_URL = "{}/json.htm?type=command&param=udevice&idx={}&nvalue=0&svalue=".format(DOM_BASE_URL, DOM_DEV_IDX)


NAME = "signalDomoticzService"
PIDFILE = '/var/run/' + NAME + '.pid'
LOGFILE = '/var/log/' + NAME + '.log'


signal = None


def msgRcv(timestamp, source, groupID, message, attachments):
    """callback - what to do if a message is received

    Arguments:
        timestamp {[type]} -- [description]
        source {[type]} -- [description]
        groupID {[type]} -- [description]
        message {[type]} -- [description]
        attachments {[type]} -- [description]
    """
    if groupID:
        # got an group message - try to fetch group name as well
        msg = "Message {} received in group {}".format(message, signal.getGroupName(groupID))
    else:
        msg = "Message {} received from {} ".format(message, source)

    if attachments and attachments[0]:
        # got at least one attachment
        kind = filetype.guess(attachments[0])
        msg = "{} attachment {} type {}".format(msg, attachments[0], kind.extension)
    print(msg)
    url = "{}{}".format(DOM_JSN_URL, urllib.parse.quote(msg))
    print("update domoticz {} ".format(url))
    # r = requests.get(DOM_JSN_URL, auth=('user', 'pass'))
    r = requests.get(url)
    if(r.status_code == 200):
        jResult = r.json()
        # TODO check for value
    else:
        # TODO should be handeled?
        print("sending to domoticz failed")

    return


if __name__ == '__main__':

    print('Starting up ...')
    try:
        with pidfile.PIDFile(PIDFILE):
            #print('Process started')
            # time.sleep(30)
            bus = SystemBus()
            loop = GLib.MainLoop()
            signal = bus.get('org.asamk.Signal')
            signal.onMessageReceived = msgRcv
            print('Startup complete')
            # Tell systemd that our service is ready
            notify(Notification.READY)

            loop.run()

    except pidfile.AlreadyRunningError:
        print('Already running.')
