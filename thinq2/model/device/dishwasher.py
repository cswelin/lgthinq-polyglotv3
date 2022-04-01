from dataclasses import field
from marshmallow_dataclass import dataclass

from thinq2.schema import CamelCaseSchema

from .base import Device


@dataclass(base_schema=CamelCaseSchema)
class DishWasherDevice(Device):
    state: dict = field(metadata=dict(data_key="dishwasher"))
