from card import *
import enum
import math
import itertools
import random

class hands():
    def __init__(self):
        self.remaining_cards = set()
        for suit in Suite:
            for rank in Rank:
                self.remaining_cards.add(GameCard(rank, suit))

        ROYAL_FLUSH = 10 #done
        STRAIGHT_FLUSH = 9 #done
        FOUR_OF_A_KIND = 8 #done
        FULL_HOUSE = 7
        FLUSH = 6 #done
        STRAIGHT = 5 #done
        THREE_OF_A_KIND = 4 #done, opp doesn't restrict our two cards tho
        TWO_PAIR = 3
        ONE_PAIR = 2 #done
        HIGH_CARD = 1 #done, revisit later to double-check math
        
        '''
        for index, card in enumerate(self.remaining_cards):
            print(index, card)
        '''
        self.normalized_hands = []
    
    def set_hand_for_new_round(self, your_cards, center_cards):
        '''
        To avoid calling time consuming functions in this class over and over again

        Both arguments are sets of cards
        '''
        self.your_two_cards = your_cards
        self.rank_list = rank_dict = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "JACK", "QUEEN", "KING", "ACE"]

        self.your_cards_set = your_cards.union(center_cards)
        self.opp_cards_set = center_cards

        self.your_cards_dict_suite_key = dict()
        self.opp_cards_dict_suite_key = dict()
        self.remaining_cards_suite_key = dict()

        self.your_cards_dict_rank_key = dict()
        self.opp_cards_dict_rank_key = dict()
        self.remaining_cards_rank_key = dict()
        

        #this updates remaining_cards which keeps track of what's in the deck/opp cards
        for card in center_cards.union(your_cards):
            if card in self.remaining_cards:
                self.remaining_cards.remove(card)

        self.num_hands_self = math.comb(len(self.remaining_cards), 7 - len(self.your_cards_set))
        self.num_hands_opp = math.comb(len(self.remaining_cards), 7 - len(self.opp_cards_set))

        #this creates an easier structure to find flushes and straights and stuff
        for card in center_cards:
            suite_str = card.convert_value_to_string("Suite")
            rank_str = card.convert_value_to_string("Rank")
            self.your_cards_dict_suite_key.setdefault(suite_str,[]).append(rank_str)
            self.opp_cards_dict_suite_key.setdefault(suite_str,[]).append(rank_str)

            self.your_cards_dict_rank_key.setdefault(rank_str,[]).append(suite_str)
            self.opp_cards_dict_rank_key.setdefault(rank_str,[]).append(suite_str)

        for card in your_cards:
            suite_str = card.convert_value_to_string("Suite")
            rank_str = card.convert_value_to_string("Rank")
            self.your_cards_dict_suite_key.setdefault(suite_str,[]).append(rank_str)
            self.your_cards_dict_rank_key.setdefault(rank_str,[]).append(suite_str)

        for card in self.remaining_cards:
            suite_str = card.convert_value_to_string("Suite")
            rank_str = card.convert_value_to_string("Rank")
            self.remaining_cards_rank_key.setdefault(rank_str,[]).append(suite_str)
            self.remaining_cards_suite_key.setdefault(suite_str,[]).append(rank_str)

        royal_flush = [self.make_royal_flush(True)/self.num_hands_self*100, self.make_royal_flush(False)/self.num_hands_opp*100]
        straight_flush = [self.make_straight_flush(True)/self.num_hands_self*100, self.make_straight_flush(False)/self.num_hands_opp*100]
        four_of_a_kind = [self.make_four_of_a_kind(True)/self.num_hands_self*100, self.make_four_of_a_kind(False)/self.num_hands_opp*100]

        flush = [self.make_flush(True)/self.num_hands_self*100, self.make_flush(False)/self.num_hands_opp*100]
        straight = [self.make_straight(True)/self.num_hands_self*100, self.make_straight(False)/self.num_hands_opp*100]
        three_of_a_kind = [self.make_three_of_a_kind_new(True)/self.num_hands_self*100, self.make_three_of_a_kind_new(False)/self.num_hands_opp*100]
        
        one_pair = [self.make_one_pair(True)/self.num_hands_self*100, self.make_one_pair(False)/self.num_hands_opp*100]
        high_card = [self.make_high_card(True)/self.num_hands_self*100, self.make_high_card(False)/self.num_hands_opp*100]
        full_house = [(self.make_three_of_a_kind(True) - self.make_three_of_a_kind_new(True))/self.num_hands_self*100, (self.make_three_of_a_kind(False) - self.make_three_of_a_kind_new(False))/self.num_hands_opp*100]
        two_pair = [max(0, (100 - four_of_a_kind[0] - full_house[0] - three_of_a_kind[0] - one_pair[0]-high_card[0])), max(0, (100 - four_of_a_kind[1] - full_house[1] - three_of_a_kind[1] - one_pair[1]-high_card[1]))]

        all_hands = [royal_flush, straight_flush, four_of_a_kind, full_house, flush, straight, three_of_a_kind, two_pair, one_pair, high_card]
        #adjustments ------------------------------------------------------------
        def adjust_all(multiplier, index, args):
            for hand in args:
                if len(hand) == 0:
                    continue
                hand[index] *= multiplier

        for i, hand in enumerate(all_hands[:6]):
            if len(hand) == 0:
                continue
            if hand[0] == 100:
                adjust_all(0, 0, all_hands[i+1:])
            if hand[1] == 100:
                adjust_all(0, 1, all_hands[i+1:])

        if (flush[0]+straight_flush[0]+royal_flush[0]) == 100:
            adjust_all(0,0,all_hands[5:])

        adjust_all(1-(flush[0]+straight_flush[0]+royal_flush[0])/100, 0, [high_card, one_pair])
        adjust_all(1-(flush[1]+straight_flush[1] + royal_flush[1])/100, 1, [high_card, one_pair])

        adjust_all(1-(straight[0])/200, 0, [high_card, one_pair, two_pair])
        adjust_all(1-(straight[1])/200, 1, [high_card, one_pair, two_pair])

        adjust_all(1-(straight[0])/40, 0, [high_card])
        adjust_all(1-(straight[1])/40, 1, [high_card])

        self.print_hands = [royal_flush, straight_flush, four_of_a_kind, full_house, flush, straight, three_of_a_kind, two_pair, one_pair, high_card]
        self.print_hand_names = ["Royal Flush", "Straight Flush", "Four of a Kind", "Full House","Flush", "Straight", "Three of a Kind", "Two Pair", "One Pair", "High Card"]
        self.adjusted_best_hand_percentage = [True, True, True, False, "Close", "Close", False, "False++", False, False]
        sum_our_hands = sum(x[0] for x in self.print_hands)
        sum_opp_hands = sum(x[1] for x in self.print_hands)
        self.normalized_hands = [[x[0]/sum_our_hands*100, x[1]/sum_opp_hands*100] for x in self.print_hands]

        self.acces_dict = {"Royal Flush":0, "Straight Flush":1, "Four of a Kind":2, "Full House":3,"Flush":4, "Straight":5, "Three of a Kind":6, "Two Pair":7, "One Pair":8, "High Card":9}
        #---------------------------------------------------------------------------------------

        #print(all_hands)

    def find_our_best_hand(self):
        pass

    def make_royal_flush(self, our_bot = True, check_and_return_bool = False):
        '''
        If our_bot is False, we calculate for the opponent

        If check_and_return_bool is true, this function simply checks if a royal flush exists
        in the hand and returns a boolean

        Otherwise, this function returns the number of ways to make a royal flush
        '''
        if our_bot:
            suite_dict_to_check = self.your_cards_dict_suite_key
            rank_dict_to_check = self.your_cards_dict_rank_key
            cards_set = self.your_cards_set
        else:
            suite_dict_to_check = self.opp_cards_dict_suite_key
            rank_dict_to_check = self.opp_cards_dict_rank_key
            cards_set = self.opp_cards_set

        if check_and_return_bool:
            suites = {"SPADE", "HEART", "DIAMOND", "CLUB"}
            for royal in ["KING", "QUEEN", "JACK", "10", "ACE"]:
                if royal not in rank_dict_to_check or not suites:
                    return False
                
                kept_suites = set()
                for potential_card in rank_dict_to_check[royal]:
                    kept_suites.add(potential_card)

                suites = suites.intersection(kept_suites)
            return True
        else:
            num_cards_to_be_revealed = 7 - len(cards_set)
            suites = {"SPADE", "HEART", "DIAMOND", "CLUB"}
            ranks = ["KING", "QUEEN", "JACK", "10", "ACE"]
            
            potential_hand_suites = dict()

            num_hands = 0
            for suit in suite_dict_to_check:
                if len(suite_dict_to_check[suit]) < 5 - num_cards_to_be_revealed:
                    pass
                else:
                    suit_is_possible = True
                    num_cards_important_in_deck = 0
                    for rank in ranks:
                        converted_rank = GameCard.string_to_value(None, "Rank", rank)
                        converted_suite = GameCard.string_to_value(None, "Suite", suit)
                        if rank not in suite_dict_to_check[suit] and GameCard(converted_rank, converted_suite) not in self.remaining_cards:
                            suit_is_possible = False
                            break
                        elif rank in suite_dict_to_check[suit]:
                            num_cards_important_in_deck += 1
                    
                    if suit_is_possible:
                        num_cards_important_outside_deck = 5 - num_cards_important_in_deck
                        num_cards_extra = num_cards_to_be_revealed - num_cards_important_outside_deck
                        #print(num_cards_important_in_deck, num_cards_important_outside_deck, num_cards_extra)
                        if num_cards_important_outside_deck <= num_cards_to_be_revealed:
                            num_hands += 1 * math.comb(len(self.remaining_cards) - num_cards_important_outside_deck, num_cards_extra)
            return num_hands
        
    def make_straight_flush(self, our_bot = True, check_and_return_bool = False):
        if our_bot:
            suite_dict_to_check = self.your_cards_dict_suite_key
            rank_dict_to_check = self.your_cards_dict_rank_key
            cards_set = self.your_cards_set
        else:
            suite_dict_to_check = self.opp_cards_dict_suite_key
            rank_dict_to_check = self.opp_cards_dict_rank_key
            cards_set = self.opp_cards_set

        if check_and_return_bool:
            return self.make_flush(our_bot, True) and self.make_straight(our_bot, True)
            for suit in suite_dict_to_check:
                numbered_ranks = []
                ranks = suite_dict_to_check[suit]
                for rank in ranks:
                    numbered_ranks.append(GameCard.string_to_value(None,"Rank", rank))
                
                numbered_ranks.sort()

                in_a_row_counter = 0
                last_num = -1000
                for rank in numbered_ranks:
                    #base case
                    if in_a_row_counter == 5:
                        return True
                    
                    #keeping track of number of cards in a straight
                    if rank == last_num + 1 or rank == 0 and numbered_ranks[-1] == 12:
                        in_a_row_counter += 1
                    else:
                        in_a_row_counter = 1

                    last_num = rank
                if in_a_row_counter == 5:
                    return True
            return False
        
        else:
            num_hands = 0
            num_cards_to_be_revealed = 7 - len(cards_set)

            for rank_value in range(-1, 9):
                suites = {"SPADE", "HEART", "DIAMOND", "CLUB"}
                ranks = []
                for potential_rank in range(rank_value, rank_value + 5):
                    potential_rank = potential_rank % 13
                    ranks.append(GameCard.value_to_string(None,"Rank", potential_rank))
                potential_hand_suites = dict()

                for suit in suite_dict_to_check:
                    if len(suite_dict_to_check[suit]) < 5 - num_cards_to_be_revealed:
                        pass
                    else:
                        suit_is_possible = True
                        num_cards_important_in_deck = 0
                        for rank in ranks:
                            converted_rank = GameCard.string_to_value(None, "Rank", rank)
                            converted_suite = GameCard.string_to_value(None, "Suite", suit)
                            if rank not in suite_dict_to_check[suit] and GameCard(converted_rank, converted_suite) not in self.remaining_cards:
                                suit_is_possible = False
                                break
                            elif rank in suite_dict_to_check[suit]:
                                num_cards_important_in_deck += 1
                        
                        if suit_is_possible:
                            num_cards_important_outside_deck = 5 - num_cards_important_in_deck
                            num_cards_extra = num_cards_to_be_revealed - num_cards_important_outside_deck
                            #print(num_cards_important_in_deck, num_cards_important_outside_deck, num_cards_extra)
                            if num_cards_important_outside_deck <= num_cards_to_be_revealed:
                                num_hands += 1 * math.comb(len(self.remaining_cards) - num_cards_important_outside_deck, num_cards_extra)
                #(ranks, num_hands)
            #6s
            for rank_value in range(-1, 8):
                suites = {"SPADE", "HEART", "DIAMOND", "CLUB"}
                ranks = []
                for potential_rank in range(rank_value, rank_value + 6):
                    potential_rank = potential_rank % 13
                    ranks.append(GameCard.value_to_string(None,"Rank", potential_rank))
                potential_hand_suites = dict()

                for suit in suite_dict_to_check:
                    if len(suite_dict_to_check[suit]) < 6 - num_cards_to_be_revealed:
                        pass
                    else:
                        suit_is_possible = True
                        num_cards_important_in_deck = 0
                        for rank in ranks:
                            converted_rank = GameCard.string_to_value(None, "Rank", rank)
                            converted_suite = GameCard.string_to_value(None, "Suite", suit)
                            if rank not in suite_dict_to_check[suit] and GameCard(converted_rank, converted_suite) not in self.remaining_cards:
                                suit_is_possible = False
                                break
                            elif rank in suite_dict_to_check[suit]:
                                num_cards_important_in_deck += 1
                        
                        if suit_is_possible:
                            num_cards_important_outside_deck = 6 - num_cards_important_in_deck
                            num_cards_extra = num_cards_to_be_revealed - num_cards_important_outside_deck
                            #print(num_cards_important_in_deck, num_cards_important_outside_deck, num_cards_extra)
                            if num_cards_important_outside_deck <= num_cards_to_be_revealed:
                                num_hands -= 1 * math.comb(len(self.remaining_cards) - num_cards_important_outside_deck, num_cards_extra)
            return num_hands - self.make_royal_flush(our_bot)
    
    def make_four_of_a_kind(self, our_bot = True, check_and_return_bool = False):
        if our_bot:
            suite_dict_to_check = self.your_cards_dict_suite_key
            rank_dict_to_check = self.your_cards_dict_rank_key
            cards_set = self.your_cards_set
        else:
            suite_dict_to_check = self.opp_cards_dict_suite_key
            rank_dict_to_check = self.opp_cards_dict_rank_key
            cards_set = self.opp_cards_set

        if check_and_return_bool:
            for rank in rank_dict_to_check:
                if len(rank_dict_to_check[rank]) == 4:
                    return True
            return False
        else:
            num_hands = 0
            num_cards_to_be_revealed = 7 - len(cards_set)
            for rank in range(13):
                #no overlap since you can't have 2 four of a kinds thank god 
                rank_str = GameCard.value_to_string(None, "Rank", rank)
                if not our_bot:
                    player_ranks = []
                    for card in self.your_two_cards:
                        player_ranks.append(card.convert_value_to_string("Rank"))
                    if rank_str in player_ranks:
                        continue
                if rank_str in rank_dict_to_check:
                    num_cards_important_in_deck = len(rank_dict_to_check[rank_str])
                else:
                    num_cards_important_in_deck = 0
                num_cards_important_outside_deck = 4 - num_cards_important_in_deck
                num_cards_extra = num_cards_to_be_revealed - num_cards_important_outside_deck
                if num_cards_important_outside_deck <= num_cards_to_be_revealed:
                    num_hands += 1 * math.comb(len(self.remaining_cards) - num_cards_important_outside_deck, num_cards_extra)
            return num_hands
        
    def make_flush(self, our_bot = True, check_and_return_bool = False):
        if our_bot:
            suite_dict_to_check = self.your_cards_dict_suite_key
            rank_dict_to_check = self.your_cards_dict_rank_key
            cards_set = self.your_cards_set
        else:
            suite_dict_to_check = self.opp_cards_dict_suite_key
            rank_dict_to_check = self.opp_cards_dict_rank_key
            cards_set = self.opp_cards_set

        if check_and_return_bool:
            for suit in suite_dict_to_check:
                if len(suite_dict_to_check[suit]) >= 5:
                    return True
            return False
        else:
            num_hands = 0
            num_cards_to_be_revealed = 7 - len(cards_set)
            for suit in range(4):
                suit_str = GameCard.value_to_string(None, "Suite", suit)
                #print(rank_dict_to_check, suit_str)
                if suit_str in suite_dict_to_check:
                    num_cards_important_in_deck = len(suite_dict_to_check[suit_str])
                    #print(suit_str, num_cards_important_in_deck)
                else:
                    num_cards_important_in_deck = 0
                num_cards_important_outside_deck = 5 - num_cards_important_in_deck
                #num_cards_extra = num_cards_to_be_revealed - num_cards_important_outside_deck
                #print(num_cards_important_outside_deck, num_cards_extra, num_cards_to_be_revealed)
                for num_flush_to_draw in range(max(0,num_cards_important_outside_deck), 8):
                    if num_flush_to_draw <= num_cards_to_be_revealed:
                        num_cards_extra = num_cards_to_be_revealed - num_flush_to_draw
                        num_hands += 1 * math.comb(len(self.remaining_cards) - len(self.remaining_cards_suite_key[suit_str]), num_cards_extra) *math.comb(len(self.remaining_cards_suite_key[suit_str]), num_flush_to_draw)
            return num_hands - self.make_straight_flush(our_bot=our_bot) - self.make_royal_flush(our_bot)

    def make_three_of_a_kind(self, our_bot = True, check_and_return_bool = False):
        if our_bot:
            suite_dict_to_check = self.your_cards_dict_suite_key
            rank_dict_to_check = self.your_cards_dict_rank_key
            cards_set = self.your_cards_set
        else:
            suite_dict_to_check = self.opp_cards_dict_suite_key
            rank_dict_to_check = self.opp_cards_dict_rank_key
            cards_set = self.opp_cards_set

        if check_and_return_bool:
            possible = False
            for rank in rank_dict_to_check:
                if len(rank_dict_to_check[rank]) == 4:
                    return False
                if len(rank_dict_to_check[rank]) == 3:
                    possible = True
            return possible
        else:
            '''
            num_hands = 0
            num_cards_to_be_revealed = 7 - len(cards_set)
            for rank in range(13): 
                rank_str = Card.value_to_string(None, "Rank", rank)
                #print(rank_dict_to_check, rank_str)
                if rank_str in rank_dict_to_check:
                    num_cards_important_in_deck = len(rank_dict_to_check[rank_str])
                    #print(rank_str, num_cards_important_in_deck)
                else:
                    num_cards_important_in_deck = 0
                num_cards_important_outside_deck = 3 - num_cards_important_in_deck
                num_cards_extra = num_cards_to_be_revealed - num_cards_important_outside_deck
                #print(num_cards_important_outside_deck, num_cards_extra, num_cards_to_be_revealed)
                if num_cards_important_outside_deck <= num_cards_to_be_revealed and num_cards_important_outside_deck >=0:
                    num_hands += 1 * math.comb(len(self.remaining_cards) - len(self.remaining_cards_rank_key[rank_str]), num_cards_extra)*math.comb(len(self.remaining_cards_rank_key[rank_str]), num_cards_important_outside_deck)
            '''
            num_cards_until_three = []
            dict_of_cards_until_three = {0:0, 1:0, 2:0, 3:0}
            num_cards_to_be_revealed = 7 - len(cards_set)
            for rank in range(13):
                #print(rank, rank_dict_to_check.keys())
                rank = GameCard.value_to_string(None, "Rank", rank)
                if rank in rank_dict_to_check:
                    if len(rank_dict_to_check[rank]) == 4:
                        return 0
                    num = 3 - len(rank_dict_to_check[rank])
                    num_cards_until_three.append(num)
                    dict_of_cards_until_three[num] += 1
                else:
                    num_cards_until_three.append(3)
                    dict_of_cards_until_three[3] += 1

            split_up_table = { #format [(which ones we're finishing), num_extra, (list of people to give extras to and not make 3)]
                7:[[(3,3), 1, [3]],   [(3,), 4, [3]]], #no cards revealed -> all 3s
                6:[[(3,3), 0, [3,2]], [(3,2), 1, [3]], [(3,), 3, [3,2]], [(2,), 4, [3]]], #1 card revealed -> all 3s except 1 2
                5:[[(3,2), 0, [3,2]], [(3,1), 1, [3]], [(2,2), 1, [3]], [(3,), 2, [3, 2]], [(2,), 3, [3, 2]], [(1,), 4, [3]]], #one 1 and all 3s or two 2s and rest 3s
                4:[[(3,1), 0, [3,2]], [(2,2), 0, [3]], [(2,1), 1, [3]], [(3,), 1, [3,2]], [(2,), 2, [3,2]], [(1,), 3, [3,2]], [(), 4, [3]]], #3 revealed, one 0, one 1 one 2, three 2s
                3:[[(2,1), 0, [3,2]], [(1,1), 1, [3]], [(3,), 0, [3,2]], [(2,), 1, [3,2]], [(1,), 2, [3,2]], [(), 3, [3,2]]], #4 revealed, one 0 one 2, two 1s, one 1 two 2s, four 2s
                2:[[(1,1), 0, [3,2]], [(2,), 0, [3,2]], [(1,), 1, [3,2]], [(), 2, [3,2]]], #5 revealed, one 0 one 1, one 0 two 2s, two 1s one 2, one 1 three 2s, five 2s
                1:[[(1,), 0, [3,2]], [(), 1, [3,2]]]
            }

            if num_cards_to_be_revealed == 0:
                if self.make_three_of_a_kind(our_bot=True, check_and_return_bool=True):
                    return 1
                return 0

            distribution = split_up_table[num_cards_to_be_revealed]
            #print("3 of a kind",dict_of_cards_until_three, num_cards_to_be_revealed)
            num_hands = 0
            for potential_way in distribution:
                already_have_hand = dict_of_cards_until_three[0] != 0
                finish_3s, to_distribute_3s = 0, 0
                finish_2s, to_distribute_2s = 0, 0
                finish_1s, to_distribute_1s = 0, 0
                finishes = [0, finish_1s,finish_2s,finish_3s]
                new_dict_of_cards_until_three = {}

                #print(potential_way[0], potential_way)
                

                for num in potential_way[0]:
                    #print("here")
                    if num == 3: finish_3s += 1
                    if num == 2: finish_2s += 1
                    if num == 1: finish_1s += 1
                finishes = [0, finish_1s,finish_2s,finish_3s]
                if len(potential_way[0]) == 0:
                    finishes[0] = 1
                possible = True
                comb_finishes = 1
                #print("finishes", finishes)
                for key in dict_of_cards_until_three:
                    if dict_of_cards_until_three[key] < finishes[key]:
                        possible = False
                    else:
                        if key != 0: 
                            comb_finishes *= math.comb(dict_of_cards_until_three[key],finishes[key]) * (key + 1) ** finishes[key]
                            new_dict_of_cards_until_three[key] = dict_of_cards_until_three[key] - finishes[key]
                #print(comb_finishes, possible)
                #print("Dict:", dict_of_cards_until_three, new_dict_of_cards_until_three,"\n")
                if not possible: 
                    continue
                if already_have_hand:
                    comb_finishes = 1
                comb_finishes *= helper_func_distribute_extras_three_kind(new_dict_of_cards_until_three, potential_way[1], already_have_hand)
                #print(comb_finishes)
                num_hands+=comb_finishes
            return num_hands
    
    def make_three_of_a_kind_new(self, our_bot = True, check_and_return_bool = False):
        if our_bot:
            suite_dict_to_check = self.your_cards_dict_suite_key
            rank_dict_to_check = self.your_cards_dict_rank_key
            cards_set = self.your_cards_set
        else:
            suite_dict_to_check = self.opp_cards_dict_suite_key
            rank_dict_to_check = self.opp_cards_dict_rank_key
            cards_set = self.opp_cards_set

        if check_and_return_bool:
            possible = False
            for rank in rank_dict_to_check:
                if len(rank_dict_to_check[rank]) == 4:
                    return False
                if len(rank_dict_to_check[rank]) == 3:
                    possible = True
            return possible
        
        #Starting other code
        num_cards_until_three = []
        dict_of_cards_until_three = {0:0, 1:0, 2:0, 3:0}
        num_cards_to_be_revealed = 7 - len(cards_set)
        
        if num_cards_to_be_revealed == 0:
            if self.make_three_of_a_kind_new(our_bot, check_and_return_bool=True):
                return 1
            return 0

        for rank in range(13):
            rank = GameCard.value_to_string(None, "Rank", rank)
            if rank in rank_dict_to_check:
                if len(rank_dict_to_check[rank]) == 4:
                    return 0
                num = 3 - len(rank_dict_to_check[rank])
                num_cards_until_three.append(num)
                dict_of_cards_until_three[num] += 1
            else:
                num_cards_until_three.append(3)
                dict_of_cards_until_three[3] += 1

        return self.helper_new_three(num_cards_to_be_revealed, len(self.your_two_cards), len(self.opp_cards_set),our_bot, num_cards_until_three,dict_of_cards_until_three)

        if(num_cards_to_be_revealed == 7): #must be split 3-3-1 or 3-1-1-1-1
            if our_bot:
                return math.comb(13, 2) * 16 * math.comb(11, 1) * 4 + 13 * 4 * math.comb(12, 4) * 4**4
            else:
                total_hands = 0
                if len(self.your_cards_dict_rank_key) == 1: #no cards revealed yet, your two cards have same rank
                    #3-3-1
                    total_hands += math.comb(12, 2) * 16 * 2#1 is on your cards
                    total_hands += math.comb(12, 2) * 16 * 10 * 4#1 is not on your cards
                    #3-1-1-1-1
                    total_hands += (12 * 4) * 2 * math.comb(11, 3) * 4**3 #1 is on your cards
                    total_hands += (12 * 4) * math.comb(11, 4) * 4**4 #1 is not on your cards
                elif len(self.your_cards_dict_rank_key) == 2:
                    #3-3-1
                    total_hands += math.comb(11, 2) * 16 * 2 * 2#1 is on your cards, 3 is not one of your cards
                    total_hands += math.comb(11, 2) * 16 * 9 * 4#1 is not on your cards, 3 is not one of your cards
                    total_hands += (2 * 1) * (11 * 4) #one of your cards is a 3, the other is a 1
                    total_hands += 12 * 4 #both of your cards are a 3, 1 is not in your cards
                    #3-1-1-1-1
                    total_hands += (11 * 4) * (2 * 3) * math.comb(10, 3) * 4**3#3 not, 1 is on one of your card
                    total_hands += (11 * 4) * 3 * 3 * math.comb(10,2) * 16 #3 not, 1 is on both of your cards
                    total_hands += (11 * 4) * math.comb(10, 4) * 4**4 #3 not, 1 is not on your card
                else:
                    return -1
                return total_hands
        elif(num_cards_to_be_revealed == 6):
            return -1
        elif(num_cards_to_be_revealed == 5): #only our bot uses
            if not our_bot:
                return -1
            if len(self.your_cards_dict_rank_key) == 1:
                total_hands = 0
                #3-3-1
                total_hands += 2 * 12 * 4 * 11 * 4#add one to the rank, need a 1 and a 3
                #3-1-1-1-1
                total_hands += 2 * math.comb(12, 4) * 4**4 #add one to the rank, need four 1s
            elif len(self.your_cards_dict_rank_key) == 2:
                total_hands = 0
                #3-3-1
                total_hands += 3 * 3 * 11 * 4#add two to both, need a 1
                total_hands += 2 * 3 * 11 * 4#add two to one, need a 3
                #3-1-1-1-1
                total_hands += 2 * 3 * math.comb(11,3) * 4**3#add a two to one, need three 1s
                total_hands += 11 * 4 * math.comb(10, 2) * 16#need one 3, two 1s
                return total_hands
            else:
                return -1
        elif(num_cards_to_be_revealed == 4):
            if our_bot:
                return -1
            
            #two cards for player, three center cards 3, 2-1, 1-1-1
            
        elif(num_cards_to_be_revealed == 3):
            pass
        elif(num_cards_to_be_revealed == 2):
            pass
        elif(num_cards_to_be_revealed == 1):
            pass
        
    def helper_new_three(self, num_cards_to_be_revealed, num_player_cards, num_center_cards, our_bot, num_cards_until_three, dict_of_cards_until_three):
        #3-3-1 or 3-1-1-1-1
        #print(num_cards_until_three, dict_of_cards_until_three)
        #if num_player_cards != 2:
            #return -1
        #print("here")
        
        if dict_of_cards_until_three[0] + dict_of_cards_until_three[1] + dict_of_cards_until_three[2] > 5:
            return 0
        #print("here")
        comb_list = []
        one_list = []
        two_list = []
        for rank, item in enumerate(num_cards_until_three):
            if item not in [0,1,2]:
                if GameCard.value_to_string(None, "Rank", rank) in self.remaining_cards_rank_key:
                    comb_list.append(len(self.remaining_cards_rank_key[GameCard.value_to_string(None, "Rank", rank)]))
                else:
                    comb_list.append(0)
            else:
                comb_list.append(0)
                if item == 1:
                    if GameCard.value_to_string(None, "Rank", rank) in self.remaining_cards_rank_key:
                        comb_list.append(len(self.remaining_cards_rank_key[GameCard.value_to_string(None, "Rank", rank)]))
                    else:
                        comb_list.append(0)
                if item == 2:
                    if GameCard.value_to_string(None, "Rank", rank) in self.remaining_cards_rank_key:
                        comb_list.append(len(self.remaining_cards_rank_key[GameCard.value_to_string(None, "Rank", rank)]))
                    else:
                        comb_list.append(0)
    
        num_hands = 0
        #3-1-1-1-1
        if dict_of_cards_until_three[0] + dict_of_cards_until_three[1] > 1:
            num_hands += 0
        else:
            if dict_of_cards_until_three[0] == 1:
                #all combinations of getting four 1
                combs = itertools.combinations(comb_list, num_cards_to_be_revealed)
                num_hands += sum(math.prod(x) for x in combs) #* math.prod(two_list)
            elif dict_of_cards_until_three[1] == 1:
                #all combinations of getting four 1s * num ways to choose third card
                rank_of_two = GameCard.value_to_string(None, "Rank", num_cards_until_three.index(1))
                combs = itertools.combinations(comb_list, num_cards_to_be_revealed - 1)
                comb_sum = sum(math.prod(x) for x in combs)
                if rank_of_two in self.remaining_cards_rank_key:
                    num_hands += comb_sum * len(self.remaining_cards_rank_key[rank_of_two]) #* math.prod(two_list)
            else: #no 1s or 0s to pick the 3
                #picking a 2 for the three
                num_ways_to_pick_3 = 0
                for a in two_list:
                    num_ways_to_pick_3 += math.comb(a, 2)
                combs = itertools.combinations(comb_list, num_cards_to_be_revealed - 2)
                num_ways_to_pick_1 = sum(math.prod(x) for x in combs)
                
                num_hands += num_ways_to_pick_3 * num_ways_to_pick_1
                
                #not picking a 2 for the three
                #picking a 3 for the three
                for index, left_in_remaining in enumerate(comb_list):
                    new_list = comb_list[:index] + comb_list[index + 1:]
                    #print(new_list)
                    if num_cards_to_be_revealed > 3 and left_in_remaining >= 3:
                        combs = itertools.combinations([x for x in new_list if x!=0], num_cards_to_be_revealed - 3)
                        ways_to_pick_1 = sum(math.prod(x) for x in combs if x)
                        #print(left_in_remaining, ways_to_pick_1, math.comb(left_in_remaining, 3))
                        num_hands += math.comb(left_in_remaining, 3) * ways_to_pick_1
        return num_hands
        '''
        #3-3-1
        num_hands = 0
        if dict_of_cards_until_three[0] + dict_of_cards_until_three[1] + dict_of_cards_until_three[2] > 3 or dict_of_cards_until_three[0] + dict_of_cards_until_three[1] > 2:
            num_hands += 0
        else:
            
            #if dict_of_cards_until_three[0] == 2:
            #    if num_cards_to_be_revealed == 1:
             #       #need to pick a one from all of the remaining ranks
             #       num_hands += sum(comb_list)
            
            if dict_of_cards_until_three[1] == 0: #KKK-Q-Q KKK-QQQ Q-Q-Q
                num_needed_threes = 2 - dict_of_cards_until_three[0]
                #Choose 3s from 1s
                if dict_of_cards_until_three[0] + dict_of_cards_until_three[2] >= 2:
                    ways_to_select_threes_from_ones = itertools.combinations(two_list, num_needed_threes)
                    total_ways_to_pick_three = sum(math.prod(x) for x in ways_to_select_threes_from_ones if x)
                    if num_needed_threes == len(two_list):
                        total_ways_to_pick_one = sum(comb_list)
                    else: #elif num_needed_threes + 1 == len(two_list)
                        total_ways_to_pick_one = 1
                    num_hands += total_ways_to_pick_three * total_ways_to_pick_one
                return num_hands
                #choose one 1 and and one 3
                num_hands = 0
                if dict_of_cards_until_three[2] in [1,2] and num_needed_threes == 2:
                    if dict_of_cards_until_three[2] == 1: #only have one card down
                        ways_to_choose_three_one_from_threes = 0
                        for index, num in enumerate(comb_list):
                            new_list = comb_list[:index] + comb_list[index + 1:]
                            ways_to_choose_three = math.comb(comb_list[index], 3)
                            ways_to_choose_one = sum(new_list)
                            ways_to_choose_three_one_from_threes += ways_to_choose_three * ways_to_choose_one
                        num_hands += math.comb(two_list[0], 2) * ways_to_choose_three_one_from_threes
                    elif dict_of_cards_until_three[1] == 2: #have two different cards down
                        ways_to_choose_one_three_from_ones = math.comb(two_list[0],2) + math.comb(two_list[1], 2)
                        ways_to_choose_three = sum(math.comb(x, 3) for x in comb_list)
                        num_hands += ways_to_choose_one_three_from_ones * ways_to_choose_three
                return num_hands
            
                #Don't choose a 1 to be three
                pass
            elif dict_of_cards_until_three[2] == 0:
                if dict_of_cards_until_three[0] + dict_of_cards_until_three[1] == 2:
                    pass
                elif dict_of_cards_until_three[0] + dict_of_cards_until_three[1] == 1:
                    pass
                else:
                    pass
            else:
                #dict_of_cards_until_three[2] != 0
                pass
        return -1'''




    def make_straight(self, our_bot = True, check_and_return_bool = False):
        if our_bot:
            suite_dict_to_check = self.your_cards_dict_suite_key
            rank_dict_to_check = self.your_cards_dict_rank_key
            cards_set = self.your_cards_set
        else:
            suite_dict_to_check = self.opp_cards_dict_suite_key
            rank_dict_to_check = self.opp_cards_dict_rank_key
            cards_set = self.opp_cards_set

        if check_and_return_bool:
            for rank_value in range(-1, 9):
                ranks = []
                for potential_rank in range(rank_value, rank_value + 5):
                    potential_rank = potential_rank % 13
                    ranks.append(GameCard.value_to_string(None,"Rank", potential_rank))

                possible = True
                for rank in ranks:
                    if rank not in rank_dict_to_check:
                        possible = False
                        break
                if possible:
                    return True
            return False
        ###############################
        num_hands = 0
        num_cards_to_be_revealed = 7 - len(cards_set)

        # for 5
        for rank_value in range(-1, 9):
            ranks = []
            for potential_rank in range(rank_value, rank_value + 5):
                potential_rank = potential_rank % 13
                ranks.append(GameCard.value_to_string(None,"Rank", potential_rank))
            #print(ranks)
            comb_list_ranks = []
            needed_rank_names = []
            sum_bad = 0
            for rank in ranks:
                if rank not in rank_dict_to_check:
                    comb_list_ranks.append(len(self.remaining_cards_rank_key[rank]))
                    needed_rank_names.append(rank)
                    sum_bad += len(self.remaining_cards_rank_key[rank])
            
            if len(comb_list_ranks) > num_cards_to_be_revealed:
                #print("sad", num_cards_to_be_revealed, comb_list_ranks, needed_rank_names)
                pass
            else:
                for select_n_from_needed_ranks in range(len(comb_list_ranks), num_cards_to_be_revealed + 1):
                    #print(num_cards_to_be_revealed, comb_list_ranks, needed_rank_names, select_n_from_needed_ranks, self.straight_helper_func(comb_list_ranks, select_n_from_needed_ranks) * math.comb(len(self.remaining_cards) - sum_bad, num_cards_to_be_revealed - select_n_from_needed_ranks))
                    num_hands += self.straight_helper_func(comb_list_ranks, select_n_from_needed_ranks) * math.comb(len(self.remaining_cards) - sum_bad, num_cards_to_be_revealed - select_n_from_needed_ranks)
        
        #for 6s
        for rank_value in range(-1, 8):
            ranks = []
            for potential_rank in range(rank_value, rank_value + 6):
                potential_rank = potential_rank % 13
                ranks.append(GameCard.value_to_string(None,"Rank", potential_rank))

            comb_list_ranks = []
            sum_bad = 0
            for rank in ranks:
                if rank not in rank_dict_to_check:
                    comb_list_ranks.append(len(self.remaining_cards_rank_key[rank]))
                    sum_bad += len(self.remaining_cards_rank_key[rank])
            
            if len(comb_list_ranks) > num_cards_to_be_revealed:
                pass
            else:
                for select_n_from_needed_ranks in range(len(comb_list_ranks), num_cards_to_be_revealed + 1):
                    pass
                    num_hands -= self.straight_helper_func(comb_list_ranks, select_n_from_needed_ranks) * math.comb(len(self.remaining_cards) - sum_bad, num_cards_to_be_revealed - select_n_from_needed_ranks)
        return num_hands - self.make_straight_flush(our_bot) - self.make_royal_flush(our_bot)
    
    def straight_helper_func(self, combination_of_needed_ranks, num_from_ranks): #time consuming
        current_spread = []
        combination_of_needed_ranks = tuple(combination_of_needed_ranks)

        def recursive(comb_list, num_left):
            num_hands = 0
            if not comb_list:
                if num_left == 0:
                    return 1
                else:
                    return 0
            
            first_index, *comb_list = comb_list
            for a in range(1, first_index+1):
                num_hands += math.comb(first_index, a) * recursive(comb_list, num_left - a)
            return num_hands

        return recursive(combination_of_needed_ranks, num_from_ranks)

    def make_high_card(self, our_bot = True, check_and_return_bool = False):
        if our_bot:
            suite_dict_to_check = self.your_cards_dict_suite_key
            rank_dict_to_check = self.your_cards_dict_rank_key
            cards_set = self.your_cards_set
        else:
            suite_dict_to_check = self.opp_cards_dict_suite_key
            rank_dict_to_check = self.opp_cards_dict_rank_key
            cards_set = self.opp_cards_set

        num_cards_to_be_revealed = 7 - len(cards_set)

        if check_and_return_bool:
            for rank in rank_dict_to_check:
                if len(rank_dict_to_check[rank]) > 1:
                    return False
            return True
        else:
            for rank in rank_dict_to_check:
                if len(rank_dict_to_check[rank]) > 1:
                    return 0
            
            #not perfect for opponent with our info
            if our_bot:
                return math.comb(13 - len(rank_dict_to_check.keys()), num_cards_to_be_revealed) * 4 ** num_cards_to_be_revealed
            else:
                our_cards = self.your_cards_set - self.opp_cards_set
                player_ranks = []
                for card in our_cards:
                    player_ranks.append(card.convert_value_to_string("Rank"))
                
                try:
                    zero_in_dict = player_ranks[0] in rank_dict_to_check
                    one_in_dict = player_ranks[1] in rank_dict_to_check
                except:
                    return math.comb(13 - len(rank_dict_to_check.keys()), num_cards_to_be_revealed) * 4 ** num_cards_to_be_revealed
                #print(rank_dict_to_check, player_ranks)
                if one_in_dict and zero_in_dict:
                    #print("1")
                    return math.comb(13 - len(rank_dict_to_check.keys()), num_cards_to_be_revealed) * 4 ** num_cards_to_be_revealed
                elif player_ranks[0] == player_ranks[1] and not one_in_dict:
                    #print("2")
                    return (math.comb(13 - len(rank_dict_to_check.keys()) - 1, num_cards_to_be_revealed) * 4 ** num_cards_to_be_revealed 
                            + 2 * math.comb(13 - len(rank_dict_to_check.keys())- 1, num_cards_to_be_revealed-1) * 4 ** (num_cards_to_be_revealed-1))
                elif (zero_in_dict and not one_in_dict) or (not zero_in_dict and one_in_dict):
                    #print("3")
                    return (math.comb(13 - len(rank_dict_to_check.keys()) - 1, num_cards_to_be_revealed) * 4 ** num_cards_to_be_revealed
                            + 3 * math.comb(13 - len(rank_dict_to_check.keys()) - 1, num_cards_to_be_revealed - 1) * 4 ** (num_cards_to_be_revealed-1))
                elif not zero_in_dict and not one_in_dict:
                    #print("4h", num_cards_to_be_revealed, len(rank_dict_to_check.keys()) )
                    return (math.comb(13 - len(rank_dict_to_check.keys())-2, num_cards_to_be_revealed) * 4 ** num_cards_to_be_revealed
                            + 6 * math.comb(13 - len(rank_dict_to_check.keys()) - 2, num_cards_to_be_revealed - 1) * 4 ** (num_cards_to_be_revealed-1)
                            + 9 * math.comb(13 - len(rank_dict_to_check.keys()) - 2, num_cards_to_be_revealed - 2) * 4 ** (num_cards_to_be_revealed-2))
                else:
                    raise KeyError("Come fix me!")
    
    def make_one_pair(self, our_bot = True, check_and_return_bool = False):
        if our_bot:
            suite_dict_to_check = self.your_cards_dict_suite_key
            rank_dict_to_check = self.your_cards_dict_rank_key
            cards_set = self.your_cards_set
        else:
            suite_dict_to_check = self.opp_cards_dict_suite_key
            rank_dict_to_check = self.opp_cards_dict_rank_key
            cards_set = self.opp_cards_set

        remaining_suite_dict = self.remaining_cards_suite_key
        remaining_rank_dict = self.remaining_cards_rank_key
        num_cards_to_be_revealed = 7 - len(cards_set)

        if check_and_return_bool:
            num_2s = 0
            for rank in rank_dict_to_check:
                if len(rank_dict_to_check[rank]) > 2:
                    return False
                elif len(rank_dict_to_check[rank]) == 2:
                    num_2s += 1
            if num_2s == 1:
                return True
            return False
        else:
            nums_1, num_2s = 0, 0
            for rank in rank_dict_to_check:
                if len(rank_dict_to_check[rank]) > 2:
                    return 0
                elif len(rank_dict_to_check[rank]) == 2:
                    num_2s += 1
                elif len(rank_dict_to_check[rank]) == 1:
                    nums_1 += 1
            if num_2s > 1:
                return 0
            elif num_2s == 1:
                if our_bot:
                    return math.comb(13 - num_2s - nums_1, num_cards_to_be_revealed) * 4**num_cards_to_be_revealed
                else:
                    our_cards = self.your_two_cards
                    player_ranks = []
                    for card in our_cards:
                        player_ranks.append(card.convert_value_to_string("Rank"))
                    try:
                        zero_in_dict = player_ranks[0] in rank_dict_to_check
                        one_in_dict = player_ranks[1] in rank_dict_to_check
                    except:
                        return math.comb(13 - num_2s - nums_1, num_cards_to_be_revealed) * 4**num_cards_to_be_revealed
        

                    if one_in_dict and zero_in_dict:
                        return math.comb(13 - num_2s - nums_1, num_cards_to_be_revealed) * 4**num_cards_to_be_revealed
                    elif player_ranks[0] == player_ranks[1] and not one_in_dict:
                        return (math.comb(13 - num_2s - nums_1 - 1, num_cards_to_be_revealed) * 4**num_cards_to_be_revealed
                                + 2 * math.comb(13 - num_2s - nums_1 - 1, num_cards_to_be_revealed - 1) * 4**(num_cards_to_be_revealed-1))
                    elif (zero_in_dict and not one_in_dict) or (not zero_in_dict and one_in_dict):
                        return (math.comb(13 - num_2s - nums_1 - 1, num_cards_to_be_revealed) * 4**num_cards_to_be_revealed
                                + 3 * math.comb(13 - num_2s - nums_1 - 1, num_cards_to_be_revealed - 1) * 4**(num_cards_to_be_revealed-1))
                    elif not zero_in_dict and not one_in_dict:
                        return (math.comb(13 - num_2s - nums_1 - 2, num_cards_to_be_revealed) * 4**num_cards_to_be_revealed
                                + math.comb(13 - num_2s - nums_1 - 2, num_cards_to_be_revealed - 1) * 4**(num_cards_to_be_revealed-1) * 6
                                +9 * math.comb(13 - nums_1 - num_2s - 2, num_cards_to_be_revealed - 2) * 4**(num_cards_to_be_revealed-2))
                    else:
                        raise KeyError("Come fix me!")
            else:
                if our_bot:
                    num_hands = 0
                    num_singles = len(rank_dict_to_check)

                    #making a totally new pair
                    if num_cards_to_be_revealed >= 2:
                        num_hands += math.comb(13-num_singles, 1) * 6 * math.comb(13-num_singles-1, num_cards_to_be_revealed-2) * 4**(num_cards_to_be_revealed-2)
                    #making a pair from one card that already exists
                    if num_cards_to_be_revealed >= 1:
                        num_hands += num_singles * 3 * math.comb(13 - num_singles, num_cards_to_be_revealed - 1) * 4**(num_cards_to_be_revealed - 1)

                    return num_hands
                else:
                    num_hands = 0
                    num_singles = len(rank_dict_to_check)

                    our_cards = self.your_two_cards
                    player_ranks = []
                    for card in our_cards:
                        player_ranks.append(card.convert_value_to_string("Rank"))
                    
                    try:
                        zero_in_dict = player_ranks[0] in rank_dict_to_check
                        one_in_dict = player_ranks[1] in rank_dict_to_check
                    except:
                        return self.make_one_pair(True)

                    #making a totally new pair
                    if num_cards_to_be_revealed >= 2:
                        if one_in_dict and zero_in_dict:
                            num_hands += 6 * (13-num_singles) * math.comb(13 - num_singles - 1, num_cards_to_be_revealed - 2) * 4**(num_cards_to_be_revealed -2)
                        elif (one_in_dict and not zero_in_dict) or (zero_in_dict and not one_in_dict):
                            num_hands += (3 * math.comb(13 - num_singles - 1, num_cards_to_be_revealed - 2) * 4**(num_cards_to_be_revealed - 2) #pair on the one they chosen
                                          + 6 * math.comb(13 - num_singles - 1, 1) * math.comb(13 - num_singles - 2, num_cards_to_be_revealed - 2) * 4 ** (num_cards_to_be_revealed - 2)) #pair on one not chosen, no singles on one chosen
                            if num_cards_to_be_revealed >= 3:
                                num_hands += 6 * math.comb(13 - num_singles - 1, 1) * 3 * math.comb(13 - num_singles - 2, num_cards_to_be_revealed - 3) * 4**(num_cards_to_be_revealed - 3) #pair on one not chosen, single on one chosen
                        elif(player_ranks[0] == player_ranks[1] and not zero_in_dict):
                            num_hands += 1 * math.comb(13 - num_singles - 1, num_cards_to_be_revealed - 2) #pair on our_bots
                            num_hands += 6 * (13 - num_singles - 1) * math.comb(13 - num_singles - 2, num_cards_to_be_revealed - 2) * 4**(num_cards_to_be_revealed - 2) #pair not on our_bots, card not on it
                            
                            if num_cards_to_be_revealed >= 3:
                                num_hands += 6 * (13 - num_singles - 1) * 2 * math.comb(13 - num_singles - 2, num_cards_to_be_revealed - 3) * 4**(num_cards_to_be_revealed-3) #pair not on our_bots, card on it
                        elif(not zero_in_dict and not one_in_dict and player_ranks[0] != player_ranks[1]):
                            num_hands += 2*3 * math.comb(13-num_singles - 2, num_cards_to_be_revealed - 2)*4**(num_cards_to_be_revealed-2)#pair on our_bot hands, card not on our_bot hands
                            num_hands += 6 * (13 - num_singles - 2) * math.comb(13-num_singles - 3, num_cards_to_be_revealed - 2) * 4**(num_cards_to_be_revealed - 2) #pair not on our_bot hands, card not on our_bot hands

                            if num_cards_to_be_revealed >= 3:
                                num_hands += 2*3*3*math.comb(13 - num_singles - 2, num_cards_to_be_revealed - 3) * 4**(num_cards_to_be_revealed-3) #pair on our_bot hands, card on our_bot hands
                                num_hands += 6 * (13 - num_singles - 2) * 3 * math.comb(13-num_singles-3, num_cards_to_be_revealed-3) * 4**(num_cards_to_be_revealed - 3)#pair not on our_bot hands, card on one of our_bot hands
                            if num_cards_to_be_revealed >= 4:
                                num_hands += 6 * (13 - num_singles - 2) * 3 * 3 * math.comb(13 - num_singles - 3, num_cards_to_be_revealed - 4) * 4**(num_cards_to_be_revealed - 4)#pair not on our_bot hands, card on both of our_bot hands
                        else:
                            raise KeyError("Missing a case apparently")
                    
                    #making a pair from one card that already exists
                    if num_cards_to_be_revealed >= 1:
                        if one_in_dict and zero_in_dict and player_ranks[0] == player_ranks[1]:
                           num_hands += 1 * math.comb(13 - num_singles, num_cards_to_be_revealed - 1) * 4**(num_cards_to_be_revealed - 1) #create pair on our_bot
                           num_hands += 3 * (num_singles - 1) * math.comb(13 - num_singles, num_cards_to_be_revealed - 1) * 4**(num_cards_to_be_revealed -1)#don't create pair on our_bot
                        elif one_in_dict and zero_in_dict and player_ranks[0] != player_ranks[1]:
                            num_hands += 2 * 2 * math.comb(13 - num_singles, num_cards_to_be_revealed - 1) * 4**(num_cards_to_be_revealed -1) #pair on one of them
                            num_hands += 3 * (num_singles - 2) * math.comb(13 - num_singles, num_cards_to_be_revealed - 1) * 4**(num_cards_to_be_revealed -1)#pair not on one of them
                        elif (one_in_dict and not zero_in_dict) or (zero_in_dict and not one_in_dict):
                            if num_cards_to_be_revealed >= 2:
                                num_hands += 2 * 3 * math.comb(13 - num_singles - 1, num_cards_to_be_revealed - 2) * 4 ** (num_cards_to_be_revealed - 2)#pair on it card on it
                                num_hands += 3 * (num_singles - 1) * 3 * math.comb(13 - num_singles - 1, num_cards_to_be_revealed - 2) * 4**(num_cards_to_be_revealed - 2)#not on pair, card on it
                            num_hands += 2 * math.comb(13 - num_singles - 1, num_cards_to_be_revealed - 1) * 4**(num_cards_to_be_revealed -1)#pair on it card not on it
                            num_hands += 3 * (num_singles - 1) * math.comb(13 - num_singles - 1, num_cards_to_be_revealed - 1) * 4**(num_cards_to_be_revealed -1)#not on pair card not on it
                        elif (not one_in_dict and not zero_in_dict) and player_ranks[0] == player_ranks[1]:
                            if num_cards_to_be_revealed >= 2:
                                num_hands += 3 * num_singles * 2 * math.comb(13 - num_singles - 1, num_cards_to_be_revealed - 2) * 4**(num_cards_to_be_revealed - 2)#choose the bot card
                            num_hands += 3 * num_singles * math.comb(13 - num_singles - 1, num_cards_to_be_revealed - 1) * 4 ** (num_cards_to_be_revealed - 1)#don't choose the bot card
                        elif (not one_in_dict and not zero_in_dict) and player_ranks[0] != player_ranks[1]:
                            if num_cards_to_be_revealed >= 2:
                                num_hands += (3 * num_singles) * 3 * math.comb(13 - num_singles - 2, num_cards_to_be_revealed - 2) * 4**(num_cards_to_be_revealed - 2)#on one card
                            if num_cards_to_be_revealed >= 3:
                                num_hands += (3 * num_singles) * 3 * 3 * math.comb(13 - num_singles - 2, num_cards_to_be_revealed - 3) * 4**(num_cards_to_be_revealed - 3)#on two cards
                            num_hands += (3 * num_singles) * math.comb(13 - num_singles - 2, num_cards_to_be_revealed - 1) * 4 ** (num_cards_to_be_revealed -1)#on none cards
                        else:
                            raise KeyError("Missing a case apparently")

                    return num_hands

    def check_two_pair(self, our_bot = True):
        if our_bot:
            suite_dict_to_check = self.your_cards_dict_suite_key
            rank_dict_to_check = self.your_cards_dict_rank_key
            cards_set = self.your_cards_set
        else:
            suite_dict_to_check = self.opp_cards_dict_suite_key
            rank_dict_to_check = self.opp_cards_dict_rank_key
            cards_set = self.opp_cards_set

        num_twos = 0
        for a in rank_dict_to_check.values():
            if len(a) == 2:
                num_twos += 1
        if num_twos >= 2:
            return True
        return False

    def check_full_house(self, our_bot = True):
        if our_bot:
            suite_dict_to_check = self.your_cards_dict_suite_key
            rank_dict_to_check = self.your_cards_dict_rank_key
            cards_set = self.your_cards_set
        else:
            suite_dict_to_check = self.opp_cards_dict_suite_key
            rank_dict_to_check = self.opp_cards_dict_rank_key
            cards_set = self.opp_cards_set

        three_plus = 0
        two = 0
        for a in rank_dict_to_check:
            if len(a) == 2:
                two += 1
            elif len(a) >= 3:
                three_plus += 1

        if two + three_plus > 2 and three_plus > 1:
            return True
        return False

    def randomize_hand(self):
        self.remaining_cards = set()
        for suit in Suite:
            for rank in Rank:
                self.remaining_cards.add(GameCard(rank, suit))
        hands = random.sample(sorted(self.remaining_cards), 2)
        self.set_hand_for_new_round(set(hands), set())
        hands_2 = random.sample(sorted(self.remaining_cards), 5)
        self.set_hand_for_new_round(set(hands), set(hands_2))

    def approx_win_tie_loss_percentages(self):
        win_percentage = 0
        tie_percentage = 0
        loss_percentage = 0
        for index, hand in enumerate(self.normalized_hands):
            tie_percentage += hand[0] * hand[1] / 100
            for opp_hand in (self.normalized_hands[index+1:]):
                win_percentage += hand[0] * opp_hand[1] / 100
            for opp_hand in (self.normalized_hands[:index]):
                loss_percentage += hand[0] * opp_hand[1] / 100

        return (win_percentage, tie_percentage, loss_percentage)
            
                
    def print_hand_percentages(self):
        func_names = ["Royal Flush", "Straight Flush", "Four of a Kind", "Flush", "Straight", "Three of a Kind","One Pair", "High Card"]
        functions = [self.make_royal_flush, self.make_straight_flush, self.make_four_of_a_kind, self.make_flush, self.make_straight, self.make_three_of_a_kind, self.make_one_pair, self.make_high_card]
        best_hand_percentage = [True, True, True, "Close", "Close", False, False, False]
        print("\n\nYour Hand:")
        hand = set(card.str_version() for card in self.your_two_cards)
        print(hand)
        print("\nCenter Cards")
        hand = set(card.str_version() for card in self.opp_cards_set)
        print(hand)
        print("\n-----------------------------------------------------\nAll Percentages\n-----------------------------------------------------\nHand\t\t\tPlayer\tOpp\tBest Hand %")
        for name, func,truth in zip(func_names,functions, best_hand_percentage):
            if name == "Flush":
                print(name + "\t\t\t" + str(round(func(our_bot = True)/ self.num_hands_self * 100, 2)) + "%\t" + str(round(func(our_bot = False)/ self.num_hands_opp * 100, 2)) + "%\t" + str(truth))
            else:
                print(name + "\t\t" + str(round(func(our_bot = True)/ self.num_hands_self * 100, 2)) + "%\t" + str(round(func(our_bot = False)/ self.num_hands_opp * 100, 2)) + "%\t" + str(truth))
        print("-----------------------------------------------------\nAdjusted\n-----------------------------------------------------")
        for name, percentage,truth in zip(self.print_hand_names,self.normalized_hands, self.adjusted_best_hand_percentage):
            if name == "Flush":
                print(name + "\t\t\t" + str(round(percentage[0], 2)) + "%\t" + str(round(percentage[1], 2)) + "%\t" + str(truth))
            else:
                print(name + "\t\t" + str(round(percentage[0], 2)) + "%\t" + str(round(percentage[1], 2)) + "%\t" + str(truth))

        print("\n\n", self.approx_win_tie_loss_percentages())

    def get_hand_percentages(self, our_bot = True):
        if our_bot:
            return [x[0] for x in self.normalized_hands]
        else:
            return [x[1] for x in self.normalized_hands]
