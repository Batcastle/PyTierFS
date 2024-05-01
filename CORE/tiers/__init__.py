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
import tiers.fs_interface as fs_int
import threading
import queue
import _io
import random as rand
import time

def multicall_threader(*args, func=None, que=None, ignore_errors=False, **kwargs):
    """Call the given function, with the given arguments.

    If queue is not None, return data back up the queue once the function exits.
    """
    if ignore_errors:
        try:
            output = func(*args, **kwargs)
        except as e:
            output = None
            print("Error occured on drive thread.")
            print(e)
    else:
        output = func(*args, **kwargs)
    if None not in (que, output):
        que.put(output)


class Tier():
    """Creation, handling, and destruction of tiers"""
    def __init__(self, tier_settings: dict, drive_settings: dict) -> None:
        """Setup a storage tier"""
        self.drives = {}
        for each in drive_settings:
            self.drives[drive_settings[each]["nickname"]] = fs_int.init(each, drive_settings[each])

        self.tier_settings - tier_settings

    def index(self) -> None:
        """Index all drives"""
        if len(self.drives) > 1:
            self.multithreader("refresh_index")
        self.drives[self.drives.keys()[0]].refresh_index()

    def get_drive_names(self):
        """Get drive names"""
        return self.drives.keys()

    def apply_index(self, index) -> bool:
        """Apply previously saved index"""
        for each in self.drives:
            if each in index.keys():
                self.drives[each]._set_index(index[each])

    def file_exists(self, file_path: str) -> bool:
        """Check if a file exists in this tier"""
        if len(self.drives) > 1:
            return self.multithreader("check_file_exists", file_path)
        return self.drives[self.drives.keys()[0]].check_file_exists(file_path)

    def open_file(self, file_path: str) -> _io.TextIOWrapper:
        """Return file stream object for editing"""
        if len(self.drives) > 1:
            return self.multithreader("open_file", file_path, ignore_errors=True)
        try:
            return self.drives[self.drives.keys()[0]].open_file(file_path)
        except FileNotFoundError:
            return None

    def remove_file(self, file_path: str) -> bool:
        """Delete file"""
        if len(self.drives) > 1:
            return self.multithreader("delete_file", file_path, ignore_errors=True)
        try:
            return self.drives[self.drives.keys()[0]].delete_file(file_path)
        except FileNotFoundError:
            return None

    def move_file(self, src_path: str, dest_path: src) -> bool:
        """Move file"""
        self.copy_file(src_path, dest_path)
        self.remove_file(src_path)

    def copy_file(self, src_path: str, dest_path: src) -> bool:
        """Copy file"""
        # Handle a single drive
        if len(self.drives) == 1:
            if self.drives[self.drives.keys()[0]].get_free() > self.drives[self.drives.keys()[0]].get_node(src_path)["size"]:
                return self.drives[self.drives.keys()[0]].copy_file(src_path, dest_path)
            raise OSError(f"{self.self.drives.keys()[0]} has no space left.")
        # Handling multiple drives
        # First, see which drives have the file on it, so we can get info about that file.
        resident_drives = []
        for each in self.drives:
            if self.drives[each].check_file_exists(src_path):
                resident_drives.append(each)
        if len(resident_drives) == 0:
            raise FileNotFoundError(f"File {src_path} does not exist on this tier.")
        file_info = self.drives[resident_drives[0]].get_node(src_path)
        # Second, see if ANY drives have enough space for a new file. If not, just throw an error
        allowed_drives = []
        for each in self.drives:
            if self.drives[each].get_free() > file_info["size"]:
                allowed_drives.append(each)
        if len(allowed_drives) == 0:
            raise OSError("No drives with enough space available on this tier.")
        # Below here, we know all drives in allowed_drives have enough space.
        # Check if allowed_drives and resident_drives have ANY drives that are the same. If they do, we can copy the drive on a single
        # drive, which will be faster that moving it between drives.
        copied = False
        for each in resident_drives:
            for each1 in allowed_drives:
                if each == each1:
                    # We have a drive with both the file, and enough space for a copy
                    return self.drives[each].copy_file(src_path, dest_path)
        # There are no drives with both the file, and enough space copy to another drive
        if self.tier_settings["fill_method"] == "largest_first":
            space_amounts = {}
            for each in allowed_drives:
                space_amounts[each] = self.drives[each].get_free()
            # we have the amount of free space on all the drives, now need to find out which has the most
            most = ["", 0]
            for each in space_amounts:
                if space_amounts[each] > most[1]:
                    most = [each, space_amounts[each]]
            # We have the drive we want. Now to set the necessary variable
            selected_drive = most[0]
        elif self.tier_settings["fill_method"] == "random":
            selected_drive = rand.sample(allowed_drives, 1)[0]
        else:
            print(f"Setting {self.tier_settings['fill_method']} not understood for 'fill_method', defaulting to random.")
            selected_drive = rand.sample(allowed_drives, 1)[0]
        src_stream = self.drive[resident_drives[0]].open_file(src_path)
        dest_stream = self.drive[selected_drive].make_new_file(dest_path)
        dest_stream.write(src_stream.read())
        dest_stream.close()
        src_stream.close()
        return True

    def get_file_info(self, path) -> dict:
        """Copy file"""
        if len(self.drives) > 1:
            return self.multithreader("get_node", path, ignore_errors=True)
        try:
            return self.drives[self.drives.keys()[0]].get_node(path)
        except FileNotFoundError:
            return None

    def make_new_file(self, path: str) ->_io.TextIOWrapper:
        """Make a new file on a random drive on this tier"""
        if len(self.drives) > 1:
            if self.drives[self.drives.keys()[0]].get_used() > self.tier_settings["available_space_file_limit"]:
                return self.drives[self.drives.keys()[0]].make_new_file(path)
            raise OSError(f"{self.self.drives.keys()[0]} has no space left.")
        # Drives with enough space on them for the new file
        allowed_drives = []
        for each in self.drives:
            if self.drives[each].get_used() > self.tier_settings["available_space_file_limit"]:
                allowed_drives.append(each)
        if len(allowed_drives) == 0:
            raise OSError("No drives with enough space available on this tier.")
        lucky_drive = rand.sample(allowed_drives, 1)[0]
        return self.drives[lucky_drive].make_new_file(path)


    def dump_index(self) -> dict:
        """Dump master index"""
        master_index = {}
        for each in self.drives:
            master_index[each] = self.drives[each].get_index()
            self.drives[each].detach()
        return master_index

    def shut_down(self) -> dict:
        """Detatch all drives, dumping their indexs"""
        master_index = self.dump_index()
        del self
        return master_index

    def multithreader(self, func, *args, use_queue=True, **kwargs):
        """Arbirtary multithreading function"""
        threads = {}
        for each in self.drives:
            function = getattr(self.drives[each], func)
            if use_queue:
                que = queue.Queue()
                threads[each] = [threading.Thread(target=multicall_threader,
                                                  args=(*args,),
                                                  kwargs=dict({"func": function,
                                                               "que": que}, **kwargs)),
                                 que]
            else:
                threads[each] = [threading.Thread(target=multicall_threader,
                                                  args=(*args,),
                                                  kwargs=dict({"func": function}, **kwargs))]
            threads[each][0].start()
        for each in threads:
            if not threads[each][0].is_alive():
                threads[each][0].join()
        if use_queue():
            for each in threads:
                if not threads[each][1].empty():
                    return threads[each][1].get()

    def get_index_ages(self):
        """Get ages of all drive indexs"""
        output ={}
        for each in self.drives:
            output[each] = self.drives[each].index_time
        return output

    def drop_access_points(self):
        """Drop access points on all files in all drives"""
        if len(self.drives) > 1:
            return self.multithreader("drop_access_points", use_queue=False)
        return self.drives[self.drives.keys()[0]].drop_access_points()


