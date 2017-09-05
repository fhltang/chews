# chews: Cheap Workstation

## Objective

Chews is a tool for managing the life cycle of cloud workstations.

By _workstation_, we mean a virtual machine intended to be switched on
and off rather than to be continually running as a server.

See [Design](docs/design.md).

Chews [originally had a more ambitious
objective](docs/original_objective.md) which is currently infeasible.

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

    sudo apt-get install protobuf
    git clone https://github.com/fhltang/chews.git
    cd chews
    virtualenv --no-site-packages --distribute .env && source .env/bin/activate && pip install -r requirements.txt
    make chews

### Create a cloud workstation

We can reuse the example workstations in the config file in `configs/test.config`.

To create the Debian workstation:

    CONFIG=configs/test.config
    ./chews.py --config_file ${CONFIG} --project ${MY_PROJECT?} create test

In the current implementation, the workstation is in state ON after
creation.

Once the `create` command completes, the workstation is created.  You
can ssh into workstation using the normal GCE methods.  For example,
from the [VM instances
console](https://console.cloud.google.com/compute/instances) you can
find the VM instance and connect using the SSH option.

On initial creation, you will have to set up the workstation,
e.g. format and mount any extra disks.

### Using the cloud workstation

#### Checking workstation state

You can check the state of the workstation using the `printassets` command:

    $ ./chews.py --config_file ${CONFIG} --project ${MY_PROJECT?} printassets
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

Alternatively, you can use the `poweroff` command:

    ./chews.py --config_file ${CONFIG} --project ${MY_PROJECT?} poweroff test

#### Switching on the workstation

If the workstation is in state OFF, you can switch it on using the
`poweron` command:

    ./chews.py --config_file ${CONFIG} --project ${MY_PROJECT?} poweron test

Alternatively, you can just find and start the VM instance using the GCP console.

#### Dessicating the workstation

If you do not intend to use the workstation for a while, you can
Dessicate it.  This will reduce the hourly cost of the workstation
preserving the contents of the block devices in snapshots (which are
cost less per GB-month and you are charged only for the used blocks on
the disks) and delete the VM instance and its block devices.

To dessicate, the workstation has to be in state OFF, you can use the
`dessicate` command:

    ./chews.py --config_file ${CONFIG} --project ${MY_PROJECT?} dessicate test

#### Rehydrating the workstation

To use a dessicated workstation, you have to Rehydrate it using the
`rehydrate` command:

    ./chews.py --config_file ${CONFIG} --project ${MY_PROJECT?} rehydrate test

In the current implementation, the workstation is in state ON
immediately after rehydration.

#### Deleting the workstation

Sorry, this is not implemented yet.

You will have to delete any GCE assets (VM instance, disks and
snapshots) manually.  You can determine the names of the assets using
the `printassets` commmand.
