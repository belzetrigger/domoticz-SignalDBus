#!/usr/bin/python3
"""
Author: belze
This is an example to fire back to domoticz via http to use switchcommand.
Better would be to find a way to use the update/switch url direct as 
custom http action
"""
import argparse
import json
import requests
import urllib.parse

ARG_DESCR = "usage: msg"

# settings for domoticz
DOM_BASE_URL = "http://127.0.0.1:8080"  # base url for domoticz
DOM_DEV_IDX = 69  # id of switch device
DOM_SGNL_CMD = "sendNotification"  # sendGroupNotification
DOM_SGNL_SUBJECT = "Domoticz Message:"
MSG = "test text"  # dummy text
# http://dom-pi:8080/json.htm?type=command&param=switchlight&idx=69&switchcmd=sendNotification%20Hello my Single Friend
# http://dom-pi:8080/json.htm?type=command&param=switchlight&idx=69&switchcmd=sendGroupNotification%20Hello group%20Bla


def forceSendMsg(cmd: str, subj: str, msg: str, attachments: str = None):
    rc: int = 0
    print(msg)
    mergedCmd = "{} {} {}".format(cmd, subj, msg)
    sUrl = "{}/json.htm?type=command&param=switchlight&idx={}&switchcmd={}".format(
        DOM_BASE_URL, DOM_DEV_IDX, urllib.parse.quote(mergedCmd))
    print("call signal commander within domoticz: {} ".format(sUrl))
    r = requests.get(sUrl)
    if(r.status_code == 200):
        jResult = r.json()
        # TODO check for value
        # exit(0)
    else:
        # TODO should be handeled?
        print("sending to domoticz failed")
        rc = 1
    return rc


# Initialize parser
parser = argparse.ArgumentParser(description=ARG_DESCR)
# Add long and short argument
parser.add_argument("--msg", "-m", help="the msg to send", type=str)
parser.add_argument("--subj", "-s", help="the subject", type=str, default=DOM_SGNL_SUBJECT)
parser.add_argument("--cmd", "-c", help="the cmd to use", type=str, default=DOM_SGNL_CMD)
parser.add_argument("--idx", "-i", help="the device index", type=int)

# reed arguments
args = parser.parse_args()


rc = forceSendMsg(args.cmd, args.subj, args.msg)
exit(rc)
