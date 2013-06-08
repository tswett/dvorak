import random

def phenny_command(commands, priority = 'medium'):
    def decorator(func):
        func.commands = commands
        func.priority = priority
        return func

    return decorator

def public_only(func):
    def public_only_func(phenny, input):
        if input.sender == input.nick: # sent in private
            phenny.notice(input.nick, 'This command can only be used in public.')
        else: # sent in public
            func(phenny, input)

    return public_only_func

class Card:
    # An individual card, located in a Deck and in a Pile.

    def __init__(self, deck, idnum, title):
        self.deck = deck
        self.idnum = idnum
        self.title = title
        self.pile = None

    def __str__(self):
        return unicode(self).encode('utf-8')

    def __unicode__(self):
        return ('Card %s: %s' % (self.idnum, self.title))

    def show_location(self):
        if self.pile != None:
            return 'In pile: %s' % self.pile.name
        else:
            return 'Nowhere'

    def move_to(self, pile):
        if self.pile != None:
            self.pile.remove(self)

        self.pile = pile

        if self.pile != None:
            pile.append(self)

class Deck(dict):
    # An object containing the entire state of a game.

    def __init__(self):
        self.next_idnum = 1

        self.piles = {}
        self.piles['draw'] = Pile(self, 'Draw pile')
        self.piles['discard'] = Pile(self, 'Discard pile')

        self.piles['hands'] = {}

    def new_card(self, title):
        card = Card(self, self.next_idnum, title)
        self[self.next_idnum] = card
        self.next_idnum += 1
        return card

    def get_card(self, idnum):
        return self[idnum]

    def delete_card(self, idnum):
        self[idnum].move_to(None)
        del self[idnum]

    def get_pile(self, path):
        path_parts = path.split('.')
        init_parts, last_part = path_parts[:-1], path_parts[-1]

        current_place = self.piles

        for part in init_parts:
            if part not in current_place:
                current_place[part] = {}
            current_place = current_place[part]

        if last_part not in current_place:
            current_place[last_part] = Pile(self, path)

        return current_place[last_part]

    def get_hand(self, player):
        hands = self.piles['hands']

        if player in hands:
            return hands[player]
        else:
            hand = Pile(self, "%s's hand" % player)
            hands[player] = hand
            return hand

class Pile(list):
    # A pile of Cards out of one particular Deck.

    def __init__(self, deck, name):
        self.deck = deck
        self.name = name

    def show_cards(self):
        return ', '.join([unicode(card) for card in self]) or 'empty'

    def place_on_top(self, other_pile):
        for card in self[:]:
            card.move_to(other_pile)

deck = Deck()

def say_back(phenny, input, response):
    if input.sender == input.nick: # sent in private
        phenny.notice(input.nick, response) # send back a NOTICE
    else: # sent in public
        phenny.say(response) # sent back a PRIVMSG

@phenny_command(['newcard'])
@public_only
def new_card(phenny, input):
    card_title = input.group(2)
    card = deck.new_card(card_title)
    say_back(phenny, input, unicode(card))

@phenny_command(['cardtitle'])
def card_title(phenny, input):
    card_idnum = int(input.group(2))
    say_back(phenny, input, unicode(deck.get_card(card_idnum)))

@phenny_command(['where'])
@public_only
def where_card(phenny, input):
    card_idnum = int(input.group(2))
    say_back(phenny, input, deck[card_idnum].show_location())

@phenny_command(['move'])
@public_only
def move_card(phenny, input):
    card_idnum_str, pile_name = input.group(2).split(' ')

    card_idnum = int(card_idnum_str)
    pile = deck.get_pile(pile_name)

    deck[card_idnum].move_to(pile)
    say_back(phenny, input, 'Card moved to pile: %s.' % pile.name)

@phenny_command(['list'])
@public_only
def list_pile(phenny, input):
    say_back(phenny, input, deck.get_pile(input.group(2)).show_cards())

@phenny_command(['listhand'])
def list_hand(phenny, input):
    say_back(phenny, input, deck.get_hand(input.nick).show_cards())

@phenny_command(['shuffle'])
@public_only
def shuffle_pile(phenny, input):
    pile = deck.get_pile(input.group(2))
    random.shuffle(pile)
    say_back(phenny, input, 'Pile shuffled: %s.' % pile.name)

@phenny_command(['draw'])
@public_only
def draw_card(phenny, input):
    if deck.get_pile('draw'):
        card = deck.get_pile('draw')[-1]
        card.move_to(deck.get_hand(input.nick))
        say_back(phenny, input, 'Card drawn.')
    else:
        say_back(phenny, input, 'No cards in draw pile.')

@phenny_command(['moveallto'])
@public_only
def move_all_cards_to(phenny, input):
    for idnum in deck:
        deck[idnum].move_to(deck.get_pile(input.group(2)))
    say_back(phenny, input, 'Cards moved.')

@phenny_command(['delete'])
@public_only
def delete_card(phenny, input):
    deck.delete_card(int(input.group(2)))
    say_back(phenny, input, 'Card deleted.')

@phenny_command(['placeon'])
@public_only
def place_on(phenny, input):
    first_pile, second_pile = input.group(2).split(' ')
    deck.get_pile(first_pile).place_on_top(deck.get_pile(second_pile))
    say_back(phenny, input, 'Cards moved.')

@phenny_command(['printallpiles'])
@public_only
def print_all_piles(phenny, input):
    say_back(phenny, input, unicode(deck.piles))

@phenny_command(['reset'])
@public_only
def reset_deck(phenny, input):
    global deck
    deck = Deck()
    say_back(phenny, input, 'Deck reset.')
