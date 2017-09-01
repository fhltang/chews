# POD classes for representing configuration.
#
# TODO: Find serialise/deserialise to text options.

import collections

NodeConfig = collections.namedtuple('NodeConfig', [
    'size',  # str, e.g. 'n1-standard-4'
])

VolumeConfig = collections.namedtuple('DiskConfig', [
    'name',  # string, scoped within Cloud workstation config
    'size',  # number, size in GB
    'volume_type',  # string, e.g. 'pd-standard' or 'pd-ssd'
])

# Cloud workstation config
CwsConfig = collections.namedtuple('CwsConfig', [
    'name',
    'node',   # NodeConfig
    'volumes',  # list of VolumeConfig, must be non-empty and first disk is boot disk
    'location',  # str
    'image_family',  # str, used for creation only
])

Config = collections.namedtuple('Config', [
    'provider',  # str, e.g. GCE
    'project',  # project name
    'cloud_workstations',  # list of CwsConfig
])
