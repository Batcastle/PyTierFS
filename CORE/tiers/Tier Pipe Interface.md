# Tiering Pipe Interface
When starting up a tier, a program is expected to pass 3 data structures:

    - **Tier Settings**
        - This is the dictionary of settings for the given tier.
    - **Drive Settings**
        - This is the dictionary of settings for each given drive in a tier.
    - **Communication Pipe**
        - Processes are expected to pass a multiprocessing.Pipe object to provide communication with the parent process
        - This pipe is expected to be duplex.

The communication between the parent and child process is pretty simple to follow, as it follows a simple, structured format:

```
    ["COMMAND", "data1", "data2", data3, ...]
```

Available commands are as follows:

## STARTUP
### Aliased to: START, INIT
Pass ["START"], ["STARTUP"], or ["INIT"] to initialize the tier. This is NOT done automatically, in case tier start up needs to be staggered.

No data needs to be passed with this, and any passed will be ignored.

## GET_FILE_INFO
Get info on a file at a given path. This includes file size in bytes, UID, GID, and more.

The path to the file desired must be passed with this, otherwise a "TypeError" or "FileNotFoundError" will be raised.

## OPEN_FILE
Returns open file descriptor for requested file.

The path to the file desired must be passed with this, otherwise a "TypeError" or "FileNotFoundError" will be raised.

## COPY_FILE
Copies a file from one location to another

The source path and destination path must both be provided.

Example:

```
    ["COPY_FILE", <src_file>, <dest_file>]
```

## MOVE_FILE
Moves a file from one location to another

The source path and destination path must both be provided.

Example:

```
    ["MOVE_FILE", <src_file>, <dest_file>]
```


## MAKE_NEW_FILE
### Aliased to: NEW_FILE
Creates a new file at the provided location and returns an open file descriptor to allow for immediate usage of the file.

## DELETE_FILE
### Aliased to: REMOVE_FILE, REMOVE, DELETE
Permanently deletes the indicated file.

## EXISTS
This simply checks if a file exists. True if yes, False if no.

## SHUTDOWN
SHUTDOWN disconnects the tier's associated drives from the system, dumps the tier's master index, and clears the tier object. Resetting up the tier requires creating a new tier object. This command returns the tier's master index for saving to disk.

## DUMP_INDEX
Return's the tier's master index

## REFRESH_INDEX
Refresh the tier's master index

## APPLY_SAVED_INDEX
If a tier starts up with no index (like with a RAM Disk), apply an previously saved index, after files have been copied to the tier, externally.

## GET_DRIVE_NAMES
Get the names of all drives associated with a tier.
