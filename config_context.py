# A context carrying the loaded configuration.

from libcloud.compute.types import Provider
from libcloud.compute.providers import get_driver

import config

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
