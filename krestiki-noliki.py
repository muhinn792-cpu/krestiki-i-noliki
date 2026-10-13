from __future__ import annotations

import gc
import math
import os
import random
import sys

EMPTY = " "
HUMAN = "X"
BOT = "O"
MIN_SIZE = 3
MAX_SIZE = 12
CLEAR_AFTER = 50

printed_lines = 0
move_log: list[tuple[str, int, int]] = []


def flush_memory() -> None:
    global printed_lines
    os.system("cls" if os.name == "nt" else "clear")
    move_log.clear()
    printed_lines = 0
    gc.collect()


def bump(n: int) -> None:
    global printed_lines
    printed_lines += n


def say(text: str = "") -> None:
    print(text)
    bump(1)


def flush_if_needed(board: list[list[str]] | None = None) -> None:
    if printed_lines < CLEAR_AFTER:
        return
    flush_memory()
    if board is not None:
        render(board)


def ask_size() -> tuple[int, int]:
    while True:
        raw = input("Ширина и высота: ").strip().replace(",", " ").replace("x", " ").replace("х", " ")
        bump(1)
        parts = raw.split()
        if len(parts) != 2:
            continue
        try:
            width, height = int(parts[0]), int(parts[1])
        except ValueError:
            continue
        if MIN_SIZE <= width <= MAX_SIZE and MIN_SIZE <= height <= MAX_SIZE:
            return width, height


def new_board(height: int, width: int) -> list[list[str]]:
    return [[EMPTY for _ in range(width)] for _ in range(height)]


def win_length(height: int, width: int) -> int:
    return min(height, width)


def iter_windows(board: list[list[str]], k: int):
    height, width = len(board), len(board[0])
    for r in range(height):
        for c in range(width - k + 1):
            yield [board[r][c + i] for i in range(k)]
    for c in range(width):
        for r in range(height - k + 1):
            yield [board[r + i][c] for i in range(k)]
    for r in range(height - k + 1):
        for c in range(width - k + 1):
            yield [board[r + i][c + i] for i in range(k)]
    for r in range(height - k + 1):
        for c in range(k - 1, width):
            yield [board[r + i][c - i] for i in range(k)]


def winner_of(board: list[list[str]], k: int) -> str | None:
    for window in iter_windows(board, k):
        first = window[0]
        if first != EMPTY and all(cell == first for cell in window):
            return first
    return None


def empty_cells(board: list[list[str]]) -> list[tuple[int, int]]:
    return [
        (r, c)
        for r, row in enumerate(board)
        for c, cell in enumerate(row)
        if cell == EMPTY
    ]


def board_full(board: list[list[str]]) -> bool:
    return not empty_cells(board)


def render(board: list[list[str]]) -> None:
    height, width = len(board), len(board[0])
    col_w = max(3, len(str(width)) + 2)
    row_w = max(2, len(str(height)))
    header = " " * (row_w + 1) + "".join(str(c + 1).center(col_w) for c in range(width))
    line = " " * row_w + "+" + "+".join("-" * col_w for _ in range(width)) + "+"
    print()
    print(header)
    print(line)
    rows_printed = 3
    for r, row in enumerate(board):
        cells = "|".join(row[c].center(col_w) for c in range(width))
        print(f"{str(r + 1).rjust(row_w)}|{cells}|")
        print(line)
        rows_printed += 2
    print()
    rows_printed += 1
    bump(rows_printed)


def evaluate(board: list[list[str]], k: int, me: str, foe: str) -> int:
    score = 0
    weights = [0] + [10 ** (n - 1) for n in range(1, k + 1)]
    for window in iter_windows(board, k):
        mine = window.count(me)
        theirs = window.count(foe)
        if mine and theirs:
            continue
        if mine:
            if mine == k:
                return 10 ** 8
            score += weights[mine]
        elif theirs:
            if theirs == k:
                return -(10 ** 8)
            score -= weights[theirs] * 2
    height, width = len(board), len(board[0])
    cr, cc = (height - 1) / 2, (width - 1) / 2
    for r, row in enumerate(board):
        for c, cell in enumerate(row):
            dist = abs(r - cr) + abs(c - cc)
            bonus = max(0, int((height + width) - dist))
            if cell == me:
                score += bonus
            elif cell == foe:
                score -= bonus
    return score


def search_depth(empty_count: int) -> int:
    if empty_count <= 9:
        return empty_count
    if empty_count <= 12:
        return 6
    if empty_count <= 16:
        return 5
    if empty_count <= 25:
        return 4
    return 3


def ordered_moves(board: list[list[str]]) -> list[tuple[int, int]]:
    height, width = len(board), len(board[0])
    cr, cc = (height - 1) / 2, (width - 1) / 2
    cells = empty_cells(board)
    cells.sort(key=lambda rc: (abs(rc[0] - cr) + abs(rc[1] - cc), rc[0], rc[1]))
    return cells


