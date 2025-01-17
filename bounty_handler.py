import math
class Bounty():
    def __init__(self):
        self.bounty = {"A":1, "2":1, "3":1, "4":1, "5":1, "6":1, "7":1, "8":1, "9":1, "T":1, "J":1, "Q":1, "K":1}

    def handle_new_round(self, round_num, your_cards, center_cards, opp_cards, bounty_hit, opp_won):
        if round_num % 25 == 1:
            self.bounty = {"A":1, "2":1, "3":1, "4":1, "5":1, "6":1, "7":1, "8":1, "9":1, "T":1, "J":1, "Q":1, "K":1}
        
        your_cards = [card[0] for card in your_cards]
        opp_cards = [card[0] for card in opp_cards]
        center_cards = [card[0] for card in center_cards]

        if opp_won:
            if bounty_hit:

                if not opp_cards:
                    for card in center_cards:
                        self.bounty[card] += 1
                    #for card in [card for card in your_cards if card not in center_cards]:
                        #self.bounty[card] = 0

                else:
                    for card in self.bounty:
                        if ((card in center_cards) or (card in opp_cards) and self.bounty[card] != 0):
                            self.bounty[card] += 1
                        else:
                            self.bounty[card] = 0
            
            else:

                for card in opp_cards:
                    self.bounty[card] = 0
                
                for card in center_cards:
                    self.bounty[card] = 0

    def get_chance_bounty_hit(self, center_cards):
        center_cards = set(card[0] for card in center_cards)
        try:
            result = sum(self.bounty[card]/sum(self.bounty.values()) for card in center_cards)
        except:
            result = 0
        if result == 0:
            result = 1-12/13*12/13

        return result
        


    def get_normalized_percentages(self):
        ranks = ["2", "3", "4", "5", "6", "7", "8", "9", "T", "J", "Q", "K", "A"]
        sum_of_all = sum(self.bounty.values())

        for a in range(13):
            try:
                ranks[a] = round(self.bounty[ranks[a]]/sum_of_all, 3)
            except:
                ranks[a] = 0
        #print("ranks",ranks)
        return ranks
                
                    

