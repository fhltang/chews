# Code for managing life cycle of Cloud Workstations.

import datetime
import enum
import hashlib

import libcloud


class Error(Exception):
    pass


class StateError(Error):
    pass


class Volume(object):
    _SALT = 'volume'
    
    def __init__(self, context, cws_name, volume_name):
        self._context = context
        self._cws = self._context.get_cws(cws_name)
        self._volume = self._context.get_volume(cws_name, volume_name)

    def unique_name(self):
        full_name = '%s-%s' % (self._cws.name, self._volume.name)
        m = hashlib.md5()
        m.update('%s%s' % (full_name, self._SALT))
        return '%s-%s' % (full_name, m.hexdigest())

    def snapshot_name_prefix(self):
        return 'ss-%s-' % self.unique_name()


# Cloud Workstation states
class CwsState(enum.Enum):
    NOT_EXIST = 0
    DESSICATED = 1
    OFF = 2
    ON = 3
    RECOVERABLE_ERROR = 4  # A non-standard state which can be recovered
    UNRECOVERABLE_ERROR = 5  # A non-standard state which requires operator intervention

    
class Cws(object):
    def __init__(self, context, cws_name):
        self._context = context
        self._cws = self._context.get_cws(cws_name)

        self._all_volumes = set()
        self._snapshots = []
        self._volume_count = 0
        self._snapshot_count = 0

        self._populate()

    def _populate(self):
        driver = self._context.driver()
        self._all_volumes = set(v.name for v in driver.list_volumes())
        all_snapshots = [s.name for s in driver.ex_list_snapshots()]

        self._volume_count = 0
        self._snapshot_count = 0
        # Find the latest snapshot for each volume
        self._snapshots = [None] * len(self._cws.volumes)
        for i, vc in enumerate(self._cws.volumes):
            v = Volume(self._context, self._cws.name, vc.name)
            if v.unique_name() in self._all_volumes:
                self._volume_count += 1
            for s in all_snapshots:
                if s.startswith(v.snapshot_name_prefix()):
                    if self._snapshots[i] is None or s > self._snapshots[i]:
                        self._snapshots[i] = s
            if self._snapshots[i] is not None:
                self._snapshot_count += 1


    def unique_name(self):
        return self._cws.name

    def state(self):
        # Check if state is NOT_EXIST.
        # First determine if any volumes exist.
        driver = self._context.driver()
            
        if self._volume_count == 0 and self._snapshot_count == 0:
            return CwsState.NOT_EXIST

        if self._volume_count == len(self._cws.volumes):
            # As a hack, use the GCE extension to get a Node by name.
            # libcloud has no native way to do this.
            try:
                node = driver.ex_get_node(self.unique_name())
            except libcloud.common.google.ResourceNotFoundError:#
                # This is actually a recoverable error since we could
                # just recreate the node.  For now, we just pretend it
                # is an unrecoverable error.
                return CwsState.UNRECOVERABLE_ERROR
            # libcloud documentation suggests node.state should be of
            # type libcloud.compute.types.NodeState but I am getting
            # str
            if node.state == 'running':
                return CwsState.ON
            elif node.state == 'stopped':
                return CwsState.OFF

        # State is considered to be DESSICATED only if each volume has
        # at least one snapshot and the latest snapshot for each
        # volume has the same timestamp (in the name).
        if self._snapshot_count == len(self._cws.volumes):
            timestamps = set()
            for i, vc in enumerate(self._cws.volumes):
                v = Volume(self._context, self._cws.name, vc.name)
                snapshot_name = self._snapshots[i]
                timestamps.add(snapshot_name[len(v.snapshot_name_prefix()):])
            if len(timestamps) == 1:
                return CwsState.DESSICATED

        return CwsState.UNRECOVERABLE_ERROR

    def _create_node_and_attach_volumes(self):
        driver = self._context.driver()

        boot_volume = Volume(self._context, self._cws.name, self._cws.volumes[0].name)
        node = driver.create_node(
            self._cws.name, self._cws.node.size, None,
            location=self._cws.location, use_existing_disk=True,
            ex_boot_disk=boot_volume.unique_name(), ex_disk_auto_delete=False)

        for i, vc in enumerate(self._cws.volumes):
            if i == 0:
                continue
            v = Volume(self._context, self._cws.name, vc.name)
            driver.attach_volume(node, driver.ex_get_volume(v.unique_name()), ex_boot=i==0)

    def create(self):
        if self.state() != CwsState.NOT_EXIST:
            raise StateError('Cloud Workstation must be in state NOT_EXIST in order to Create.')

        driver = self._context.driver()
        for i, vc in enumerate(self._cws.volumes):
            image_family = None
            if i == 0:
                image_family = self._cws.image_family
            v = Volume(self._context, self._cws.name, vc.name)
            driver.create_volume(
                vc.size, v.unique_name(), location=self._cws.location,
                ex_image_family=image_family, use_existing=False, ex_disk_type=vc.volume_type)

        self._create_node()

    def stop(self):
        if self.state() != CwsState.ON:
            raise StateError('Cloud workstation must be in state ON in order to Stop.')

        driver = self._context.driver()
        node = driver.ex_get_node(self.unique_name())
        # Annoyingly, libcloud has no native way to stop an instance.
        # We must use the GCE extension.
        driver.ex_stop_node(node)

    def dessicate(self):
        if self.state() != CwsState.OFF:
            raise StateError('Cloud workstation must be in state OFF in order to Dessicate.')

        driver = self._context.driver()

        node = driver.ex_get_node(self.unique_name())

        driver.destroy_node(node)

        volumes = self._context.get_volumes(self._cws.name)
        timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
        for volume in volumes:
            vol = Volume(self._context, self._cws.name, volume.name)
            v = driver.ex_get_volume(vol.unique_name())
            snapshot_name = '%s%s' % (vol.snapshot_name_prefix(), timestamp)
            driver.create_volume_snapshot(v, snapshot_name)
            driver.destroy_volume(v)

    def rehydrate(self):
        state = self.state()
        if state != CwsState.DESSICATED:
            raise StateError('Cloud workstation must be in state DESSICATED to Rehydrate.  State is %s' % state)

        driver = self._context.driver()

        for i, vc in enumerate(self._cws.volumes):
            snapshot = self._snapshots[i]
            v = Volume(self._context, self._cws.name, vc.name)
            driver.create_volume(
                None, v.unique_name(), location=self._cws.location,
                snapshot=snapshot, use_existing=False,
                ex_disk_type=vc.volume_type)

        self._create_node_and_attach_volumes()
