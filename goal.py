"""CSC148 Assignment 2

=== CSC148 Winter 2020 ===
Department of Computer Science,
University of Toronto

This code is provided solely for the personal and private use of
students taking the CSC148 course at the University of Toronto.
Copying for purposes other than this use is expressly prohibited.
All forms of distribution of this code, whether as given or with
any changes, are expressly prohibited.

Authors: Diane Horton, David Liu, Mario Badr, Sophia Huynh, Misha Schwartz,
and Jaisie Sin

All of the files in this directory and all subdirectories are:
Copyright (c) Diane Horton, David Liu, Mario Badr, Sophia Huynh,
Misha Schwartz, and Jaisie Sin

=== Module Description ===

This file contains the hierarchy of Goal classes.
"""
from __future__ import annotations
import random
from typing import List, Tuple
from block import Block
from settings import colour_name, COLOUR_LIST


def generate_goals(num_goals: int) -> List[Goal]:
    """Return a randomly generated list of goals with length num_goals.

    All elements of the list must be the same type of goal, but each goal
    must have a different randomly generated colour from COLOUR_LIST. No two
    goals can have the same colour.

    Precondition:
        - num_goals <= len(COLOUR_LIST)
    """
    colour_copy = COLOUR_LIST[:]
    rand_goal = random.randint(0, 1)
    goals = []
    for _ in range(num_goals):
        clr = colour_copy.pop(random.randint(0, len(colour_copy) - 1))
        if rand_goal == 1:      # 1 refers to perimeter goal
            goals.append(PerimeterGoal(clr))
        else:       # 0 refers to blob goal
            goals.append(BlobGoal(clr))
    return goals


