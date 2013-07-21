# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from collections import Mapping
from xml.etree import ElementTree as etree

from django.utils import six


def etree2dict(root, d=None):
    """
    It's recursive...

    A quick primer:

    <a a1="1" a2="2" a3="3">
      something
      <b>another thing</b>
      <b>yet another thing</b>
      <c>forever alone</c>
    </a>

    converts to

    {'a': {u'__attrib__'  : {'a1': '1', 'a2': '2', 'a3': '3'},
           u'__content__' : 'something',
            'b'           : ['another thing', 'yet another thing'],
            'c'           : 'forever alone'}}

    """
    if d is None:
        d = {}

    # content
    text = root.text.strip() if root.text is not None else ''
    val = {'__content__': text} if text else {}

    # attributes
    if len(root.attrib) > 0:
        val['__attrib__'] = root.attrib.copy()

    for child in root:
        etree2dict(child, val)

    if len(val) == 0:
        val = ''
    elif len(val) == 1:
        val = val.get('__content__', val)

    if root.tag not in d:
        d[root.tag] = val
    else:
        if not isinstance(d[root.tag], list):
            d[root.tag] = [d[root.tag]]
        d[root.tag].append(val)

    return d


def xml2dict(xml, encoding='utf-8'):
    if not xml or not isinstance(xml, six.string_types):
        raise TypeError
    if isinstance(xml, six.text_type):
        xml = xml.encode(encoding)

    parser = etree.XMLParser(encoding=encoding)
    parser.feed(xml)
    root = parser.close()
    return etree2dict(root)


def dict2etree(d):
    """This MODIFIES the dictionary `d`.

    """
    if len(d) != 1:
        raise ValueError('One root to rule them all... please? {}'.format(d))

    def inner(d, root=None):
        for key in d:
            # TODO: is d[key] an instance of Sequence but not of basestring?
            if isinstance(d[key], list):
                for i in d[key]:
                    root = inner({key: i}, root)
                continue

            if root is None:
                el = root = etree.Element(key)
            else:
                el = etree.SubElement(root, key)

            if isinstance(d[key], six.string_types):
                el.text = d[key]

            elif isinstance(d[key], Mapping):
                el.attrib = d[key].pop('__attrib__', {}).copy()
                el.text = d[key].pop('__content__', '')
                inner(d[key], el)

            else:
                el.text = six.text_type(d[key])

        return root

    return inner(d)


def dict2xml(d, encoding='utf-8', response_encoding='utf-8'):
    root = dict2etree(d)
    xml = etree.tostring(root, encoding=encoding)
    xml = xml.decode(response_encoding)
    return xml
