
from thinq2.model.device.laundry import LaundryDevice
from thinq2.controller.thinq import ThinQ
import udi_interface
import sys
import time
import urllib3

LOGGER = udi_interface.LOGGER

class DishWasherNode(udi_interface.Node):
    """
    This is the class that all the Nodes will be represented by. You will
    add this to Polyglot/ISY with the interface.addNode method.

    Class Variables:
    self.primary: String address of the parent node.
    self.address: String address of this Node 14 character limit.
                  (ISY limitation)
    self.added: Boolean Confirmed added to ISY

    Class Methods:
    setDriver('ST', 1, report = True, force = False):
        This sets the driver 'ST' to 1. If report is False we do not report
        it to Polyglot/ISY. If force is True, we send a report even if the
        value hasn't changed.
    reportDriver(driver, force): report the driver value to Polyglot/ISY if
        it has changed.  if force is true, send regardless.
    reportDrivers(): Forces a full update of all drivers to Polyglot/ISY.
    query(): Called when ISY sends a query request to Polyglot for this
        specific node
    """
    def __init__(self, polyglot, primary, address, name, device, thinQ):
        """
        Optional.
        Super runs all the parent class necessities. You do NOT have
        to override the __init__ method, but if you do, you MUST call super.

        :param polyglot: Reference to the Interface class
        :param primary: Parent address
        :param address: This nodes address
        :param name: This nodes name
        """    

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
        """
        Optional.
        This method is called after Polyglot has added the node per the
        START event subscription above
        """

        self._reportDriver()
        self.http = urllib3.PoolManager()

    def _reportDriver(self):
        LOGGER.debug('%s: get GV0=%s',self.lpfx,self.getDriver('GV0'))
        self.setDriver('GV0', self.laundryDevice.state["remainTimeMinute"])
        LOGGER.debug('%s: get GV0=%s',self.lpfx,self.getDriver('GV0'))
        
        LOGGER.debug('%s: get GV1=%s',self.lpfx,self.getDriver('GV1'))
        self.setDriver('GV1', self.laundryDevice.state["remoteStart"] == "REMOTE_START_ON")
        LOGGER.debug('%s: get GV1=%s',self.lpfx,self.getDriver('GV1'))

        LOGGER.debug('%s: get GV2=%s',self.lpfx,self.getDriver('GV2'))
        self.setDriver('GV2', self.laundryDevice.state["state"] == "POWERON" )
        LOGGER.debug('%s: get GV2=%s',self.lpfx,self.getDriver('GV2'))

        LOGGER.debug('%s: get GV3=%s',self.lpfx,self.getDriver('GV3'))
        self.setDriver('GV3', self.laundryDevice.state["door"] != "CLOSE" )
        LOGGER.debug('%s: get GV3=%s',self.lpfx,self.getDriver('GV3'))
        
        LOGGER.debug('%s: get ST=%s',self.lpfx,self.getDriver('ST'))
        self.setDriver('ST', 1)
        LOGGER.debug('%s: get ST=%s',self.lpfx,self.getDriver('ST'))
        
    def poll(self, polltype):
        """
        This method is called at the poll intervals per the POLL event
        subscription during init.
        """

        if 'longPoll' in polltype:
            self._longPoll()
        else:
            self._shortPoll()

    def _shortPoll(self):
        LOGGER.debug('shortpoll (node)')
    
    def _longPoll(self):
        LOGGER.debug('longPoll (node)')
        
        try:
            device = self.thinQ.get_device(self.device.device_id)
            self.device = device
            self._reportDriver()

        except Exception as e:
            LOGGER.error('longPoll error %s', e)

    def cmd_on(self, command):
        """
        Example command received from ISY.
        Set DON on DishWasher.
        Sets the ST (status) driver to 1 or 'True'
        """
        self.setDriver('ST', 1)

    def cmd_off(self, command):
        """
        Example command received from ISY.
        Set DOF on DishWasher
        Sets the ST (status) driver to 0 or 'False'
        """
        self.setDriver('ST', 0)

    def cmd_ping(self,command):
        """
        Not really a ping, but don't care... It's an example to test LOGGER
        in a module...
        """
        LOGGER.debug("cmd_ping:")
        r = self.http.request('GET',"google.com")
        LOGGER.debug("cmd_ping: r={}".format(r))


    def query(self,command=None):
        """
        Called by ISY to report all drivers for this node. This is done in
        the parent class, so you don't need to override this method unless
        there is a need.
        """
        self.reportDrivers()

    """
    Optional.
    This is an array of dictionary items containing the variable names(drivers)
    values and uoms(units of measure) from ISY. This is how ISY knows what kind
    of variable to display. Check the UOM's in the WSDK for a complete list.
    UOM 2 is boolean so the ISY will display 'True/False'
    """
    drivers = [
        {'driver': 'ST', 'value': 0, 'uom': 2},
        {'driver': 'GV0', 'value': 0, 'uom': 44}, # Time Remaining 
        {'driver': 'GV1', 'value': 0, 'uom': 2},  # Remote Start
        {'driver': 'GV2', 'value': 0, 'uom': 2},  # Power state
        {'driver': 'GV3', 'value': 0, 'uom': 2}   # Door State
    ]

    """
    id of the node from the nodedefs.xml that is in the profile.zip. This tells
    the ISY what fields and commands this node has.
    """
    id = 'dishwasherid'

    """
    This is a dictionary of commands. If ISY sends a command to the NodeServer,
    this tells it which method to call. DON calls setOn, etc.
    """
    commands = {
                    'PING': cmd_ping
                }
