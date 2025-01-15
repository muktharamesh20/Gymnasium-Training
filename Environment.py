import gym
from gym import spaces
import numpy as np
import random
from treys import Evaluator, Card
import bounty_handler

class BountyHoldemEnv(gym.Env):
    def __init__(self):
        super(BountyHoldemEnv, self).__init__()
        self.evaluator = Evaluator()
        self.max_rounds = 1000
        self.action_space = spaces.MultiDiscrete(10)  # 0: fold, 1: call, 2: bet, 3: check; bet amounts in increments of 10 (0 to 400)

        # Define the observation space for the first tensor
        self.tensor1_shape = (4, 13, 6)
        space1 = spaces.MultiBinary(self.tensor1_shape)

        # Define the observation space for the second tensor
        self.tensor2_shape = (4, 9, 24)
        space2 = spaces.MultiBinary(self.tensor2_shape)

        # Combine the two spaces into a single observation space
        self.observation_space = spaces.Tuple((space1, space2))

        self.ranks = "23456789TJQKA"
        self.reset()

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

    def reset(self):
        self.rounds_played = 0
        self.action_round = 0
        self.player_delta = 0
        self.opponent_delta = 0
        self.player_stack = 400
        self.opponent_stack = 400
        self.pot = 0
        self.current_bet = 0
        self.opp_current_bet = 0
        self.street = 'pre-flop'
        self.deck = self.create_deck()
        self.player_hand = self.deal_cards(2)
        self.community_cards = []
        self.opponent_hand = self.deal_cards(2)
        self.assign_bounties()
        self.opp_bounty_handler = bounty_handler.Bounty()
        self.player_bounty_handler = bounty_handler.Bounty()
        self.betting_action_log = dict()
        self.action_log = dict()
        state = self.get_round_initial_state(True)
        return state

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
        self.street = 'pre-flop'
        self.deck = self.create_deck()
        self.player_hand = self.deal_cards(2)
        self.community_cards = []
        self.opponent_hand = self.deal_cards(2)


    def get_round_initial_state(self, first_first_round = False, opponent_model=None):
        if self.rounds_played > self.max_rounds:
            raise Exception("Game Over")

        if first_first_round:
            self.betting_action_log['preflop'] = [1,1]
            self.action_log["preflop"] = ["small blind", "big blind"]
            self.player_stack -= 1
            self.opponent_stack -= 2
            player_state = self.get_state(True)
            return player_state

        # Determine whose turn it is first based on the round number
        player_is_dealer = self.rounds_played % 2 == 0

        if self.street == "pre-flop" and self.action_round == 0:
            self.betting_action_log['preflop'] = [1,1]
            self.action_log["preflop"] = ["small blind", "big blind"]

            if player_is_dealer: #player's action first
                self.player_stack -= 1
                self.opponent_stack -= 2

                player_state = self.get_state(True)
                return player_state
            else:
                self.player_stack -= 2
                self.opponent_stack -= 1   

                opp_state, reward, done, _ = self.handle_opponent(opponent_model) #opponent makes an action
                player_state = self.get_state(True)
                return player_state
            
        raise Exception("Invalid Starting State")
            
    def step(self, action, dealer, opponent_model = None):
        assert self.action_space.contains(action), "Invalid Action"


        
        




        '''
        if dealer:
            # Player's turn
            if self.street == 'pre-flop' and self.action_round != 0:
                state, reward, done, info = self.handle_opponent(opponent_model)
            
            state, reward, done, info = self.handle_player(action)
        else:
            # Opponent's turn
            if opponent_model:
                state, reward, done, info = self.handle_opponent(opponent_model)
            if not done:
                state, reward, done, info = self.handle_player(action)

        return state, reward, done, info'''

    def handle_player(self, action_type):
        if action_type == 0:  # fold
            self.opponent_delta += 1
            reward = -self.current_bet
            reward, done, my_bounty_hit, opp_bounty_hit = self.handle_round_end(-1, False)
            self.reset_round()
            return self.state, reward, True, {}  # Opponent wins, round over
        else:  # call, bet, or check
            if not self.handle_betting(action_type):
                #self.rounds_played += 1
                if self.rounds_played >= self.max_rounds:
                    done = True
                    if self.player_delta > self.opponent_delta:
                        reward = -1000 + 100000
                    else:
                        reward = -1000 - 100000
                    return self.state, reward, done, {}
                self.reset_round()
                return self.state, -1000, True, {}  # Illegal action, round over

        if self.street == 'pre-flop':
            self.community_cards += self.deal_cards(3, self.community_cards)
            self.street = 'flop'
        elif self.street == 'flop':
            self.community_cards += self.deal_cards(1, self.community_cards)
            self.street = 'turn'
        elif self.street == 'turn':
            self.community_cards += self.deal_cards(1, self.community_cards)
            self.street = 'river'

        reward = self.calculate_reward()
        done = self.rounds_played >= self.max_rounds
        if done:
            if self.player_delta > self.opponent_delta:
                reward += 100000
            else:
                reward -= 100000
        return self.state, reward, done, {}

    def handle_opponent(self, opponent_model):
        curr_state = self.get_state(False)

        if isinstance(opponent_model, list): #just inputed a random prob distribution
            opponent_action = random.choice([0,1,2,3,4,5,6,7,8,9], weights=np.array(opponent_model) * self.get_legal_actions(False))
        else: #actually have a model
            opponent_action, _ = opponent_model.predict(curr_state)

        if opponent_action[0] == 0:  # fold
            reward, done, player_bounty_hit, opp_bounty_hit = self.handle_round_end(result=1, opp_cards_revealed=False)
            player_state = self.get_state(True)
            self.reset_round()
            return player_state, reward, done, {}  # Player wins, round over
        else:  # call, bet, or check
            self.betting_action_log.append(o)
            if not self.handle_betting(opponent_action):
                #self.rounds_played += 1
                if self.rounds_played >= self.max_rounds:
                    done = True
                    if self.player_delta > self.opponent_delta:
                        reward = -1000 + 100000
                    else:
                        reward = -1000 - 100000
                    return self.get_state(True), reward, done, {}
                self.reset_round()
                return self.get_state(True), -1000, True, {}  # Illegal action, round over

        if self.street == 'pre-flop':
            self.community_cards += self.deal_cards(3)
            self.street = 'flop'
        elif self.street == 'flop':
            self.community_cards += self.deal_cards(1)
            self.street = 'turn'
        elif self.street == 'turn':
            self.community_cards += self.deal_cards(1)
            self.street = 'river'

        reward = self.calculate_reward()
        done = self.rounds_played >= self.max_rounds
        if done:
            if self.player_delta > self.opponent_delta:
                reward += 100000
            else:
                reward -= 100000
        return self.get_state(True), reward, done, {}

    def handle_betting(self, action):
        # Implement the logic for handling betting actions
        pass

    def assign_bounties(self):
        self.player_bounty = random.choice(self.ranks)
        self.opponent_bounty = random.choice(self.ranks)

    def get_legal_actions(self, player_not_opp = True):
        #9 Cols: fold, check, call, 1/2 pot, 3/4 pot, 1 pot, 3/2 pot, 2 pots, all in
        if player_not_opp:
            stack = self.player_stack 
        else:
            stack = self.opponent_stack

        if self.street == "pre-flop":
            if self.betting_action_log["pre-flop"] == [1,1]:
                return np.array([1,0,1,0,0,1,1,1,1])
            else:
                bet_options = np.array([0.5 * self.pot, 0.75 * self.pot, self.pot, 1.5 * self.pot, 2 * self.pot, stack])
                bet_options = np.round(bet_options).astype(int)
                last_bet = self.betting_action_log[self.street][-1]
                legal_actions = np.arary([1, 0, 1] + [1 if (x > last_bet * 2 and x <= stack) or x == stack else 0 for x in bet_options])
                return legal_actions
        else:
            bet_options = np.array([0.5 * self.pot, 0.75 * self.pot, self.pot, 1.5 * self.pot, 2 * self.pot, stack])
            bet_options = np.round(bet_options).astype(int)
            if sum(self.betting_action_log[self.street]) == 0: #checks or nothing has happend
                legal_actions = np.array([0, 1, 0] + [1 if (x > 2 and x <= stack) else 0 for x in bet_options])
            else:
                last_bet = self.betting_action_log[self.street][-1]
                legal_actions = np.array([1, 0, 1] + [1 if (x > last_bet * 2 and x <= stack) or x == stack else 0 for x in bet_options])
            return legal_actions


    def get_state(self, player_not_opp = True):
        # Implement the logic for getting the current state
        state = [np.zeros(shape = self.tensor1_shape),np.zeros(shape = self.tensor2_shape)]

        '''
        4x13x6
        4x13 my bounty 
        4x13 opponent bounty potential
        4x13 hole cards
        4x13 flop cards
        4x13 turn cards
        4x13 river cards
        '''
        if player_not_opp:
            for card in self.player_hand:
                rank, suit = card
                rank_index = self.ranks.index(rank)
                suit_index = 'hdcs'.index(suit)
                state[0][suit_index][rank_index][3] = 1
            
            my_bounty_index = self.ranks.index(self.player_bounty)
            state[0][:,my_bounty_index,0] = np.array([1,1,1,1])
        else:
            for card in self.opponent_hand:
                rank, suit = card
                rank_index = self.ranks.index(rank)
                suit_index = 'hdcs'.index(suit)
                state[0][suit_index][rank_index][3] = 1

            opp_bounty_index = self.ranks.index(self.opponent_bounty)
            state[0][:][opp_bounty_index][1] = 1

        for index, card in enumerate(self.community_cards):
            rank, suit = card
            rank_index = self.ranks.index(rank)
            suit_index = 'hdcs'.index(suit)
            if index < 3: #flop
                channel_index = 2 
            elif index == 3: #turn
                channel_index = 3
            elif index == 3: #river
                channel_index = 4
            state[0][rank_index][suit_index][channel_index] = 1
        '''
        index 1: #Card Space

        4x10x24
        4 Rows: my action, opp action, sum of actions, legality of action
        10 Cols: fold, check, call, bet, 1/2 pot, 3/4 pot, 1 pot, 3/2 pot, 2 pots, all in
        24 Channels: Each round, 6 actions
        '''


        

    def evaluate_hands(self):
        player_hand = [Card.new(card) for card in self.player_hand]
        community_cards = [Card.new(card) for card in self.community_cards]
        opponent_hand = [Card.new(card) for card in self.opponent_hand]

        player_score = self.evaluator.evaluate(community_cards, player_hand)
        opponent_score = self.evaluator.evaluate(community_cards, opponent_hand)

        if player_score < opponent_score:
            return 1  # Player wins
        elif player_score > opponent_score:
            return -1  # Opponent wins
        else:
            return 0  # Tie

    def handle_round_end(self, result, opp_cards_revealed = False):
        '''
        This function handles updates the bounty class, figures out the correct rewards to give to the player
        and opponent bot, and returns the reward and done status of the game.

        Returns: reward, done, my_bounty_hit, opp_bounty_hit
        '''
        self.rounds_played += 1

        normal_winnings = 400 - self.opponent_stack #how much the opponent bet over the round
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
                reward = -(1.5 * normal_winnings + 10)
            else:
                reward = -normal_winnings
        else:
            if player_hits_bounty and not opponent_hits_bounty:
                reward = 0.25 * normal_winnings + 10
            elif not player_hits_bounty and opponent_hits_bounty:
                reward = -0.25 * normal_winnings - 10
            else:
                reward = 0

        self.player_delta += reward
        self.opponent_delta -= reward

        done = self.rounds_played >= self.max_rounds
        if done:
            if self.player_delta > self.opponent_delta:
                reward += 100000
            else:
                reward -= 100000
        
        return reward, done, player_hits_bounty, opponent_hits_bounty

    def render(self):
        def format_card(card):
            rank, suit = card
            suit_symbols = {'h': '♥', 'd': '♦', 'c': '♣', 's': '♠'}
            return f"{rank}{suit_symbols[suit]}"

        formatted_player_hand = [format_card(card) for card in self.player_hand]
        formatted_community_cards = [format_card(card) for card in self.community_cards]

        print("=== Game State ===")
        print(f"Player Hand: {' '.join(formatted_player_hand)}")
        print(f"Community Cards: {' '.join(formatted_community_cards)}")
        print(f"Pot: {self.pot}")
        print(f"Player Stack: {self.player_stack}")
        print(f"Opponent Stack: {self.opponent_stack}")
        print(f"Current Bet: {self.current_bet}")
        print(f"Street: {self.street}")
        print(f"Bounty: {self.player_bounty}")
        print("==================")

# Register the environment
gym.envs.registration.register(
    id='BountyHoldem-v0',
    entry_point='__main__:BountyHoldemEnv',
)

# Example usage
if __name__ == "__main__":
    env = gym.make('BountyHoldem-v0')
    env.reset()
    env.render()

'''
state = 

index 0: #Bet space

4x13x6
4x13 my bounty 
4x13 opponent bounty potential
4x13 hole cards
4x13 flop cards
4x13 turn cards
4x13 river cards

index 1: #Card Space

4x10x24
4 Rows: my action, opp action, sum of actions, legality of action
10 Cols: fold, check, call, bet, 1/2 pot, 3/4 pot, 1 pot, 3/2 pot, 2 pots, all in
24 Channels: Each round, 6 actions

'''