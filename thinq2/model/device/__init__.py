from .base import Device
from .laundry import LaundryDevice
from .dishwasher import DishWasherDevice

device_types = {
    201: LaundryDevice,
    202: LaundryDevice,
    204: DishWasherDevice
}
