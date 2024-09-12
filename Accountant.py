import click
import logging.config

from click_shell import shell

from Requests import register_ux3, directory_register
from utils import *
from Account import AccountGroup, Account

__author__ = "Ivan Shiriaev"
__maintainer__ = "Ivan Shiriaev"
__version__ = 0.31

logging.config.fileConfig("config/log.conf")
log = logging.getLogger("Accountant")


@shell(prompt="Accountant > ", intro="Welcome to the Great Accountant script!", chain=True)
#@click.group(chain=True)
@click.pass_context
def main(ctx):
    """Main command group, that's it"""
    ctx.obj = {}
    log.info(f"We are starting here!")
    ctx.call_on_close(lambda: log.info("exiting the app"))


@main.command("qa")
def qa():
    """Setting up environment to work on qa"""
    ENV.QA.SET()


@main.command("dev")
def dev():
    """Setting up environment to work on development"""
    ENV.DEV.SET()


@main.command("prod")
def prod():
    """Setting up environment to work on production"""
    ENV.PROD.SET()


@main.command("acc")
# @click.option("--data", type=str, prompt="Enter email or userId", required=True)
@click.argument("data", type=str, required=True)
@click.pass_context
def acc(ctx, data):
    """\b
    Select account to work with.
    First we will try to find it locally,
    Then in DynamoDB if not found

    DATA - Information to search account by, can be userId or email address"""
    # Local Search
    acc = Account.get_local(data)
    if acc:
        log.debug(f"Account {data} was found locally")
        ctx.obj['account'] = acc
        return
    # Confirming search in remote DB, commented out for now, doing automatically
    # click.echo("Should we check the database?")
    # if not confirm(): return
    # Search in remote DB by the data type
    if is_usrId(data):
        acc = Account.from_userid(data)
    elif email := ensure_email(data):
        acc = Account.from_email(email)
    else:
        log.error(f"cannot search in db with that sort of data {data}")
        return
    # account
    if acc:
        log.debug(f"Account {data} was found in remote db")
        ctx.obj['account'] = acc
        """click.echo("Save Account to disk?")
        if confirm():"""
        # lets save account automatically for now
        acc.save_local()
        AccountGroup().save_accounts()
    else:
        log.error(f"Account {data} was not found in remote db")


@main.command("show")
@click.option("-s", "--hash", is_flag=True, help="Print out hashed userId (for the LaunchDarkly).")
@click.option("-f", "--full", is_flag=True, help="Print out raw account json.")
@click.pass_context
def show_context(ctx, hash, full):
    """Show information about the account"""
    if 'account' not in ctx.obj:
        log.error("Account was not specified, select the account first.")
        return
    click.echo(ctx.obj['account'])
    if full:
        click.echo(expand(dec_to_int(ctx.obj['account'].data)))
    if hash:
        click.echo(sha_256(ctx.obj['account']['userId']))


@main.command("reset")
@click.pass_context
def reset_context(ctx):
    """Clear out the context, like selected account or list of accounts"""
    ctx.obj.clear()
    log.debug("The context was reset.")


@main.command("remove")
@click.pass_context
def remove_account(ctx):
    """Remove the account from the list of saved accounts"""
    if 'account' in ctx.obj:
        ctx.obj['account'].remove()
    else:
        log.error("Account was not specified, select the account first.")


@main.command("update")
@click.pass_context
def update_account(ctx):
    """Refresh the account data from the database"""
    if 'account' in ctx.obj:
        ctx.obj['account'].refresh()
    else:
        log.error("Account was not specified")


@main.command("list")
# @click.argument("filter", nargs=-1)
@click.pass_context
def list_accounts(ctx):
    """\b
    List the accounts,
    narrow down the list by using 'filter' command"""
    if 'accounts' not in ctx.obj:
        ctx.obj['accounts'] = AccountGroup()
    click.echo(ctx.obj['accounts'].list_repr())


@main.command("filter")
@click.argument("args", required=True, nargs=-1, type=str)
@click.pass_context
def filter_list_argument(ctx, args):
    """\b
    Filter the list of the accounts.
    Provide arguments one by one after the filter command.
    Example: 'filter z1 partner qa'
    Filter by country code: US, FR, etc.
    Filter by geographical zone: EU, Z1, LATAM.
    Filter by environment dev, qa, etc.
    Filter by partner company.
    Filter by last update (not yet).
    Filter by Devices (not yet).
    Filter by provisioned devices (not yet).

    View the list of your accounts with 'list' command.
    """
    log.debug(str(args))
    if 'accounts' not in ctx.obj:
        ctx.obj['accounts'] = AccountGroup()
    cc, flt = sort_args(args)
    if cc:
        ctx.obj['accounts'] = ctx.obj['accounts'].filter_by_cc(cc)
    for arg in flt:
        ctx.obj['accounts'] = ctx.obj['accounts'].filter(arg)

