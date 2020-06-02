"""
Author:      XuLin Yang
Student id:  904904
Date:        
Description: 
"""

from advance_model import *
from collections import Counter
from copy import deepcopy


def seeTile(tile_grab: TileGrab):
    print(
        [tile_grab.tile_type,
         tile_grab.number,
         tile_grab.pattern_line_dest,
         tile_grab.num_to_pattern_line,
         tile_grab.num_to_floor_line])


class myPlayer(AdvancePlayer):
    IGNORE_BONUS_THRESHOLD = 3

    # initialize
    # The following function should not be changed at all
    def __init__(self, _id):
        super().__init__(_id)
        self.weights = [1, -0.4, 0.015]
        self.curr_round = -1

    # Each player is given 5 seconds when a new round started
    # If exceeds 5 seconds, all your code will be terminated and
    # you will receive a timeout warning
    def StartRound(self, game_state: GameState):
        self.curr_round += 1
        print("---------- round", self.curr_round, "start ------------")
        return None

    # Each player is given 1 second to select next best move
    # If exceeds 5 seconds, all your code will be terminated,
    # a random action will be selected, and you will receive
    # a timeout warning
    def SelectMove(self, moves: [(Move, int, TileGrab)], game_state: GameState):
        # move[1] is factory ID that illustrate the source of tile, -1 for center
        move_collection = dict()

        # # FIXME this will timeout, think another way to consider opponent action
        # for p in game_state.players:
        #     if p.id != self.id:
        #         self.other_available = p.GetAvailableMoves()

        for m in moves:
            move_collection[m] = self.getQValue(game_state, m)

        # find the action with highest Q value
        maxQ = float("-inf")
        curr_max = None
        for key in move_collection.keys():
            if move_collection[key] > maxQ:
                curr_max = key
                maxQ = move_collection[key]

        ns = self.getNextState(game_state, curr_max)

        print("   ", self.id, ":", self.featureExtractor(game_state, curr_max))
        print("   ", "this:", self.expectScore(game_state), " that:", self.expectScore(ns))
        print("")
        return curr_max

    def getQValue(self, game_state: GameState, action) -> float:
        """get the Q value for a specify state with the performed action"""
        q_value = 0.0
        features = self.featureExtractor(game_state, action)

        for i in range(len(self.weights)):
            q_value += self.weights[i] * features[i]

        return q_value

    def update(self, game_state: GameState, action) -> None:
        """
            update weight, this will be called at the beginning of each state to
            update the parameters for previous state and action
        """
        next_state = self.getNextState(game_state, action)
        reward = 0

    def featureExtractor(self, game_state: GameState, move: (Move, int, TileGrab)) -> list:
        """
        return the feature that we extract from a specific game state
        that can be used for Q value calculation

        feature = [expected score, bonus at end]

        :return a dictionary that contains the value we want to use in this game
        """
        features = []
        next_state = self.getNextState(game_state, move)

        # expected score for the current action exec
        if self.curr_round < myPlayer.IGNORE_BONUS_THRESHOLD:
            expect_gain = self.expectGain(game_state, next_state)

            # TODO: examine this field
            # suppose 90% of game end in 5 rounds
            if move[0] == Move.TAKE_FROM_CENTRE and not game_state.first_player_taken and \
                    self.curr_round < 4:
                # get first player token
                expect_gain += 1

            # only ignore the positive mark
            if expect_gain > 0:
                expect_gain *= 0.1

            features.append(expect_gain)
        else:
            features.append(self.expectGain(game_state, next_state))

        # penalise add only a few grad to a long pattern
        tile_grab: TileGrab = move[-1]
        line_n = game_state.players[self.id].lines_number

        if tile_grab.pattern_line_dest != -1:
            if line_n[tile_grab.pattern_line_dest] == 0:
                # total capacity - tile already have - # we going to add
                remains = (tile_grab.pattern_line_dest + 1) - tile_grab.num_to_pattern_line
                features.append(remains)
            else:
                features.append(0)
        else:
            features.append(0)

        # give a slightly higher point to collect more
        features.append(move[-1].num_to_pattern_line)

        # # give bonus to the line that
        # if tile_grab.pattern_line_dest != -1:
        #     features.append(line_n[tile_grab.pattern_line_dest])
        # else:
        #     features.append(0)

        return features

    def getNextState(self, game_state: GameState, action) -> GameState:
        """give a state and action, return the next state"""
        next_state: GameState = deepcopy(game_state)
        next_state.ExecuteMove(self.id, action)
        return next_state

    def expectGain(self, curr_state, next_state):
        curr_expected_score, curr_bonus = self.expectScore(curr_state)
        next_expected_score, next_bonus = self.expectScore(next_state)

        return next_expected_score + next_bonus - curr_expected_score - curr_bonus

    def expectScore(self, state: GameState):
        """
            calculate the expected reward for a state, including the end of game score
            :param state should be deep copied state and applied the selected action
        """
        my_state: PlayerState = state.players[self.id]
        expected_score, _ = ScoreRound(my_state)
        bonus = my_state.EndOfGameScore()
        return expected_score, bonus

    def flipCoin(self) -> bool:
        return True if random.random() < self.epsilon else False


