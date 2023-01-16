
from thinq2.model.device.washerdryer import WasherDryerDevice
from thinq2.controller.thinq import ThinQ
import udi_interface
import sys
import time
import urllib3
import json
from utils import Utilities

LOGGER = udi_interface.LOGGER

class WasherDryerNode(udi_interface.Node):
  
    def __init__(self, polyglot, primary, address, name, device, thinQ):
        self.device = device
        self.snapshot = device.snapshot
        self.name = name
        self.thinQ = thinQ
        self.poly = polyglot
        self.lpfx = '%s:%s' % (self.id, address)
        
        super().__init__(polyglot, primary, address, name)

        self.poly.subscribe(self.poly.START, self.start, address)
        self.poly.subscribe(self.poly.POLL, self.poll)

    def start(self):
        self.device = self.thinQ.get_device(self.device.device_id)
        self.device.on_update(self._on_update)
        self.snapshot = self.device.snapshot
        self._reportDriver()

    def _on_update(self, device):
        LOGGER.debug('%s: _on_update message=%s', self.lpfx,json.dumps(device.snapshot.state))
        self.snapshot = device.snapshot
        self._reportDriver()

    def _reportDriver(self):
        LOGGER.debug('%s: object=%s', self.lpfx,json.dumps(self.snapshot.state))

        self.setDriver('ST', 1)
        minutes = int(self.snapshot.state["remainTimeMinute"]) + (int(self.snapshot.state["remainTimeHour"]) * 60)
        self.setDriver('GV0', minutes)

        state = self.snapshot.state["state"]

        if state in Utilities.state_to_gv.keys():
            self.setDriver('GV2', Utilities.state_to_gv[state])
        
    def poll(self, polltype):
        if 'longPoll' in polltype:
            LOGGER.debug('%s: longPoll (node)', self.lpfx,)
            self._update()
    
    def _update(self):
        try:
            self.snapshot = self.thinQ.get_device(self.device.device_id).snapshot
            self._reportDriver()
        except Exception as e:
            LOGGER.error('%s: longPoll error %s', self.lpfx, e)
        
    def query(self,command=None):
        LOGGER.debug('query (node)')
        self._update()

    drivers = [
        {'driver': 'ST', 'value': 0, 'uom': 2},
        {'driver': 'GV0', 'value': 0, 'uom': 44}, # Time Remaining 
        {'driver': 'GV2', 'value': 0, 'uom': 25}  # Device state
    ]

    commands = {
                    'QUERY': query,
                }

    id = 'laundryid'
