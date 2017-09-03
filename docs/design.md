# Chews Design

## Objective

Chews is a tool for managing the life cycle of cloud workstations.

By _workstation_, we mean a virtual machine intended to be switched on
and off rather than to be continually running as a server.

## Design Decisions

### Snapshots

The life cycle of the cloud workstation will involve a state where the
persistent data is stored in snapshots rather than in virtual block
devices.  Snapshots are smaller (because they only store allocated
blocks) and are also cheaper per GB.  This saves money when the
workstation is not being used.

### Metadata (workstation state)

The tool will need to determine which state the workstation is in,
e.g. powered on, powered off (but block devices available), block
device data only present in snapshots.  Rather than maintaining a
database (or other stateful store) of this metadata, the
implementation will query the metadata about the cloud assets (such as
virtual machine, block devices and snapshots).  This requires
inferring workstation state from state of these various cloud assets
but makes it simpler to install and use the tools.

### Metadata (workstation configuration)

The workstation configuration (e.g. virtual machine size and number of
disks) will be stored in a structured text-format file.  This
configuration file is intended to be editable by hand (possibly with
some machine-assistance) and simple to store, possibly in a version
control system.

## Detailed Design

### Workstation states

A workstation will be implemented using three forms of cloud assets:
Virtual Machine Instance, Block Devices and Snapshots.  There will be
three normal states for the workstation: ON, OFF and DESSICATED.

Summarising:

   - ON: Workstation is usable, e.g. via ssh or RDP.
   - OFF: Workstation is not usable but can quickly be transitioned to
     ON.
   - DESSICATED: Workstation is not usable.  Block device data exist
     but cannot be directly accessed.  Workstation can be transitioned
     to either OFF or ON states but may require some time to rebuild
     the block devices and virtual machine instance.

The following table explains the expected mapping of workstation
states to cloud asset states.

| State      | VM Instance        | Block Devices | Snapshots |
| ---------- | ------------------ | ------------- | --------- |
| ON         | Exists and running | Exist         | May exist |
| OFF        | Exists but stoped  | Exist         | May exist |
| DESSICATED | Absent             | Absent        | Exist     |
| NOT_EXIST  | Absent             | Absent        | Absent    |

The NOT_EXIST state is no a normal state but describes the state
before the workstation is created or after it is deleted.

### Asset names

Since the workstation state is distributed over state of different
cloud assets, we need consider how they will be associated with each
other.  The implementation will use naming conventions to tie the
assets together.

Name collisions would be bad: not only would it cause problems
creating the cloud asset but there is the risk that the we may
unintentionally interfere with other cloud assets.  To minimise name
collisions, the implementation inserts hashes into the names of block
devices and snapshots.

Specifically:

   - VM instance will take the same name as the workstation.

   - Each block device will have a name scoped to within the
     workstation, e.g. `boot` or `data`.  The block devices are named
     by concatenating the workstation name, block device name and a
     hash.  E.g. `test-boot-4474c5969e0202f87ccf9e5481a3f43c` could be
     the name of disk `boot` for workstation `test`.

   - Snapshot names will be derived from the disk name and a
     timestamp.  We format the timestamp so that a lexicographical
     ordering of snapshot names is in timestamp order.
     E.g. `ss-test-boot-4474c5969e0202f87ccf9e5481a3f43c-20170901232047`
     could be the name of a snapshot for disk `boot` for workstation
     `test`.

## Use Cases

Here are a list of use cases and an description of what the workflow
might look like.

### Create a new workstation

Status: IMPLEMENTED

   1. Edit configuration file and define a new workstation, specifying
      the workstation name, size, its disks and a location for where it
      should be created.
   2. Run command to create the workstation.
   3. Connect to the workstation (e.g. via ssh or RDP) and configure
      the workstation, e.g. format disks and install apps.

Workstation end state: ON

### Power down

Status: IMPLEMENTED

After using the workstation, it is time to go to the pub.  The
workstation will not be used until the next day.  We can save some
money by not paying for a running VM Instance while drinking.

The workstation can be powered down by shutting down the VM Instance.
This can be done either via the OS or by running a command.

Workstation end state: OFF

### Power up

Status: IMPLEMENTED

It is the next day.  The hangover from drinking in the pub is not too
bad.  It is time to use the workstation again.  The workstation is
powered up by starting the VM Instance.

Workstation end state: ON

### Dessicate

Status: IMPLEMENTED

It is time to go on vacation.  The workstation will not be used for
weeks.  We can save some money by not paying for the virtual block
devices and instead move their data into snapshots.

Run a command to transitions the workstation from OFF to DESSICATED.
This is achieved by snapshotting all block devices.  Once snapshotted,
the block devices are deleted.  The VM Instance is deleted.

Workstation end state: DESSICATED

### Rehydrate

Status: IMPLEMENTED

Back from vacation, it is time to use the workstation again.

Run a command to transition the workstation from DESSICATED to OFF (or
ON).  This is achieved by creating new block devices from the most
recent snapshots and then creating a new VM Instance using the newly
created block devices.

Workstation end state: OFF (or ON)

### Migrate a workstation

There already exists a workstation with persistent disks but the
assets do not follow the naming conventions.

   1. Stop existing workstation.
   2. Run migration command to generate a configuration for an
      equivalent workstation.
   3. Run migration command to snapshot disks on existing workstation
      to snapshots using names consistent with the new workstation and
      delete VM instance.  At this point, the new workstation is in
      state DESSICATED.
   4. Rehydrate workstation.
   5. [Optional] Delete original workstation disks.

### VM Instance Resize

Status: IMPLEMENTED

The VM Instance does not have enough memory or cpu cores.
(Alternatively, the VM Instance has surplus memory or cpu cores and
costs too much.)

   1. Edit configuration file to change the workstation size.
   2. Power down the workstation.
   3. Run a command to delete the VM Instance and create a new VM
      Instance of the new workstation size

Editing the configuration file is required so that the workstation is
created with the correct size on Rehydration.

### Change a disk type

Status: IMPLEMENTED

A disk is currently an HDD-backed block device.  Changing it to an
SSD-backed block device would improve performance.  (Similarly,
changing an SSD-backed block device to an HDD-backed block device
would save money.)

   1. Edit configuration file to change the disk type.
   2. Dessicate the workstation.
   3. Rehydrate the workstation.

### Add extra disks to workstation

The VM Instance does not have enough disks.

   1. Edit configuration file to add extra disks
   2. Run a command to create the new disks.
   3. Connect to the workstation and use its OS to configure the new
      disks.

Editing the configuration is required to make sure that the new disks
are managed.

### Change the size of a disk

   1. [Shrink only] Use the OS to shrink filesystem and partitions on
      the disk to be made smaller.
   2. Edit configuration file and change disks size
   3. Run command to Dessicate workstation.
   4. Run command to Rehydrate workstation.
   5. [Grow only] Use the OS to expand the partitions and filesystem
      to use the extra space on the disk.

### Recover from inconsistent state

The last run of a command was interrupted.  The assets are in states that
are inconsistent with any normal state for the workstation.

There should be an easy way to recover.