#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2004-2013 Zuza Software Foundation
# Copyright 2013-2015 Evernote Corporation
#
# This file is part of Pootle.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, see <http://www.gnu.org/licenses/>.

import json

from functools import wraps
from importlib import import_module

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.http import HttpResponseBadRequest
from django.utils import timezone
from django.utils.encoding import force_unicode
from django.utils.functional import Promise

# Timezone aware minimum for datetime (if appropriate) (bug 2567)
from datetime import datetime, timedelta
datetime_min = datetime.min
if settings.USE_TZ:
    datetime_min = timezone.make_aware(datetime_min, timezone.utc)

from pootle.core.markup import Markup


def import_func(path):
    i = path.rfind('.')
    module, attr = path[:i], path[i+1:]
    try:
        mod = import_module(module)
    except ImportError, e:
        raise ImproperlyConfigured('Error importing module %s: "%s"'
                                   % (module, e))
    try:
        func = getattr(mod, attr)
    except AttributeError:
        raise ImproperlyConfigured(
            'Module "%s" does not define a "%s" callable function'
            % (module, attr))

    return func


def dictsum(x, y):
    return dict((n, x.get(n, 0)+y.get(n, 0)) for n in set(x) | set(y))


class PootleJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder for Pootle.

    This is mostly implemented to avoid calling `force_unicode` all the time on
    certain types of objects.
    https://docs.djangoproject.com/en/1.4/topics/serialization/#id2
    """
    def default(self, obj):
        if (isinstance(obj, Promise) or isinstance(obj, Markup) or
            isinstance(obj, datetime)):
            return force_unicode(obj)

        return super(PootleJSONEncoder, self).default(obj)


def jsonify(obj):
    """Serialize Python `obj` object into a JSON string."""
    if settings.DEBUG:
        indent = 4
    else:
        indent = None

    return json.dumps(obj, indent=indent, cls=PootleJSONEncoder)


def ajax_required(f):
    """Check that the request is an AJAX request.

    Use it in your views:

    @ajax_required
    def my_view(request):
        ....

    Taken from:
    http://djangosnippets.org/snippets/771/
    """
    @wraps(f)
    def wrapper(request, *args, **kwargs):
        if not settings.DEBUG and not request.is_ajax():
            return HttpResponseBadRequest("This must be an AJAX request.")
        return f(request, *args, **kwargs)

    return wrapper


def to_int(value):
    """Converts `value` to `int` and returns `None` if the conversion is
    not possible.
    """
    try:
        return int(value)
    except ValueError:
        return None


def get_max_month_datetime(dt):
    next_month = dt.replace(day=1) + timedelta(days=31)
    if settings.USE_TZ:
        tz = timezone.get_default_timezone()
        next_month = timezone.localtime(next_month, tz)

    return next_month.replace(day=1, hour=0, minute=0, second=0) - \
        timedelta(microseconds=1)


def get_date_interval(month):
    now = start = end = timezone.now()
    if month is None:
        month = start.strftime('%Y-%m')

    start = datetime.strptime(month, '%Y-%m')
    if settings.USE_TZ:
        tz = timezone.get_default_timezone()
        start = timezone.make_aware(start, tz)

    if start < now:
        if start.month != now.month or start.year != now.year:
            end = get_max_month_datetime(start)
    else:
        end = start

    start = start.replace(hour=0, minute=0, second=0)
    end = end.replace(hour=23, minute=59, second=59, microsecond=999999)

    return [start, end]
