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
import subprocess as subproc
import os
import tiers.fs_interface.etc as etc


class Interface(etc.Interface):
    """Create and manage a RAMDisk"""
    def __init__(self, size: int, unit: str, mount_point: str) -> None:
        """Create the RAM disk and mount it"""
        if not os.path.exists(mount_point):
            etc.recursive_mkdir(mount_point)
        use_unit =""
        if unit.lower() in ("m", "mb", "mib", "megabytes"):
            use_unit = "m"
        elif unit.lower() in ("g", "gb", "gib", "gigabytes"):
            use_unit = "g"
        else:
            raise BufferError(f"Not a valid unit: {units}")
        self.unit = use_unit
        self.size = size
        self.drive = "pytierfs-ramdisk"
        # Do not index the drive, as it will be empty. No point.
        super().__init__(self.drive, mount_point, index=False)

    def calc_size(self):
        """Override getting size from kernel since we already know it.
           Just scale the size to whatever unit we want.
        """
        if self.unit.lower() in ("g", "gb", "gib", "gigabytes"):
            self.size = self.size * 1024
            self.unit = "m"

    def _mount(self):
        """Mount drive at mountpoint"""
        subproc.check_call(["mount", "-t" "tmpfs", "-o", f"size={self.size}{self.unit}",
                             "tmpfs", self.prefix])

    def _check_connected(self):
        """This just needs to always return None"""
        pass

