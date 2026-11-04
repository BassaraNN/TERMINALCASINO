from typing import List, Optional

from casino.types import GameContext
from casino.accounts import Account
from casino.stats import GameStats
from ..base import Roulette

from ..constants import (
    ROULETTE_HEADER,
    HEADER_OPTIONS,
    STANDARD_AMERICAN_ROULETTE_WHEEL,
    ROULETTE_TABLE,
    SEC_BTWN_SPIN,
    TOTAL_ROTATIONS,
    ROWS,
    COLS,
)

class AmericanRoulette(Roulette):
    """Plays roulette using American rules."""

    def __init__(self, ctx: GameContext, accounts: List[Account]):
        super().__init__(ctx, accounts)
        self.wheel = STANDARD_AMERICAN_ROULETTE_WHEEL
        self.valid_numbers = [number for (number, _, _, _) in self.wheel]


def play_roulette(context: GameContext) -> None:
    continue_game = True

    # Temporary fix
    # TODO: fix argument in play_roulette to only except `List[GameContext]`
    # and not `GameContext`
    # Access account data
    accounts = [context.account]

    roulette = AmericanRoulette(context, accounts)
    stats = GameStats("American Roulette", context.account.balance)
    while continue_game:
        roulette.reset_round()
        roulette.view.render_header()

        # Input to stop loop from running constantly
        choice = roulette.view.prompt("Press [Enter] to start a new round and [q] to quit: ")

        if choice.lower() in {"q", "quit"}:
            continue_game = False
            break
        prev_balance = context.account.balance
        status = roulette.submit_bets(context)
        if status == "BANKRUPT":
            break

        roulette.spin_wheel(context)
        roulette.payout()
        if context.account.balance > prev_balance:
            stats.wins += 1
            stats.rounds_played += 1
        elif context.account.balance < prev_balance:
            stats.losses += 1
            stats.rounds_played += 1
        roulette.view.refresh_roulette_topbar()

        play_again = None

        while True:
            valid_choices = ["N", "NO", "Y", "YES", ""]
            play_again = roulette.view.prompt("🤵: Would you like to play another round (Y/n): ")

            if play_again.upper() not in valid_choices:
                roulette.view.show_message("Please enter 'Yes' or 'No'.")
                continue
            if play_again.lower() in {"n", "no"}:
                #cprint("Quitting roulette...")
                continue_game = False
                break
            elif play_again == "" or play_again.lower() in {"y", "yes"}:
                continue_game = True
                break
    stats.ending_balance = context.account.balance
    roulette.view.show_stats(stats)
    #cprint("Exiting roulette...")
    #sleep(0.5)
