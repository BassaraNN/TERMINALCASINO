from typing import List, Optional
import time
import shutil
import re
import sys
import casino.utils as utils

from casino.types import GameContext
from casino.utils import clear_screen, cprint, cinput, display_topbar
from casino.stats import display_stats

from ..constants import SEC_BTWN_SPIN, ROULETTE_TABLE, ROWS, COLS, STANDARD_AMERICAN_ROULETTE_WHEEL, STANDARD_EUROPEAN_ROULETTE_WHEEL

ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")

def _visible_len(s: str) -> int:
    return len(ANSI_RE.sub("", s))


def cprint_ansi_center(line: str, end: str = "\n") -> None:
    """Center a string that may contain ANSI escape codes."""
    width = shutil.get_terminal_size().columns
    vis = _visible_len(line)
    pad_left = max(0, (width - vis) // 2)
    print((" " * pad_left) + line, end=end)


def cprint_table_center(block: str) -> None:
    lines = block.strip("\n").splitlines()
    term_width = shutil.get_terminal_size().columns

    max_len = max(_visible_len(line) for line in lines)
    pad_left = max(0, (term_width - max_len) // 2)

    for line in lines:
        padded_line = " " * pad_left + line
        print(f"{utils.theme['color']}{padded_line}{utils.theme['reset']}")


def render_cell(num_str: str, color: str) -> str:
    bg = {"black": "40",
          "red": "41",
          "green": "42"}
    return f"\x1b[{bg[color]}m\x1b[97m{num_str}\x1b[0m"



class RouletteView:
    def __init__(self, ctx: GameContext, header_option: dict, table: str) -> None:
        self.context = ctx
        self.header_option = header_option
        self.table = table
        
    def display_roulette_topbar(self) -> None:
        display_topbar(self.context.account, self.header_option["header"], margin=self.header_option["margin"])

    def show_message(self, message: str, end: str = "\n") -> None:
        cprint(message, end=end)

    def show_table(self) -> None:
        cprint_table_center(self.table)

    def prompt(self, message: str) -> str:
        return cinput(message)

    def clear_screen(self) -> None:
        clear_screen()

    def pause(self, seconds: float) -> None:
        time.sleep(seconds)

    def show_stats(self, stats) -> None:
        display_stats(stats)


    def refresh_roulette_topbar(self) -> None:
        # Number of lines occupied by the topbar: header (3 lines) + user/balance line + margin
        header_lines = len(self.header_option["header"].strip("\n").splitlines())
        margin = self.header_option.get("margin", 1)
        total_lines = header_lines + 1 + margin

        sys.stdout.write("\x1b[s")  # Save current cursor position
        sys.stdout.write("\x1b[H")  # Move cursor to top-left corner

        # Clear all topbar lines
        for _ in range(total_lines):
            sys.stdout.write("\x1b[2K")  # clear line
            sys.stdout.write("\x1b[1B")  # down 1 line

        # Move back to top-left and redraw the topbar
        sys.stdout.write("\x1b[H")
        self.display_roulette_topbar()

        # Restore cursor position so the rest of the screen stays intact
        sys.stdout.write("\x1b[u")
        sys.stdout.flush()


    def render_outside_bets_menu(self) -> None:
        self.render_header()
        title = "Outside bets:"
        options = [
            "[1] Red / Black",
            "[2] Odd / Even",
            "[3] High / Low",
            "[4] Dozen",
            "[5] Column",
        ]

        content_width = max(len(title), *(len(o) for o in options))
        left_pad = 2
        right_pad = 2
        box_width = content_width + left_pad + right_pad

        cprint("┌" + "─" * box_width + "┐")
        cprint("│" + title.center(box_width) + "│")
        cprint("│" + " " * box_width + "│")

        for opt in options:
            line = " " * left_pad + opt.ljust(content_width) + " " * right_pad
            cprint("│" + line + "│")

        cprint("└" + "─" * box_width + "┘")
    
    def render_header(self) -> None:
        clear_screen()
        self.display_roulette_topbar()

    
    def print_wheel(self, wheel: list[tuple], highlighted_num = None) -> None:
        ROULETTE_GRID = [['  ' for _ in range(COLS)] for _ in range(ROWS)]
        
        # clear current grid
        for row in range(len(ROULETTE_GRID)):
            for col in range(len(ROULETTE_GRID[0])):
                ROULETTE_GRID[row][col] = ' ' # each empty spot is 2 spaces

        for (num_str, color, row, col) in wheel:
            # col += 29
            if num_str != "00" and int(num_str.strip()) < 10:
                num_str = " " + num_str
            if num_str.strip() == highlighted_num.strip():
                # the spot in the column before and column after the number become *'s
                ROULETTE_GRID[row][col-1] = "*"
                ROULETTE_GRID[row][col+1] = "*"

            if color == "green":
                ROULETTE_GRID[row][col] = f"\x1b[42m\x1b[97m{num_str}\x1b[0m"
            elif color == "black":
                ROULETTE_GRID[row][col] = f"\x1b[40m\x1b[97m{num_str}\x1b[0m"
            else:
                ROULETTE_GRID[row][col] = f"\x1b[41m\x1b[97m{num_str}\x1b[0m"

        wheel_lines = ["".join(row) for row in ROULETTE_GRID]
        for line in wheel_lines:
            cprint_ansi_center(line)
    
    def wheel_animation(self, wheel: list[tuple], sequence: list[str], sec_btwn_spins: float = SEC_BTWN_SPIN) -> None:
        for num in sequence:
            clear_screen()
            self.display_roulette_topbar()
            self.print_wheel(wheel, highlighted_num = num)
            time.sleep(sec_btwn_spins)


    def prompt_with_error(self, prompt: str, validator, error_text: str, render_table: bool = False,
                      transform=lambda s: s.strip().lower(),):
        last_error = ""
        while True:
            self.render_header()
            if render_table:
                cprint_table_center(self.table)
            if last_error:
                cprint(f"🤵: {last_error}")

            answer = transform(cinput(prompt))
            if validator(answer):
                return answer
            last_error = error_text
        
    
