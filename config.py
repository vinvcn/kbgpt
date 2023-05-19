"""
setup the configuration from config.yaml
"""
__all__ = ["profile"]
import logging
import sys
from os import environ
from pathlib import Path
from pprint import pformat

import yaml
from mergedeep import merge

from configs.profiles import Profile

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s.%(msecs)03d [%(levelname)s]"
    + " %(filename)s %(message)s",
    handlers=[
        logging.FileHandler("debug.log"),
        logging.StreamHandler(sys.stdout),
    ],
)
# Load config items from config.yaml.
# Use Path.resolve() to get the absolute path of the parent directory
yaml_dir = Path(__file__).resolve().parent
yaml_path = yaml_dir / "config.yaml"  # Use Path / operator to join paths


def load_yaml_config(path):
    """Load a yaml file and return a dictionary of its contents."""
    try:
        with open(path, "r", encoding="utf-8") as stream:
            return yaml.safe_load(stream)
    except yaml.YAMLError as exc:
        logging.exception(exc)
        return None


# Load the config and update the global variables
yaml_config = load_yaml_config(yaml_path)
profile = None
if yaml_config is not None:
    logging.info("Loaded config from %s:", yaml_path)
    logging.info("\n%s", pformat(yaml_config))
    default_config = yaml_config["DEFAULT"]
    active_profile = (
        environ["KBGPT_APP_ACTIVE_PROFILE"]
        if "KBGPT_APP_ACTIVE_PROFILE" in environ
        else yaml_config["PROFILE"]
    )
    merged_profile = merge({}, default_config, yaml_config[active_profile])
    profile = Profile(**merged_profile)
    logging.basicConfig(
        level=logging.DEBUG if profile.sanic.debug else logging.INFO,
        format="%(asctime)s.%(msecs)03d [%(levelname)s]"
        + " %(filename)s %(message)s %(pathname)s:%(lineno)d",
        handlers=[
            logging.FileHandler("debug.log"),
            logging.StreamHandler(sys.stdout),
        ],
    )
else:
    logging.error("Could not load config from %s.", yaml_path)
    sys.exit(1)  # Exit the program if the config is invalid
