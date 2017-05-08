"""
Defines the Handler class
"""

import logging
import threading
import subprocess
import Queue

from config import ConfigParser

class Handler(threading.Thread):
    """
    A handler class that can stop/start/restart
    the target process
    """

    KEY_STOP = "stop"
    KEY_START = "start"

    def __init__(self, config):
        threading.Thread.__init__(self)
        self.logger = logging.getLogger(__name__)

        self._configure(config) # Must come first after logger init

        self.queue = Queue.Queue()
        self.stopped = False

        self.handlers = {
            "stop": self._target_stop,
            "start": self._target_start,
            "restart": self._target_restart
        }

    def _configure(self, config):
        """
        Reads and validates configuration
        """
        try:
            self.logger.info("Configuration:")

            # Save original config
            self.config = config

            # Get configured stop action
            # If none specified, we will use the default termination
            # functionality of psutil
            self.stop_cmd = []
            if Handler.KEY_STOP in self.config:
                self.stop_cmd = ConfigParser.parse_cmdline(self.config[Handler.KEY_STOP])
            self.logger.info("Stop cmdline: %s", self.stop_cmd)

            self.start_cmd = ConfigParser.parse_cmdline(self.config[Handler.KEY_START])
            self.logger.info("Start cmdline: %s", self.start_cmd)
        except KeyError as err:
            raise RuntimeError("Bad {0} configuration: {1}".format(__name__, err))

    def _intro(self):
        self.logger.info("Starting")

    def _outro(self):
        self.logger.info("Stopped")

    def _target_stop(self, target):
        if target is None:
            self.logger.info("Stop skipped, target not active")
            return

        if self.stop_cmd:
            subprocess.Popen(self.stop_cmd)
        else:
            target.terminate()
            target.wait(timeout=3)

        self.logger.info("Stop issued!")

    def _target_start(self, target):
        subprocess.Popen(self.start_cmd)
        self.logger.info("Start issued!")

    def _target_restart(self, target):
        self._target_stop(target)
        self._target_start(target)

    def _process(self, request):
        target = request["target"]
        react = request["react"]
        for reaction in react:
            if target is None:
                self.logger.info("Handling an inactive target -> Executing %s",
                                 reaction)
            else:
                self.logger.info("Handling target [%s] pid [%d] -> Executing %s",
                                 target.name(), target.pid, reaction)
            self.handlers[reaction](target)

    def enqueue(self, request):
        """
        Add a handling request
        """
        self.queue.put(request)

    def stop(self):
        """
        Stop the handler
        """
        self.stopped = True
        # Insert fake item to ensure we exit the blocking the get()
        self.queue.put("*")

    def run(self):
        self._intro()
        while True:
            request = self.queue.get()
            if self.stopped:
                break
            self._process(request)
        self._outro()