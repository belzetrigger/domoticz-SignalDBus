

# domoticz-SignalDBus
<!---
[![GitHub license](https://img.shields.io/github/license/belzetrigger/domoticz-SignalDBus.svg)](https://github.com/belzetrigger/domoticz-SignalDBus/blob/master/LICENSE)
-->

[![PyPI pyversions](https://img.shields.io/badge/python-3.6%20|%203.7%20|%203.8-blue.svg)]() 
[![Plugin version](https://img.shields.io/badge/version-0.0.1-red.svg)](https://github.com/belzetrigger/domoticz-SignalDBus/branches/)

Early state of notification plugin that works with [Secure Messenger Signal](https://signal.org/)

| Device | Image          | Comment                                          |
| ------ | -------------- | ------------------------------------------------ |
| Test   | todo add image | test quickly sending messages to number or group |


## Summary
I recently come across [Unoffical WhatsApp Notification](https://www.domoticz.com/wiki/Unofficial_Whatsapp_-_Notification_System_-_Doorbell_example). Nice one. 
I just prefer Signal. So why not try similar thing with Signal. So here we are. 
Using an [Interface](https://github.com/AsamK/signal-cli/) that expose the signal functions to DBus. So they should be available without knowing and integrating original libs to Domoticz Plugin.

This plugin is open source.

Relays on:
https://github.com/AsamK/signal-cli/
https://github.com/WhisperSystems/libsignal-service-java
and DBus https://dbus.freedesktop.org/doc/dbus-python/index.html

Images: Signal Logo from signal.org and there github. 

## Prepare Whisper System aka Signal 
- install java: `sudo apt-get install default-jre`
- create a new user signal-cli: `sudo adduser signal-cli`
- check last version from signal-cli under https://github.com/AsamK/signal-cli/releases 
- install it
  ```bash
  export VERSION="0.6.7"
  wget https://github.com/AsamK/signal-cli/releases/download/v"${VERSION}"/signal-cli-"${VERSION}".tar.gz
  sudo tar xf signal-cli-"${VERSION}".tar.gz -C /opt
  sudo ln -sf /opt/signal-cli-"${VERSION}"/bin/signal-cli /usr/local/bin/
  ```
### register
- most easiest way is to use user `signal-cli` so we can avoid copying data to `/var/lib/signal-cli`
- change user
    ```bash
    su signal-cli # become user signal-cli
    signal-cli -u +49xxx register --voice # (omit --voice if using mobile phone number)
    # wait for calling machine to get pin code, replace yyyyyy with the real code
    signal-cli -u +49xxx verify yyyyyy
    ```
### test and trust
#### send
- just send your self a message
    ```bash
    signal-cli -u +49xxx send -m "This is a message" +4916xx
    ```
#### recieve
- just pick your mobile and send an answer
    ```bash
    signal-cli -u +49aaaa receive
    ```
#### trust
- to trust a number we need to get the id
    ```bash
    signal-cli -u +49xxx listIdentities # get all identities aka numbers
    # search in the out number and fetch secure number 
    signal-cli -u +49xxx trust +4916xxx -v 242142142424242121214xxxxxxxxxxxxxxxxxx 
    # to check just run again
    signal-cli -u +49xxx listIdentities 
    ```

### dbus
- detailed information see https://github.com/AsamK/signal-cli/wiki/DBus-service 
- install need packages: `sudo apt install libunixsocket-java`
- download needed service files from https://github.com/AsamK/signal-cli/tree/master/data 
- copy files 
    ```bash
    sudo cp org.asamk.Signal.conf /etc/dbus-1/system.d/
    sudo cp org.asamk.Signal.service /usr/share/dbus-1/system-services/
    sudo cp signal.service /etc/systemd/system/
    ```
- set used and registered number
    ```bash
    sudo sed -i -e "s|%dir%|/usr/local|" -e "s|%number%|+49xxx|" /etc/systemd/system/signal.service
    ```
- if used user `signal-cli` for registration, remove the config parameter from ExecStart
- should look like: `
    ```bash
    [...]
    ExecStart=/usr/local/bin/signal-cli -u +49xxx daemon --system
    [...]
    ```
- if used other user, copy your signal config to lib folder and give permissions
    ```
    sudo cp -R ~/.local/share/signal-cli/ /var/lib/signal-cli
    sudo chown -R signal-cli: /var/lib/signal-cli
    ```
- reload
    ```bash
    sudo systemctl daemon-reload
    sudo systemctl enable signal.service
    sudo systemctl reload dbus.service
    ```

#### test dbus
- to test send just run
    ```bash
    dbus-send --system --type=method_call --print-reply --dest="org.asamk.Signal" /org/asamk/Signal org.asamk.Signal.sendMessage string:MessageText array:string: string:+4916xx
    ```
- to check if receiving works use dbus monitor  `dbus-monitor --system`  and send a message
#### good to know
- first call might take some time, as the java stuff must first get started

#### dbus over tcp
Idea was to expose dbus via tcp and integrate it over domoticzs connection into 
this plugin. But this did not work as expected.
Under Rasbian I touched the `/lib/systemd/system/dbus.socket`
```bash
[Socket]
ListenStream=/var/run/dbus/system_bus_socket
ListenStream=55558  # <-- Add this line
```
Restarted and checked if tcp port gets listed `netstat -plntu | grep 55558`

To test if connection is working, you can use DFEET and add a new connection to `tcp:host=localhost,port=55558` if X11 is on. Otherwise just quickly try `python3`
```python
import dbus
db=dbus.bus.BusConnection('tcp:host=localhost,port=55558')
[...]
```
Further reading: https://stackoverflow.com/questions/10158684/connecting-to-dbus-over-tcp 
Besides of this, to expose system bus over tcp might be also a security risk as well.



## Installation and Setup Plugin
- a running Domoticz: tested with 2020.1 with Python 3.7
- needed python modules:
    - for dbus we need dbus-python
    - on my Pi it was available with out doing anything and its also not listed in pip3 list
- clone project
    - go to `domoticz/plugins` directory 
    - clone the project
        ```bash
        cd domoticz/plugins
        git clone https://github.com/belzetrigger/domoticz-SignalDBus.git
        ```
- or just download, unzip and copy to `domoticz/plugins`
- Optional: enable TCP feature
  ```python
    # config
    USE_SYSTEM_BUS = True
  ```
- restart Domoticz service
- Now go to **Setup**, **Hardware** in your Domoticz interface. There add
**Signal Messenger via DBus**.
### Settings
<!-- prettier-ignore -->


| Parameter    | Information                                                                              |
| ------------ | ---------------------------------------------------------------------------------------- |
| name         | Domoticz standard hardware name.                                                         |
| IP Address   | only used if dbus is exposed via TCP                                                     |
| port         | only used if dbus is exposed via TCP                                                     |
| recipient    | a phone number to send the messages to, use with country code e.g. <code>+4916...</code> |
| group        | optional name of a signal group to send to                                               |
| Update every | Polling time, at the moment just used for is a live ping to bus                          |
| Debug        | if True, the log will be hold a lot more output.                                         |
## Usage
### Selector Switch for testing
this functions are supported
* test if in `/etc/systemd/system/signal.service` defined number is registered and usable via dbus
* send a Message to phone Number from config
* send a Message to phone Number from config with dummy picture
* send a Message to group from config
* send a Message to group from config with dummy picture
* for attachments we need absolute path to file! 
  for test we just use logo from `.../domoticz/www/ images/logo/180.png`
* Name of switch will change and show result as suffix and give so some feedback
as this works via command you can also use json `[...]/json.htm?type=command&param=switchlight&idx=69&switchcmd=Set%20Level&level=40`


## Bugs and ToDos
* add a receiver
* more stability like 
  * check if connected 
  * check given parameters
* might just hook on the bus, if msg send required and use 
  heart beat to check if is available                                                               

## Versions
| Version | Note                                                               |
| ------- | ------------------------------------------------------------------ |
| 0.0.1   | First version of this plugin. Supports sending to group and number |


## State
Under development but main function runs quite stabile.

## links and similar projects
- https://wiki.fhem.de/wiki/SiSi
- https://knx-user-forum.de/forum/supportforen/openhab/1139194-whisper-systems-signal-messenger-client-einrichten



