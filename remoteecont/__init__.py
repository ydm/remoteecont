# -*- coding: utf-8 -*-
# pylint: disable=W0141, W0142

from __future__ import unicode_literals

from collections import Sequence
import copy
import datetime

from remoteecont import xmlutils


class RemoteEcont(object):
    """Simple interface for communication with Econt services."""
 
    def __init__(self, service_url, parcel_url, username, password,
                 transfer_class):
        self._service_url = service_url
        self._parcel_url = parcel_url
        self._username = username
        self._password = password
        self._transfer_class = transfer_class

    def access_clients(self):
        """Информация за клиентите на текущия потребител."""
        raise NotImplementedError

    def account_roles(self):
        """Информация за достъпа на служител."""
        raise NotImplementedError

    def cancel_shipment(self):
        raise NotImplementedError

    def check_cd_agreement(self):
        """Проверка на валидност за споразумение за наложен платеж."""
        raise NotImplementedError

    def cities(self, cities, updated_time):
        """Информация за населените места."""
        raise NotImplementedError

    def cities_quarters(self, cities, updated_time):
        """Информация за кварталите на населените места."""
        raise NotImplementedError

    def cities_regions(self, cities, updated_time):
        """Информация за регионите."""
        raise NotImplementedError

    def cities_streets(self, cities, updated_time):
        """Информация за улиците в населените места."""
        raise NotImplementedError

    def cities_zones(self, cities, updated_time):
        """Информация за зоните на населените места."""
        raise NotImplementedError

    def client_info(self, ein, egn, _id):
        """Информация за клиент."""
        raise NotImplementedError

    def countries(self):
        """Информация за държавите, обслужвани от Еконт."""
        raise NotImplementedError

    def delivery_days(self, delivery_days):
        """
        Информация кои са дните за разнос по дадена дата (за пратки в България).

        На страница 26. от документацията четем: Ако има само една
        дата за разнос (денят след приеман е на пратката е работен
        ден), се връща празен резултат.  Ако има повече възможни дати
        (следващия ден с дежурства, първия работен ден след почивни
        дни, ...) се връщат възможните дати за разнос.

        """
        raise NotImplementedError

    def offices(self, updated_time):
        """Информация за офисите на Еконт Експрес."""
        raise NotImplementedError

    def post_boxes(self):
        """Информация за всички пощенски кутии на Еконт Експрес."""
        raise NotImplementedError

    def profile(self):
        """Информация за профила на клиента с подадения акаунт."""
        raise NotImplementedError

    def registration_request(self):
        """
        Информация за заявките за регистрация в е-еконт.

        Ебати описанието...  Държа да отбележа, че всички описания съм
        ги взел от официалната документация.

        """
        raise NotImplementedError

    def shipments(self, sender_city, receiver_city, _id, full_tracking='ON'):
        """Информация за статуса на товарителници."""
        raise NotImplementedError

    def shipping(self, loadings, system):
        """Генериране на пратка в е-еконт, тарифиране на пощенска пратка."""
        raise NotImplementedError

    def tariff_courier(self):
        """
        Информация за текущата стандартна куриерска/карго тарифа на
        Еконт Експрес

        """
        raise NotImplementedError

    def tariff_post(self):
        """
        Информация за текущата стандартна пощенска тарифа на Еконт
        Експрес.

        """
        raise NotImplementedError