def would_win(board: list[list[str]], r: int, c: int, symbol: str, k: int) -> bool:
    board[r][c] = symbol
    won = winner_of(board, k) == symbol
    board[r][c] = EMPTY
    return won


def alphabeta(
    board: list[list[str]],
    depth: int,
    alpha: int,
    beta: int,
    maximizing: bool,
    k: int,
    me: str,
    foe: str,
) -> int:
    w = winner_of(board, k)
    if w == me:
        return 10 ** 8 + depth
    if w == foe:
        return -(10 ** 8) - depth
    empties = ordered_moves(board)
    if depth == 0 or not empties:
        return evaluate(board, k, me, foe)

    if maximizing:
        best = -math.inf
        for r, c in empties:
            board[r][c] = me
            val = alphabeta(board, depth - 1, alpha, beta, False, k, me, foe)
            board[r][c] = EMPTY
            if val > best:
                best = val
            if best > alpha:
                alpha = best
            if beta <= alpha:
                break
        return int(best)

    best = math.inf
    for r, c in empties:
        board[r][c] = foe
        val = alphabeta(board, depth - 1, alpha, beta, True, k, me, foe)
        board[r][c] = EMPTY
        if val < best:
            best = val
        if best < beta:
            beta = best
        if beta <= alpha:
            break
    return int(best)


def bot_move(board: list[list[str]], k: int, me: str, foe: str) -> tuple[int, int]:
    moves = ordered_moves(board)
    if not moves:
        raise RuntimeError("нет клеток")

    for r, c in moves:
        if would_win(board, r, c, me, k):
            return r, c
    for r, c in moves:
        if would_win(board, r, c, foe, k):
            return r, c

    depth = search_depth(len(moves))
    best_score = -math.inf
    best_cells: list[tuple[int, int]] = [moves[0]]
    for r, c in moves:
        board[r][c] = me
        score = alphabeta(board, depth - 1, -math.inf, math.inf, False, k, me, foe)
        board[r][c] = EMPTY
        if score > best_score:
            best_score = score
            best_cells = [(r, c)]
        elif score == best_score:
            best_cells.append((r, c))
    return random.choice(best_cells)


def ask_human_move(board: list[list[str]]) -> tuple[int, int]:
    height, width = len(board), len(board[0])
    while True:
        raw = input("Ход: ").strip()
        bump(1)
        parts = raw.replace(",", " ").split()
        if len(parts) != 2:
            continue
        try:
            row, col = int(parts[0]), int(parts[1])
        except ValueError:
            continue
        if not (1 <= row <= height and 1 <= col <= width):
            continue
        r, c = row - 1, col - 1
        if board[r][c] != EMPTY:
            continue
        return r, c


def who_starts() -> str:
    starter = random.choice(["human", "bot"])
    if starter == "human":
        say("Первый: ты (X)")
    else:
        say("Первый: бот (X)")
    return starter


def wipe_progress(board: list[list[str]] | None = None) -> None:
    if board is not None:
        for row in board:
            for i in range(len(row)):
                row[i] = EMPTY
        board.clear()
    move_log.clear()
    flush_memory()


def play_once() -> list[list[str]]:
    width, height = ask_size()
    k = win_length(height, width)
    board = new_board(height, width)

    starter = who_starts()
    if starter == "human":
        human_sym, bot_sym = HUMAN, BOT
        turn = "human"
    else:
        human_sym, bot_sym = BOT, HUMAN
        turn = "bot"

    render(board)

    while True:
        flush_if_needed(board)
        if turn == "human":
            r, c = ask_human_move(board)
            board[r][c] = human_sym
            move_log.append((human_sym, r, c))
        else:
            r, c = bot_move(board, k, bot_sym, human_sym)
            board[r][c] = bot_sym
            move_log.append((bot_sym, r, c))
            say(f"{bot_sym}: {r + 1} {c + 1}")

        render(board)

        won = winner_of(board, k)
        if won == human_sym:
            say("Победа")
            return board
        if won == bot_sym:
            say("Поражение")
            return board
        if board_full(board):
            say("Ничья")
            return board

        turn = "bot" if turn == "human" else "human"


def ask_again() -> bool:
    while True:
        raw = input("да/нет: ").strip().lower()
        if raw in {"д", "да", "y", "yes"}:
            return True
        if raw in {"н", "нет", "n", "no"}:
            return False


def restart_game() -> None:
    os.execv(sys.executable, [sys.executable, *sys.argv])


def main() -> None:
    while True:
        board = play_once()
        again = ask_again()
        wipe_progress(board)
        if not again:
            sys.exit(0)
        restart_game()


if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        sys.exit(0)
