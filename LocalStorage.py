import json
import logging
import os

from dotenv import load_dotenv

log = logging.getLogger("LocalStorage")


class LocalStorage:
    INSTANCE = {}

    def __new__(cls, env):

        if not isinstance(cls.INSTANCE.get(env), cls):
            log.debug(f"Creating Local storage instance for {env}")

            inst = super().__new__(cls)

            load_dotenv(f"config/.env.{env}", override=True)

            inst.accounts_path = os.getenv('JSON_ACCOUNTS')
            # inst.devices_path = os.getenv('JSON_DEVICES')

            inst.accounts = inst.get_accounts()
            log.info(f"Loaded {inst.number_of_saved_accounts} accounts from disk")
            cls.INSTANCE[env] = inst
        return cls.INSTANCE[env]

    def get_accounts(self):
        try:
            with open(self.accounts_path, "r", encoding="utf-8") as file:
                return json.load(file)
        except OSError as e:
            log.error(f"Exception when trying to load a file '{self.accounts_path}'")
            log.exception(e)
            raise OSError(f"Exception when trying to load a file '{self.accounts_path}'")
        except json.JSONDecodeError as e:
            log.error(f"Exception when trying to read json '{self.accounts_path}'")
            log.exception(e)
            raise json.JSONDecodeError(f"Exception when trying to read json '{self.accounts_path}'")

    def save_accounts(self):
        try:
            with open(self.accounts_path, "w", encoding="utf-8") as file:
                json.dump(self.accounts, file, indent=2)
                log.info(f"Saved {self.number_of_saved_accounts} accounts to disk")
        except OSError as e:
            log.error(f"Exception when trying to save a file '{self.accounts_path}'")
            log.exception(e)
            raise OSError(f"Exception when trying to save a file '{self.accounts_path}'")

    @property
    def number_of_saved_accounts(self):
        return len(self.accounts)
