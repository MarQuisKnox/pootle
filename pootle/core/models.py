#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2013-2015 Evernote Corporation
#
# This file is part of Pootle.
#
# Pootle is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# translate is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with translate; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA


from .cache import get_cache
from .mixins import TreeItem


cache = get_cache('redis')


class Revision(object):
    """Wrapper around the revision counter stored in Redis."""

    CACHE_KEY = 'pootle:revision'
    INITIAL = 0

    @classmethod
    def initialize(cls, force=False):
        """Initializes the revision with `cls.INITIAL`.

        :param force: whether to overwrite the number if there's a
            revision already set or not.
        :return: `True` if the initial value was set, `False` otherwise.
        """
        if force:
            return cls.set(cls.INITIAL)

        return cls.add(cls.INITIAL)

    @classmethod
    def get(cls):
        """Gets the current revision number.

        :return: The current revision number, or the initial number if
            there's no revision stored yet.
        """
        return cache.get(cls.CACHE_KEY, cls.INITIAL)

    @classmethod
    def set(cls, value):
        """Sets the revision number to `value`, regardless of whether
        there's a value previously set or not.

        :return: `True` if the value was set, `False` otherwise.
        """
        return cache.set(cls.CACHE_KEY, value)

    @classmethod
    def add(cls, value):
        """Sets the revision number to `value`, only if there's no
        revision already set.

        :return: `True` if the value was set, `False` otherwise.
        """
        return cache.add(cls.CACHE_KEY, value)

    @classmethod
    def incr(cls):
        """Increments the revision number.

        :return: the new revision number after incrementing it, or the
            initial number if there's no revision stored yet.
        """
        try:
            return cache.incr(cls.CACHE_KEY)
        except ValueError:
            return cls.INITIAL


class VirtualResource(TreeItem):
    """An object representing a virtual resource.

    A virtual resource doesn't live in the DB and has a unique
    `pootle_path` of its own. It's a simple collection of actual
    resources.

    For instance, this can be used in projects to have cross-language
    references.

    Don't use this object as-is, rather subclass it and adapt the
    implementation details for each context.
    """
    def __init__(self, resources, pootle_path, *args, **kwargs):
        self.resources = resources  #: Collection of underlying resources
        self.pootle_path = pootle_path

        super(VirtualResource, self).__init__(*args, **kwargs)

    def __unicode__(self):
        return self.pootle_path

    ### TreeItem

    def get_children(self):
        return self.resources

    def get_cachekey(self):
        return self.pootle_path

    ### /TreeItem
