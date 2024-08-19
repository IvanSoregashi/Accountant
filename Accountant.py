import click
import logging.config

from click_shell import shell

from utils import expand, is_email, is_usrId

from Account import Account
from DynamoDB import DynamoDB
from LocalStorage import LocalStorage


__author__ = "Ivan Shiriaev"
__maintainer__ = "Ivan Shiriaev"
__version__ = 0.12

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
    ctx.obj['account'] = acc
    log.info(f"Account selected: {repr(acc)}")

@main.command("account")
@click.option("-m", "--email", callback=find_by_email)
@click.pass_context
def account(ctx, email):
    pass
@main.command("acc")
#@click.option("--data", type=str, prompt="Enter email or userId", required=True)
@click.argument("data", type=str, required=True)
@click.pass_context
def acc(ctx, data):
    if is_usrId(data):
        log.info(f"Searching by userId {data}")
        acc = Account[data]
    else:
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

if __name__ == "__main__":
    main()
