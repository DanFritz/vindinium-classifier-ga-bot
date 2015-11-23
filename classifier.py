from message import Message

import random
import string

class Classifier:
    """A classifier consists of two parts.
        1. The rule is used to match against messages for when the classifier activates.
        2. The output consists of a list of messages to be added to the message queue"""
    # NOTE Rules are created using the following alphabet
    # {None(The don't care state), [0], [1], [2], [3], [4], [5],
    #   [0,1], [0,2], [0,3], [0,4], [0,5],
    #   [1,2], [1,3], [1,4], [1,5],
    #   [2,3], [2,4], [2,5],
    #   [3,4], [3,5],
    #   [4,5],
    #   [0,1,2], [0,1,3] [0,1,4], [0,1,5], [0,2,3], [0,2,4], [0,2,5], [0,3,4], [0,3,5], [0,4,5],
    #   [1,2,3], [1,2,4], [1,2,5], [1,3,4], [1,3,5], [1,4,5],
    #   [2,3,4], [2,3,5], [2,4,5],
    #   [3,4,5],
    #   [0,1,2,3], [0,1,2,4], [0,1,2,5], [0,1,3,4], [0,1,3,5], [0,1,4,5], [0,2,3,4], [0,2,3,5], [0,2,4,5], [0,3,4,5],
    #   [1,2,3,4], [1,2,3,5], [1,2,4,5], [1,3,4,5],
    #   [2,3,4,5],
    #   [0,1,2,3,4], [0,1,2,3,5], [0,1,2,4,5], [0,1,3,4,5], [0,2,3,4,5],
    #   [1,2,3,4,5] }
    
    def __init__(self):
        self.conditions = []
        self.conditions.append( [ None ] * len( Message.game_msg_index) )
        self.strength = 100
        self.specifity = 0
        self.output = None, 'Wait'
        self.identifier = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(10))
        self.source_classifiers = []
        self.game_activations = 0
        self.total_activations = 0
        self.age = 0

    def __str__(self):
        retval = ""
        retval += "Identifier: "
        retval += self.identifier
        retval += "\n  Strength: "
        retval += str(self.strength)
        retval += "\n  Output: "
        retval += str(self.output)
        retval += "\n  Specifity: "
        retval += str(self.specifity)
        retval += "\n  Total Activations: "
        retval += str(self.total_activations)
        retval += "\n  Game Activations: "
        retval += str(self.game_activations)
        retval += "\n  Conditions\n"
        for cond in self.conditions:
            for i,v in enumerate(cond):
                retval += "    %30s " % Message.game_msg_def[i] + str(v) + "\n"
        return retval
    def __repr__(self):
        return str(self)

    def print_status(self):
        return "%s %3d %5d %3d %2d %6s %f" % ( self.identifier, self.age, self.total_activations, self.game_activations, self.specifity, self.output[1], self.strength )

    def new_game(self):
        self.game_activations = 0

    def game_over(self):
        self.total_activations += self.game_activations
        self.age += 1


    def remove_other_subset( self, other ):
        """Remove the specified value of other from self"""
        for i, cond in enumerate(self.conditions):
            for j, x in enumerate(cond):
                if ( x != None or other.conditions[i][j] != None ):
                    if ( x != None ):
                        new_x = x[:]
                    else:
                        new_x = range(6)
                    if ( other.conditions[i][j] != None 
                        and new_x != other.conditions[i][j] ):
                        for y in other.conditions[i][j]:
                            if y in new_x:
                                new_x.remove(y)
                                self.specifity += 1
                    self.conditions[i][j] = new_x

    def is_subset( self, other ):
        """Check to see if other is a subset of self"""
        if ( self.output != other.output ):
            return False
        for i, cond in enumerate(self.conditions):
            for j, x in enumerate(cond):
                if ( x != None ):
                    if ( other.conditions[i][j] == None ):
                        return False
                    for y in other.conditions[i][j]:
                        if ( y not in x ):
                            return False
        return True
    def __eq__( self, other ):
        """Check to see if other is a subset of self"""
        if ( not isinstance(other,Classifier) ):
            return False
        if ( self.output != other.output ):
            return False
        if ( self.conditions != other.conditions ):
            return False

        return True
    def __ne__( self, other ):
        if ( not isinstance(other,Classifier) ):
            return True
        if ( self.output != other.output ):
            return True
        if ( self.conditions != other.conditions ):
            return True
        return False
    def __lt__( self, other ):
        return ( self.strength < other.strength )
    def __le__( self, other ):
        return ( self.strength <= other.strength )
    def __gt__( self, other ):
        return ( self.strength > other.strength )
    def __ge__( self, other ):
        return ( self.strength >= other.strength )

    def check_activate( self, messages ):
        """Return true if the messages activate the rule."""
        if ( self.strength <= 0 ):
            return False
        conditions_to_match = self.conditions[:]
        self.source_classifiers = []
        for m in messages:
            for c in conditions_to_match:
                if ( m.rule_matches(c) ):
                    conditions_to_match.remove(c)
                    if ( None != m.emitter ):
                        self.source_classifiers.append( m.emitter )
            if len(conditions_to_match) == 0:
                return True
        return False

    def self_activates( self ):
        if ( self.output[0] == None ):
            return False
        if ( self.check_activate([self.output[0]])):
            return True
        return False
                
    def bid( self ):
        bid = 0.02 * ( self.specifity / float( 5 * len(Message.game_msg_index) ) ) * self.strength
        return bid
    def pay( self, paid ):
        self.strength += paid
        if ( self.strength < 0 ):
            self.strength = 0
    def activate( self, price ):
        """Pay the price and count a classifier activation"""
        self.pay(-price)
        self.game_activations += 1
    def breeding_value( self ):
        return self.strength + self.specifity * 5
