# This file is executed on every boot (including wake-boot from deepsleep)
#import esp
#esp.osdebug(None)
Host = "pan-tilt1"   
WIFI_SSID = "Video2G"
WIFI_PWD = 'NDI Cameras'
def do_connect():
    import network
    network.hostname(Host)
    sta_if = network.WLAN(network.STA_IF)
    if not sta_if.isconnected():
        print('connecting to network...')
        #TODO: try connecting to both home network and falcon ridge streaming
        sta_if.active(True)
        sta_if.connect(WIFI_SSID, WIFI_PWD)
        while not sta_if.isconnected():
            pass
    print('network config: ', Host, " ",
          sta_if.ifconfig())
    ap_if = network.WLAN(network.AP_IF)
    if ap_if.active():
        ap_if.active(False)
    
do_connect()

#import webrepl
#webrepl.start()
