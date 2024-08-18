from click_shell import shell
import click, logging.config

__author__ = "Ivan Shiriaev"
__maintainer__ = "Ivan Shiriaev"
__version__ = 0.1

logging.config.fileConfig('config/log.conf')
log = logging.getLogger("Accountant")


@shell(prompt="Accountant > ", intro="Welcome!")
def main():
    log.info("main")


@main.command("info")
def get_account_info():
    log.info("get_account_info 2")


if __name__ == "__main__":
    main()
