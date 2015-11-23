from game import Game
from message import Message
from classifier import Classifier
from collections import deque

import random
import pickle
import os.path
import ga


class ClassifierSystem:
    
    decisions = ['Heal','Mine','Attack','Wait']
    def __init__(self):
        #self.classifiers = self._get_test_classifiers()
        random.seed()
        self.classifiers = []
        self.depickle()
        if ( not self.classifiers ):
            self.classifiers = [ self._create_classifier() for x in range(500) ]
        self.max_active = 4
        self.active = deque([])
        self.matches = []

    def _create_classifier(self, message = None):
        """Create a new classifier that optionally matches a message"""
        c = Classifier()
        min_specifity = 10
        total_str = 0
        if self.classifiers:
            for classify in self.classifiers:
                total_str += classify.strength
            average_str = total_str / len(self.classifiers)
            c.strength = average_str
        else:
            c.strength = 100

        # Set condition
        elements = range(len(Message.game_msg_index))
        random.shuffle(elements)
        elements_specifity = [ random.randint(1,5) for x in xrange(len(Message.game_msg_index))]
        c.specifity = 0

        # Create the condition
        condition_num = 0
        for i,value in enumerate(elements):
            c.specifity += 6 - elements_specifity[i]
            c.conditions[condition_num][value] = \
                random.sample(xrange(0,5),elements_specifity[i] )

            # Ensure message's value is in the condition
            if ( message != None ):
                if ( message.status[value] not in c.conditions[condition_num][value] ):
                    c.conditions[condition_num][value][0] = message.status[value]

            c.conditions[condition_num][value].sort()

            # Stop adding to the condition sometime after you have > min_specifity
            if ( c.specifity > min_specifity ):
                if ( random.random() < float(i) / float(len(Message.game_msg_index) ) ):
                    break
            if ( random.random() < 0.01 and c.specifity < min_specifity * 0.3 and len(c.conditions) == 1 ):
                c.conditions.append( [ None ] * len( Message.game_msg_index) )
                condition_num +=1

        # Set output
        if (random.random() < 0.1):
            while True:
                output_message = Message()
                output_message.classifier_message()
                output_message.emitter = c
                if ( not c.self_activates() ):
                    break
        else:
            output_message = None
        c.output = output_message, random.choice(['Heal','Mine','Attack','Wait'])
        return c
        

    def _get_test_classifiers(self):
        """Set the classifiers to a set of custom built classifiers"""
        c = [ Classifier() for x in range(7) ]

        # If you are less than 1/2 life, go heal
        c[0].identifier = 'heal 1/2 life'
        c[0].conditions[0][Message.game_msg_index['source']] = [0]
        c[0].conditions[0][Message.game_msg_index['life']] = [0, 1, 2]
        c[0].specifity = 8
        c[0].output = None, 'Heal'

        # If enemy has atleast 1 mine, has less health than you, and is within 2 steps
        # attack him
        c[1].identifier = 'Attack close1'
        c[1].conditions[0][Message.game_msg_index['source']] = [0]
        c[1].conditions[0][Message.game_msg_index['near_dist']] = [0, 1]
        c[1].conditions[0][Message.game_msg_index['near_life']] = [0, 1, 2]
        c[1].conditions[0][Message.game_msg_index['near_mine']] = [1, 2, 3, 4, 5]
        c[1].specifity = 13
        c[1].output = None, 'Attack'

        # If you have more than 1/2 life, mine
        c[2].identifier = 'Mine Standard'
        c[2].conditions[0][Message.game_msg_index['source']] = [0]
        c[2].conditions[0][Message.game_msg_index['life']] = [3, 4, 5]
        c[2].specifity = 8
        c[2].output = None, 'Mine'

        # If you are next to a mine, and don't have max life, heal
        c[3].identifier = 'Heal at taver'
        c[3].conditions[0][Message.game_msg_index['source']] = [0]
        c[3].conditions[0][Message.game_msg_index['life']] = [0, 1, 2, 3, 4]
        c[3].conditions[0][Message.game_msg_index['tavern_dist']] = [0]
        c[3].specifity = 11
        c[3].output = None, 'Heal'

        # If you have more mines than anyone else, and there is an enemy
        # approaching, go to the nearest tavern
        c[4].identifier = 'enemy coming '
        c[4].conditions[0][Message.game_msg_index['source']] = [0]
        c[4].conditions[0][Message.game_msg_index['rel_mines']] = [3, 4, 5]
        c[4].conditions[0][Message.game_msg_index['tavern_enemy_relative_distance']] = [0, 1, 2, 3]
        c[4].specifity = 10
        c[4].output = None, 'Heal'

        # Idling rule
        c[5].identifier = 'Idle         '
        c[5].conditions[0][Message.game_msg_index['source']] = [0]
        c[5].specifity = 5
        c[5].output = None, 'Wait'

        # A bad rule, should lose strength
        c[6].identifier = 'Bad attack   '
        c[6].conditions[0][Message.game_msg_index['source']] = [0]
        c[6].conditions[0][Message.game_msg_index['life']] = [0,1,2]
        c[6].conditions[0][Message.game_msg_index['near_dist']] = [0,1,2]
        c[6].conditions[0][Message.game_msg_index['near_life']] = [3,4,5]
        c[6].specifity = 15
        c[6].output = None, 'Attack'
        return c

    def _weighted_choice( self, choices ):
        """Choose one of choices proportional to the strength values"""
        total = sum( strength for strength, out, sources in choices )
        r = random.uniform(0,total)
        upto = 0
        for strength , c, sources in choices:
            if upto + strength > r:
                return strength, c.output[1]
            upto += strength
        return None

    def _single_disburse( self, amount ):
        """Disburse the credit to the active classifiers"""
        if ( len( self.active ) > 0 ):
            for y in self.active[-1]:
                c, source_classifiers = y
                c.pay( amount )
                for z in source_classifiers:
                    z.pay( amount / float(len(source_classifiers)) )

    def _delayed_disburse( self, amount ):
        """Disburse the credit to the active classifiers"""
        if ( len( self.active ) >= 2 ):
            for x in range(len(self.active)/2,self.max_active):
                if ( x < len(self.active) ):
                    for y in self.active[x]:
                        c, source_classifiers = y
                        c.pay( amount / float(len(self.active)/2) )
                        for z in source_classifiers:
                            z.pay( amount / float(len(source_classifiers)) )

    def _disburse( self, amount ):
        """Disburse the credit to the active classifiers"""
        for x in self.active:
            for y in x:
                c, source_classifiers = y
                c.pay( amount / float(len(self.active)) )
                for z in source_classifiers:
                    z.pay( amount / float(len(source_classifiers)) )


    def _credit_allocation( self ):
        """Give credit to the current situation to the active classifiers"""
        # Payoff results from previous turn
        # Detect Death
        # TODO this does not work if you die on your spawn point
        if ( self.game.hero.pos != self.expected_pos
             and self.game.hero.pos == self.game.hero.spawn ):

             self._disburse(-15 * self.prev_mines )
             self.active = deque([])
        # If you didn't die, pay active classifers by the amount of gold gained
        else:
            # If you captured a mine or killed someone who had mines, reward
            if ( self.game.hero.mines > self.prev_mines ):
                self._single_disburse(10 * (self.game.hero.mines - self.prev_mines) )
                self.healing_loop = 0

            # Reward for gold earned
            #self._disburse( self.game.hero.gold - self.prev_gold )
            
            # Reward for healing
            if ( self.game.hero.life > self.prev_life and self.prev_life < 81 ):
                # Prevent healing loop
                if ( self.healing_loop < 4 ):
                    self._single_disburse(10 * self.game.hero.mines )
                self.healing_loop += 1

        if ( len(self.active) >= self.max_active ):
            self.active.popleft()
    def _end_of_game_credit_allocation( self ):
        """Disburse credit based on number of allocations in the game, and the game result"""
        reward = 0
        enemies = sorted( self.game.enemies_list, key = lambda x: x.gold )
        if ( self.game.hero.gold <= enemies[0].gold * 0.5 ):
            reward = -0.2
        elif ( self.game.hero.gold <= enemies[0].gold ):
            reward = 0
        elif ( self.game.hero.gold < enemies[1].gold ):
            reward = 0.3
        elif ( self.game.hero.gold < enemies[2].gold ):
            reward = 1
        elif ( self.game.hero.gold < enemies[2].gold * 1.5 ):
            reward = 2
        else:
            reward = 3
        for c in self.classifiers:
            c.pay(reward*c.game_activations)




    def __str__( self ):
        """Output for debugging"""
        retval = ""
        retval += "Classifier list\n"
        for c in self.classifiers:
            retval += c.__str__()
        retval += "END Classifiers\n"
        return retval

    def print_classifier_status( self ):
        """Output for debugging"""
        print "Classifier status"
        for c in sorted(self.classifiers):
            print c.print_status()

    def decide( self ):
        """Decide what action to take this turn"""
        self._credit_allocation();
        
        # Process the input_interface Messages
        self.matches = []
        messages = self.input_interface[:]
        self.input_interface = []

        # Find all classifiers that match the input messages
        #print "match",
        for c in self.classifiers:
            if ( c.check_activate(messages) ):
                #print c.identifier,
                #print ",",
                message, action = c.output
                if ( None == action ):
                    c.pay(c.bid())
                    if ( None != message ):
                        self.input_interface.append( message )
                else:
                    self.matches.append( ( c.bid(), c, c.source_classifiers ) )
        #print ""

        # if not enough matches, create one
        while ( len( self.matches ) < 3 ):
            c = self._create_classifier(messages[-1])
            self.classifiers.append(c)
            self.matches.append( ( c.bid(), c, c.source_classifiers ) )
            #print "CREATED NEW CLASSIFIER"
            #print self.classifiers[-1]

        # Choose an action from the matches to output
        choice = self._weighted_choice(self.matches)
        #print "choice",
        #print choice

        # activate all of the classifiers that specified the chosen action
        # and send any output messages to the input interface
        if ( None != choice ):
            paid, winner = choice
            activated = []
            for m in self.matches:
                bid, c, source_classifiers = m
                if c.output[1] == winner:
                    activated.append( (c, source_classifiers ) )
                    c.activate(paid)
                    message, action = c.output
                    if ( None != message ):
                        self.input_interface.append( message )
            self.active.append(activated)
            return action
        else:
            return 'None'
    def new_game(self):
        """Initialize the bot with a new game."""
        for c in self.classifiers:
            c.new_game()
        self.healing_loop = 0

    def finish_game(self):
        """End of game cleanup tasks"""
        self._end_of_game_credit_allocation()
        for c in self.classifiers:
            c.game_over()
        print "Maximum classifier strength before normalization = %f" % self.classifiers[-1].strength
        self.classifiers = ga.step_generation( self.classifiers )
        self.classifiers.sort()
        self.print_classifier_status()

    def depickle( self ):
        """Read the classifiers from a file"""
        if ( os.path.exists('data_'+self.key) ):
            f = open('data_'+self.key, 'r')
            self.classifiers = pickle.load( f)
            f.close()
    def pickle( self ):
        """Write the classifiers to a file to be loaded later"""
        f = open('data_'+self.key, 'w')
        pickle.dump(self.classifiers, f)
        f.close()