'''@main.command("f")
@click.option("-c", required=False, type=click.Choice(COUNTRY_IP))
@click.option("-r", required=False, type=click.Choice(REGION))
@click.option("-f", required=False, type=click.Choice(FILTERS))
#@click.option("-r", "--region", prompt=True)
@click.pass_context
def filter_list_options(ctx, c, r, f):
    if 'accounts' not in ctx.obj:
        ctx.obj['accounts'] = AccountGroup()
    #ctx.obj['accounts'] = ctx.obj['accounts'].filter(env_dev)
    print(c)
    print(r)
    print(f)
    #print(region)'''



'''@main.command("eng")
@click.pass_context
def get_engagements(ctx):
    if 'account' not in ctx.obj:
        log.warning("Account was not specified")
        return
    items = ctx.obj['account'].get_engagements()
    click.echo(expand(dec_to_int(items)))


@main.command("peng")
@click.pass_context
def get_engagements(ctx):
    ctx.obj['account'].refresh_engagements()'''


'''@main.command("create")
@click.option("-m", "--email", prompt=True, required=True)
@click.option("-c", "--country", default="US")
@click.option("-l", "--language", default="en")
@click.option("-t", "--type", required=True)
@click.pass_context
def create_account(ctx, email, country, language, type):
    if ENV.IS_NOT_SET():
        ENV.CHOOSE().SET()
    match type:
        case '3': userId = Requests.register_ux3(ensure_email(email), country.upper(), language.lower())
        case '4o': Account.create_4i(ensure_email(email), country.upper(), language.lower())
        case '4d': create_directory(ensure_email(email), country.upper(), language.lower())'''


@main.command("reg3")
@click.option("-m", "--email", prompt=True, type=str, required=True, help="email address of the account")
@click.option("-c", "--country", prompt=True, type=str, default="US", help="Country Code of the account")
@click.option("-l", "--language", type=str, default="en", help="language assigned to the account")
@click.pass_context
def create_legacy_account(ctx, email, country, language):
    """Register legacy account with custom country and language"""
    userId = register_ux3(ensure_email(email), country.upper(), language.lower())
    acc = Account.from_userid(userId)
    ctx.obj['account'] = acc
    acc.save_local()
    AccountGroup().save_accounts()


@main.command("reg4")
@click.option("-m", "--email", prompt=True, type=str, required=True, help="email address of the account")
@click.option("-c", "--country", prompt=True, type=str, default="US", help="Country Code of the account")
@click.option("-l", "--language", type=str, default="en", help="language assigned to the account")
@click.option("-v", "--verify", is_flag=True, help="auto-verify email address")
@click.option("-a", "--mfa", is_flag=True, help="Disable mfa? works only on dev environment right now")
@click.option("-o", "--location", type=str, default="Home", help="Create default location")
@click.pass_context
def create_directory_account(ctx, email, country, language, verify, mfa, location):
    """\b
    Register new account via directory API with custom country and language,
    auto verify email, disable mfa (dev), create default location with the use of flags.
    Corporate VPN is necessary for use of Directory API."""
    userId = directory_register(
        ensure_email(email),
        country.upper(),
        language.lower(),
        verify,
        mfa,
        location)
    acc = Account.from_userid(userId)
    ctx.obj['account'] = acc
    acc.save_local()
    AccountGroup().save_accounts()


@main.command("unmigrate")
@click.pass_context
def unmigrate(ctx):
    """Unmigrate the currently selected account"""
    if "account" not in ctx.obj:
        log.error("Account was not specified")
        return
    log.info(f"Un-migrating account {repr(ctx.obj['account'])}. Be aware: corporate VPN connection is necessary.")
    if not ctx.obj['account'][ux_field]:
        log.error("Account had not been migrated")
        return
    resp = ctx.obj['account'].unmigrate()
    (log.info if resp.ok else log.error)(f"Response: {str(resp.content)}")


@main.command("exp")
def experiment():
    """Experimental function"""
    pass


if __name__ == "__main__":
    main()


