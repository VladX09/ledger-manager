import typing as t
from pathlib import Path

import pydantic
import typer
from loguru import logger
from rich.panel import Panel

from ledger_manager.api import use_cases
from ledger_manager.api.models import Consts
from ledger_manager.api.services import ExchangeRatesAPIException, LedgerClientException
from ledger_manager.console import console

from .common import CONTEXT_SETTINGS, CommonParams, ErrorHandlingTyper
from .reports import app as reports_app

app = ErrorHandlingTyper(rich_markup_mode="rich")


@app.callback()
def common_options(
        ctx: typer.Context,
        config_file: Path = typer.Option(
            f"./{Consts.DEFAULT_CONFIG_FILE_NAME}",
            "--config-file",
            "-f",
        ),
        enable_logs: bool = typer.Option(
            False,
            "-v",
            "--verbose",
            is_flag=True,
        ),
):
    ctx.obj = CommonParams(config_file=config_file)
    if enable_logs:
        logger.enable("ledger_manager")
        logger.debug("Debug enabled")

    logger.debug("Got config: {}", ctx.obj.config.dict())


@app.error_handler(
    pydantic.ValidationError,
    LedgerClientException,
    ExchangeRatesAPIException,
)
def validation_error_handler(error: pydantic.ValidationError) -> int:
    console.print(Panel(str(error), border_style="red", title=error.__class__.__qualname__))
    return 1


app.add_typer(reports_app, name="reports", no_args_is_help=True)


@app.command(context_settings=CONTEXT_SETTINGS)
def forward(
    ctx: typer.Context,
    ledger_args: t.Optional[t.List[str]] = typer.Argument(None, help="Ledger CLI arguments"),
    filter_patterns: t.Optional[t.List[str]] = typer.Option(
        None,
        "-f",
        help="Use it instead of Ledger cmd args for extended regexes",
    ),
):
    """Forward commands to Ledger.

    Adds some ledger-manager sugar:
        - transactions file from config
        - price DB file from config
        - python-style regexes for accounts (if specified by the -f option)
    """
    common_params: CommonParams = ctx.obj
    ledger_args = ledger_args or []

    use_cases.forward(
        *ledger_args,
        config=common_params.config,
        patterns=filter_patterns,
    )


@app.command()
def update_db(ctx: typer.Context):
    """Update price db file.

    - Adds exchange rates to the price DB file for all the dates from the start date (from config)
    till the current date
    - Ignores dates that are currently in the price DB file
    - Uses configured main currency, currency list to sync, and currency aliases
    - Uses [blue]https://api.apilayer.com/exchangerates_data[/blue] API for exchange rates
    - [red]API key required![/red]
    """
    common_params: CommonParams = ctx.obj

    use_cases.update_price_db(config=common_params.config)


@app.command()
def show_config(ctx: typer.Context):
    """Show current config.

    Config is merged by local config file, envvars, appdir and builtin defaults.

    """

    common_params: CommonParams = ctx.obj
    console.print_json(common_params.config.json())
