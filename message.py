class Message:
    """Messages consist of a status list. that convey meaning on aspects of the
       current state.  The message is created using the alphabet
       {0,1,2,3,4,5}"""

    # The message index can be used to refer to a position in the message by
    # what it means
    game_msg_def = [ 'source',
                       'life',
                       'rel_mines',
                       'tavern_dist',
                       'near_dist',
                       'near_life',
                       'near_mine',
                       'med_dist',
                       'med_life',
                       'med_mine',
                       'far_dist',
                       'far_life',
                       'far_mine',
                       'tavern_enemy_relative_distance',
                     ]
    game_msg_index = { v: i for (i,v) in enumerate(game_msg_def) }

    first_enemy_index = game_msg_index['near_dist']

    def __init__(self, emitter = None ):
        self.status = [0] * len(self.game_msg_index)
        self.emitter = emitter

    def __str__(self):
        print "HIHI"
        return str(self.status)

    def _relative_tavern_enemy_distance( self, tavern_dist, enemy_dist ):
        relative = tavern_dist - enemy_dist
        if ( relative > 6 ):
            return 0
        elif ( relative > 3 ):
            return 1
        elif ( relative > 0 ):
            return 2
        elif ( relative > -1 ):
            return 3
        elif ( relative > -4 ):
            return 4
        else:
            return 5

    def _relative_distance( self, distance ):
        """Returns path distance to enemy on a scale of 0 to 5"""
        if ( distance < 2 ):
            return 0
        elif ( distance < 3 ):
            return 1
        elif ( distance < 4 ):
            return 2
        elif ( distance < 8 ):
            return 3
        elif ( distance < 16 ):
            return 4
        else:
            return 5

    def _relative_life( self, enemy_life, hero_life ):
        """Returns enemy's life realative to the hero's on a scale of 0 to 5"""
        if hero_life > enemy_life + 40:
            return 0
        elif hero_life > enemy_life + 20:
            return 1
        elif hero_life > enemy_life:
            return 2
        elif hero_life > enemy_life - 20:
            return 3
        elif hero_life > enemy_life - 40:
            return 4
        else:
            return 5

    def _relative_mines( self, mines, total_mines, enemies ):
        """Returns number of mines owned relative to total on the board on a
           scale of 0 to 5"""
        enemy_max = 0
        unowned = total_mines - mines
        for pos,e in enemies.iteritems():
            unowned -= e.mines
            if e.mines > enemy_max:
                enemy_max = e.mines

        if ( unowned > total_mines / 3 ):
            if ( mines > enemy_max + 2 ):
                return 4
            elif ( mines > enemy_max ):
                return 3
            else:
                return 2
        elif ( mines > enemy_max + 3 ):
            return 5
        elif ( mines > enemy_max + 1 ):
            return 4
        elif ( mines > enemy_max ):
            return 3
        elif ( mines > enemy_max - 1 ):
            return 2
        elif ( mines > enemy_max - 3 ):
            return 1
        else:
            return 0

    def _absolute_mines( self, mines, total_mines ):
        """Returns number of mines owned relative to total on the board on a
           scale of 0 to 5"""
        return int( ( mines / float(len( total_mines )) ) * 6 - 0.01)


    def game_message(self,game):

        # Indicate message source is the game status
        self.status[self.game_msg_index['source']] = 0

        self.status[self.game_msg_index['life']] = \
            int( ( game.hero.life / 100.0 ) * 6 - 0.01) 
        self.status[self.game_msg_index['rel_mines']] = \
            self._relative_mines( game.hero.mines, len( game.board.mines_list), game.enemies )

        if ( None == game.board.taverns_list[0].path):
            tavern_dist = 999
        else:
            tavern_dist = len(game.board.taverns_list[0].path)
        self.status[self.game_msg_index['tavern_dist']] = \
            self._relative_distance( tavern_dist )
  
        enemy_msg_index = { 'dist': 0, 'life': 1, 'mine': 2 }

        # Initialize the dictionary of values for each enemy
        enemy_status = [ { 'dist': 0, 'values': [0] * len(enemy_msg_index) }
            for x in range(3) ]
        i = 0
        for pos,enemy in game.enemies.iteritems():
            if ( None == enemy.path):
                distance = 999
            else:
                distance = len(enemy.path)
            enemy_status[i]['dist'] = distance
            enemy_status[i]['values'][enemy_msg_index['dist']] = \
                self._relative_distance(distance)
            enemy_status[i]['values'][enemy_msg_index['life']] = \
                self._relative_life( enemy.life, game.hero.life )
            enemy_status[i]['values'][enemy_msg_index['mine']] = \
                self._absolute_mines( enemy.mines, game.board.mines )
            i += 1

        # Enter the information for each enemy into the message sorted by proximity
        enemy_status.sort()
        index = self.first_enemy_index
        for enemy in enemy_status:
            for v in enemy['values']:
                self.status[index] = v
                index +=1
        self.status[self.game_msg_index['tavern_enemy_relative_distance']] = self._relative_tavern_enemy_distance( tavern_dist, enemy_status[0]['dist'] )
        #print self.status

    def rule_matches(self,condition):
        """Return true if a given condition matches the message.
           A rule is said to match a message if the message value at each position is
           in the list of the rule at that same position, or the rule value is None at
           that position."""
        i = 0
        for x in condition:
            if ( None != x ):
                if ( self.status[i] not in x ):
                    return False
            i += 1

        return True
                
