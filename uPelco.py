# -*- coding: utf-8 -*-
"""
Pelco-D library for ESP32
Based on https://github.com/ivanovys/Pelco-D-Python/blob/master/Pelco.py
"""
from config import Debug

try:
    from machine import UART
except ImportError:
    if Debug():
        print("UART import failed")
    # Unix: Make a dummy UART object
    class UART:
        def __init__(self, port, baudrate):
            pass
        def init(self, baudrate, bits, parity, stop, tx, rx):
            pass
        def close(self):
            pass
        def write(self, cmd):
            pass
        
import time
import io

class Frame:     
    # Frame format:	|synch byte|address|command1|command2|data1|data2|checksum|
    # Bytes 2 - 6 are Payload Bytes
    _frame = {
        'synch_byte': b'\xFF',		# Synch Byte, always FF		-	1 byte
        'address':	b'\x00',		# Address			-	1 byte
        'command1':	b'\x00',		# Command1			-	1 byte
	'command2':	b'\x00', 	# Command2			-	1 byte
        'data1':	b'\x00', 	# Data1	(PAN SPEED):		-	1 byte
	'data2':	b'\x00', 	# Data2	(TILT SPEED):		- 	1 byte 
	'checksum':	b'\x00'		# Checksum:			-       1 byte
    }
       
    _command2_code = {
	'DOWN' : b'\x10',
	'UP'   : b'\x08',	
	'LEFT' : b'\x04',
	'RIGHT': b'\x02',
	'UP-RIGHT' : b'\x0A',
	'DOWN-RIGHT': b'\x12',
	'UP-LEFT'   : b'\x0C',
        'DOWN-LEFT' : b'\x14',
	'STOP' : b'\x00',
        'ZOOM-IN' : b'\x00',
        'ZOOM-OUT' : b'\x00',
        'FOCUS-FAR' : b'\x00',
        'FOCUS-NEAR': b'\x00'
    }
     
    def __init__(self, address=1):
        self._frame['address']=bytes([address])
        
    # accepts bytes arrays, not strings
    def _construct_cmd(self, command1 = b'\x00',command2=b'\x00', pan_speed=b'\x00', tilt_speed=b'\x00' ):
        
        self._frame['command1']=command1
                   
        if command2 not in self._command2_code:
            self._frame['command2']=command2
        else:
            self._frame['command2']=self._command2_code[command2]     
        
        self._frame['data1'] = pan_speed
        self._frame['data2'] = tilt_speed

        self._checksum(self._payload_bytes())

        cmd = self._frame['synch_byte']+self._payload_bytes()+self._frame['checksum']
        if Debug():
            print("Pelco command: ", cmd.hex())
        return cmd
   
    def _payload_bytes(self):
        return self._frame['address']+self._frame['command1']+\
                    self._frame['command2']+self._frame['data1'] +\
                    self._frame['data2']
    
    def _checksum(self, payload_bytes):
        chksum = 0
        for b in payload_bytes:
            chksum = (chksum + b) % 256
            
        self._frame['checksum'] = bytes([chksum])
        

class PelcoDevice:  

    # convert a speed percentage (0-100%) to a speed code (0-0x3f)
    # return a bytes array containing the code
    def percent2speed(self, percent):
        speed = int(percent*0x3f/100)
        if Debug():
            print("percent2speed ", percent, "%->", speed)
        return bytes([speed])
        
    #connect
    def __init__(self, port=1, baudrate=2400, tx=17, rx=16, timeout_=0):    
        self._device=UART(port, baudrate, tx=tx)
        self._device.init(baudrate, bits=8, parity=None, stop=1, tx=tx, rx=rx)
        self._command=Frame()
    
    def unconnect(self):
        self._device.close()
    
    # Start camera moving
    # accepts a direction code string, and speeds as a percentage of max
    def move(self, side, pan_speed=0, tilt_speed=0):
        """ 'DOWN','UP','LEFT','RIGHT','UP-RIGHT','UP-LEFT','DOWN-RIGHT','DOWN-LEFT','STOP'"""
        cmd=self._command._construct_cmd(command2=side,
                                         pan_speed=self.percent2speed(pan_speed),
                                         tilt_speed=self.percent2speed(tilt_speed))
        self._device.write(cmd)
        
    def set_home_position(self):
        """As HOME Preset 11  - \x0B """
        cmd=self._command._construct_cmd(command2=b'\x03', pan_speed=b'\x00',tilt_speed=b'\x0B')
    
    def go_to_home(self):
        """As HOME Preset 11  - \x0B """
        cmd=self._command._construct_cmd(command2=b'\x07', pan_speed=b'\x00',tilt_speed=b'\x0B')
        self._device.write(cmd)
              
    def go_to_zero(self):
        cmd=self._command._construct_cmd(command2=b'\x07', pan_speed=b'\x00',tilt_speed=b'\x22')
        self._device.write(cmd)
       
    def set_preset(self, num_preset):
        """ preset 1 - 255 . 11 used as Home"""
        cmd=self._command._construct_cmd(command2=b'\x03', pan_speed=b'\x00',tilt_speed=num_preset)
        self._device.write(cmd)
        
    def go_to_preset(self, num_preset):
        """ preset 1 - 255 . 11 used as Home"""
        cmd=self._command._construct_cmd(command2=b'\x07', pan_speed=b'\x00',tilt_speed=num_preset)
        self._device.write(cmd)
    
    def manual_command(self, com1,com2,data1,data2):
        cmd=self._command._construct_cmd(command1 = com1,command2=com2, pan_speed=data1, tilt_speed=data2)
        self._device.write(cmd)
       
    
