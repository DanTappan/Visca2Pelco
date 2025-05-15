#
# Configuration variables
#
debug = False

def Debug():
    return debug

#
# Network Configuration
#

#
# Hostname
#
Host = "pan-tilt2"

#
# Network Type:
# WIFI
# ETH01
#
NETWORK='ETH01'
ETHVer='v1.4'	# v1.0 or or v1.4

# WIFI Config, if NETWORK == WIFI
#WIFI_SSID = "Video2G"
#WIFI_PWD = 'NDI Cameras'

#
# Connection to PAN/Tilt Controller
#
# Strictly, we don't need the RX pin because we don't receive from the UART
# but some boards will crash if the machine/UART driver uses the default pins.
# specify just to make sure.
PANTILT_TX = 17
PANTILT_RX = 5
PANTILT_BAUD = 2400

#
# Connect to the network
#
def NetworkConnect():
    import network
    
    network.hostname(Host)
    if NETWORK == 'ETH01':
        import machine
        print(Host, "- Connecting to Ethernet Network", ETHVer)
        if ETHVer == 'v1.0':
            lan = network.LAN(mdc=machine.Pin(23),
                              mdio=machine.Pin(18),
                              phy_type=network.PHY_LAN8720,
                              phy_addr=1, power=None)
        elif ETHVer == 'v1.4':
            lan = network.LAN(mdc=machine.Pin(23),
                              mdio=machine.Pin(18),
                              phy_type=network.PHY_LAN8720,
                              phy_addr=1,
                              power=machine.Pin(16))
        else:
            print("Unknown ETH01 version")
        
        while True:
            lan.active(True)
            ipaddr = lan.ipconfig("addr4")
            if ipaddr[0] != '0.0.0.0':
                break
        print("Address:", ipaddr)

    elif NETWORK == 'WIFI':
        sta_if = network.WLAN(network.STA_IF)
        if not sta_if.isconnected():
            print('connecting to WIFI network...')
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
    else:
        print("Network type unknown: ", NETWORK, " network connect failed")


