from message import Message

import random
import string

class Classifier:
    """A classifier consists of two parts.
        1. The rule is used to match against messages for when the classifier activates.
        2. The output consists of a list of messages to be added to the message queue"""
    # TODO add classifier strength as described in the paper.

    # NOTE Rules are created using the following alphabet
    # {None(Matches any value), [0], [1], [2], [3], [4], [5],
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
        self.strength = 100
        self.specifity = 0
        self.output = None, 'RandomWalk'
        self.identifier = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(10))

    def check_activate( self, messages ):
        """Return true if the messages activate the rule."""
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
                
    def bid( self ):
        bid = 0.1 * ( self.specifity / float( 5 * len(Message.game_msg_index) ) ) * self.strength
        return bid
    def pay( self, paid ):
        self.strength += paid
        if ( self.strength < 0 ):
            self.strength = 0
