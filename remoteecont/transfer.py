# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import pycurl

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO


class Transfer(object):
    """
    Basic interface for transferring and exchanging data with a remote
    service.
    """

    def append_file(self, name, filepath, content_type, filename):
        raise NotImplementedError()

    def append_data(self, name, value):
        raise NotImplementedError()

    def append_str_as_file(self, name, content, content_type=None, filename=None):
        raise NotImplementedError()

    def perform(self, url):
        raise NotImplementedError

    def close(self):
        raise NotImplementedError


class CurlTransfer(Transfer):

    def __init__(self):
        self._curl = pycurl.Curl()
        self._data = []

    # Suppress `used built-in function 'map'`
    # pylint: disable=W0141
    def _prepare_data(self, data):
        """
        Simple method that converts all unicode strings in a nested
        sequence structure to byte strings.
        """
        if isinstance(data, list):
            return map(self._prepare_data, data)
        elif isinstance(data, tuple):
            return tuple(map(self._prepare_data, data))
        elif isinstance(data, unicode):
            return data.encode('utf-8')
        else:
            return data

    def append_file(self, name, filepath, content_type, filename):
        raise NotImplementedError()

    def append_data(self, name, value):
        self._data.append((name, (pycurl.FORM_CONTENTS, value)))

    def append_str_as_file(self, name, content,
                           content_type='text/plain; charset=UTF-8',
                           filename=None):
        if filename is None:
            filename = '%s.txt' % name

        t = ('{}"; filename="{}'.format(name, filename),
             (pycurl.FORM_CONTENTS, content,
              pycurl.FORM_CONTENTTYPE, content_type))

        self._data.append(t)

    def perform(self, url):
        """
        Perform a request.  Argument `url` should be a byte string.
        """
        out = StringIO()

        # self._curl.setopt(pycurl.HTTPHEADER, ['Expect:'])
        # self._curl.setopt(pycurl.VERBOSE, 1)

        self._curl.setopt(pycurl.URL, url)
        self._curl.setopt(pycurl.HTTPPOST, self._prepare_data(self._data))
        self._curl.setopt(pycurl.WRITEFUNCTION, out.write)

        self._curl.perform()
        return out.getvalue()

    def close(self):
        self._curl.close()
