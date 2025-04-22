#
from ViscaServer import ViscaServer
from PelcoViscaCamera import ViscaCamera
import uasyncio
from config import Debug

#
#
def main():
    camera = ViscaCamera()
    s = ViscaServer(camera)
    l = uasyncio.get_event_loop()
    l.run_until_complete(s.serve())
    

main()
