#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import requests
import re
import ga
from bot import TesterBot3000

TIMEOUT=15

def get_new_game_state(session, server_url, key, mode='training', number_of_turns = 10):
    """Get a JSON from the server containing the current state of the game"""

    if(mode=='training'):
        #Don't pass the 'map' parameter if you want a random map
        params = { 'key': key, 'turns': number_of_turns, 'map': 'm1'}
        api_endpoint = '/api/training'
    elif(mode=='arena'):
        params = { 'key': key}
        api_endpoint = '/api/arena'

    #Wait for 10 minutes
    r = session.post(server_url + api_endpoint, params, timeout=10*60)

    if(r.status_code == 200):
        return r.json()
    else:
        print("Error when creating the game")
        print(r.text)

def move(session, url, direction):
    """Send a move to the server
    
    Moves can be one of: 'Stay', 'North', 'South', 'East', 'West' 
    """

    try:
        r = session.post(url, {'dir': direction}, timeout=TIMEOUT)

        if(r.status_code == 200):
            return r.json()
        else:
            print("Error HTTP %d\n%s\n" % (r.status_code, r.text))
            return {'game': {'finished': True}}
    except requests.exceptions.RequestException as e:
        print(e)
        return {'game': {'finished': True}}


def is_finished(state):
    return state['game']['finished']

def run_game(server_url, key, mode, turns, bot):
    """Starts a game with all the required parameters"""

    # Create a requests session that will be used throughout the game
    session = requests.session()

    if(mode=='arena'):
        print('Connected and waiting for other players to join…')
    # Get the initial state
    state = get_new_game_state(session, server_url, key, mode, turns)

    # Initialize the bot
    bot.new_game(state)
    print("Playing at: " + state['viewUrl'])

    turn = 0
    while not is_finished(state):
        # Some nice output ;)
        turn += 1
        gold_totals = "\r" + str(turn) + \
                " : " + str(bot.game.hero.gold) + \
                " " + str(bot.game.enemies_list[0].gold) + \
                " " + str(bot.game.enemies_list[1].gold) + \
                " " + str(bot.game.enemies_list[2].gold) 
        #sys.stdout.write('.')
        sys.stdout.write(gold_totals)
        
        sys.stdout.flush()

        # Choose a move
        direction = bot.move(state)

        # Send the move and receive the updated game state
        url = state['playUrl']
        state = move(session, url, direction)

    # Clean up the session
    bot.classifiers = ga.step_generation( bot.classifiers )
    bot.print_classifier_status()
    session.close()


if __name__ == "__main__":
    if (len(sys.argv) < 4):
        print("Usage: %s <key> <[training|arena]> <number-of-games|number-of-turns> [server-url]" % (sys.argv[0]))
        print('Example: %s mySecretKey training 20' % (sys.argv[0]))
    else:
        key = sys.argv[1]
        mode = sys.argv[2]

        if(mode == "training"):
            number_of_games = 1
            number_of_turns = int(sys.argv[3])
        else: 
            number_of_games = int(sys.argv[3])
            number_of_turns = 300 # Ignored in arena mode

        if(len(sys.argv) == 5):
            server_url = sys.argv[4]
        else:
            server_url = "http://vindinium.org"
        bot = TesterBot3000(key)

        for i in range(number_of_games):
            run_game(server_url, key, mode, number_of_turns, bot)
            print("\nGame finished: %d/%d" % (i+1, number_of_games))

        bot.pickle()
