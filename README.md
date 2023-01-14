# ThingQ V2

A PolyglotV3 node server plugin for monitoring LG ThinQv2 device vias their ThinQ platform.

#### Installation

This node server can be installed from the PG3 NodeServer Store.

## Supported Devices

| *Device* | *Support* 
| --- | --- | 
| Refrigerator | 🚫 |
| Air Purifier | 🚫 |
| Washer & Dryer | ✔️ | 
| Dishwasher | ✔️ | 
| Dehumidifier | 🚫 |
| AC | 🚫 |

# Configuration

1. Navigate to the "Configuration" tab after installing via PG3 NodeServer store
2. Add Language and Country codes under typed configuration parameters

   country code: Your account [country alpha-2 code](https://www.countrycode.org), e.g., US for the USA.
   language code:  Your account language code, e.g., en-US, en-CA, fr-CA, vi-VN.

3. When prompted with a Notice, click the link and login
4. Once redirected to a blank page, copy the URL (address) and save that as a custom config with they key `auth_key`

eg. `auth_key`: `https://kr.m.lgaccount.com/login/iabClose?state=.....`

4. Save and profit!