import click
import logging.config

from click_shell import shell

from utils import expand, is_email, is_usrId, envron
from obscura import *

from Account import Account
from DynamoDB import DynamoDB
from LocalStorage import LocalStorage

__author__ = "Ivan Shiriaev"
__maintainer__ = "Ivan Shiriaev"
__version__ = 0.16

logging.config.fileConfig("config/log.conf")
log = logging.getLogger("Accountant")


@shell(prompt="Accountant > ", intro="Welcome to the Great Accountant script!", chain=True)
#@click.group(chain=True)
@click.pass_context
def main(ctx):
    ctx.obj = {}
    log.info(f"We are starting here!")


@main.command("qa")
@click.pass_context
def qa(ctx): env_setup(ctx, env_qa)


@main.command("dev")
@click.pass_context
def dev(ctx): env_setup(ctx, env_dev)


def env_setup(ctx, env):
    log.info(f"Setting up {env} environment.")
    ctx.obj['environment'] = env
    local = LocalStorage(env)
    aws = DynamoDB(env)
    ctx.obj['local'] = local
    ctx.obj['db'] = aws
    Account.set_up(aws, local)
    #ctx.obj['account'] = Account.


@main.command("show")
@click.pass_context
def show_context(ctx):
    log.info(ctx.obj)


@main.command("list")
def list_accounts():
    click.echo(Account.list_strings())

@main.command("acc")
#@click.option("--data", type=str, prompt="Enter email or userId", required=True)
@click.argument("data", type=str, required=True)
@click.pass_context
def acc(ctx, data):
    if is_usrId(data):
        log.info(f"Searching by userId {data}")
        if "environment" not in ctx.obj:
            log.warning(f"Environment is not set, trying to set up")
            if envron(data) == env_qa:
                env_setup(ctx, env_qa)
            else:
                env_setup(ctx, env_dev)
        acc = Account.find_by_usrid(data)
    else:
        if "environment" not in ctx.obj:
            log.error(f"Environment is not set up! Aborting operation.")
            return
        log.info(f"Searching by{"" if is_email(data) else " partial"} email {data}")
        acc = Account.find_by_email(data)
    if not acc:
        log.warning(f"Account ({data}) not found")
        return
    ctx.obj['account'] = acc
    log.info(f"Account selected: {repr(acc)}")


@click.command("create")
@click.option("-m", "--email", prompt=True, required=True)
@click.option("-u", "--ux", prompt=True, required=True)
@click.option("-a", "--api", required=False)
@click.option("-c", "--country", prompt=True, required=True, default="US")
@click.option("-l", "--language", prompt=True, required=True, default="en-us")
@click.pass_context
def create_account(ctx, email, ux, api, country, language): pass


@click.command("unmigrate")
@click.pass_context
def unmigrate(ctx):
    if "account" not in ctx.obj:
        log.error("Account was not specified")
        return
    if not ctx.obj['account'][ux_field]:
        log.error("Account had not been migrated")
        return
    ctx.obj['account'].unmigrate()


if __name__ == "__main__":
    main()
