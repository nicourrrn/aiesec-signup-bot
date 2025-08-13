import logging
from datetime import datetime

import toml


class Config:
    def __init__(self, config_part="../config.toml"):
        self.path = config_part
        with open(config_part, "r") as f:
            self.config = toml.load(f)
            logging.debug(f"Config: {self.config}")

    @property
    def google(self):
        return self.config["google"]

    @property
    def bot_token(self):
        return self.config["bot_token"]

    def save_tokens(self, access_token: str, refresh_token: str, expires_in: datetime):
        self.config["google"]["access_token"] = access_token
        self.config["google"]["refresh_token"] = refresh_token
        self.config["google"]["expires_in"] = expires_in
        with open(self.path, "w") as f:
            toml.dump(self.config, f)
            logging.debug(f"Saved: {self.config}")
