import click
import logging.config

from click_shell import shell

from utils import expand

from Account import Account
from DynamoDB import DynamoDB
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
    local = LocalStorage("goldenqa")
    aws = DynamoDB("goldenqa")
    ctx.obj['local'] = local
    ctx.obj['db'] = aws
    Account.set_up(aws, local)
    #load_dotenv(f"config/.env.goldenqa", override=True)


@main.command("dev")
@click.pass_context
def dev(ctx):
    ctx.obj['environment'] = "goldendev"
    local = LocalStorage("goldendev")
    aws = DynamoDB("goldendev")
    ctx.obj['local'] = local
    ctx.obj['db'] = aws
    Account.set_up(aws, local)


@main.command("show")
@click.pass_context
def show_context(ctx):
    log.info(f"env {ctx.obj['environment']}")
    log.info(f"first email: {next(iter(ctx.obj['local'].accounts.values()))['email']}")

def find_by_email(ctx, param, value):
    acc = Account.find_by_email(value)
    click.echo(expand(acc))
@main.command("acc")
@click.option("-m", "--email", callback=find_by_email)
@click.pass_context
def acc(ctx, email):
    pass


if __name__ == "__main__":
    main()
