import os
import sys
import json
import logging
from pathlib import Path
from collections import abc


class Configuration(abc.MutableMapping):
    """
    Configuration object for the bot
    Dictionary(json) like object that stores the configuration of the bot
    """

    def __init__(self, config_file="config.json"):
        self.log: logging.Logger = logging.getLogger(f"{self.__class__.__name__}")
        self.log.debug("Initializing  config with file: %s", config_file)
        self.config_file: str = config_file
        self.__config: dict = {}
        self.setup()

    def __getitem__(self, __k: str) -> str:
        return self.__config[__k]

    def __getattr__(self, key: str) -> any:
        return self.__config[key]

    def __setitem__(self, __k: str, __v: any) -> None:
        self.__config[__k] = __v

    def __delitem__(self, __k: str) -> None:
        del self.__config[__k]

    def __repr__(self) -> str:
        return repr(self.__config)

    def __len__(self) -> int:
        return len(self.__config)

    def __iter__(self) -> iter:
        return iter(self.__config)

    def to_json(self) -> dict:
        """
        Return the configuration as a json object
        """
        return self.__config

    def from_json(self, src: dict) -> None:
        """
        Load the configuration from a json object
        """
        self.__config = src.copy()

    def load(self) -> None:
        """
        Load the configuration from the config file
        """
        with open(self.config_file, "r", encoding="utf-8") as f:
            self.from_json(json.load(f))

    def store(self) -> None:
        """
        Store the configuration to the config file
        """
        with open(self.config_file, "w", encoding="utf-8") as f:
            json.dump(self.to_json(), f)

    def _setup_config_from_terminal(self) -> None:
        """
        Setup the bot configuration from terminal
        """
        self.log.debug("Setting up configuration from terminal")
        with open("config_example.json", "r", encoding="utf-8") as f:
            expected = json.load(f)
        keys = list(expected)
        vals = [input(f"{k}?: ") for k in keys]
        self.__config = dict(zip(keys, vals))
        self.store()

    def setup(self) -> None:
        """
        Initialize the configuration
        Try reading previously stored configuration from the config file
        If the file does not exist, or is not readable, prompt the user to
        setup the configuration
        """
        self.log.debug("Configuration setup")
        if not os.path.exists(f"{Path.home()}/.csbot"):
            os.makedirs(f"{Path.home()}/.csbot")
        loaded = False
        while not loaded:
            try:
                self.load()
                loaded = True
            except (
                FileNotFoundError,
                json.decoder.JSONDecodeError,
                KeyError,
            ) as config_error:
                self.log.debug("%s", config_error)
                if (
                    input("Would you like to setup the config from the terminal? y/n ")
                    == "y"
                ):
                    self._setup_config_from_terminal()
                else:
                    sys.exit(f"Please setup your config: {self.config_file}")
