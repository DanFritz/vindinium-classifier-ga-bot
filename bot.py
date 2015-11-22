from game import Game
from message import Message
from classifier import Classifier
from collections import deque
from classifier_system import ClassifierSystem

import random

class Bot:
    pass

class TesterBot3000(Bot, ClassifierSystem):
    def __init__(self, key = "NONE"):
        """Initialize the bot's classifiers."""
        self.key = key
        self.input_interface = []
        ClassifierSystem.__init__(self)
        self.action = 'Wait'

    def new_game(self, state):
        """Initialize the bot with a new game."""
        self.game = Game(state)
        print "I am player",
        print self.game.hero.ident
        print "My position",
        print self.game.hero.pos
        self.expected_pos = self.game.hero.pos
        self.prev_mines = 0
        self.prev_gold = 0
        self.prev_life = 100
        ClassifierSystem.new_game(self)

    def finish_game(self):
        ClassifierSystem.finish_game(self)
        

    def move(self, state):
        """Use the game state to decide what action to take, and then output
           the direction to move."""
        self.game.update(state)
        message = Message()
        message.game_message(self)
        self.input_interface.append( message )

        self.action = self.decide()

        retval = 'Stay'
        if ( self.action == 'Heal' ):
            if ( None != self.game.board.taverns_list[0].path ):
                retval = self.game.board.taverns_list[0].path[0]
        elif ( self.action == 'Mine' ):
            if ( None != self.game.board.mines_list[0].path ):
                retval = self.game.board.mines_list[0].path[0]
        elif ( self.action == 'Attack' ):
            if ( None != self.game.enemies_list[0].path ):
                retval = self.game.enemies_list[0].path[0]
        elif ( self.action == 'Wait' ):
            retval = 'Stay'
        self.expected_pos = self.game.board.to( self.game.hero.pos, retval )
        self.prev_mines = self.game.hero.mines
        self.prev_gold = self.game.hero.gold
        self.prev_life = self.game.hero.life

        return retval



