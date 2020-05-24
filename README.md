# chews: Cheap Workstation

## Objective

Chews is a tool for managing the life cycle of cloud workstations.

By _workstation_, we mean a virtual machine intended to be switched on
and off rather than to be continually running as a server.

See [Design](docs/design.md).

Chews [originally had a more ambitious
objective](docs/original_objective.md) which is currently infeasible.

Before, the use case was analogous to the Zipcar of workstations: rather than
own your own workstation, you rent one whenever you need one.

Now, the use case is analogous to the U-Haul of workstations: you own
your own physical workstation, but when you need something different
for a specific purpose (e.g. more ram, cpu cores or a different OS),
you rent it.

## Usage

The scripts currently support maintaining the cloud workstation life
cycle on Google Compute Platform (GCP).

At the moment, it only supports [Application Default
Credentials](https://developers.google.com/identity/protocols/application-default-credentials).
Since the scripts will modify GCE assets, this means that you have to
either run the scripts on a Google Compute Engine (GCE) VM Instance
using a service account with read/write permissions to Compute Engine,
or you can use the Google Cloud Shell which already has the correct
permissions.

WARNING: There are some very rough edges!

### Setting up GCP

Go to the [GCP Console](http://console.cloud.google.com).

Either select an existing Project or create a new one.  Pick (and
remember) the globally unique project ID for your project.  Assign
this project ID to shell variable `${MY_PROJECT}`.

Make sure GCE is enabled for your project by using the [Compute Engine
Console](https://console.cloud.google.com/compute).  Note that you
will have to provide payment details (such as a credit card), even if
you sign up for and intend to only use the free trial.

### Setting up Chews

Start Google Cloud Shell using the icon in the top right of the GCP Console.

Install chews:

    git clone https://github.com/fhltang/chews.git
    cd chews
    docker build -t chews .

Now set up a convenience alias:

    CONFIG=configs/test.config
    alias chews="docker run -it chews --config_file ${CONFIG} --project ${MY_PROJECT?}"

This will build a `docker` image. To verify that this was successful, print the
test config:

    chews printconfig

The config files must be in the container so to use your own config, you will need
to bind mount a volume e.g. by passing the `-v` argument to `docker run`.

### Create a cloud workstation

We can reuse the example workstations in the config file in `configs/test.config`.

To create the Debian workstation:

    chews create test

In the current implementation, the workstation is in state ON after
creation.

Once the `create` command completes, the workstation is created.  You
can ssh into workstation using the normal GCE methods.  For example,
from the [VM instances
console](https://console.cloud.google.com/compute/instances) you can
find the VM instance and connect using the SSH option, or you can use
the `gcloud` command

    gcloud compute ssh test

On initial creation, you will have to set up the workstation,
e.g. format and mount any extra disks.

### Using the cloud workstation

#### Checking workstation state

You can check the state of the workstation using the `printassets` command:

    $ chews printassets
    Workstation test
      State CwsState.ON
      Volume test-boot-b1821a
      Volume test-data-230eeb
    Workstation win-test
      State CwsState.NOT_EXIST
      Volume win-test-boot-bc9a92
      Volume win-test-data-53d695

#### Switching off the workstation

The easiest way to switch off the workstation is from the OS on the VM
instance itself.

Alternatively, you can use the `powerdown` command:

    chews powerdown test

Confirm status

    $ chews printassets
    Workstation test
      State CwsState.OFF
      Volume test-boot-b1821a
      Volume test-data-230eeb
    Workstation win-test
      State CwsState.NOT_EXIST
      Volume win-test-boot-bc9a92
      Volume win-test-data-53d695

#### Switching on the workstation

If the workstation is in state OFF, you can switch it on using the
`powerup` command:

    chews powerup test

Alternatively, you can just find and start the VM instance using the GCP console.

#### Dessicating the workstation

If you do not intend to use the workstation for a while, you can
Dessicate it.  This will reduce the hourly cost of the workstation
preserving the contents of the block devices in snapshots (which are
cost less per GB-month and you are charged only for the used blocks on
the disks) and delete the VM instance and its block devices.

To dessicate, the workstation has to be in state OFF, you can use the
`dessicate` command:

    chews dessicate test

Check status of dessicated workstation:

    $ chews printassets
    Workstation test
      State CwsState.DESSICATED
      Volume test-boot-b1821a
        Snapshot test-boot-b1821a-1590360677
      Volume test-data-230eeb
        Snapshot test-data-230eeb-1590360677
    Workstation win-test
      State CwsState.NOT_EXIST
      Volume win-test-boot-bc9a92
      Volume win-test-data-53d695

If you have dessicated more than once, you will have some old snapshots hanging around.
To save some space, we can delete some old snapshots using the
`tidysnapshots` command:

    chews tidysnapshots test

#### Rehydrating the workstation

To use a dessicated workstation, you have to Rehydrate it using the
`rehydrate` command:

    chews rehydrate test

In the current implementation, the workstation is in state ON
immediately after rehydration.

#### Deleting the workstation

Sorry, this is not implemented yet.

You will have to delete any GCE assets (VM instance, disks and
snapshots) manually.  You can determine the names of the assets using
the `printassets` command as explained in the Section [Checking
workstation state](#checking-workstation-state).

#### Writing your own configuration

Chews reads the workstation configuration from a file.  The format of
the file a text-format
[protobuf](https://developers.google.com/protocol-buffers/) message.
The [example configuration](configs/test.config) illustrates the
syntax.  There is documentation about the different configuration
fields in the [protobuf definition](proto/config.proto).

To make your config file accessible to the docker image, you will need
to bind mount it.  For example, if your config is file
`myconfigs/chews.config`, you can define your alias as follows

    alias chews="docker run -it --read-only -v $(pwd)/myconfigs:/configs chews --config_file /configs/chews.config --project=${MY_PROJECT?}"

Note that you should not store your configuration file only on the
Google Cloud Shell.  The Cloud Shell is automatically deleted if you
do not use it for a while.  It is better to store your configuration
file in a source code repository elsewhere.

### When things go wrong

Unfortunately, there has been no effort (yet) to implement recovery of
workstations from non-standard states.  It is easily possible to end
up with assets in states which do not match a canonical workstation
state, e.g. when the `chews` script is interrupted, or when the assets
have been changed externally.

When this happens, you will have to manually change the assets until
they match a canonical state.  The easiest state to transition to
DESSICATED.  To get to this state, you have make sure there is a
snapshot for each disk with the correct names.

The naming convention for disks is

    ${workstation_name}-${disk_name}-${hash}

and for snapshots is

    ${workstation_name}-${disk_name}-${hash}-${timestamp}

The hash is computed by the chews and is the same value for both disks
and their snapshots.  You can use `printassets` command to determine
the hash.

Then pick a timestamp in seconds since epoch (in UTC) that is later
than the timestamp used for any existing snapshots.  Ideally, you want
to pick a timestamp in the past to make sure that any future snapshots
are created with a larger timestamp.  The easiest way is to look at
the existing snapshot names, find the one with the greatest timestamp
and then increment that timestamp by 1.  If there are no snapshots,
then pick a timestamp of '0000000000' (ten consecutive 0s).

Finally, create a snapshot for each disk using the your chosen
timestamp.  Note that the timestamp has to be the same for all disks.

After this, delete the VM instance and the disks.  The workstation
should now be in state DESSICATED and you should be able to Rehydrate.