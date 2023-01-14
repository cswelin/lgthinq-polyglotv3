import udi_interface
import os 
import re
import json 
import sys
import time
import threading
from enum import Enum

# My Template Node
from thinq2.controller.auth import ThinQAuth
from thinq2.controller.thinq import ThinQ
from thinq2.client.objectstore import ObjectStoreClient
from thinq2.model.device.dishwasher import DishWasherDevice
from thinq2.model.device.washerdryer import WasherDryerDevice
from nodes import WasherDryerNode
from nodes import DishWasherNode

LOGGER = udi_interface.LOGGER
LOG_HANDLER = udi_interface.LOG_HANDLER
Custom = udi_interface.Custom
ISY = udi_interface.ISY

class ConfigurationState(Enum):
    Start = 1 
    WaitingForRegion = 2
    Region = 3
    Redirect = 4
    WaitingForAuthentication = 5
    Authentication = 6
    Ready = 7

# IF you want a different log format than the current default
LOG_HANDLER.set_log_format('%(asctime)s %(threadName)-10s %(name)-18s %(levelname)-8s %(module)s:%(funcName)s: %(message)s')

class ThinQController(udi_interface.Node):
    def __init__(self, polyglot, primary, address, name):
        super(ThinQController, self).__init__(polyglot, primary, address, name)
        self.poly = polyglot
        self.name = 'LG ThinQ Controller'  # override what was passed in
        self.hb = 0
        
        # Config
        self.auth_url           = None
        self.thinq              = None
        self.handler_config_st  = None 
        self.config_state       = ConfigurationState.Start
        self.cfg_language_code  = None
        self.cfg_country_code   = None

        self.n_queue = []

        self.Parameters      = Custom(polyglot, 'customparams')
        self.Notices         = Custom(polyglot, 'notices')
        self.TypedParameters = Custom(polyglot, 'customtypedparams')
        self.TypedData       = Custom(polyglot, 'customtypeddata')

        self.poly.subscribe(self.poly.START,                self.start, address)
        self.poly.subscribe(self.poly.STOP,                 self.stop)
        self.poly.subscribe(self.poly.CUSTOMPARAMS,         self.parameterHandler)
        self.poly.subscribe(self.poly.CUSTOMTYPEDPARAMS,    self.typedParameterHandler)
        self.poly.subscribe(self.poly.CUSTOMTYPEDDATA,      self.typedDataHandler)
        self.poly.subscribe(self.poly.POLL,                 self.poll)
        self.poly.subscribe(self.poly.ADDNODEDONE,          self.node_queue)

        self.poly.subscribe(self.poly.CONFIG,               self.handler_config)
        self.poly.ready()

        self.poly.addNode(self)

    def start(self):
        self.Notices.clear()

        self.checkAuthState()
        self.poly.updateProfile()
        self.poly.setCustomParamsDoc()
        self.heartbeat(0)

    def stop(self):
        LOGGER.debug('stopping')

    def handler_config(self, cfg_data):
        LOGGER.info(f'cfg_data={cfg_data}')
        self.cfg_longPoll = int(cfg_data['longPoll'])
        self.handler_config_st = True

    def parameterHandler(self, params):
        self.Parameters.load(params)
        LOGGER.debug('Loading parameters now')
        self.check_params()

        if params != None:
            url = params["auth_url"]
            if url != None:
                self.auth_url = params["auth_url"]
                if self.config_state.value < ConfigurationState.Authentication.value:
                    self.config_state = ConfigurationState.Authentication
                    self.checkAuthState()

    def typedParameterHandler(self, params):
        self.TypedParameters.load(params)
        LOGGER.debug('Loading typed parameters now')
        LOGGER.debug(params)

    def typedDataHandler(self, params):
        self.TypedData.load(params)
        LOGGER.debug('Loading typed data now')
        LOGGER.debug(params)

        if params is not None:
            region_config = params['region_config']
            if region_config is not None:
                self.cfg_language_code  = region_config['language_code']
                self.cfg_country_code   = region_config['country_code']
                LOGGER.debug('config_state {} < {}'.format(self.config_state.value, ConfigurationState.Region.value))
                if self.config_state.value < ConfigurationState.Region.value:
                    LOGGER.debug('set config state to region')
                    self.config_state = ConfigurationState.Region
                    self.checkAuthState()

    def poll(self, flag):
        if 'longPoll' in flag:
            LOGGER.debug('longPoll (controller)')
            # self.heartbeat()
            self.discover()
        else:
            self.heartbeat()
            self.shortPoll()
            LOGGER.debug('shortPoll (controller)')

    def shortPoll(self):
        self.Notices.clear()

        LOGGER.debug("starting short poll: {}".format(self.config_state))

        self.checkAuthState()
        
    def checkAuthState(self):
        if self.config_state.value < ConfigurationState.Ready.value and os.path.exists("state/state.json"):
            LOGGER.debug("state file exists")
            with open("state/state.json", "r") as f:
                self.config_state = ConfigurationState.Ready
                self.thinq = ThinQ(json.load(f))
                LOGGER.debug("loaded state file, discovering")
                self.startThinQ()
                self.discover()
                
        elif self.config_state == ConfigurationState.Start:
            self.Notices['region'] = "Please set region_code and country_code below"
            LOGGER.debug("Please set the following variables if the default is not correct:")
            self.config_state = ConfigurationState.WaitingForRegion
        
        elif self.config_state == ConfigurationState.WaitingForRegion:
            LOGGER.debug("do nothing... waiting on region configurations")
       
        elif self.config_state == ConfigurationState.Region:
            self.Notices.clear()
          
            auth = ThinQAuth(language_code=self.cfg_language_code, country_code=self.cfg_country_code)
            msg ='Please <a target="_blank" href="{}/">Sign-in to LG ThinQ account</a> and save the redirect URL to auth_url custom variable'.format(auth.oauth_login_url)
            self.Notices['auth_url'] = msg
          
            LOGGER.debug("authentication url {}".format(auth.oauth_login_url))
            self.config_state = ConfigurationState.WaitingForAuthentication
        
        elif self.config_state == ConfigurationState.WaitingForAuthentication:
            auth = ThinQAuth(language_code=self.cfg_language_code, country_code=self.cfg_country_code)
            msg ='Please <a target="_blank" href="{}/">Sign-in to LG ThinQ account</a> and save the redirect URL to auth_url custom variable'.format(auth.oauth_login_url)
            self.Notices['auth_url'] = msg

            LOGGER.debug("do nothing... authentication redirection")
       
        elif self.config_state == ConfigurationState.Authentication:
            self.config_state = ConfigurationState.Ready                

            auth = ThinQAuth(language_code=self.cfg_language_code, country_code=self.cfg_country_code)
            auth.set_token_from_url(self.auth_url)
            
            self.thinq = ThinQ(auth=auth)
            self.saveThinQState()
            
            LOGGER.debug("Done authenticating, call discover")
            
            self.startThinQ()
            self.discover()
       
        elif self.config_state == ConfigurationState.Ready:
            LOGGER.debug("do nothing... READY")
    
    def saveThinQState(self): 
        with open("state/state.json", "w") as f:
            json.dump(vars(self.thinq), f)

    def startThinQ(self):
        self.thinq.start()

    def thinqHandler(self, client, userdata, msg):
        print(msg.payload)

    def query(self,command=None):
        nodes = self.poly.getNodes()
        for node in nodes:
            if nodes[node] != self:
                nodes[node].query()

    def discover(self, *args, **kwargs):
        if self.config_state != ConfigurationState.Ready:
            LOGGER.debug("Trying to discover while not authorized")
            return False
        
        devices = self.thinq.mqtt.thinq_client.get_devices()
        for device in devices.items:
            LOGGER.info("{}: {} (model {})".format(device.device_id, device.alias, device.model_name))
            
            address = self.get_valid_node_address("l{}".format(device.device_id))
            node    = self.poly.getNode(address)
            
            if node is None:
                alias = self.get_valid_node_name('LG-{}'.format(device.alias))
                if isinstance(device.snapshot, WasherDryerDevice):
                    self.add_node(WasherDryerNode(self.poly, self.address, address, alias, device, self.thinq))
                elif isinstance(device.snapshot, DishWasherDevice):
                    self.add_node(DishWasherNode(self.poly, self.address, address, alias, device, self.thinq))
            else:
                node.query()
        return True
        
    def add_node(self,node):
        anode = self.poly.addNode(node)
        LOGGER.debug(f'got {anode}')
        self.wait_for_node_done()
        if anode is None:
            LOGGER.error('Failed to add node address')
        return anode
    
    def node_queue(self, data):
        self.n_queue.append(data['address'])

    def wait_for_node_done(self):
        while len(self.n_queue) == 0:
            time.sleep(0.1)
        self.n_queue.pop()

    def get_valid_node_address(self, deviceID):
        # Only allow utf-8 characters
        #  https://stackoverflow.com/questions/26541968/delete-every-non-utf-8-symbols-froms-string
        name = bytes(deviceID, 'utf-8').decode('utf-8','ignore')
        # Remove <>`~!@#$%^&*(){}[]?/\;:"'` characters from name
        # make it lower case, and only 14 characters
        return re.sub(r"[-<>`~!@#$%^&*(){}[\]?/\\;:\"']+", "", name.lower()[:14])

    # Removes invalid charaters for ISY Node description
    def get_valid_node_name(self, name):
        # Only allow utf-8 characters
        #  https://stackoverflow.com/questions/26541968/delete-every-non-utf-8-symbols-froms-string
        name = bytes(name, 'utf-8').decode('utf-8','ignore')
        # Remove <>`~!@#$%^&*(){}[]?/\;:"'` characters from name
        return re.sub(r"[<>`~!@#$%^&*(){}[\]?/\\;:\"']+", "", name)
        
    def heartbeat(self,init=False):
        LOGGER.debug('heartbeat: init={}'.format(init))
        if init is not False:
            self.hb = init
        LOGGER.debug('heartbeat: hb={}'.format(self.hb))
        if self.hb == 0:
            self.reportCmd("DON",2)
            self.hb = 1
        else:
            self.reportCmd("DOF",2)
            self.hb = 0

    def set_module_logs(self,level):
        logging.getLogger('urllib3').setLevel(level)

    def check_params(self):
        self.Notices.clear()
        
        self.TypedParameters.load( [
                {
                    'name': 'region_config',
                    'title': 'Region Configuration',
                    'desc': 'Region Configuration',
                    'isList': False,
                    'params': [
                        {
                            'name': 'language_code',
                            'title': 'Langauge Code (en-CA, fr-CA, en-US, etc)',
                            'isRequired': True,
                        },
                        {
                            'name': 'country_code',
                            'title': 'Country Code (CA, US, etc)',
                            'isRequired': True,
                        }
                    ]
                }
            ],
            True
        )

    id = 'controller'
    commands = {
        'QUERY': query,
        'DISCOVER': discover
    }
    drivers = [
        {'driver': 'ST', 'value': 1, 'uom': 2},
    ]
