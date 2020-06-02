import sys

sys.path.append("players/StaffTeamEasy")

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

    def advance_get_available_actions(self, moves: [(Move, int, TileGrab)], game_state: GameState, player_id: int):
        player_state = game_state.players[player_id]

        result = [[] for _ in range(5)]

        for action in moves:
            move, factory, tile_grab = action

            pattern_tile_numbers = tile_grab.pattern_line_dest + 1

            current_pattern_line_has = player_state.lines_number[tile_grab.pattern_line_dest]

            take_from_center = move == Move.TAKE_FROM_CENTRE

            first_player_taken = take_from_center and not game_state.first_player_taken

            no_tile_to_floor_line = tile_grab.num_to_floor_line == 0
            only_take_first_player_token = tile_grab.num_to_pattern_line == 1 and first_player_taken

            # print(move, factory, seeTile(tile_grab))
            # print(no_tile_to_floor_line, only_take_first_player_token,
            #       (pattern_tile_numbers == current_pattern_line_has + tile_grab.num_to_pattern_line, pattern_tile_numbers, current_pattern_line_has, tile_grab.num_to_pattern_line)
            #       )
            # 1. fill a line and with no tile to floor line or only one 1st player token
            if (no_tile_to_floor_line or only_take_first_player_token) and \
                    pattern_tile_numbers == current_pattern_line_has + tile_grab.num_to_pattern_line and \
                    tile_grab.num_to_pattern_line > 0:
                # print(0)
                result[0].append(action)
                continue

            # 2. not fill a line and with no tile to floor line or only one 1st player token
            if (no_tile_to_floor_line or only_take_first_player_token) and \
                    pattern_tile_numbers > current_pattern_line_has + tile_grab.num_to_pattern_line and \
                    tile_grab.num_to_pattern_line > 0:
                result[1].append(action)
                # print(1)
                continue

            # 3. fill a line and with some tile to floor line or only one 1st player token
            if ((not no_tile_to_floor_line) or only_take_first_player_token) and \
                    pattern_tile_numbers == current_pattern_line_has + tile_grab.num_to_pattern_line and \
                    tile_grab.num_to_pattern_line > 0:
                result[2].append(action)
                # print(2)
                continue

            # 4. not fill a line and with some tile to floor line or only one 1st player token
            if ((not no_tile_to_floor_line) or only_take_first_player_token) and \
                    pattern_tile_numbers > current_pattern_line_has + tile_grab.num_to_pattern_line and \
                    tile_grab.num_to_pattern_line > 0:
                result[3].append(action)
                # print(3)
                continue

            # 5. others
            # print(4)
            result[4].append(action)

        return result

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

        # ns = self.getNextState(game_state, curr_max)

        # print("   ", self.id, ":", self.featureExtractor(game_state, curr_max))
        # print("   ", "this:", self.expectScore(game_state), " that:", self.expectScore(ns))
        # print("")

        pruned_actions = self.advance_get_available_actions(moves, game_state, self.id)

        for i, group in enumerate(pruned_actions):
            if curr_max in group:
                print(i+1, (curr_max[0], curr_max[1], seeTile(curr_max[2])), "cur group takes {}/{}({:.2f}%) of total actions".format(len(group), len(moves), len(group) / len(moves) * 100))
                break

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
        expect_gain = self.expectGain(game_state, next_state)

        # expected score for the current action exec
        if self.curr_round < myPlayer.IGNORE_BONUS_THRESHOLD:

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
            features.append(expect_gain)

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
        copy_curr = deepcopy(curr_state)
        copy_next = deepcopy(next_state)
        curr_expected_score, curr_bonus = self.expectScore(copy_curr)
        next_expected_score, next_bonus = self.expectScore(copy_next)

        return next_expected_score + next_bonus - curr_expected_score - curr_bonus

    def expectScore(self, state: GameState):
        """
            calculate the expected reward for a state, including the end of game score
            :param state should be deep copied state and applied the selected action
        """
        my_state: PlayerState = state.players[self.id]
        my_state_copy = deepcopy(my_state)
        expected_score, _ = my_state_copy.ScoreRound()
        bonus = my_state_copy.EndOfGameScore()
        return expected_score, bonus

    def flipCoin(self) -> bool:
        return True if random.random() < self.epsilon else False