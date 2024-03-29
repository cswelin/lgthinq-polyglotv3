from thinq2.schema import controller
from thinq2.util import memoize
from thinq2.client.thinq import ThinQClient
from thinq2.controller.mqtt import ThinQMQTT
from thinq2.controller.auth import ThinQAuth
from thinq2.controller.device import ThinQDevice
from thinq2.model.config import ThinQConfiguration
from thinq2.model.mqtt import MQTTMessage

@controller(ThinQConfiguration)
class ThinQ:

    _devices = []

    def get_device(self, device_id):
        device = ThinQDevice(self.thinq_client.get_device(device_id), auth=self.auth)
        self._devices.append(device)
        return device

    def start(self, logger):
        self.mqtt.on_device_message = self._notify_device
        self.mqtt.logger = logger
        self.mqtt.loop_start()

    def _notify_device(self, message: MQTTMessage):
        for device in self._devices:
            if device.device_id == message.device_id:
                device.update(message.data.state.reported)

    @property
    @memoize
    def thinq_client(self):
        return ThinQClient(base_url=self.auth.gateway.thinq2_uri, auth=self.auth)

    @controller
    def auth(self, auth):
        return ThinQAuth(auth)

    @controller
    def mqtt(self, mqtt):
        return ThinQMQTT(mqtt, auth=self.auth)
