"""
Defines the Cycler class
"""

import logging

from periodic_timer import PeriodicTimer

class Cycler(object):
    """
    A simple object that uses a periodic timer and
    pushes investigation requests each time it's triggered
    """

    KEY_FREQ = "freq"
    KEY_MANIFEST = "manifest"
    KEY_CHECK = "check"
    KEY_REACT = "react"

    MANIFEST_ITEM = [KEY_CHECK, KEY_REACT]

    def __init__(self, config, investigator):
        self.logger = logging.getLogger(__name__)

        self._configure(config) # Must come first after logger init

        self.investigator = investigator
        self.periodic_timer = PeriodicTimer(self.freq, self._trigger)

    def _configure(self, config):
        """
        Reads and validates configuration
        """
        try:
            self.logger.info("Configuration:")

            # Save original config
            self.config = config

            # Get configured frequency
            self.freq = self.config[Cycler.KEY_FREQ]
            self.logger.info("Freq: %d sec", self.freq)

            # Get and check configured manifest
            # Rules:
            # Manifest is a dictionary
            # Each item in the dictionary is a item, which is also a dictionary
            # Each item has exactly the same keys as Cycler.KEY_MANIFEST
            # Each key's value is a list of strings
            self.manifest = self.config[Cycler.KEY_MANIFEST]
            for idx, item in enumerate(self.manifest):
                if len(item) != len(Cycler.MANIFEST_ITEM):
                    raise KeyError("Manifest item[{0}] misconfigured".format(idx))

                for key in item:
                    if key not in Cycler.MANIFEST_ITEM:
                        raise KeyError("Manifest item[{0}] bad key[{1}]".format(idx, key))

                    if not isinstance(item[key], list):
                        raise KeyError("Manifest item[{0}] bad key[{1}] value: "
                                       "not a list".format(idx, key))

                    for val in item[key]:
                        if not isinstance(val, basestring):
                            raise KeyError("Manifest item[{0}] bad key[{1}] value: "
                                           "contains non-string".format(idx, key))
            self.logger.info("Manifest: %s", str(self.manifest))
        except KeyError as err:
            raise RuntimeError("Bad {0} configuration: {1}".format(__name__, err))

    def _intro(self):
        self.logger.info("Starting")

    def _outro(self):
        self.logger.info("Stopped")

    def _trigger(self):
        for item in self.manifest:
            self.logger.info("Enqueuing request: %s", item)
            self.investigator.enqueue(item)

    def stop(self):
        """
        Stop the cycler
        """
        self.periodic_timer.stop()
        self._outro()

    def start(self):
        """
        Start the cycler.
        It will execute the specified action every 'freq' seconds
        """
        self._intro()
        self.periodic_timer.start()