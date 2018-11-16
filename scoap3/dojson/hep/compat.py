"""Compatibility module for Python 2 and 3.
The code is inspired by ``six`` library and cheat sheet from
`http://python-future.org/compatible_idioms.html`_
"""

import sys

PY2 = sys.version_info[0] == 2
PY3 = sys.version_info[0] == 3

if PY3:
    import io

    StringIO = io.StringIO
    BytesIO = io.BytesIO

    binary_type = bytes
    string_types = str,
    text_type = str

    def iteritems(d, **kw):
        """Return iterator with dict items."""
        return iter(d.items(**kw))


    from itertools import zip_longest  # noqa
else:
    import StringIO

    StringIO = BytesIO = StringIO.StringIO

    binary_type = str
    string_types = basestring,
    text_type = unicode

    def iteritems(d, **kw):
        """Return iterator with dict items."""
        return iter(d.iteritems(**kw))


    from itertools import izip_longest as zip_longest  # noqa
