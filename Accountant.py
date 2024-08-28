import click
import logging.config

from click_shell import shell

from utils import *
from Account import AccountGroup, Account

__author__ = "Ivan Shiriaev"
__maintainer__ = "Ivan Shiriaev"
__version__ = 0.22

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


@main.command("show")
@click.option("-s", "--hash", is_flag=True, help="Print out hashed userId (for the LaunchDarkly).")
@click.option("-f", "--full", is_flag=True, help="Print out Full account json.")
@click.pass_context
def show_context(ctx, hash, full):
    log.info(ctx.obj)
    if full: click.echo(expand(ctx.obj['account'].data))
    if hash: log.info(sha_256(ctx.obj['account']['userId']))


@main.command("reset")
@click.pass_context
def reset_context(ctx):
    log.debug("resetting context")
    ctx.obj.clear()


@main.command("remove")
@click.pass_context
def remove_account(ctx):
    if 'account' in ctx.obj:
        ctx.obj['account'].remove()
    else:
        log.error("Account was not specified")


@main.command("update")
@click.pass_context
def update_account(ctx):
    if 'account' in ctx.obj:
        ctx.obj['account'].refresh()
    else:
        log.error("Account was not specified")


@main.command("list")
@click.pass_context
def list_accounts(ctx):
    if 'accounts' in ctx.obj:
        lst = ctx.obj['accounts'].list_repr()
    else:
        lst = AccountGroup().list_repr()
    click.echo(lst)
    AccountGroup().save_accounts()


@main.command("acc")
#@click.option("--data", type=str, prompt="Enter email or userId", required=True)
@click.argument("data", type=str, required=True)
@click.pass_context
def acc(ctx, data):
    acc = Account.get_local(data)
    if acc:
        log.debug(f"Account {data} was found locally")
        ctx.obj['account'] = acc
        return
    click.echo("Should we check the database?")
    if not confirm(): return
    if is_usrId(data):
        acc = Account.from_userid(data)
    elif email := ensure_email(data):
        env = ctx.obj.get('environment', confirm_env())
        acc = Account.from_email(email, env)
    else:
        log.error(f"cannot search in db with that sort of data {data}")
    if acc:
        log.debug(f"Account {data} was found in remote db")
        ctx.obj['account'] = acc
        click.echo("Save Account to disk?")
        if confirm():
            acc.save_local()
            AccountGroup().save_accounts()
    else:
        log.error(f"Account {data} was not found in remote db")



@click.command("create")
@click.option("-m", "--email", prompt=True, required=True)
@click.option("-u", "--ux", prompt=True, required=True)
@click.option("-a", "--api", required=False)
@click.option("-c", "--country", prompt=True, required=True, default="US")
@click.option("-l", "--language", prompt=True, required=True, default="en-us")
@click.pass_context
def create_account(ctx, email, ux, api, country, language):
    pass


@main.command("unmigrate")
@click.pass_context
def unmigrate(ctx):
    if "account" not in ctx.obj:
        log.error("Account was not specified")
        return
    log.info(f"Un-migrating account {repr(ctx.obj['account'])}. Be aware: corporate VPN connection is necessary.")
    if not ctx.obj['account'][ux_field]:
        log.error("Account had not been migrated")
        return
    resp = ctx.obj['account'].unmigrate()
    (log.info if resp.ok else log.error)(f"Response: {str(resp.content)}")


if __name__ == "__main__":
    main()
