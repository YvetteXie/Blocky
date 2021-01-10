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
Misha Schwartz, and Jaisie Sin.

=== Module Description ===

This file contains the hierarchy of player classes.
"""
from __future__ import annotations
from typing import List, Optional, Tuple
import random
import pygame

from block import Block
from goal import Goal, generate_goals

from actions import KEY_ACTION, ROTATE_CLOCKWISE, ROTATE_COUNTER_CLOCKWISE, \
    SWAP_HORIZONTAL, SWAP_VERTICAL, SMASH, PASS, PAINT, COMBINE


def create_players(num_human: int, num_random: int, smart_players: List[int]) \
        -> List[Player]:
    """Return a new list of Player objects.

    <num_human> is the number of human player, <num_random> is the number of
    random players, and <smart_players> is a list of difficulty levels for each
    SmartPlayer that is to be created.

    The list should contain <num_human> HumanPlayer objects first, then
    <num_random> RandomPlayer objects, then the same number of SmartPlayer
    objects as the length of <smart_players>. The difficulty levels in
    <smart_players> should be applied to each SmartPlayer object, in order.
    """
    players = []
    colours = []
    num_players = num_human + num_random + len(smart_players)
    for i in range(num_players):
        goal = generate_goals(1)[0]
        while goal.colour in colours:
            goal = generate_goals(1)[0]
        colours.append(goal.colour)
        if i < num_human:
            players.append(HumanPlayer(i, goal))
        elif num_human <= i < num_human + num_random:
            players.append(RandomPlayer(i, goal))
        else:
            difficulty = smart_players[i - num_human - num_random]
            players.append(SmartPlayer(i, goal, difficulty))
    return players


def _get_block(block: Block, location: Tuple[int, int], level: int) -> \
        Optional[Block]:
    """Return the Block within <block> that is at <level> and includes
    <location>. <location> is a coordinate-pair (x, y).

    A block includes all locations that are strictly inside of it, as well as
    locations on the top and left edges. A block does not include locations that
    are on the bottom or right edge.

    If a Block includes <location>, then so do its ancestors. <level> specifies
    which of these blocks to return. If <level> is greater than the level of
    the deepest block that includes <location>, then return that deepest block.

    If no Block can be found at <location>, return None.

    Preconditions:
        - 0 <= level <= max_depth
    """
    if not (block.position[0] <= location[0] < (block.position[0] + block.size)
            and block.position[1] <= location[1] < (block.position[1] +
                                                    block.size)):
        return None
    if block.level == level or (block.level < level and not block.children):
        return block
    else:
        target = None
        for child in block.children:
            if _get_block(child, location, level) is not None:
                target = _get_block(child, location, level)
        return target


def _get_random_block(player: Player, board: Block) -> Block:
    """Return a randomly selected block in <board> for <player>.
    Note that the selected block can be <board> itself.
    """
    selected_block = None
    if not board.children:
        selected_block = board
    else:
        pos_x = board.position[0]
        pos_y = board.position[1]
        while selected_block is None or (selected_block.level ==
                                         board.max_depth and
                                         selected_block.colour ==
                                         player.goal.colour):
            x = random.randint(pos_x, pos_x + board.size - 1)
            y = random.randint(pos_y, pos_y + board.size - 1)
            level = random.randint(0, board.max_depth)
            selected_block = _get_block(board, (x, y), level)
    return selected_block


def _get_valid_actions(player: Player, board: Block) -> \
        List[Tuple[str, Optional[int]]]:
    """Return a list of tuples representing the valid actions that <player> can
    perform on <board>.
    """
    valid_move = []
    for action in [ROTATE_CLOCKWISE, ROTATE_COUNTER_CLOCKWISE, SWAP_HORIZONTAL,
                   SWAP_VERTICAL, SMASH, PAINT, COMBINE]:
        copy_board = board.create_copy()
        successful = False
        if action == PAINT:
            successful = copy_board.paint(player.goal.colour)
        elif action == COMBINE:
            successful = copy_board.combine()
        elif action in [ROTATE_CLOCKWISE, ROTATE_COUNTER_CLOCKWISE]:
            successful = copy_board.rotate(action[1])
        elif action in [SWAP_VERTICAL, SWAP_HORIZONTAL]:
            successful = copy_board.swap(action[1])
        elif action == SMASH:
            successful = copy_board.smash()

        if successful:
            valid_move.append(action)
    return valid_move


class Player:
    """A player in the Blocky game.

    This is an abstract class. Only child classes should be instantiated.

    === Public Attributes ===
    id:
        This player's number.
    goal:
        This player's assigned goal for the game.
    """
    id: int
    goal: Goal

    def __init__(self, player_id: int, goal: Goal) -> None:
        """Initialize this Player.
        """
        self.goal = goal
        self.id = player_id

    def get_selected_block(self, board: Block) -> Optional[Block]:
        """Return the block that is currently selected by the player.

        If no block is selected by the player, return None.
        """
        raise NotImplementedError

    def process_event(self, event: pygame.event.Event) -> None:
        """Update this player based on the pygame event.
        """
        raise NotImplementedError

    def generate_move(self, board: Block) -> \
            Optional[Tuple[str, Optional[int], Block]]:
        """Return a potential move to make on the game board.

        The move is a tuple consisting of a string, an optional integer, and
        a block. The string indicates the move being made (i.e., rotate, swap,
        or smash). The integer indicates the direction (i.e., for rotate and
        swap). And the block indicates which block is being acted on.

        Return None if no move can be made, yet.
        """
        raise NotImplementedError


def _create_move(action: Tuple[str, Optional[int]], block: Block) -> \
        Tuple[str, Optional[int], Block]:
    """Return a move that will be preformed on <block>.

    The move is a tuple consisting of a string, an optional integer, and
    a block. The string and the optional integer is the <action>, where the
    string indicates the move being made (i.e., rotate, swap, or smash), and the
    integer indicates the direction (i.e., for rotate and swap). And the block
    indicates which block is being acted on.
    """
    return action[0], action[1], block


class HumanPlayer(Player):
    """A human player that chooses moves based on user input.

    === Private Attributes ===
    _level:
        The level of the Block that the user selected most recently.
    _desired_action:
        The most recent action that the user is attempting to do.

    == Representation Invariants concerning the private attributes ==
        _level >= 0
    """
    id: int
    goal: Goal
    _level: int
    _desired_action: Optional[Tuple[str, Optional[int]]]

    def __init__(self, player_id: int, goal: Goal) -> None:
        """Initialize this HumanPlayer with the given <renderer>, <player_id>
        and <goal>.
        """
        Player.__init__(self, player_id, goal)

        # This HumanPlayer has not yet selected a block, so set _level to 0
        # and _selected_block to None.
        self._level = 0
        self._desired_action = None

    def get_selected_block(self, board: Block) -> Optional[Block]:
        """Return the block that is currently selected by the player based on
        the position of the mouse on the screen and the player's desired level.

        If no block is selected by the player, return None.
        """
        mouse_pos = pygame.mouse.get_pos()
        block = _get_block(board, mouse_pos, min(self._level, board.max_depth))

        return block

    def process_event(self, event: pygame.event.Event) -> None:
        """Respond to the relevant keyboard events made by the player based on
        the mapping in KEY_ACTION, as well as the W and S keys for changing
        the level.
        """
        if event.type == pygame.KEYDOWN:
            if event.key in KEY_ACTION:
                self._desired_action = KEY_ACTION[event.key]
            elif event.key == pygame.K_w:
                self._level = max(0, self._level - 1)
                self._desired_action = None
            elif event.key == pygame.K_s:
                self._level += 1
                self._desired_action = None

    def generate_move(self, board: Block) -> \
            Optional[Tuple[str, Optional[int], Block]]:
        """Return the move that the player would like to perform. The move may
        not be valid.

        Return None if the player is not currently selecting a block.
        """
        block = self.get_selected_block(board)

        if block is None or self._desired_action is None:
            return None
        else:
            move = _create_move(self._desired_action, block)

            self._desired_action = None
            return move


class RandomPlayer(Player):
    """A random player, which is a computer player that, as the name implies,
    chooses moves randomly.

    === Private Attributes ===
    _proceed:
        True when the player should make a move, False when the player should
    wait.
    """
    id: int
    goal: Goal
    _proceed: bool

    def __init__(self, player_id: int, goal: Goal) -> None:
        """Initialize this RandomPlayer with the given <player_id> and <goal>.
        """
        Player.__init__(self, player_id, goal)
        self._proceed = False

    def get_selected_block(self, board: Block) -> Optional[Block]:
        """Return the block on <board> that is currently selected by the
        RandomPlayer.

        If no block is selected, return None. Note that the RandomPlayer never
        selects any block.
        """
        return None

    def process_event(self, event: pygame.event.Event) -> None:
        """Communicates that the RandomPlayer should make a move by setting
        _proceed to True iff the user clicks their mouse.
        """
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self._proceed = True

    def generate_move(self, board: Block) -> \
            Optional[Tuple[str, Optional[int], Block]]:
        """Return a valid, randomly generated move.

        A valid move is a move other than PASS that can be successfully
        performed on the <board>.

        This function does not mutate <board>.
        """
        if not self._proceed:
            return None  # Do not remove
        selected_block = _get_random_block(self, board)
        valid_actions = _get_valid_actions(self, selected_block)
        self._proceed = False  # Must set to False before returning!
        if not valid_actions:
            return None
        else:
            selected_action = random.choice(valid_actions)
            return _create_move(selected_action, selected_block)


class SmartPlayer(Player):
    """A smart player, which a computer player that chooses moves more
    intelligently: It generates a set of random moves and, for each move, checks
    what its score would be if it were to make that move. Then it picks the one
    that yields the best score.

    === Private Attributes ===
    _proceed:
        True when the player should make a move, False when the player should
    wait.
    _difficulty:
        A level which indicates how difficult it is to play against it.

    == Representation Invariants concerning the private attributes ==
        _difficulty >= 0
    """
    id: int
    goal: Goal
    _proceed: bool
    _difficulty: int

    def __init__(self, player_id: int, goal: Goal, difficulty: int) -> None:
        """Initialize this SmartPlayer with the given <player_id>, <goal>,
        and <difficulty>.
        """
        Player.__init__(self, player_id, goal)
        self._difficulty = difficulty
        self._proceed = False

    def get_selected_block(self, board: Block) -> Optional[Block]:
        """Return the block on <board> that is currently selected by the
        SmartPlayer.

        If no block is selected, return None. Note that the SmartPlayer never
        selects any block.
        """
        return None

    def process_event(self, event: pygame.event.Event) -> None:
        """Communicates that the SmartPlayer should make a move by setting
        _proceed to True iff the user clicks their mouse.
        """
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self._proceed = True

    def generate_move(self, board: Block) -> \
            Optional[Tuple[str, Optional[int], Block]]:
        """Return a valid move by assessing multiple valid moves and choosing
        the move that results in the highest score for this player's goal (i.e.,
        disregarding penalties).

        A valid move is a move other than PASS that can be successfully
        performed on the <board>. If no move can be found that is better than
        the current score, this player will pass.

        This function does not mutate <board>.
        """
        if not self._proceed:
            return None  # Do not remove
        self._proceed = False  # Must set to False before returning!
        improved = 0
        best_move = None
        best_block = None
        score = self.goal.score(board)
        all_actions = [ROTATE_CLOCKWISE, ROTATE_COUNTER_CLOCKWISE,
                       SWAP_VERTICAL, SWAP_HORIZONTAL, PAINT, COMBINE, SMASH]

        for _ in range(self._difficulty):
            copy_board = board.create_copy()
            selected_block = _get_random_block(self, copy_board)
            valid_actions = _get_valid_actions(self, selected_block)
            if not valid_actions:
                rand_action = PASS
            else:
                rand_action = random.choice(valid_actions)
                while rand_action not in valid_actions:
                    rand_action = random.choice(all_actions)
            if rand_action == PAINT:
                selected_block.paint(self.goal.colour)
            elif rand_action == COMBINE:
                selected_block.combine()
            elif rand_action in [ROTATE_CLOCKWISE, ROTATE_COUNTER_CLOCKWISE]:
                selected_block.rotate(rand_action[1])
            elif rand_action in [SWAP_VERTICAL, SWAP_HORIZONTAL]:
                selected_block.swap(rand_action[1])
            elif rand_action == SMASH:
                selected_block.smash()

            if self.goal.score(copy_board) - score > improved:
                improved = self.goal.score(copy_board) - score
                best_move = rand_action
                best_block = selected_block

        if improved == 0:
            return _create_move(PASS, board)
        else:
            original_block = _get_block(board, best_block.position,
                                        best_block.level)
            return _create_move(best_move, original_block)


if __name__ == '__main__':
    import python_ta
    python_ta.check_all(config={
        'allowed-io': ['process_event'],
        'allowed-import-modules': [
            'doctest', 'python_ta', 'random', 'typing', 'actions', 'block',
            'goal', 'pygame', '__future__'
        ],
        'max-attributes': 10,
        'generated-members': 'pygame.*'
    })
