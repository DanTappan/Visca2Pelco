import uselect
import usocket
import uasyncio
import struct
import time
from debug import Debug

#VISCA_INQUIRY = struct.unpack("!H", b'\x01\x10')[0]
#VISCA_CMD = struct.unpack("!H", b'\x01\x00')[0]
#VISCA_REPLY = struct.unpack("!H", b'\x01\x11')[0]
#VISCA_SET = struct.unpack("!H", b'\x01\x20')[0]
#VISCA_CTL = struct.unpack("!H", b'\x02\x00')[0]
#VISCA_CTL_REPLY = struct.unpack("!H", b'\x02\x01')[0]

# these are 'shorts' received in network byte order
VISCA_INQUIRY = 0x0110
VISCA_CMD = 0x0100
VISCA_REPLY = 0x0111
VISCA_SET = 0x0120
VISCA_CTL = 0x0200
VISCA_CTL_REPLY = 0x0201

SEQUENCE_NUM_MAX = 2 ** 32 - 1

def visca_typestr(type):
    typedict = {
        VISCA_INQUIRY : "INQUIRY",
        VISCA_REPLY : "REPLY",
        VISCA_SET : "SET",
        VISCA_CTL : "CTL",
        VISCA_CTL_REPLY : "CTL_REPLY",
        VISCA_CMD : "CMD"
        }
    return(typedict[type])

class ViscaPkt:
    def __init__(self, pkt):
        try:
            fmt = "!HHL"
            (self._payloadtype,
             self._payloadlen,
             self._sequence) = struct.unpack(fmt, pkt)
            self._payload = pkt[struct.calcsize(fmt):]
            self._timestamp = time.ticks_ms()
            if Debug():
                print("rcv Visca: (", visca_typestr(self._payloadtype), ", ",
                      self._payloadlen, ", ",
                      self._sequence, "): ",
                      self._payload.hex())
        except:
            if Debug():
                print("Bad format Visca pkt: ", pkt)
            self._payloadtype = 0
            self._payloadlen = 0
            self._sequence = 0
            
    def payload_type(self):
        return(self._payloadtype)

    def payload(self):
        return(self._payload)

    def sequence_check(self, old_visca):
        # check the sequence number of a new visca packet against the last received from source
        #
        # ignore stale (older than 1 minute) buffered packets,
        # otherwise make sure sequence number has changed.
        #
        # for now, we assume only one command at a time, so the check for "changed" means
        # "don't repeat last command" rather than strictly enforcing increasing sequence numbers
        #
        # note that we special case a sequence number of -1, because some controllers
        # seem to use that on all commands.
        #
        if Debug():
            print("visca sequence check: old ", old_visca, " new seq ", self._sequence)
        return (old_visca == None or
                time.ticks_diff(time.ticks_ms(), old_visca._timestamp) > 60000 or
                self._sequence == SEQUENCE_NUM_MAX or
                (self._sequence != old_visca._sequence) 
                )

    def compose(self):
        return(struct.pack("!HHL", self._payloadtype, self._payloadlen, self._sequence) + self._payload)

    def reply(self, payload):
        self._payloadtype = VISCA_REPLY
        self._payloadlen = len(payload)
        self._payload = payload
        return self.compose()
    
    
class ViscaCmd:
    def __init__(self, visca):
        self._visca = visca
    
# Visca server
class ViscaServer:
    def __init__(self, camera, polltimeout=1, max_packet=1024):
        ai = usocket.getaddrinfo("0.0.0.0", 52381)[0]
        self.sock = usocket.socket(usocket.AF_INET, usocket.SOCK_DGRAM)
        self.sock.setblocking(False)
        self.sock.bind(ai[-1])

        self._cbdict = {}
        self._seqdict = {}
    
        self.polltimeout = polltimeout
        self.max_packet = max_packet
        self._camera = camera
        
    def close(self):
        self.sock.close()

    def send_reply(self, code, data=None):
        s = self.sock
        addr = self._curr_addr
        pkt = self._curr_pkt
        if data == None:
            buf = b'\x90' + code + b'\xff'
        else:
            buf = b'\x90' + code + data + b'\xff'
        buf = pkt.reply(buf)
        if Debug():
            print("send Visca: ", buf.hex())
        s.sendto(buf, addr)

    def send_ack(self):
        self.send_reply(b'\x40')
    
    def send_error(self, payload):
        self.send_reply(b'\x60', payload)
        
    def send_complete(self, payload=None):
        self.send_reply(b'\x50', payload)
   
    async def serve(self):
        s = self.sock
        p = uselect.poll()
        p.register(s, uselect.POLLIN)
        to = self.polltimeout
        while True:
            try:
                if p.poll(to):
                    buf, addr = s.recvfrom(self.max_packet)
                    pkt = ViscaPkt(pkt=buf)
                    if (pkt._payloadlen != 0):
                        lastpkt = self._seqdict.get(addr)
                        if pkt.sequence_check(lastpkt):
                            # Sequence ok, save in history
                            self._seqdict[addr] = pkt
                            self._curr_pkt = pkt
                            self._curr_addr = addr
                        
                            # process packet ...
                            #
                            if pkt.payload_type() == VISCA_CMD or pkt.payload_type() == VISCA_INQUIRY:
                                payload = pkt.payload()
                                fmt = "!BBBB"
                                (unit, set_or_inq, target, sub) = struct.unpack(fmt, payload)
                                # see ViscamCamera.py for the usage of the 'switch' method
                                #
                                if set_or_inq == 1:
                                    self._camera.switch("set", target, sub,
                                                        payload[struct.calcsize(fmt):])
                                    self.send_complete()
                                else:
                                    rv = self._camera.switch("get", target, sub,
                                                         payload[struct.calcsize(fmt):])
                                    self.send_complete(rv)

                                await uasyncio.sleep(0)

                await uasyncio.sleep(0)
            except uasyncio.core.CancelledError:
                # Shutdown server
                s.close()
                return
