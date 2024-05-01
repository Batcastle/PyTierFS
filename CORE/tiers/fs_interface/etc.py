#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  btr.py
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
"""File System Interface for miscilaneous other filesystems"""
import os
import subprocess as subproc
import copy
import magic
import shutil
import _io
import time

# TODO: Create function to check presence of file in index. Check for speed against os.path.exists()

def recursive_mkdir(path):
    """ Recursively make directories down a file path

    This function is functionally equivallent to: `mkdir -p {path}'
    """
    path = path.split("/")
    for each in enumerate(path):
        dir = "/".join(path[:each[0] + 1])
        # prevent calling mkdir() on an empty string
        if dir != "":
            try:
                os.mkdir(dir)
            except FileExistsError:
                pass

class Interface():
    """Interface for most file systems"""
    def __init__(self, drive: str, mountpoint: str, index=True):
        """Initialize file system"""
        # mount drive
        self.prefix = mountpoint
        self.drive = drive
        self._check_connected()
        self.made_mountpoint = False
        if not os.path.exists(mountpoint):
            recursive_mkdir(mountpoint)
            self.made_mountpoint = True
        if not os.path.isdir(mountpoint):
            raise FileNotFoundError(f"Directory {mountpoint} is actually a file.")
        self._mount()
        self.index = {}
        self.index_time = 0
        # if we already have an index to load, don't make a new one.
        if index:
            self.refresh_index()
        self.calc_size()

    def _check_connected(self) -> None:
        """Check the assigned drive is connected

        Throws IOError if not connected, exits with None if connected
        """
        if not os.path.exists(self.drive):
            raise IOError(f"{drive} is not connected.")

    def _mount(self):
        """Mount drive at mountpoint"""
        try:
            subproc.check_call(["mount", "-o", "rw,remount", drive, mountpoint])
        except subproc.CalledProcessError:
            subproc.check_call(["mount", drive, mountpoint])

    def get_index(self) -> dict:
        """Return index for the entire drive"""
        return copy.deepcopy(self.index)

    def refresh_index(self) -> None:
        """Refresh drive index. True if successful, false otherwise

        If a node is a file. it will have this structure:
            {
                "type": "file",
                "path": "path/to/obj/as/string"
            }

        for a directory:
            {
                "type": "dir",
                "path": "path/to/obj/as/string",
                "contents": {}
            }

        The key will be the file or folder name
        """
        def index_folder_single(path: str) -> dict:
            """Index a folder"""
            if os.path.isfile(path):
                return {"type": "file", "path": path}
            contents = os.walk(path)
            output = {}
            count = 0
            for each in contents:
                if count == 0:
                    for each1 in each[1]:
                        output[each1] = {"type": "dir"}
                        if path[-1] == "/":
                            output[each1]["path"] = path + each1
                        else:
                            output[each1]["path"] = path + "/" + each1
                        try:
                            stat = os.stat(output[each1]["path"])
                        except FileNotFoundError:
                            stat = [None] * 10
                        output[each1]["size"] = stat[6]
                        output[each1]["uid"] = stat[4]
                        output[each1]["gid"] = stat[5]
                        output[each1]["atime"] = stat[7]
                        output[each1]["mtime"] = stat[8]
                        output[each1]["ctime"] = stat[9]
                    for each1 in each[2]:
                        output[each1] = {"type": "file"}
                        if path[-1] == "/":
                            output[each1]["path"] = path + each1
                        else:
                            output[each1]["path"] = path + "/" + each1
                        try:
                            stat = os.stat(output[each1]["path"])
                        except FileNotFoundError:
                            stat = [None] * 10
                        output[each1]["size"] = stat[6]
                        output[each1]["uid"] = stat[4]
                        output[each1]["gid"] = stat[5]
                        output[each1]["atime"] = stat[7]
                        output[each1]["mtime"] = stat[8]
                        output[each1]["ctime"] = stat[9]
                        output[each1]["access_count"] = 0
                        try:
                            output[each1]["file_type"] = magic.from_file(output[each1]["path"], mime=True)
                        except OSError:
                            output[each1]["file_type"] = None
                    break
            return output


        def index(starter_index: dir) -> dir:
            for each in starter_index:
                if starter_index[each]["type"] == "dir":
                    starter_index[each]["contents"] = index_folder_single(starter_index[each]["path"])
            for each in starter_index:
                if starter_index[each]["type"] == "dir":
                    starter_index[each]["contents"] = index(starter_index[each]["contents"])
            return starter_index

        self.index = index_folder_single(self.prefix)
        self.index = index(self.index)
        self.index_time = time.time()


    def _get_relative_path(self, path):
        """Convert absolute to relative path"""
        if self.prefix != path[:len(self.prefix)]:
            if path[0] == "/":
                return path[1:]
            return path
        return path[(len(self.prefix) + 1):]


    def get_node(self, location):
        """Get info about location"""
        new_loc = self._get_relative_path(location)
        folder_list = new_loc.split("/")
        current_dict = copy.deepcopy(self.index)
        count = 1
        for folder in folder_list:
            if folder in current_dict:
                if count < len(folder_list):
                    if "contents" in current_dict[folder].keys():
                        current_dict = current_dict[folder]["contents"]
                    else:
                        raise FileNotFoundError(f"File {location} does not exist")
                else:
                    return current_dict[folder]
            else:
                raise FileNotFoundError(f"File {location} does not exist")
            count += 1


    def _set_index(self, index: dict):
        """Manually apply an index"""
        # check index before applying. Throw error if something wrong
        self.index = copy.deepcopy(index)

    def open_file(self, file_path: str) -> _io.TextIOWrapper:
        """Open a file for reading/writing to"""
        new_loc = self._get_relative_path(file_path)
        if not self.check_file_exists(new_loc):
            raise FileNotFoundError(f"File {new_loc} does not exist.")
        self.get_node(file_path)["access_count"] += 1
        return open(new_loc, "b+")

    def delete_file(self, file_path: str) -> None:
        """Delete a file"""
        new_loc = self._get_relative_path(file_path)
        if not self.check_file_exists(new_loc):
            raise FileNotFoundError(f"File {file_path} does not exist.")
        os.remove(file_path)

        # we now need to remove the node from the index
        # Get parent index
        new_path = "/".join(new_loc.split("/")[:-1])
        parent_node = self.get_node(new_path)
        file_name = new_loc.split("/")[-1]

        # Due to Python's pass-by-refrence nature, parent_node points to the location of file_name's parent in the index
        # If you delete this pointer, it only deletes the pointer, nothing below it. Like how a symbolic link works.
        # However, you can easily go inside the parent node and delete things from the index from there.
        del parent_node[file_name]
        self.index_time = time.time()

    def _create_new_node(self, file_path: str) -> None:
        """Create a new node in the index"""
        # we now need to remove the node from the index
        # Get parent index
        new_path = "/".join(new_loc.split("/")[:-1])
        parent_node = self.get_node(new_path)
        file_name = new_loc.split("/")[-1]
        parent_node[file_name] = {"path": file_path}
        try:
            os.listdir(file_path)
            parent_node[file_name]["type"] = "dir"
        except NotADirectoryError:
            parent_node[file_name]["type"] = "file"
            parent_node[file_name]["file_type"] = magic.from_file(file_path, mime=True)
        try:
            stat = os.stat(output[each1]["path"])
        except FileNotFoundError:
            stat = [None] * 10
        parent_node[file_name]["uid"] = stat[4]
        parent_node[file_name]["gid"] = stat[5]
        parent_node[file_name]["atime"] = stat[7]
        parent_node[file_name]["mtime"] = stat[8]
        parent_node[file_name]["ctime"] = stat[9]
        parent_node[file_name]["access_count"] = 0

        # new node created. Update self.index_time
        self.index_time = time.time()

    def make_new_file(self, file_path: str) -> _io.TextIOWrapper:
        """Create a new file"""
        new_loc = self._get_relative_path(file_path)
        self._create_new_node(file_path)
        return open(new_loc, "xb")

    def copy_file(self, source_path: str, dest_path: str):
        """Copy a file from one place to another"""
        source = self._get_relative_path(source_path)
        dest = self._get_relative_path(dest_path)
        if not self.check_file_exists(source):
            raise FileNotFoundError(f"File {source} does not exist.")
        # copy file
        try:
            shutil.copy(source, dest)
        except PermissionError:
            return False
        self._create_new_node(dest_path)
        return True

    def move_file(self, source_path: str, dest_path: str):
        """Move a file from one place to another"""
        if self.copy_file(source_path, dest_path):
            self.get_node(dest_path)["access_count"] = self.get_node(source_path)["access_count"] + 1
            self.delete_file(source_path)
        else:
            raise OSError(f"An error has occured moving file {source_path} to {dest_path}. Keeping original.")

    def check_file_exists(self, file_path: str) -> bool:
        """Check file exists on disk"""
        # This is here to provide a faster function for this later on
        # we can't use os.path.exists() for this, in case there is a false positive
        try:
            self.get_node(file_path)
            return True
        except FileNotFoundError:
            return False

    def detach(self):
        """Unmount drive and remove mountpoint if necessary"""
        try:
            subproc.check_call(["umount", self.prefix])
        except CalledProcessError:
            subproc.check_call(["umount", "-l", self.prefix])
        if self.made_mountpoint:
            os.rmdir(self.prefix)
        del self

    def get_size(self):
        """Get size of drive"""
        try:
            return self.size
        except UnboundLocalError:
            self.calc_size()
            return self.size

    def calc_size(self):
        """Calculate size of device"""
        size = json.loads(subproc.check_output(["lsblk", "--json", "--bytes", "--output", "fsize"]))["blockdevices"]["size"]
        self.size = size / 1024**2
        self.units = "m"

    def get_used(self):
        """Get amount of drive used"""
        size = json.loads(subproc.check_output(["lsblk", "--json", "--bytes", "--output", "fsused"]))["blockdevices"]["size"]
        return size / 1024**2

    def get_free(self):
        """Get amount of free space on drive"""
        return self.size - self.get_used()

    def drop_access_points(self):
        """Drop access points on everything by 1"""
        def get_files(data):
            files = []

            def _traverse(node):
                if "contents" in node:
                    for each in node["contents"]:
                        if each["type"] == "file":  # If it's an empty dict, it's a file
                            files.append(each)
                        else:
                            _traverse(each)

            _traverse(data)
            return files

        files = get_files(self.drives)
        for each in files:
            each["access_count"] -= 1