def ScoreRound(player_state: PlayerState):
    used_tiles = []

    score_inc = 0

    # 1. Move tiles across from pattern lines to the wall grid
    for i in range(player_state.GRID_SIZE):
        # Is the pattern line full? If not it persists in its current
        # state into the next round.
        if player_state.lines_number[i] == i + 1:
            tc = player_state.lines_tile[i]
            col = int(player_state.grid_scheme[i][tc])

            # Record that the player has placed a tile of type 'tc'
            player_state.number_of[tc] += 1

            # Clear the pattern line, add all but one tile into the
            # used tiles bag. The last tile will be placed on the
            # players wall grid.
            for j in range(i):
                used_tiles.append(tc)

            player_state.lines_tile[i] = -1
            player_state.lines_number[i] = 0

            # Tile will be placed at position (i,col) in grid
            player_state.grid_state[i][col] = 1

            # count the number of tiles in a continguous line
            # above, below, to the left and right of the placed tile.
            # above = 0
            # for j in range(col - 1, -1, -1):
            #     val = player_state.grid_state[i][j]
            #     above += val
            #     if val == 0:
            #         break
            # below = 0
            # for j in range(col + 1, player_state.GRID_SIZE, 1):
            #     val = player_state.grid_state[i][j]
            #     below += val
            #     if val == 0:
            #         break
            # left = 0
            # for j in range(i - 1, -1, -1):
            #     val = player_state.grid_state[j][col]
            #     left += val
            #     if val == 0:
            #         break
            # right = 0
            # for j in range(i + 1, player_state.GRID_SIZE, 1):
            #     val = player_state.grid_state[j][col]
            #     right += val
            #     if val == 0:
            #         break

            # # If the tile sits in a contiguous vertical line of
            # # tiles in the grid, it is worth 1*the number of tiles
            # # in this line (including itgame_state).
            # if above > 0 or below > 0:
            #     score_inc += (1 + above + below)
            #
            # # In addition to the vertical score, the tile is worth
            # # an additional H points where H is the length of the
            # # horizontal contiguous line in which it sits.
            # if left > 0 or right > 0:
            #     score_inc += (1 + left + right)
            #
            # # If the tile is not next to any already placed tiles
            # # on the grid, it is worth 1 point.
            # if above == 0 and below == 0 and left == 0 \
            #         and right == 0:
            #     score_inc += 1

            score_inc += 1

    # Score penalties for tiles in floor line
    penalties = 0
    for i in range(len(player_state.floor)):
        penalties += player_state.floor[i] * player_state.FLOOR_SCORES[i]
        player_state.floor[i] = 0

    used_tiles.extend(player_state.floor_tiles)
    player_state.floor_tiles = []

    # Players cannot be assigned a negative score in any round.
    score_change = score_inc + penalties
    if score_change < 0 and player_state.score < -score_change:
        score_change = -player_state.score

    player_state.score += score_change
    player_state.player_trace.round_scores[-1] = score_change

    return (player_state.score, used_tiles)
