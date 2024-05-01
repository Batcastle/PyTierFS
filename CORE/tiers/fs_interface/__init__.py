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
"""Set up for each different FS"""
import psutil
import os
import json
import subprocess as subproc


def init(drive: str, settings: dict):
    """Dynamically create FileSystem() class for given file systems"""
    if drive.lower() != "ramdisk":
        try:
            parts = json.loads(subproc.check_output(["lsblk", "--json", "--output", "fstype", drive]))
        except subproc.CalledProcessError:
            raise FileNotFoundError(f"Drive not found: {drive}")
        parts = parts["blockdevices"][0]
        if parts["fstype"].lower() == "ntfs":
            import tiers.fs_interface.ntfs as fs
        elif parts["fstype"].lower() == "ext4":
            import tiers.fs_interface.ext4 as fs
        elif parts["fstype"].lower() == "zfs":
            import tiers.fs_interface.zfs as fs
        else:
            import tiers.fs_interface.etc as fs
    else:
        import tiers.fs_interface.ramdisk as fs


    """
    All FS interface files need to have a class named "Interface"
    """
    class FileSystem(fs.Interface):
        """Filesystem interface class"""
        def __init__(self, settings: dict) -> None:
            """Initialize"""
            if settings["volatile"] or (settings["drive"].lower() == "ramdisk"):
                super().__init__(settings["size"], settings["units"], settings["mount_point"])
                self.is_ramdisk = True
            else:
                super().__init__(settings["drive"], settings["mount_point"])
                self.is_ramdisk = False


    settings["drive"] = drive
    return FileSystem(settings)
