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
import json
import os
import warnings
import psutil


class Settings():
    def __init__(self, settings_file="settings.json") -> dict:
        """Load settings"""
        self.default_settings = {
"DRIVES": {
        "RAMDISK": {
                    "mount_point": "/mnt/pytierfs/ramdisk", # mount at a slightly different location from the other drives, to prevent collisions
                    "size": round((psutil.virtual_memory().total / 2) / (1024 ** 2)), # allocate half of all memory to our RAM disk. This might be adjusted in the future
                    "units": "mb",
                    "nickname": "PyTierFS-RAMDISK",
                    "volatile": True # easy marker if something is a RAMDisk or RAMDisk-like object, without having to check names
                }
        },
"TIERS": {
        "global": {
                "dedup_internal": True, # Only keep one copy of each file per tier
                "dedup_external": False, # Allow copies of each file to exist on other tiers
                "use_root": False, # Do not use the root partition as a tier. This is done to avoid wear and tear on the root drive.
                "escalation_number": 20 # how many access points a file must have to be escalted to a higher tier
            },
        "by_tier": {
            "RAMDISK": {
                    "drives": ["RAMDISK"],
                    "tier_number": 99,
                    "available_space_file_limit": 25, # in megabytes, if a drive on this tier has this amount of space or less available on it, the tier will refuse to create a new file on it
                    "fill_method": "random", # Control whether a tier spreads files randomly across allocated drives, or puts them on the drive with the most free space first. Acceptable values are "random" and "largest_first". Default is "random"
                    "max_index_age": 300, # maximum number of seconds to go without refreshing a drive's index. If a drive has a file added, removed, copied, etc, it resets this timer.
                    "drop_time": 10800 # Seconds until files start losing access points, leading to them being dropped to lower tiers. Does not reset.
                }
        }
    },
"GUI": {},
"FTP": {},
"API": {},
"SMB": {},
"PARALLELIZATION": {
        # if True, use multiprocessing, if False, use threading
        "tiers": {
                "RAMDISK": True
            },
        "core": True,
        "api": False,
        "gui": False,
        "ftp": True
    },
"NETWORKING": {
        "FTP_PORTS": {
                "tcp": [21],
                "udp": []
                },
        "FTPS_PORT": {
                "tcp": [990],
                "udp": []
                },
        "API_PORTS": {
                "HTTP": {
                        "tcp": [80],
                        "udp": [80]
                    },
                "HTTPS": {
                        "tcp": [443],
                        "udp": [443]
                    }
            },
        "GUI_PORTS": {
                "HTTP": {
                        "tcp": [8080],
                        "udp": [8080]
                    },
                "HTTPS": {
                        "tcp": [8443],
                        "udp": [8443]
                    }
            },
        "SMB_PORTS": {
                "tcp": [445],
                "udp": []
            },
        "ALLOW_API_REMOTE_ACCESS": True
    }
}
        if not os.path.exists(settings_file):
            warnings.warn(f"Settings file {settings_file} not found. Making new one...", ResourceWarning)
            with open(settings_file, "w+") as file:
                json.dump(self.default_settings, file, indent=2)
        self.settings_file = settings_file
        with open(settings_file, "r") as file:
            self.settings = json.load(file)

    def get_drive_settings(self, drive: str) -> dict:
        """Return settings for a given drive"""
        if drive not in self.settings["DRIVES"]:
            raise KeyError(f"Drive {drive} is not configured.")
        return self.settings["DRIVES"][drive]

    def get_tier_settings(self, tier: str) -> dict:
        """Return settings for a given drive"""
        if tier not in self.settings["TIERS"]["by_tier"]:
            raise KeyError(f"Tier {tier} is not configured.")
        return self.settings["TIERS"]["by_tier"][tier]

    def get_tier_settings_global(self, key: str):
        if key not in self.settings["TIERS"]["global"]:
            raise KeyError(f"Global tier setting {key} is not available. Keys: { self.settings['TIERS']['global'].keys() }")
        return self.settings['TIERS']['global'][key]

    def set_drive_settings(self, drive: str, key: str, value) -> bool:
        """Set a setting for a drive

            True if successful, false if failed
        """
        if drive not in self.settings["DRIVES"]:
            return False
        if key.lower() not in self.settings["DRIVES"][drive]:
            return False
        if key.lower() == "mount_point":
            if not os.path.exists(value):
                return False
        if key.lower() == "nickname":
            if type(value) != str:
                return False
        if key.lower() == "tier":
            if type(value) not in (int, None):
                return False
        self.settings["DRIVES"][drive][key.lower()] = value
        return True

    def add_drive_to_settings(self, drive: str, reset=False) -> bool:
        """Add a drive with default settings

            If drive already exists, returns false and does not overwrite by default.
                set reset=True to override this. This will cause add_drive_to_settings()
                to overwrite old settings, and reset a drive to default settings. If successful,
                this returns True.

            Returns True if successful, else False.
        """
        default_settings = {
                "mount_point": f"/mnt/pytierfs/drive{ len(self.settings["DRIVES"]) }",
                "tier": None,
                "nickname": f"drive{ len(self.settings["DRIVES"]) }"
            }
        if drive in self.settings["DRIVES"] and not reset:
            return False
        if not os.path.exists(drive):
            return False
        self.settings["DRIVES"][drive] = default_settings
        try:
            self.write_settings_to_disk()
        except (PermissionError, IOError, FileNotFoundError):
            return False
        return True

    def write_settings_to_disk(self):
        """Write settings to disk"""
        with open(self.settings_file, "w") as file:
            json.dump(self.settings, file, indent=2)

