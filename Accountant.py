import click
import logging.config

from click_shell import shell
from LocalStorage import LocalStorage




__author__ = "Ivan Shiriaev"
__maintainer__ = "Ivan Shiriaev"
__version__ = 0.11
logging.config.fileConfig('config/log.conf')
log = logging.getLogger("Accountant")


@shell(prompt="Accountant > ", intro="Welcome!", chain=True)
#@click.group(chain=True)
@click.pass_context
def main(ctx):
    ctx.obj = {}
    log.info(f"programs start")


@main.command("gqa")
@click.pass_context
def gqa(ctx):
    ctx.obj['environment'] = "goldenqa"
    ctx.obj['local'] = LocalStorage("goldenqa")
    #load_dotenv(f"config/.env.goldenqa", override=True)


@main.command("dev")
@click.pass_context
def dev(ctx):
    ctx.obj['environment'] = "goldendev"
    ctx.obj['local'] = LocalStorage("goldendev")


@main.command("show")
@click.pass_context
def show_context(ctx):
    log.info(f"env {ctx.obj['environment']}")
    log.info(f"first email: {next(iter(ctx.obj['local'].accounts.values()))['email']}")



if __name__ == "__main__":
    main()
