#
# Visca Camera class
#
# this implements a virtual camera for control by the ViscaServer
# methods are named based on the visca target code
# (1 == interface, 4 == camera, 6 == pantilt) and subcommand
# e.g.:
# camera.set_0x6_0x1 is a set command for the pan/tilt
# camera.get_0x6_0x12 is a query command for the pan/tilt position
#
#
# Methods can be accessed using the camera.switch method, which accepts:
# target, subcommand, and a bytes array containing VISCA command arguments
#
# Unimplemented set commands just return 
# 
# get_ methods should return a bytes array containing the response.
# Unimplimented get_ methods return an array containing '0'
#
# This version converts Visca PTZ commands to Pelco
#
import struct
import uPelco
from debug import Debug


class ViscaCamera:
    # Map a Visca direction tuple into a string
    _PTZDirection = {
        (03, 01) : 'UP',
        (03, 02) : 'DOWN',
        (01, 03) : 'LEFT',
        (02, 03) : 'RIGHT',
        (01, 01) : 'UP-LEFT',
        (02, 01) : 'UP-RIGHT',
        (01, 02) : 'DOWN-LEFT',
        (02, 02) : 'DOWN-RIGHT',
        (03, 03) : 'STOP'
        }
    # Convert a Visca speed code (1-\x18) to a percent of max (0-100%)
    def speed2percent(self, code):
        return code*100/0x18
    
    def __init__(self):
        self._focus_mode = 2
        self._Pelco = uPelco.PelcoDevice()
        pass

    def switch(self, type="set", target=0, sub=0, cmd=b'\xff'):
        handler_str = type + '_' + hex(target) + '_' + hex(sub)
        rv = getattr(self, handler_str, None)
        if rv == None:
            rv = getattr(self, "default_" + type)
        return((rv)(cmd))
        
    # Default handlers
    def default_set(self, cmd):
        pass

    def default_get(self, cmd):
        return(bytes.fromhex("00"))

    # Camera commands
    # Get/Set Focus Mode
    def get_0x4_0x38(self, cmd):
        return(bytes([self._focus_mode]))

    def set_0x4_0x38(self,cmd):
        self._focus_mode = cmd[0]
        
    # Get/Set Focus Position
    def get_0x4_0x48(self, cmd):
        return bytes.fromhex("00000000")
    def set_0x4_0x48(self, cmd):
        pass

    # Get/Set Zoom Position
    def get_0x4_0x47(self, cmd):
        return bytes.fromhex("00000000")
    def set_0x4_0x47(self, cmd):
        pass

    # PTZ Commands
    # PTZ move
    def set_0x6_0x1(self, cmd):
        (pan_speed, tilt_speed, pan, tilt) = struct.unpack("!BBBB", cmd)
        direction = self._PTZDirection[(pan, tilt)]
        
        if Debug():
            print("PTZ move: ", direction, (pan_speed, tilt_speed))

        self._Pelco.move(direction,
                         self.speed2percent(pan_speed),
                         self.speed2percent(tilt_speed))

    # PTZ Home
    def set_0x6_0x4(self, cmd):
        self._Pelco.go_to_home()  

    # PTZ Set absolute position
    # Sony is documented as 5 nybbles, PTZOptics as 4, try to handle bot
    def set_0x6_0x2(self, cmd):
        if len(cmd) > 12:
            (pan_speed, tilt_speed,
             p1, p2, p3, p4, p5,
             t1, t2, t3, t4, t5) = struct.unpack("!BBBBBBBBBBBB", cmd)
            pan_pos = (((((((p1<<4)+p2)<<4)+p3)<<4)+p4)<<4)+p5
            tilt_pos = (((((((t1<<4)+t2)<<4)+t3)<<4)+t4)<<4)+t5
        else:
            (pan_speed, tilt_speed,
             p1, p2, p3, p4, 
             t1, t2, t3, t4) = struct.unpack("!BBBBBBBBBB", cmd)
            pan_pos = (((((p1<<4)+p2)<<4)+p3)<<4)+p4
            tilt_pos = (((((t1<<4)+t2)<<4)+t3)<<4)+t4
            
        if pan_pos == 0 and tilt_pos == 0:
            self._Pelco.go_to_home()
        

    # PTZ Set relative position

    # get PTZ position
    def get_0x6_0x12(self, cmd):
        return(bytes.fromhex("0000000000000000"))