def manage_tier(tier_settings: dict, drive_settings: dict, pipe) -> None:
    """This function is meant to be run as it's own process it will not usually exit unless it receives
       a command to do so in the pipe
    """
    tier_obj = None
    prev_drop_time = 0
    while True:
        if not pipe.poll():
            # Refresh indexes if needed
            index_times = tier_obj.get_index_ages()
            cur = time.time()
            threads = []
            for each in index_times:
                if (cur - index_times[each]) >= tier_settings["max_index_age"]:
                    threads.append(threading.Thread(target=tier_obj.drives[each].refresh_index))
                    threads[-1].start()
            for each in threads:
                if not threads[each].is_alive():
                    threads[each].join()

            # Check if access points need to be dropped
            if (time.time() - prev_drop_time) >= tier_settings["drop_time"]:
                # Drop access points
            if (time.time() - cur) < 0.005:
                time.sleep(0.005)
            continue
        command = pipe.recv()
        if command[0].upper() == "GET_FILE_INFO":
            pipe.send(tier_obj.get_file_info(command[1]))
        elif command[0].upper() == "OPEN_FILE":
            pipe.send(tier_obj.open_file(command[1]))
        elif command[0].upper() == "COPY_FILE":
            pipe.send(tier_obj.copy_file(command[1][0], command[1][1]))
        elif command[0].upper() == "MOVE_FILE":
            pipe.send(tier_obj.move_file(command[1][0], command[1][1]))
        elif command[0].upper() == "DELETE_FILE":
            try:
                tier_obj.remove_file(command[1])
            except FileNotFoundError:
                pipe.send({"ERROR": "FILE_NOT_FOUND"})
        elif command[0].upper() == "EXISTS":
            pipe.send(tier_obj.check_file_exists(command[1]))
        elif command[0].upper() == "SHUTDOWN":
            index = tier_obj.shut_down()
            pipe.send(index)
            pipe.send({"SHUTDOWN": True})
            break
        elif command[0].upper() == "DUMP_INDEX":
            index = tier_obj.dump_index()
            pipe.send(index)
        elif command[0].upper() == "REFRESH_INDEX":
            pipe.send(tier_obj.index())
        elif command[0].upper() == "APPLY_SAVED_INDEX":
            pipe.send(tier_obj.apply_index(command[1]))
        elif command[0].upper() == "GET_DRIVE_NAMES":
            pipe.send({"DRIVE_NAMES": tier_obj.get_drive_names()})
        elif command[0].upper() == "STARTUP":
            tier_obj = Tier(tier_settings, drive_settings)
            pipe.send(True)
        else:
            pipe.send({"ERROR": "COMMAND_NOT_RECOGNIZED"})