class RemoteEcontXml(RemoteEcont):
    """
    Implement the Econt service communication protocol using XML
    messages.

    """

    # Request pattern
    _CITIES = '''<cities>
  <report_type>{report_type}</report_type>
  <id_zone>{id_zone}</id_zone>
  {{city_names}}
</cities>'''

    _CLIENT = '''<client>
  <username>{username}</username>
  <password>{password}</password>
</client>'''

    _GENERIC = '''<?xml version="1.0" encoding="UTF-8"?>
<request>
  {client}
  <request_type>{{request_type}}</request_type>

  {{args}}
</request>'''

    # TODO: validate=1
    _SHIPPING = '''<?xml version="1.0" encoding="UTF-8"?>
<parcels>
  {client}

  <request_type>shipping</request_type>

  {{system}}
  {{loadings}}
</parcels>
'''

    def __init__(self, service_url, parcel_url, username, password,
                 transfer_class):
        super(RemoteEcontXml, self).__init__(service_url, parcel_url, username,
                                             password, transfer_class)

        # Prepare request patterns
        client = self._CLIENT.format(username=username, password=password)
        self._GENERIC = self._GENERIC.format(client=client)
        self._SHIPPING = self._SHIPPING.format(client=client)

        # Prepare argument patterns
        tags = ['delivery_days', 'egn', 'ein', 'id', 'updated_time']
        self._arg_patterns = \
            {tag: '<{tag}>{{}}</{tag}>'.format(tag=tag) \
                 for tag in tags}

    def _args(self, **kwargs):
        args = []
        for k in filter(lambda e: kwargs[e] is not None, kwargs):
            method = '_args_{}'.format(k)
            if hasattr(self, method):
                args.append(getattr(self, method)(kwargs[k]))
        return ''.join(args)

    def _args_cities(self, cities):
        data = {'city_name': [],
                'id_zone': '',
                'report_type': ''}

        if isinstance(cities, dict):
            # treat `cities` as a dictionary
            data.update(cities)            
        elif isinstance(cities, list):
            # treat `cities` as a list of city_name string parameters
            data.update({'city_name': cities})
        else:
            # treat `cities` as a single string value
            data.update({'city_name': [cities]})

        city_names = ''.join(['<city_name>{}</city_name>'.format(e) \
                                  for e in data.pop('city_name')])

        arg = self._CITIES.format(**data)
        arg = arg.format(city_names=city_names)

        return arg

    def _args_delivery_days(self, delivery_days):
        # TODO: what if it's an isinstance of datetime.date?
        return '<delivery_days>{}</delivery_days>'.format(delivery_days)

    def _args_updated_time(self, updated_time):
        # TODO: use datetime.date
        if updated_time:
            return self._arg_patterns['updated_time'].format(updated_time)
        else:
            return ''

    def _convert_xml_to_dict(self, xml):
        data = xmlutils.xml2dict(xml)
        return data.get('response', data)

    def _generic_request(self, request_type, args=''):
        xml = self._GENERIC.format(request_type=request_type, args=args)
        return self._send_xml_service(xml)

    def _send_xml(self, xml, url):
        t = self._transfer_class()

        # t.append_data('xml', xml)
        t.append_str_as_file(
            'file', xml, 'application/xml; charset=UTF-8', 'something.xml')

        response = t.perform(url)
        t.close()
        return response

    def _send_xml_parcel(self, xml):
        return self._send_xml(xml, self._parcel_url)

    def _send_xml_service(self, xml):
        return self._send_xml(xml, self._service_url)

    def _shorthand(self, request_type, args='', key=None):
        if key is None:
            key = request_type

        xml = self._generic_request(request_type, args)
        data = self._convert_xml_to_dict(xml)

        try:
            if key != '':
                # TODO: basestring won't work for python 3
                if isinstance(data[key], basestring):
                    ret = data[key]
                else:
                    ret = data[key].get('e', data[key])
            else:
                ret = data['e']
        except KeyError:
            # TODO: TypeError is possible if the data object is not a
            # dictionary
            ret = data

        # we should always return a list for consistency
        return ret if isinstance(ret, list) else [ret]

    def access_clients(self):
        """
        Информация за клиентите на текущия потребител.
        """
        raise NotImplementedError

    def account_roles(self):
        """
        Информация за достъпа на служител.
        """
        raise NotImplementedError

    def cancel_shipment(self):
        raise NotImplementedError

    def check_cd_agreement(self):
        """
        Проверка на валидност за споразумение за наложен платеж.
        """
        raise NotImplementedError

    def cities(self, cities=None, updated_time=None):
        args = self._args(cities=cities, updated_time=updated_time)
        return self._shorthand('cities', args)

    # TODO: no cities?
    def cities_quarters(self, cities=None, updated_time=None):
        args = self._args(cities=cities, updated_time=updated_time)
        return self._shorthand('cities_quarters', args)

    # TODO: no cities?
    def cities_regions(self, cities=None, updated_time=None):
        args = self._args(cities=cities, updated_time=updated_time)
        return self._shorthand('cities_regions', args)

    # TODO: no cities?
    def cities_streets(self, cities=None, updated_time=None):
        args = self._args(cities=cities, updated_time=updated_time)
        return self._shorthand('cities_streets', args, key='cities_street')

    # TODO: This RPC method doesn't understand the `cities`
    # parameter? Remove it if so.
    def cities_zones(self, cities=None, updated_time=None):
        args = self._args(cities=cities, updated_time=updated_time)
        return self._shorthand('cities_zones', args, key='zones')

    # Suppress `used built-in function 'filter'`
    # pylint: disable=W0141
    def client_info(self, ein=None, egn=None, _id=None):
        not_none = lambda e: e[1] is not None
        arg_list = [('ein', ein), ('egn', egn), ('id', _id)]

        # filter the argument list (leave just the entries with non-null value)
        arg_list = filter(not_none, arg_list)

        f = lambda e: self._arg_patterns[e[0]].format(e[1])
        args = ''.join([f(e) for e in arg_list])

        return self._shorthand('client_info', args=args)

    def countries(self):
        return self._shorthand('countries', key='')

    def delivery_days(self, delivery_days=None):
        if delivery_days is None:
            delivery_days = datetime.date.today()
        args = self._args(delivery_days=delivery_days)
        response = self._shorthand('delivery_days', args=args)
        return map(
            lambda e: {
                'date': datetime.datetime.strptime(
                    e['date'], '%Y-%m-%d'
                ).date()
            },
            filter(lambda e: e and 'date' in e, response)
        )

    def offices(self, updated_time=None):
        return self._shorthand('offices', updated_time)

    def post_boxes(self):
        return self._shorthand('post_boxes')

    def profile(self):
        """
        Информация за профила на клиента с подадения акаунт.
        """
        raise NotImplementedError

    def registration_request(self):
        """
        Информация за заявките за регистрация в е-еконт.
        """
        raise NotImplementedError

    def shipments(self, sender_city, receiver_city, _id, full_tracking='ON'):
        """
        Информация за статуса на товарителници.
        """
        raise NotImplementedError

    def shipping(self, loadings, system):
        """Генериране на пратка в е-еконт, тарифиране на пощенска пратка.

        """
        # sender   --> подател за товарителницата
        # receiver --> получател
        # shipment --> информация за товарителницата
        default = {
            'sender' : {
                'city'               : '', # град на изпращача
                'post_code'          : '', # пощенски код
                'office_code'        : '', # офис код, ако се пр от офс
                'name'               : '', # име на фирма подател
                'name_person'        : '', # име на човек подател
                'quarter'            : '', # квартал
                'street'             : '', # улица
                'street_num'         : '', # уличен №
                'street_bl'          : '', # блок
                'street_vh'          : '', # вход
                'street_et'          : '', # етаж
                'street_ap'          : '', # № апартамент
                'street_other'       : '', # доп. информация
                'phone_num'          : ''  # телефонен номер
            },
            
            'receiver': {
                'city'               : '', # Абсолютно същото като
                'post_code'          : '', # за подателя
                'office_code'        : '',
                'name'               : '',
                'name_person'        : '',
                'receiver_email'     : '',
                'quarter'            : '',
                'street'             : '',
                'street_num'         : '',
                'street_bl'          : '',
                'street_vh'          : '',
                'street_et'          : '',
                'street_ap'          : '',
                'street_other'       : '',
                'phone_num'          : ''},
            
            'shipment': {
                'envelope_num'       : '', # номер опаковка?!
                
                # тип пратка, едно от следните:
                # PACK, DOCUMENT, PALLET, CARGO,
                # DOCUMENTPALLET
                'shipment_type'      : '',
                'description'        : '', # описание
                'pack_count'         : '', # брой пакети?!
                'weight'             : '', # тегло (В КИЛОГРАМИ)
                'tariff_code'        : '', # МИСТИКА!
                'tariff_sub_code'    : '', # DOOR_OFFICE, D_D, O_D, O_O
                'pay_after_accept'   : '', # плащане след получаване?
                'pay_after_test'     : '', # плащане след проба
                'delivery_day'       : ''  # ЗАГАДКА!
            },
            
            'payment': {
                
                # SENDER, RECEIVER, OTHER
                'side'               : '', # страна платец
                
                # CASH, CREDIT, BONUS, VOUCHER
                'method'             : '',
                
                # Сума за споделяне с получателя (ако е за
                # сметка на подателя)
                'receiver_share_sum' : '',
                
                # Процент за споделяне с получателя
                'share_percent'      : '',
                
                # Клиентски номер на платеца, само при плащане
                # на кредит
                'key_word'           : ''
            },
            
            'services': {
                # наложен платеж

                # Малко е безумен тоя начин за представяне на
                # атрибутите, честно казано... не помня вече какво съм
                # си мислил тогава и що така съм го оставил; пък и не
                # е добра абстракция на ХМЛ, FIXME :) По–добре би било
                # атрибутите да отиват в речници с този синтаксис:
                # таг__имеНаАтрибута = {...}
                'cd'                 : {'__content__': '',
                                        '__attrib__' : {'type': ''}},
                'cd_agreement_num'   : '', # споразумение за защита НП
                'cd_curreny'         : '', # валута
                'dc'                 : '', # обратна разписка
                'dc_cp'              : '', # стокова разписка
                'dp'                 : '', # двупосочна пратка
                'e'                  : '', # доставка същия ден
                'e1'                 : '', # доставка до  60 мин
                'e2'                 : '', # доставка до  90 мин
                'e3'                 : '', # доставка до 120 мин
                'oc'                 : '', # обявена стойност
                'oc_currency'        : '', # валута на `oc`
                'p'                  : '', # преоритет (ON/"")
                'pack1'              : '', # доп. опаковка (ON/"")
                'pack2'              : '',
                'pack3'              : '',
                'pack4'              : '',
                'pack5'              : '',
                'pack6'              : '',
                'pack7'              : '',
                'pack8'              : '',
                'ref'                : '', # хладилна чанта (ON/"")
            }
        }

        # Prepare <loadings>
        if not isinstance(loadings, Sequence):
            loadings = [loadings]

        rows = []
        for row in loadings:
            fusion = copy.deepcopy(default)
            fusion.update(row)
            rows.append(fusion)

        loadings_data = {'loadings': {'row': rows}}
        loadings_xml = xmlutils.dict2xml(loadings_data)

        # Prepare <system>
        system = system or {}
        system = system.get('system', system) # lolwut? :D
        system_data = {'system': system}
        system_xml = xmlutils.dict2xml(system_data)

        # Prepare and send XML data
        xml = self._SHIPPING.format(loadings=loadings_xml, system=system_xml)
        response_xml = self._send_xml_parcel(xml)

        # Parse and return the result
        return self._convert_xml_to_dict(response_xml)

    def tariff_courier(self):
        return self._shorthand('tariff_courier', key='service_types')

    def tariff_post(self):
        return self._shorthand('tariff_post', key='general_tariff')
