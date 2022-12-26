import typing as t
from datetime import datetime

import arrow
import typer

from ledger_manager.api import use_cases
from ledger_manager.api.models import AggregationType, Consts, FloorType

from .common import CommonParams

app = typer.Typer(help="Custom reports.")


@app.command(context_settings={"ignore_unknown_options": True})
def balance(
        ctx: typer.Context,
        patterns: t.Optional[t.List[str]] = typer.Argument(None),
        end: datetime = typer.Option(arrow.now().datetime, formats=[Consts.DATE_FORMAT]),
        floor: t.Optional[FloorType] = typer.Option(None, "--last"),
        begin: t.Optional[datetime] = typer.Option(None, formats=[Consts.DATE_FORMAT]),
        exchange: t.Optional[str] = typer.Option(None, "--exchange", "-X"),
):
    """Current balance with Python-style regexes for accounts.

    Accepts begin/end parameter, or last period (set by --last option).
    """
    common_params: CommonParams = ctx.obj

    use_cases.balance(
        config=common_params.config,
        patterns=patterns,
        end=end,
        floor=floor,
        begin=begin,
        exchange=exchange,
    )


@app.command()
def assets(
        ctx: typer.Context,
        exchange: t.Optional[str] = typer.Option(None, "--exchange", "-X"),
):
    """Current state of `Assets` accounts excluding `Assets:Budget` ones."""

    common_params: CommonParams = ctx.obj

    use_cases.balance(
        config=common_params.config,
        patterns=["^Assets(?!:Budget).*"],
        exchange=exchange,
    )


@app.command()
def expenses(
        ctx: typer.Context,
        end: datetime = typer.Option(arrow.now().datetime, formats=[Consts.DATE_FORMAT]),
        floor: t.Optional[FloorType] = typer.Option(FloorType.month, "--last"),
        begin: t.Optional[datetime] = typer.Option(None, formats=[Consts.DATE_FORMAT]),
        exchange: t.Optional[str] = typer.Option(None, "--exchange", "-X"),
):
    """State of `Expenses` accounts for the given period (default is last month)."""
    common_params: CommonParams = ctx.obj

    use_cases.balance(
        config=common_params.config,
        patterns=["^Expenses.*"],
        end=end,
        floor=floor,
        begin=begin,
        exchange=exchange,
    )


@app.command()
def budget(
        ctx: typer.Context,
        exchange: t.Optional[str] = typer.Option(None, "--exchange", "-X"),
):
    """State of `Assets:Budget` accounts for the last month."""
    common_params: CommonParams = ctx.obj

    use_cases.balance(
        "--depth",
        "4",
        config=common_params.config,
        patterns=[
            "^Assets:Budget:Unbudgeted$",
            "^Assets:Budget:Expenses.*$",
        ],
        floor=FloorType.month,
        exchange=exchange,
    )


@app.command()
def average(
        ctx: typer.Context,
        patterns: t.Optional[t.List[str]] = typer.Argument(None),
        end: datetime = typer.Option(arrow.now().datetime, formats=[Consts.DATE_FORMAT]),
        floor: FloorType = typer.Option(FloorType.month, "--last"),
        aggregation: AggregationType = typer.Option(AggregationType.daily, "--agg"),
        begin: t.Optional[datetime] = typer.Option(None, formats=[Consts.DATE_FORMAT]),
        exchange: t.Optional[str] = typer.Option(None, "--exchange", "-X"),
):
    """Averaged history for given accounts.

    By default uses last month transactions aggregated by day.
    """
    common_params: CommonParams = ctx.obj

    use_cases.average(
        config=common_params.config,
        patterns=patterns,
        end=end,
        floor=floor,
        begin=begin,
        aggregation=aggregation,
        exchange=exchange,
    )
