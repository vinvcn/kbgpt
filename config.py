"""
setup the configuration from config.yaml
"""
__all__ = ["profile", "PROF_MGR"]

import logging
import sys
from json import dumps
from os import environ
from pathlib import Path

import yaml
from mergedeep import merge

from configs.profiles import Profile


class ProfileManager():
    """ profile manager """

    CONFIG = "config.yaml"
    SECOND_CONFIG = "config_secondary.yaml"


    def __init__(self) -> None:
        self._primary_profile = None
        self._secondary_profile = None


    @property
    def primary_profile(self):
        """ primary profile """
        if not self._primary_profile:
            self._primary_profile = self.load_config(self.CONFIG)
        return self._primary_profile


    @property
    def secondary_profile(self):
        """ secondary profile """
        if not self._secondary_profile:
            self._secondary_profile = self.load_config(self.SECOND_CONFIG)
        return self._secondary_profile


    def load_yaml_config(self, path):
        """Load a yaml file and return a dictionary of its contents."""
        try:
            with open(path, "r", encoding="utf-8") as stream:
                return yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            logging.exception(exc)
            return None


    def load_config(self, file_name=None):
        """
        load the config from specified path
        """

        # Load config items from config.yaml.
        # Use Path.resolve() to get the absolute path of the parent directory
        yaml_dir = Path(__file__).resolve().parent
        if not file_name:
            yaml_path = yaml_dir / "configs" / "config.yaml"  # Use Path / operator to join paths
        else:
            yaml_path = yaml_dir / "configs" / file_name

        # Load the config and update the global variables
        yaml_config = self.load_yaml_config(yaml_path)
        prof = None
        if yaml_config is not None:
            logging.info("Loaded config from %s:", yaml_path)
            default_config = yaml_config["DEFAULT"]
            active_profile = (
                environ["KBGPT_APP_ACTIVE_PROFILE"]
                if "KBGPT_APP_ACTIVE_PROFILE" in environ
                else yaml_config["PROFILE"]
            )
            merged_profile = merge({}, default_config, yaml_config[active_profile])
            db_url = (
                environ["KBGPT_MYSQL_DB_URL"] if "KBGPT_MYSQL_DB_URL" in environ else None
            )
            if db_url:
                merged_profile["DB_URL"] = db_url

            prof = Profile(**merged_profile)
            logging.basicConfig(
                level=logging.DEBUG if prof.sanic.debug else logging.INFO,
                force=True,
                format="%(asctime)s.%(msecs)03d [%(levelname)s]"
                + " %(filename)s %(message)s",
                handlers=[
                    logging.FileHandler("debug.log"),
                    logging.StreamHandler(sys.stdout),
                ],
            )
            logging.debug(dumps(merged_profile, indent=4))
            return prof
        else:
            logging.error("Could not load config from %s.", yaml_path)
            return None

PROF_MGR = ProfileManager()
profile = PROF_MGR.primary_profile
