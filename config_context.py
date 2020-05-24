# A context carrying the loaded configuration.

from libcloud.compute.types import Provider
from libcloud.compute.providers import get_driver

from google.protobuf import text_format


class Error(Exception):
    pass


class InvalidConfig(Error):
    pass



class ConfigValidator(object):
    def __init__(self, config):
        """Constructor.

        Args:
          config: config_pb2.Config message, configuration to validate
        """
        self._c = config

    def _debug_string(self, message):
        return text_format.MessageToString(message)

    def _require_field(self, message, field):
        """Assert that message has a field.

        Args:
          message: google.protobuf.message.Message, message to check
          field: str, name of field to check presence of

        Raises:
          InvalidConfig if field is absent in message.
        """
        if not message.HasField(field):
            raise InvalidConfig(
                'Field %s is required: %s'
                % (field, self._debug_string(message)))

    def _validate_volume(self, volume):
        self._require_field(volume, 'name')
        self._require_field(volume, 'size')
        self._require_field(volume, 'volume_type')
        self._require_field(volume, 'max_snapshots')

    def _validate_node(self, node):
        self._require_field(node, 'size')

    def _validate_cws(self, cws):
        self._require_field(cws, 'name')

        self._require_field(cws, 'node')
        self._validate_node(cws.node)

        if len(cws.volumes) <= 0:
            raise InvalidConfig(
                'Workstation must define at least one volume: %s'
                % self._debug_string(cws))
        for v in cws.volumes:
            self._validate_volume(v)

        self._require_field(cws, 'location')
        self._require_field(cws, 'image_family')

    def validate(self):
       """Determine if the config is valid.

       Args:
         config: config_pb2.Config message, configuration

       Raises:
         InvalidConfig if config is invalid
       """
       self._require_field(self._c, 'provider')
       if self._c.provider != 'GCE':
           raise InvalidConfig('provider must take value GCE')

       self._require_field(self._c, 'project')

       for cws in self._c.cloud_workstations:
           self._validate_cws(cws)


class ConfigContext(object):
    def __init__(self, config):
        self._config = config

        self._cloud_workstations = {}
        self._volumes = {}
        self._build_indexes()

        # Only support GCE for now
        assert config.provider == 'GCE'

        ComputeEngine = get_driver(Provider.GCE)
        self._driver = ComputeEngine('', '', project=self._config.project)

    def _build_indexes(self):
        for cws in self._config.cloud_workstations:
            self._cloud_workstations[cws.name] = cws
            for v in cws.volumes:
                self._volumes[(cws.name, v.name)] = v

    def driver(self):
        return self._driver

    def get_cws(self, cws_name):
        return self._cloud_workstations[cws_name]

    def get_volume(self, cws_name, volume_name):
        return self._volumes[(cws_name, volume_name)]

    def get_volumes(self, cws_name):
        # Returned volumes order is non-deterministic.  This will have
        # to do for now.
        volumes = []
        for (name, _), v in self._volumes.items():
            if name == cws_name:
                volumes.append(v)
        return volumes
