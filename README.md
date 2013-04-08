remoteecont
===========

Python library for communication with the Econt remote API service.


##Supported API Calls
* cities
* cities_quarters
* cities_regions
* cities_streets
* cities_zones
* client_info
* countries
* delivery_days
* offices
* shipping
* tariff_courier
* tariff_post

## Unsupported API Calls
(feel free to contribute on those)
* access_clients
* account_roles
* cancel_shipment
* check_cd_agreement
* post_boxes
* profile
* registration_request
* shipments

##Example
```python
from __future__ import unicode_literals

from remoteecont import RemoteEcontXml
from remoteecont.transfer import CurlTransfer

service_url = b'http://demo.econt.com/e-econt/xml_service_tool.php'
parcel_url = b'http://demo.econt.com/e-econt/xml_parcel_import.php'

econt = RemoteEcontXml(service_url, parcel_url,  # Remote API urls
                       'itpartner', 'itpartner', # Username and password
                       CurlTransfer)

print(econt.offices('София')) # The argument is optional
print(econt.countries())
print(econt.cities_regions())
print(econt.cities_quarters())
# etc... See method signatures

# See either __init__.py or the Econt official docs for more
# information on shipment request data
loadings = [{
    'sender': ...   # Sender details
    'receiver': ... # Receiver address
    'shipment': ... # Shipment data
    'services': ...
    'payment': ...
}]

system = {
    # 'response_type': ... # You don't have to set this, the lib does it anyway
    'only_calculate': 1,
    'validate': 1
}

print(econt.shipping(loadings, system))
```

##Roadmap
The library supports everything I needed for a project of mine.  If
you find it useful, but limited in means of functionality, please feel
free to contribute.

##License
*Lesser GNU Public License*  
In brief: You you can use the library for anything, but, if you change
the code, you have to share your changes under compatible license and
(of course) notify me of them.

##Contact
If you need help, don't hesitate to contact me on
jordanMiladinov [at] gmail [dot] com