def _flatten(block: Block) -> List[List[Tuple[int, int, int]]]:
    """Return a two-dimensional list representing <block> as rows and columns of
    unit cells.

    Return a list of lists L, where,
    for 0 <= i, j < 2^{max_depth - self.level}
        - L[i] represents column i and
        - L[i][j] represents the unit cell at column i and row j.

    Each unit cell is represented by a tuple of 3 ints, which is the colour
    of the block at the cell location[i][j]

    L[0][0] represents the unit cell in the upper left corner of the Block.
    """
    if not block.children:
        flattened = []
        for _ in range(2 ** (block.max_depth - block.level)):
            col = []
            for _ in range(2 ** (block.max_depth - block.level)):
                col.append(block.colour)
            flattened.append(col)
    else:
        flattened = _flatten(block.children[1])
        for i in range((2 ** (block.max_depth - block.level))//2):
            flattened.append(_flatten(block.children[0])[i])
        for i in range((2 ** (block.max_depth - block.level)) // 2):
            flattened[i].extend(_flatten(block.children[2])[i])
        for i in range((2 ** (block.max_depth - block.level)) // 2):
            flattened[i + len(flattened)//2].\
                extend(_flatten(block.children[3])[i])
    return flattened


class Goal:
    """A player goal in the game of Blocky.

    This is an abstract class. Only child classes should be instantiated.

    === Attributes ===
    colour:
        The target colour for this goal, that is the colour to which
        this goal applies.
    """
    colour: Tuple[int, int, int]

    def __init__(self, target_colour: Tuple[int, int, int]) -> None:
        """Initialize this goal to have the given target colour.
        """
        self.colour = target_colour

    def score(self, board: Block) -> int:
        """Return the current score for this goal on the given board.

        The score is always greater than or equal to 0.
        """
        raise NotImplementedError

    def description(self) -> str:
        """Return a description of this goal.
        """
        raise NotImplementedError


class PerimeterGoal(Goal):
    """A player goal in the game of Blocky in which the player must aim to put
    the most possible units of a given colour on the outer perimeter of the
    board.

    The player’s score is the total number of unit cells of the given colour c
    that are on the perimeter. There is a premium on corner cells: they count
    twice towards the score.

    === Attributes ===
    colour:
        The target colour for this goal, that is the colour to which
        this goal applies.
    """
    colour: Tuple[int, int, int]

    def score(self, board: Block) -> int:
        """Return the current score for the perimeter goal on the given board.

        The score is always greater than or equal to 0.
        """
        flattened = _flatten(board)
        score = 0
        for x in range(len(flattened)):
            if flattened[x][0] == self.colour:
                score += 1
            if flattened[x][len(flattened) - 1] == self.colour:
                score += 1
            if flattened[0][x] == self.colour:
                score += 1
            if flattened[len(flattened) - 1][x] == self.colour:
                score += 1
        return score

    def description(self) -> str:
        """Return a precise string description of the perimeter goal and the
        target colour
        """
        target = colour_name(self.colour)
        description = f'Perimeter Goal:Put the most possible units of ' \
                      f'{target} cells on outer perimeter'
        return 'DESCRIPTION: ' + description


class BlobGoal(Goal):
    """A player goal in the game of Blocky where the player must aim for the
    largest “blob” of a given colour.

    A blob is a group of connected blocks with the same colour.

    Two blocks are connected if their sides touch; touching corners do not
    count.

    The player’s score is the number of unit cells in the largest blob of the
    given colour.

    === Attributes ===
    colour:
        The target colour for this goal, that is the colour to which
        this goal applies.
    """
    colour: Tuple[int, int, int]

    def score(self, board: Block) -> int:
        """Return the current score for blob goal on the given board.

        The score is always greater than or equal to 0.
        """
        flattened = _flatten(board)
        score = 0
        visited = []
        for _ in flattened:
            row_visited = []
            for _ in flattened[0]:
                row_visited.append(-1)
            visited.append(row_visited)
        for col in range(len(flattened)):
            for row in range(len(flattened[col])):
                if visited[col][row] == -1:
                    score = max(score, self._undiscovered_blob_size((col, row),
                                                                    flattened,
                                                                    visited))
        return score

    def _undiscovered_blob_size(self, pos: Tuple[int, int],
                                board: List[List[Tuple[int, int, int]]],
                                visited: List[List[int]]) -> int:
        """Return the size of the largest connected blob that (a) is of this
        Goal's target colour, (b) includes the cell at <pos>, and (c) involves
        only cells that have never been visited.

        If <pos> is out of bounds for <board>, return 0.

        <board> is the flattened board on which to search for the blob.
        <visited> is a parallel structure that, in each cell, contains:
            -1 if this cell has never been visited
            0  if this cell has been visited and discovered
               not to be of the target colour
            1  if this cell has been visited and discovered
               to be of the target colour

        Update <visited> so that all cells that are visited are marked with
        either 0 or 1.
        """
        col = pos[0]
        row = pos[1]
        if col < 0 or col >= len(board) or row < 0 or row >= len(board[0]):
            return 0
        elif visited[col][row] != -1:
            return 0
        elif board[col][row] != self.colour:
            visited[col][row] = 0
            return 0
        visited[col][row] = 1
        size = self._undiscovered_blob_size((col - 1, row), board, visited) + \
               self._undiscovered_blob_size((col, row - 1), board, visited) + \
               self._undiscovered_blob_size((col + 1, row), board, visited) + \
               self._undiscovered_blob_size((col, row + 1), board, visited)
        return size + 1

    def description(self) -> str:
        """Return a precise string description of blob goal and the
        target colour
        """

        target = colour_name(self.colour)
        description = f'Blob Goal: Aim for the largest group of connected ' \
                      f'{target} blocks'
        return 'DESCRIPTION: ' + description


if __name__ == '__main__':
    import python_ta
    python_ta.check_all(config={
        'allowed-import-modules': [
            'doctest', 'python_ta', 'random', 'typing', 'block', 'settings',
            'math', '__future__'
        ],
        'max-attributes': 15
    })