def helper_func_distribute_extras_three_kind(curr_card_dist, num_cards_to_distribute, already_have_triple):
    num_2s = curr_card_dist[2]
    num_3s = curr_card_dist[3]
    if num_2s == 0:
        take_away_two = 0
        take_away_one = num_cards_to_distribute
        total_possibilities = 0
        while take_away_two * 2 <= num_cards_to_distribute:
            total_possibilities += math.comb(num_3s, take_away_two) * 6**take_away_two * math.comb(num_3s - take_away_two, take_away_one) * 4**take_away_one
            take_away_two += 1
            take_away_one -= 2
        return total_possibilities
    else:
        take_away_from_the_twos = 0
        total_possibilities = 0
        while take_away_from_the_twos <= num_2s:
            take_away_two = 0
            take_away_one = num_cards_to_distribute - take_away_from_the_twos 
            while take_away_two * 2 <= num_cards_to_distribute - take_away_from_the_twos:
                keep = math.comb(num_3s, take_away_two) 
                keep *= (6**take_away_two )
                keep *=  math.comb(num_3s - take_away_two, take_away_one) * (4**take_away_one )
                keep *= math.comb(num_2s, take_away_from_the_twos) * (3**take_away_from_the_twos)
                #print(num_3s,num_2s, take_away_from_the_twos, take_away_one, take_away_two, keep)
                total_possibilities += math.comb(num_3s, take_away_two) * 6**take_away_two * math.comb(num_3s - take_away_two, take_away_one) * 4**take_away_one * math.comb(num_2s, take_away_from_the_twos) * 3**take_away_from_the_twos
                take_away_two += 1
                take_away_one -= 2
            take_away_from_the_twos += 1
        #print(total_possibilities)
        return total_possibilities
    



  
