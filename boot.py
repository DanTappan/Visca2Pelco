# This file is executed on every boot (including wake-boot from deepsleep)
#import esp
#esp.osdebug(None)
import config

config.NetworkConnect()

import main

#import webrepl
#webrepl.start()
