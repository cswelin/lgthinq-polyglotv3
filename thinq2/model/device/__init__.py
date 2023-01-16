from .base import Device
from .washerdryer import WasherDryerDevice
from .dishwasher import DishWasherDevice

device_types = {
    201: WasherDryerDevice,
    202: WasherDryerDevice,
    204: DishWasherDevice
}