hand_class = hands()
hand_class.set_hand_for_new_round({GameCard(Rank.KING, Suite.DIAMOND), GameCard(Rank.QUEEN, Suite.DIAMOND)}, {GameCard(Rank.ACE, Suite.DIAMOND), GameCard(Rank.JACK, Suite.DIAMOND), GameCard(Rank.TEN, Suite.DIAMOND)})#{Card(Rank.FOUR,Suite.CLUB), Card(Rank.TEN,Suite.CLUB), Card(Rank.THREE, Suite.CLUB), Card(Rank.TWO, Suite.CLUB)}
hand_class.print_hand_percentages()
num_straight_flush_us = hand_class.make_straight_flush(our_bot=True)
num_straight_flush_them = hand_class.make_straight_flush(our_bot=False)
'''
print(hand_class.make_royal_flush(our_bot=False))
print(hand_class.make_straight_flush(our_bot=False))
print(hand_class.num_hands_self, hand_class.num_hands_opp)
print(num_straight_flush_us/hand_class.num_hands_self, num_straight_flush_them/hand_class.num_hands_opp)

print(hand_class.make_four_of_a_kind(our_bot=False))
print(hand_class.num_hands_self, hand_class.num_hands_opp)

print(hand_class.make_flush(our_bot=True),hand_class.make_flush(our_bot=False))
print(hand_class.make_high_card(our_bot=True),hand_class.make_high_card(our_bot=False))
print(hand_class.num_hands_self, hand_class.num_hands_opp)'''
'''
print("\n\n------------------------------------------------------\n")
hand_class.print_hand_percentages()

testing_hands = hands()
correct = 0
total = 100
coolness = [0,0,0,0,0,0,0,0,0,0]
for a in range(total):
    if a%100==0:print(a)
    testing_hands.randomize_hand()
    if((testing_hands.make_royal_flush(True, True) and testing_hands.normalized_hands[testing_hands.acces_dict["Royal Flush"]][0] == 100.0) or
       (testing_hands.make_straight_flush(True, True) and testing_hands.normalized_hands[testing_hands.acces_dict["Straight Flush"]][0] == 100.0) or
       (testing_hands.make_four_of_a_kind(True, True) and testing_hands.normalized_hands[testing_hands.acces_dict["Four of a Kind"]][0] == 100.0) or
       (testing_hands.check_full_house(True) and testing_hands.normalized_hands[testing_hands.acces_dict["Full House"]][0] == 100.0) or
       (testing_hands.make_flush(True, True) and testing_hands.normalized_hands[testing_hands.acces_dict["Flush"]][0] == 100.0) or
       (testing_hands.make_straight(True, True) and testing_hands.normalized_hands[testing_hands.acces_dict["Straight"]][0] == 100.0) or
       (testing_hands.make_three_of_a_kind(True, True) and testing_hands.normalized_hands[testing_hands.acces_dict["Three of a Kind"]][0] == 100.0) or
       (testing_hands.check_two_pair(True) and testing_hands.normalized_hands[testing_hands.acces_dict["Two Pair"]][0] == 100.0) or
       (testing_hands.make_one_pair(True, True) and testing_hands.normalized_hands[testing_hands.acces_dict["One Pair"]][0] == 100.0) or
       (testing_hands.make_high_card(True, True) and testing_hands.normalized_hands[testing_hands.acces_dict["High Card"]][0] == 100.0)):
        correct += 1
        if testing_hands.make_royal_flush(True, True):
            coolness[0] += 1
        elif testing_hands.make_straight_flush(True, True):
            coolness[1] += 1
        elif testing_hands.make_four_of_a_kind(True, True):
            coolness[2] += 1
        elif testing_hands.normalized_hands[testing_hands.acces_dict["Full House"]][0] == 100.0:
            coolness[3] += 1
        elif testing_hands.make_flush(True, True):
            coolness[4] += 1
        elif testing_hands.make_straight(True, True):
            coolness[5] += 1
        elif testing_hands.make_three_of_a_kind(True):
            coolness[6] += 1
        elif testing_hands.check_two_pair(True):
            coolness[7] += 1
        elif testing_hands.make_one_pair(True, True):
            coolness[8] += 1
        elif testing_hands.make_high_card(True, True):
            coolness[9] += 1
    else:
        testing_hands.print_hand_percentages()
        print("Royal Flush", testing_hands.make_royal_flush(True, True))
        print("Straight Flush", testing_hands.make_royal_flush(True, True))
        print("Four of a Kind", testing_hands.make_royal_flush(True, True))
        print("Full House", testing_hands.make_royal_flush(True, True))
        print("Flush", testing_hands.make_royal_flush(True, True))
        print("Straight", testing_hands.make_royal_flush(True, True))
        print("Three of a Kind", testing_hands.make_royal_flush(True, True))
        print("Two Pair", testing_hands.make_royal_flush(True, True))
        print("One Pair", testing_hands.make_royal_flush(True, True))
        print("High Card", testing_hands.make_royal_flush(True, True))
    
print(correct)
for name, a in zip(testing_hands.print_hand_names, coolness):
    print(name, round(a/total*100,3))


#print(hand_class.make_three_of_a_kind_new(), hand_class.make_three_of_a_kind_new()/hand_class.num_hands_self*100)
#print(hand_class.make_three_of_a_kind_new(our_bot=False), hand_class.make_three_of_a_kind_new(our_bot=False)/hand_class.num_hands_opp*100)  #combination_of_needed_ranks, num_from_ranks
#print(hand_class.make_three_of_a_kind(our_bot=True), hand_class.num_hands_self)
#print(hand_class.make_three_of_a_kind(our_bot=False), hand_class.num_hands_opp)'''