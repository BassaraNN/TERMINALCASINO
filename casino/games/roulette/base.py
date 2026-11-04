import random
from typing import List, Optional
from casino.types import GameContext
from casino.accounts import Account
from .views import RouletteView

from .constants import (
    ROULETTE_HEADER,
    HEADER_OPTIONS,
    STANDARD_AMERICAN_ROULETTE_WHEEL,
    ROULETTE_TABLE,
    TOTAL_ROTATIONS,
    SEC_BTWN_SPIN,
    COLS,
    ROWS
)




class Roulette:
    """
    Abstract base class to play roulette.

    Only contains base functions to run roulette.

    Attributes:
        wheel (list[tuple[str, str]]): The roulette wheel, where each entry is
            a tuple like ("0", "green").
        accounts (list[Account]): List of all player accounts.
        bets (dict[str, dict[str, str, int]]): Maps each account UUID to a bet record.

        Each key is a unique account UUID, and each value is a dictionary with the fields:
            {
                "type": bet_type,
                "value": bet_value,
                "amount": bet_amount
            }

        Example:
            {
                "uuid_1": {"type": "color", "value": "red", "amount": 100},
                "uuid_2": {"type": "number", "value": "00", "amount": 50}
            }
        
    """
    headers = HEADER_OPTIONS
    tables = ROULETTE_TABLE


    def __init__(self, ctx: GameContext, accounts: List[Account]) -> None:
        """
        Initializes roulette
        """
        # Will be populated with numbers and colors
        self.wheel = list[tuple[str, str, int, int]]()

        # Colors on wheel. Includes initials
        self.valid_colors = ["red", "green", "black", "r", "g", "b"]
        self.valid_numbers = []

        self.accounts = accounts

        # Current round's bets
        self.bets = {}
        self.winning_value: Optional[tuple[str, str]] = None

        self.context = ctx
        self.view = RouletteView(ctx, self.headers, self.tables)

    @staticmethod
    def normalize_color(input_value: str) -> str:
        """
        Standardize color input from user.

        The `Roulette` class permits the user to input a shorthand version of the color,
        or the name of the color itself. This function standardizes all colors to:

            "red", "green", "black"
        """
        color_map = {
            "r": "red",
            "red": "red",
            "g": "green",
            "green": "green",
            "b": "black",
            "black": "black"
        }
        return color_map.get(input_value.lower(), input_value)

    @staticmethod
    def normalize_type(input_value: str) -> str:
        """
        Standardize bet type from user.

        The `Roulette` class permits the user to input a shorthand version of the type of bet they want,
        or the name of the bet type itself. This function standardizes all bet types to:

            "color", "number"
        """
        type_map = {
            "c" : "color",
            "color" : "color",
            "n" : "number",
            "number" : "number"
        }
        return type_map.get(input_value.lower(), input_value)

    @staticmethod
    def roulette_sort_key(value : str) -> int:
        """
        Sorts values in roulette. Used as a key in the `sorted()` function.
        """
        if value == "0":
            return -1
        elif value == "00":
            return 0
        return int(value)

    

    def spin_wheel(self, ctx: GameContext) -> tuple[str, str, int, int]:
        """
        Pick a winning color and number.

        Returns:
            tuple[str, str]: A tuple containing:
                - str: The winning number (e.g., "28", "00", "0")
                - str: The winning color (either "red", "green", or "black")
        """

        #cprint("Spinning wheel...")

        random_index = random.randint(0, len(self.wheel) - 1)
        self.winning_value = self.wheel[random_index]

        wheel_sequence = [num for num, _, _, _ in self.wheel]

        # do TOTAL_ROTATIONS number of rotations before landing on number
        sequence = (wheel_sequence * TOTAL_ROTATIONS) + wheel_sequence[:random_index + 1]
        self.view.wheel_animation(self.wheel, sequence)

        winning_number = self.winning_value[0]
        winning_color  = self.winning_value[1]

        self.view.show_message(f"Winning number: {winning_number}")
        self.view.show_message(f"Winning color: {winning_color}")

        return self.winning_value

    def reset_round(self) -> None:
        self.bets.clear()
        self.winning_value = None

    def submit_bets(self, ctx: GameContext) -> None | str:
        """
        Instruct users to submit bets.

        This function will ask users if they would like to submit a bet
        on a color or a number.

        - If users pick color, they can pick either red, green, or black
        - If users pick number, they can pick a number to bet on.
        """

        # Loop over all users
        i = 0
        while (i < len(self.accounts)):
            player_balances = 0
            for account in self.accounts:
                player_balances += account.balance
            
            if player_balances == 0:
                self.view.show_message("ERROR: All players have gone bankrupt. "
                                       "You cannot play any more roulette.")
                self.view.pause(3)
                return "BANKRUPT"

            if (self.accounts[i].balance == 0):
                self.view.show_message(f"Skipping player {i+1} because of empty balance...")
                i += 1
                continue

            will_bet = self.view.prompt(f"🤵: Would you like to bet, Player {i+1} (y/N): ")

            if will_bet == "" or will_bet.lower() in {"n", "no"}:
                self.view.show_message("User skipped betting. Moving to next user...", end="\n\n")
                i += 1
                continue
            elif will_bet.upper() == "Y" or will_bet.upper() == "YES":
                pass
            else:
                self.view.show_message("Invalid input. Enter either 'Y' for yes or 'N' for no.")
                continue

            self.view.clear_screen()
            self.view.display_roulette_topbar()
            # Input bet amount
            bet_amount = self.view.prompt(f"Player {i+1}'s Bet: ")

            # Check bet_amount is a positive integer
            try:
                bet_amount = int(bet_amount)

                if (bet_amount < 0):
                    raise ValueError
            except ValueError:
                self.view.show_message(f"ERROR: '{bet_amount}' is not a valid number. "
                                       "Please enter a positive integer.", end="\n\n")
                continue

            # Check that account has enough money to bet
            try:
                self.accounts[i].withdraw(bet_amount)
            except ValueError as error:
                if error.args and error.args[0] == "Insufficient balance":
                    self.view.show_message("Insufficient balance to place bet. Please enter a "
                                           f"bet less thanor equal to {self.accounts[i].balance}")
                continue

            self.view.clear_screen()
            self.view.display_roulette_topbar()
            self.view.show_message(f"Successfully withdrew {bet_amount} coins from Player {i+1}.")
            self.view.show_message(f"Player {i+1} remaining balance: "
                                   f"{self.accounts[i].balance} coins.")

            # Ask for desired bet type
            bet_type = ""
            valid_bet_types = ["C", "COLOR", "N", "NUMBER"]

            while True:
                bet_type = self.view.prompt(
                    "🤵: Would you like to bet on a color or a number? (C or N): "
                ).strip()

                if (bet_type.upper() in valid_bet_types):
                    break
                else:
                    self.view.show_message("Error: Invalid bet type. "
                                           "Choose either 'color' or 'number'.")

            self.view.clear_screen()
            self.view.display_roulette_topbar()

            ############################################################

            # Ask for user's specific bet
            bet_value = ""

            # Color betting
            if bet_type.lower() in {"c", "color"}:
                while True:
                    bet_value = self.view.prompt(
                        "Enter color you want to bet on (red, black, green): "
                    )
                    if bet_value.lower() in self.valid_colors:
                        break
                    else:
                        self.view.show_message("Error: Chosen color is not red, green, or black.")
            
            # Number betting
            elif bet_type.lower() in {"n", "number"}:
                while True:
                    self.view.show_table()
                    bet_value = self.view.prompt("Enter number you would like to bet on: ")

                    if bet_value in self.valid_numbers:
                        break
                    else:
                        self.view.show_message("Error: You may only enter one of the following "
                                               "numbers.")
                        sorted_numbers = sorted(self.valid_numbers,
                                                key=self.roulette_sort_key)
                        valid_numbers_str = ", ".join(sorted_numbers)
                        self.view.show_message("\t" + valid_numbers_str)
         
            # Once values are successfully chosen, save to dictionary
            account_id = str(self.accounts[i].aid)
            self.bets[account_id] = {
                "type"   : Roulette.normalize_type(bet_type.lower()),
                "value"  : Roulette.normalize_color(bet_value.lower()),
                "amount" : bet_amount
            }
            i += 1  # Move to next user

    def payout(self) -> None:
        """
        Pay out all players who picked the right color or number.
        """
        assert self.winning_value is not None
        winning_number = self.winning_value[0]
        winning_color  = self.winning_value[1]

        self.view.show_message("Paying out all winners...")
        # Loop over accounts (not bets) so each payout goes to the right player,
        # even if an earlier player skipped betting this round
        for i, account in enumerate(self.accounts):
            bet = self.bets.get(str(account.aid))
            if bet is None:
                continue

            bet_type   = bet["type"]
            bet_value  = bet["value"]
            bet_amount = bet["amount"]

            win_multiplier = 1
            # Check if user won
            if bet_type == "color" and bet_value == winning_color:
                if bet_value == "green":
                    win_multiplier += 35
                else:
                    # Find account and pay back two times original bet
                    win_multiplier += 1
            elif bet_type == "number" and bet_value == winning_number:
                # Find account and pay back 36 times original amount
                win_multiplier += 35

            if win_multiplier > 1:
                win_amount = bet_amount * win_multiplier
                account.deposit(win_amount)
                self.view.show_message(f"Player {i+1}: Won {win_amount} coins.")
            else:
                self.view.show_message(f"Player {i+1}: Lost {bet_amount} coins.")

        self.view.show_message("Finished payout.")
