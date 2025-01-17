import gymnasium as gym
from gymnasium import spaces
from sb3_contrib.ppo_mask import MaskablePPO
import numpy as np
import random
from treys import Evaluator, Card
import bounty_handler
from stable_baselines3.common.vec_env import VecEnv





class BountyHoldemEnv(gym.Env):
    def __init__(self):
        super(BountyHoldemEnv, self).__init__()
        self.evaluator = Evaluator()
        self.max_rounds = 1000
        self.action_space = spaces.MultiDiscrete([9])  # 0: fold, 1: call, 2: check, bet amounts in increments of 10 (0 to 400)

        # Observation Space
        self.observation_space_shape = (4, 13, 30)
        self.observation_space = spaces.Box(low=0, high=1, shape=self.observation_space_shape, dtype=float)

        self.ranks = "23456789TJQKA"
        self.reset()
        self.potential_opps = [[0,0,0,0,0,0,0,0,1],
                                [1,1,1,1,1,1,1,1,0],
                                [0,1,1,0,0,0,0,0,0],
                                [1,1,1,1,1,1,1,1,1],
                                MaskablePPO.load("models/masked_nenv-ent1-10k/1490000")]

    def create_deck(self):
        ranks = '23456789TJQKA'
        suits = 'hdcs'
        return [f"{rank}{suit}" for rank in ranks for suit in suits]

    def shuffle_deck(self):
        random.shuffle(self.deck)

    def deal_cards(self, num_cards, dealt_cards = []):
        self.shuffle_deck()
        for _ in range(num_cards):
            dealt_cards.append(self.deck.pop())
        return dealt_cards

    def reset(self, seed = None):
        self.player_is_dealer = True
        self.rounds_played = 0
        self.action_round = 0
        self.player_delta = 0
        self.opponent_delta = 0
        self.player_stack = 400
        self.opponent_stack = 400
        self.pot = 0
        self.current_bet = 0
        self.opp_current_bet = 0
        self.street = 'preflop'
        self.deck = self.create_deck()
        self.player_hand = self.deal_cards(2, [])
        #print("51")
        self.community_cards = []
        self.opponent_hand = self.deal_cards(2, [])
        #print("54")
        self.assign_bounties()
        self.opp_bounty_handler = bounty_handler.Bounty()
        self.player_bounty_handler = bounty_handler.Bounty()
        self.betting_action_log = dict()
        self.action_log = dict()
        state, _ = self.get_round_initial_state(True)
        return state, _

    def get_legal_action_mask(self):
        mask = np.array(self.get_legal_actions(True))
        #print("Maksed!", [index for index, i in mask if i == 1])
        return mask

    def reset_round(self):
        if self.rounds_played % 25 == 0:
            self.assign_bounties()
        self.player_stack = 400
        self.opponent_stack = 400
        self.action_round = 0
        self.rounds_played += 1
        self.pot = 0
        self.current_bet = 0
        self.opp_current_bet = 0
        self.street = 'preflop'
        self.deck = self.create_deck()
        self.player_hand = self.deal_cards(2, [])
        #print("76")
        self.community_cards = []
        self.opponent_hand = self.deal_cards(2, [])
        self.betting_action_log = dict()
        self.action_log = dict()
        #print("79")

    def get_round_initial_state(self, first_first_round = False, opponent_model=None):
        if self.rounds_played > self.max_rounds:
            raise Exception("Game Over")

        if first_first_round:
            self.betting_action_log['preflop'] = [1,1]
            self.action_log["preflop"] = ["small blind", "big blind"]
            self.player_stack -= 1
            self.opponent_stack -= 2
            self.pot += 3
            self.current_bet = 2
            player_state = self.get_state(True)
            return player_state, {}

        # Determine whose turn it is first based on the round number
        self.player_is_dealer = self.rounds_played % 2 == 0
        #print("initial round func", self.rounds_played, self.player_is_dealer)

        if self.street == "preflop" and self.action_round == 0:
            self.betting_action_log['preflop'] = [1,1]
            self.action_log["preflop"] = ["small blind", "big blind"]

            if self.player_is_dealer: #player's action first
                self.player_stack -= 1
                self.opponent_stack -= 2
                self.pot += 3
                self.current_bet = 2

                player_state = self.get_state(True)
                return player_state, {}
            else:
                self.player_stack -= 2
                self.opponent_stack -= 1   
                self.pot += 3
                self.current_bet = 2

                opp_state, reward, done, _, _ = self.handle_opponent(opponent_model) #opponent makes an action
                player_state = self.get_state(True)
                return player_state, {}, reward
            
        raise Exception("Invalid Starting State")
    
    def get_state(self, player_not_opp = True):
        # Implement the logic for getting the current state
        state = np.zeros(self.observation_space_shape) #(4,13,30)

        # 0: player hand, 1: flop, 2: turn, 3: river, 4: player bounty, 5: opponent bounty
        # 6 - 11: preflop 
        # 12 - 17: flop
        # 17 - 23: turn
        # 24 - 29: river
        if player_not_opp:
            for card in self.player_hand:
                rank, suit = card
                rank_index = self.ranks.index(rank)
                suit_index = 'hdcs'.index(suit)
                state[suit_index][rank_index][0] = 1
            
            my_bounty_index = self.ranks.index(self.player_bounty)
            state[:,my_bounty_index,4] = np.array([1,1,1,1])
            opp_bounties = self.player_bounty_handler.get_normalized_percentages()
            for index, prob in enumerate(opp_bounties):
                state[:,index,5] = np.array([prob,prob,prob,prob])
        else:
            for card in self.opponent_hand:
                rank, suit = card
                rank_index = self.ranks.index(rank)
                suit_index = 'hdcs'.index(suit)
                state[suit_index][rank_index][0] = 1

            opp_bounty_index = self.ranks.index(self.opponent_bounty)
            state[:,opp_bounty_index,4] = np.array([1,1,1,1])
            player_bounties = self.opp_bounty_handler.get_normalized_percentages()
            for index, prob in enumerate(player_bounties):
                state[:,index,5] = np.array([prob,prob,prob,prob])

        for index, card in enumerate(self.community_cards):
            rank, suit = card
            rank_index = self.ranks.index(rank)
            suit_index = 'hdcs'.index(suit)
            if index < 3: #flop
                channel_index = 1
            elif index == 3: #turn
                channel_index = 2
            elif index == 3: #river
                channel_index = 3
            state[suit_index][rank_index][channel_index] = 1

        
        if player_not_opp:
            for street_index, street in enumerate(["preflop", "flop", "turn", "river"]):
                if street in self.action_log:
                    for index, action in enumerate(self.action_log[street]):
                        #print(action)
                        state_index = index//2
                        if action == "fold": action_index = 0
                        if action == "check": action_index = 2
                        if action == "call": action_index = 1
                        if "bet" in action: action_index =  int(action[-1])
                        if action in ["small blind", "big blind"]:
                            pass
                        else:
                            state_index = min(state_index, 5)
                            if self.player_is_dealer and state_index <= 5:
                                if index % 2 == 0:
                                    state[0, action_index, 6 + state_index + 6 * street_index] = 1
                                else:
                                    state[1, action_index, 6 + state_index + 6 * street_index] = 1
                                state[2, action_index, 6 + state_index + 6 * street_index] += 1
                            elif not self.player_is_dealer and state_index <= 5:
                                if index % 2 == 0:
                                    #print(action_index, 6 + state_index + 6 * street_index)
                                    assert isinstance(action_index, int) 
                                    assert isinstance(6 + state_index + 6 * street_index, int)
                                    state[1, action_index, 6 + state_index + 6 * street_index] = 1
                                else:
                                    state[0, action_index, 6 + state_index + 6 * street_index] = 1
                                state[2, action_index, 6 + state_index + 6 * street_index] += 1
        else:
             for street_index, street in enumerate(["preflop", "flop", "turn", "river"]):
                if street in self.action_log:
                    for index, action in enumerate(self.action_log[street]):
                        state_index = index//2
                        if action == "fold": action_index = 0
                        if action == "check": action_index = 1
                        if action == "call": action_index = 2
                        if "bet" in action: action_index =  int(action[-1])
                        if action in ["small blind", "big blind"]:
                            pass
                        else:
                            state_index = min(state_index, 5)
                            if self.player_is_dealer and state_index <= 5:
                                if index % 2 == 0:
                                    state[1, action_index, 6 + state_index + 6 * street_index] = 1
                                else:
                                    state[0, action_index, 6 + state_index + 6 * street_index] = 1
                                state[2, action_index, 6 + state_index + 6 * street_index] += 1
                            elif not self.player_is_dealer and state_index <= 5:
                                if index % 2 == 0:
                                    state[0, action_index, 6 + state_index + 6 * street_index] = 1
                                else:
                                    state[1, action_index, 6 + state_index + 6 * street_index] = 1
                                state[2, action_index, 6 + state_index + 6 * street_index] += 1   

        #populate legal actions
        legal_actions = self.get_legal_actions(player_not_opp)
        for index, action in enumerate(legal_actions):
            state[3, index, 6:] = np.ones(24) * action

        #populate total cash so far
        if player_not_opp: stack = self.player_delta
        else: stack = self.opponent_delta

        state[:, 9:, 6:30] = np.ones((4, 4, 24)) * stack

        self.legal_actions = legal_actions

        return state
            
    def step(self, action, opponent_model = None):
        if not isinstance(action, int):
            action = int(action[0])
        #check if action is legal... if it's not, we end the round and give the bot a huge negative reward
        legal_actions = self.get_legal_actions(True)
        if not isinstance(action, int) or action < 0 or action > 8 or legal_actions[action] == 0:
            reward, done, _, __ = self.handle_round_end(-1, False)
            self.reset_round()
            if not done:
                info_tuple = self.get_round_initial_state(opponent_model=opponent_model)
                return info_tuple[0], -10000000, done, {}, {}
            else:
                return np.array(self.observation_space_shape), -10000000, done, {}, {}
        
        #if the action is legal, we continue the round
        if action == 0: # 0: fold, 1: call, 2: check; bet amounts in increments of 10 (0 to 400)
            self.action_log.setdefault(self.street, []).append("fold")
            reward, done, _, __ = self.handle_round_end(-1, False)
            self.reset_round()
            if not done:
                info_tuple = self.get_round_initial_state(opponent_model=opponent_model)
            else:
                return np.array(self.observation_space_shape), reward, done, {}, {}
            if len(info_tuple) == 2:
                return info_tuple[0], reward, done, {}, {}
            else:
                return info_tuple[0], reward + info_tuple[2], done, {}, {}
        elif action == 1: #call
            self.action_log.setdefault(self.street, []).append("call")
            self.betting_action_log.setdefault(self.street, []).append(0)
            if self.action_log[self.street][-2] not in ["small blind", "big blind"]:
                if "bet" in self.action_log[self.street][-2]:
                    self.player_stack -= self.betting_action_log[self.street][-2]
                    self.pot += self.betting_action_log[self.street][-2]
                if self.street == "river":
                    reward, done, _, __ = self.handle_round_end(self.evaluate_hands(), True)
                    self.reset_round()
                    info_tuple= self.get_round_initial_state(opponent_model=opponent_model)
                    if len(info_tuple) == 2:
                        return info_tuple[0], reward, done, {}, {}
                    else:
                        return info_tuple[0], reward + info_tuple[2], done, {}, {}
                else:
                    if self.street == "preflop":
                        self.community_cards = self.deal_cards(3, self.community_cards)
                        #print("246", self.community_cards)
                        self.street = "flop"
                    elif self.street == "flop":
                        self.community_cards = self.deal_cards(1, self.community_cards)
                        #print("250", self.community_cards)
                        self.street = "turn"
                    elif self.street == "turn":
                        self.community_cards = self.deal_cards(1, self.community_cards)
                        #print("254", self.community_cards)
                        self.street = "river"
                    self.current_bet = 0
                    if self.player_is_dealer:
                        return self.handle_opponent(opponent_model)
                    else:
                        return self.get_state(True), 0, False, {}, {}
            else: #call after big blind
                self.player_stack -= self.betting_action_log[self.street][-2] #should be 1
                self.pot += self.betting_action_log[self.street][-2]
                return self.handle_opponent(opponent_model)  
        elif action == 2: #check
            self.action_log.setdefault(self.street, []).append("check")
            if len(self.action_log[self.street]) >= 2 and self.action_log[self.street][-2] == "check":
                if self.street == "river":
                    reward, done, _, __ = self.handle_round_end(self.evaluate_hands(), True)
                    self.reset_round()
                    info_tuple= self.get_round_initial_state(opponent_model=opponent_model)
                    if len(info_tuple) == 2:
                        return info_tuple[0], reward, done, {}, {}
                    else:   
                        return info_tuple[0], reward + info_tuple[2], done, {}, {}
                else:
                    if self.street == "preflop":
                        self.community_cards = self.deal_cards(3, self.community_cards)
                        #print("275")
                        self.street = "flop"
                    elif self.street == "flop":
                        self.community_cards = self.deal_cards(1, self.community_cards)
                        #print("279")
                        self.street = "turn"
                    elif self.street == "turn":
                        self.community_cards = self.deal_cards(1, self.community_cards)
                        #print("283")
                        self.street = "river"
                    
                    self.current_bet = 0

                    if self.player_is_dealer:
                        return self.handle_opponent(opponent_model)
                    else:
                        return self.get_state(True), 0, False, {}, {}
            else:
                return self.handle_opponent(opponent_model)
        else: #bet
            self.action_log.setdefault(self.street, []).append("bet" + str(action))
            betting_amount = self.get_betting_options(True)[action]
            self.betting_action_log.setdefault(self.street, [])
            if not self.betting_action_log[self.street]:
                self.betting_action_log[self.street].append(betting_amount)
                raise_amount = betting_amount
            else:
                raise_amount = betting_amount - self.betting_action_log[self.street][-1]
                self.betting_action_log[self.street].append(raise_amount)
            self.player_stack -= betting_amount
            self.pot += betting_amount
            self.current_bet += raise_amount

            return self.handle_opponent(opponent_model)

    def handle_opponent(self, opponent_model):
        possible_opps = self.potential_opps
        curr_state = self.get_state(False)

        opponent_model = random.choices(possible_opps, weights=[0.01, 0.01, 0.1,0.3, 0.67])[0]

        if isinstance(opponent_model, list): #just inputed a random prob distribution
            if sum(np.array(opponent_model) * self.get_legal_actions(False)) != 0:
                opponent_action = random.choices([0,1,2,3,4,5,6,7,8], weights=np.array(opponent_model) * self.get_legal_actions(False))[0]
            else:
                #print("here")
                opponent_action = random.choices([0,1,2,3,4,5,6,7,8], weights=np.ones(9) * self.get_legal_actions(False))[0]
        elif opponent_model is None: #random opponent
            opponent_action = random.choices([0,1,2,3,4,5,6,7,8], weights=np.ones(9) * self.get_legal_actions(False))[0]
        else: #actually have a model
            opponent_action, _ = opponent_model.predict(curr_state, action_masks = curr_state[3, :9, 6])
            if not isinstance(opponent_action, int):
                opponent_action = int(opponent_action[0])
            if self.get_legal_actions(False)[opponent_action] == 0:
                opponent_action = random.choices([0,1,2,3,4,5,6,7,8], weights=np.ones(9) * self.get_legal_actions(False))[0]

        if opponent_action == 0:  # fold
            self.action_log.setdefault(self.street, []).append("fold")
            reward, done, player_bounty_hit, opp_bounty_hit = self.handle_round_end(result=1, opp_cards_revealed=False)
            if done:
                return np.zeros(self.observation_space_shape), reward, done, {}, {}
            self.reset_round()
            info_tuple = self.get_round_initial_state(opponent_model=opponent_model)
            if len(info_tuple) == 2:
                return info_tuple[0], reward, done, {}, {}
            else:
                return info_tuple[0], reward + info_tuple[2], done, {}, {}
        elif opponent_action == 1:  # call:
            self.action_log.setdefault(self.street, []).append("call")
            self.betting_action_log.setdefault(self.street, []).append(0)
            if self.action_log[self.street][-2] not in ["small blind", "big blind"]:
                if "bet" in self.action_log[self.street][-2]:
                    self.opponent_stack -= self.betting_action_log[self.street][-2]
                    self.pot += self.betting_action_log[self.street][-2]
                if self.street == "river":
                    reward, done, _, __ = self.handle_round_end(self.evaluate_hands(), True)
                    self.reset_round()
                    info_tuple = self.get_round_initial_state(opponent_model=opponent_model)
                    if len(info_tuple) == 2:
                        return info_tuple[0], reward, done, {}, {}
                    else:
                        return info_tuple[0], reward + info_tuple[2], done, {}, {}
                else:
                    if self.street == "preflop":
                        self.community_cards = self.deal_cards(3, self.community_cards)
                        #print("335")
                        self.street = "flop"
                    elif self.street == "flop":
                        self.community_cards = self.deal_cards(1, self.community_cards)
                        #print("339")
                        self.street = "turn"
                    elif self.street == "turn":
                        self.community_cards = self.deal_cards(1, self.community_cards)
                        #print("343")
                        self.street = "river"
                    
                    self.current_bet = 0

                    if self.player_is_dealer:
                        return self.handle_opponent(opponent_model)
                    else:
                        return self.get_state(True), 0, False, {}, {}
            else: #call after big blind
                self.opponent_stack -= self.betting_action_log[self.street][-2] #should be 1
                self.pot += self.betting_action_log[self.street][-2]
                return self.get_state(True), 0, False, {}, {}
        elif opponent_action == 2:  # check
            self.action_log.setdefault(self.street, []).append("check")
            if len(self.action_log[self.street]) >= 2 and self.action_log[self.street][-2] in ["check", "call"]:
                if self.street == "river":
                    reward, done, _, __ = self.handle_round_end(self.evaluate_hands(), True)
                    self.reset_round()
                    info_tuple = self.get_round_initial_state(opponent_model=opponent_model)
                    if len(info_tuple) == 2:
                        return info_tuple[0], reward, done, {}, {}
                    else:
                        return info_tuple[0], reward + info_tuple[2], done, {}, {}
                else:
                    if self.street == "preflop":
                        self.community_cards = self.deal_cards(3, self.community_cards)
                        #print("364")
                        self.street = "flop"
                    elif self.street == "flop":
                        self.community_cards = self.deal_cards(1, self.community_cards)
                        #print("368")
                        self.street = "turn"
                    elif self.street == "turn":
                        self.community_cards = self.deal_cards(1, self.community_cards)
                        #print("372")
                        self.street = "river"

                    self.current_bet = 0
                    if self.player_is_dealer:
                        return self.handle_opponent(opponent_model)
                    else:
                        return self.get_state(True), 0, False, {}, {}
            else:
                return self.get_state(True), 0, False, {}, {}
        else:  # bet
            self.action_log.setdefault(self.street, []).append("bet" + str(opponent_action))
            betting_amount = self.get_betting_options(False)[opponent_action]
            #print("betting options", self.get_betting_options(False))
            self.betting_action_log.setdefault(self.street, [])
            if not self.betting_action_log[self.street]:
                self.betting_action_log[self.street].append(betting_amount)
                raise_amount = betting_amount
            else:
                #print(self.betting_action_log)
                raise_amount = betting_amount - self.betting_action_log[self.street][-1]
                self.betting_action_log[self.street].append(raise_amount)
            #print("here, betting amount", betting_amount)
            self.opponent_stack -= betting_amount
            self.pot += betting_amount
            self.current_bet += raise_amount
            return self.get_state(True), 0, False, {}, {}

    def assign_bounties(self):
        self.player_bounty = random.choice(self.ranks)
        self.opponent_bounty = random.choice(self.ranks)

    def get_legal_actions(self, player_not_opp = True):
        #9 Cols: fold, call, check, 1/2 pot, 3/4 pot, 1 pot, 3/2 pot, 2 pots, all in
        if player_not_opp:
            stack = self.player_stack 
            opp_stack = self.opponent_stack
        else:
            stack = self.opponent_stack
            opp_stack = self.player_stack

        if self.street == "preflop":
            if self.betting_action_log["preflop"] == [1,1]:
                return np.array([1,1,0,0,0,1,1,1,1])
            else:
                bet_options = np.array([0.5 * self.pot, 0.75 * self.pot, self.pot, 1.5 * self.pot, 2 * self.pot, stack])
                bet_options = np.round(bet_options).astype(int)
                last_bet = self.betting_action_log[self.street][-1]
                legal_actions = np.array([1, 1, 0] + [1 if (x > last_bet * 2 and x <= stack) or (x == stack and opp_stack != 0) else 0 for x in bet_options])
                return legal_actions
        else:
            bet_options = np.array([0.5 * self.pot, 0.75 * self.pot, self.pot, 1.5 * self.pot, 2 * self.pot, stack])
            bet_options = np.round(bet_options).astype(int)
            #print("466", self.betting_action_log)
            if sum(self.betting_action_log.setdefault(self.street,[])) == 0: #checks or nothing has happend
                legal_actions = np.array([0, 0, 1] + [1 if (x > 2 and x <= stack) else 0 for x in bet_options])
            else:
                last_bet = self.betting_action_log[self.street][-1]
                legal_actions = np.array([1, 1, 0] + [1 if (x > last_bet * 2 and x <= stack) or x == stack else 0 for x in bet_options])
            return legal_actions
        
    def get_betting_options(self, player_not_opp = True):
        if player_not_opp:
            stack = self.player_stack 
        else:
            stack = self.opponent_stack

        bet_options = np.array([0,0,0,0.5 * self.pot, 0.75 * self.pot, self.pot, 1.5 * self.pot, 2 * self.pot, stack])
        bet_options = np.round(bet_options).astype(int)
        return bet_options


    def handle_round_end(self, result, opp_cards_revealed = False):
        '''
        This function handles updates the bounty class, figures out the correct rewards to give to the player
        and opponent bot, and returns the reward and done status of the game.

        Returns: reward, done, my_bounty_hit, opp_bounty_hit
        '''
        #self.rounds_played += 1
        #print("round end action log", self.action_log)

        normal_winnings = 400 - self.opponent_stack #how much the opponent bet over the round
        opp_winnings = 400 - self.player_stack #how much the player bet over the round
        player_hits_bounty = self.player_bounty in [card[0] for card in self.player_hand + self.community_cards]
        opponent_hits_bounty = self.opponent_bounty in [card[0] for card in self.opponent_hand + self.community_cards]

        if opp_cards_revealed:
            self.player_bounty_handler.handle_new_round(self.rounds_played, self.player_hand, self.community_cards, self.opponent_hand, opponent_hits_bounty, result == -1)
            self.opp_bounty_handler.handle_new_round(self.rounds_played, self.opponent_hand, self.community_cards, self.player_hand, player_hits_bounty, result == 1)
        else:
            self.player_bounty_handler.handle_new_round(self.rounds_played, self.player_hand, self.community_cards, [], opponent_hits_bounty, result == -1)
            self.opp_bounty_handler.handle_new_round(self.rounds_played, self.opponent_hand, self.community_cards, [], player_hits_bounty, result == 1)

        if result == 1:
            if player_hits_bounty:
                reward = 1.5 * normal_winnings + 10
            else:
                reward = normal_winnings
        elif result == -1:
            if opponent_hits_bounty:
                reward = -(1.5 * opp_winnings + 10)
            else:
                reward = -opp_winnings
        else:
            if player_hits_bounty and not opponent_hits_bounty:
                reward = 0.25 * normal_winnings + 10
            elif not player_hits_bounty and opponent_hits_bounty:
                reward = -0.25 * normal_winnings - 10
            else:
                reward = 0

        self.player_delta += reward
        self.opponent_delta -= reward

        done = self.rounds_played >= self.max_rounds - 1
        if done:
            if self.player_delta > self.opponent_delta:
                reward += 100000
            else:
                reward -= 100000
            print("done!")
        print("Winner:", result, "Reward:", reward)
        return reward, done, player_hits_bounty, opponent_hits_bounty
    
    def evaluate_hands(self):
        player_hand = [Card.new(card) for card in self.player_hand]
        community_cards = [Card.new(card) for card in self.community_cards]
        opponent_hand = [Card.new(card) for card in self.opponent_hand]

        player_score = self.evaluator.evaluate(community_cards, player_hand)
        opponent_score = self.evaluator.evaluate(community_cards, opponent_hand)

        if player_score < opponent_score:
            #print("Result: Player win" )
            return 1  # Player wins
        elif player_score > opponent_score:
            #print("Result: Opponent win")
            return -1  # Opponent wins
        else:
            #print("Result: Tie")
            return 0  # Tie

    def render(self):
        def format_card(card):
            rank, suit = card
            suit_symbols = {'h': '♥', 'd': '♦', 'c': '♣', 's': '♠'}
            return f"{rank}{suit_symbols[suit]}"

        formatted_player_hand = [format_card(card) for card in self.player_hand]
        formatted_community_cards = [format_card(card) for card in self.community_cards]

        print("=== Game State ===")
        print(f"Round: {self.rounds_played}")
        print(f'Dealer: {"Player" if self.player_is_dealer else "Opponent"}')
        print(f"Player Hand: {' '.join(formatted_player_hand)}")
        print(f"Community Cards: {' '.join(formatted_community_cards)}")
        print(f"Pot: {self.pot}")
        print(f"Player Stack: {self.player_stack}")
        print(f"Opponent Stack: {self.opponent_stack}")
        print(f"Current Bet: {self.current_bet}")
        print(f"Street: {self.street}")
        print(f"Bounty: {self.player_bounty}")
        print("==================")
        print("Action Log: ", self.action_log)
        print("Actions: 0:fold, 1:call, 2:check, 3:1/2 pot, 4:3/4 pot, 5:1 pot, 6:3/2 pot, 7:2 pots, 8:all in")
        print("Legal Actions: ", self.get_legal_actions(True))
