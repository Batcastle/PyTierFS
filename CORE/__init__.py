#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  __init__.py
#
#  Copyright 2024 Thomas Castleman <batcastle@draugeros.org>
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#
#
"""Setup interaction with each tier"""
import tiers
import multiprocessing as multiproc
import threading


def init(tier_settings: dict, drive_settings: dict, tier_multiproc_settings: dict) -> None:
    """Setup and run intra- and inter-tier processing thread(s)"""
    tiers = []
    for each in tier_settings:
        # If whether to use threads or procs has not been defined, use threads
        if each in tier_multiproc_settings:
            if tier_multiproc_settings[each]:
                # using procs
                pass
            else:
                # using threads
                pass

        else:
            pass

