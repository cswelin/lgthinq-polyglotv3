#!/usr/bin/env python
import os
import json
import signal
from pprint import pprint


from thinq2.controller.auth import ThinQAuth
from thinq2.controller.thinq import ThinQ
from thinq2.client.objectstore import ObjectStoreClient
from thinq2.model.device.dishwasher import DishWasherDevice

LANGUAGE_CODE = "en-CA"
COUNTRY_CODE = "CA"
STATE_FILE = os.environ.get("STATE_FILE", "state.json")

if os.path.exists(STATE_FILE):
    with open(STATE_FILE, "r") as f:
        thinq = ThinQ(json.load(f))
else:
    auth = ThinQAuth(language_code=LANGUAGE_CODE, country_code=COUNTRY_CODE)

    print("No state file found, starting new client session.\n")
    print(
        "Please set the following environment variables if the default is not correct:\n"
    )
    print("LANGUAGE_CODE={} COUNTRY_CODE={}\n".format(LANGUAGE_CODE, COUNTRY_CODE))
    print("Log in here:\n")
    print(auth.oauth_login_url)
    print("\nThen paste the URL to which the browser is redirected:\n")

    callback_url = input()
    auth.set_token_from_url(callback_url)
    thinq = ThinQ(auth=auth)

    print("\n")

def save_state():
    with open(STATE_FILE, "w") as f:
        json.dump(vars(thinq), f)

save_state()

devices = thinq.mqtt.thinq_client.get_devices()

if len(devices.items) == 0:
    print("No devices found!")
    exit(1)


print("UserID: {}".format(thinq.auth.profile.user_id))
print("User #: {}\n".format(thinq.auth.profile.user_no))

print("Devices:\n")

for device in devices.items:
    print("{}: {} (model {})".format(device.device_id, device.alias, device.model_name))
    pprint(device.snapshot)
    print(device.snapshot.state["remainTimeMinute"])
    #print("{}: {}".format(device.polymorph.door, device.polymorph.remainTimeHour))

#################################################################################
# example of raw MQTT access                                                    #
#################################################################################

print("\nListening for device events. Use Ctrl-C/SIGINT to quit.\n")

thinq.mqtt.on_message = lambda client, userdata, msg: print(msg.payload)
thinq.mqtt.connect()
thinq.mqtt.loop_forever()