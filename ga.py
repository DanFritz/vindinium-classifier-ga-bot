
from classifier import Classifier
from message import Message
import string
import pickle
import random
import os.path
import copy


def step_generation( classifiers ):
    random.seed()

    if ( classifiers != None ):
        classifiers.sort()
        #for c in classifiers:
            #print c
        classifiers = kill_the_weak( classifiers, 20 )
        breeders = select_breeders( classifiers, 10 )
        young = create_offspring( breeders )
        classifiers.extend(young)
    return classifiers

def kill_the_weak( classifiers, quota ):
    classifiers.sort()
    deleted = 0
    print "Killing the weak"
    new_list = []
    for i,c in enumerate(classifiers):
        if ( random.random() > float( deleted ) / quota ):
            print "  Killing %s strength %f." % (c.identifier, c.strength)
            deleted += 1
        else:
            new_list.append(c)
    return new_list

def select_breeders( classifiers, quota ):
    classifiers.reverse()
    selected = 0
    print "Selecting the strong"
    new_list = []
    for i,c in enumerate(classifiers):
        if ( random.random() > float( selected ) / quota ):
            print "  Breeding %s strength %f." % (c.identifier, c.strength)
            new_list.append(c)
            selected += 1
        if ( selected >= quota ):
            break
    return new_list

def create_offspring( breeders ):
    stock = breeders[:]
    kids = []
    random.shuffle( stock )
    print "Making babies"

    i = 0
    while i < len(stock) - 1:
        parents = stock[i], stock[i+1]
        print "  Parents %s and %s" % ( parents[0].identifier, parents[1].identifier )
        for k in range(4):
            mom = parents[ k % 2 ]
            dad = parents[ (k + 1) % 2 ]
            kid = copy.deepcopy(mom)
            kid.identifier = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(10))
            kid.strength = 100
            kid.specifity = 0
            for j,cond in enumerate(kid.conditions):
                if ( j < len ( dad.conditions ) ):
                    division = random.randrange( 1, len(Message.game_msg_def) )
                    l = 0
                    while ( l < len( Message.game_msg_def ) ):
                        if ( l > division ):
                            cond[l] = dad.conditions[j][division]
                        if ( cond[l] != None ):
                            kid.specifity += 6 - len( cond[l] )
                        l += 1
                # Chance of mutation
                if ( random.random() < 0.02 ):
                    print "MUTATION"
                    index = random.randrange( len( Message.game_msg_def ) )
                    print cond[index]
                    if ( cond[index] == None ):
                        cond[index] = random.sample(xrange(6),5)
                        cond[index].sort()
                        print "Deleting from All"
                        kid.specifity += 1
                    elif ( len(cond[index]) == 1 ):
                            print "adding to One"
                            choices = [ x for x in range(6) if not x in cond[index] ]
                            cond[index].append( random.choice( choices ) )
                            cond[index].sort()
                            kid.specifity -= 1
                    else:
                        if ( random.random() > 0.5 ):
                            print "Deleting"
                            del cond[index][random.randrange(len(cond[index]))]
                            kid.specifity += 1
                        else:
                            print "adding"
                            choices = [ x for x in range(6) if not x in cond[index] ]
                            if ( choices ):
                                cond[index].append( random.choice( choices ) )
                                cond[index].sort()
                            else:
                                cond[index] = None
                            kid.specifity -= 1
                    print cond[index]
                            
            print "    %s and %s Made %s." % (mom.identifier, dad.identifier, kid.identifier )
            kids.append( kid )
        i += 2
    return kids
