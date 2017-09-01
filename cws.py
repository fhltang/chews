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

    def unique_name(self):
        return self._cws.name

    def state(self):
        # Check if state is NOT_EXIST.
        # First determine if any volumes exist.
        driver = self._context.driver()
        all_volumes = set()
        all_snapshots = []
        for v in driver.list_volumes():
            all_volumes.add(v.name)
            snapshots = [s.name for s in driver.list_volume_snapshots(v)]
            all_snapshots.extend(snapshots)
            
        volume_count = 0
        snapshot_count = 0
        for vc in self._cws.volumes:
            v = Volume(self._context, self._cws.name, vc.name)
            if v.unique_name() in all_volumes:
                volume_count += 1
            snapshots = [s for s in all_snapshots
                         if s.startswith(v.snapshot_name_prefix())]
            if len(snapshots) > 0:
                snapshot_count += 1

        if volume_count == 0 and snapshot_count == 0:
            return CwsState.NOT_EXIST

        if volume_count == len(self._context.get_volumes(self._cws.name)):
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

        return CwsState.UNRECOVERABLE_ERROR

    def create(self):
        if self.state() != CwsState.NOT_EXIST:
            raise StateError('Cloud Workstation must be in state NOT_EXIST in order to Create.')

        driver = self._context.driver()
        for i, vc in enumerate(self._cws.volumes):
            image_family = None
            if i == 0:
                image_family = self._cws.image_family
            v = Volume(self._context, self._cws.name, vc.name)
            driver.create_volume(vc.size, v.unique_name(), location=self._cws.location, ex_image_family=image_family, use_existing=False, ex_disk_type=vc.volume_type)

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
        for volume in volumes:
            vol = Volume(self._context, self._cws.name, volume.name)
            v = driver.ex_get_volume(vol.unique_name())
            timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
            snapshot_name = '%s%s' % (vol.snapshot_name_prefix(), timestamp)
            driver.create_volume_snapshot(v, snapshot_name)
            driver.destroy_volume(v)
