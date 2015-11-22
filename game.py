import re

from collections import deque
import heapq

TAVERN = 0
AIR = -1
WALL = -2
MINE = -3

PLAYER1 = 1
PLAYER2 = 2
PLAYER3 = 3
PLAYER4 = 4

AIM = {'North': (-1, 0),
       'East':  ( 0, 1),
       'South': ( 1, 0),
       'West':  ( 0,-1),
       'Stay':  ( 0, 0)}
REVERSE_AIM = {(-1,0): 'South',
               (0, 1): 'West',
               (1, 0): 'North',
               (0,-1): 'East',
               (0, 0): 'Stay'}

class Game:
    def __init__(self, state):
        self.board = Board(state['game']['board'])
        self.threat_map = [ [0 for i in range(self.board.size)] for j in range(self.board.size)]
        self.hero = Hero(state['hero'], True)
        self.update(state)

    def update(self, state):
        """Update paths, enemy positions, and mine ownership"""
        self.state = state
        self.enemies = {}
        self.enemies_list = []
        self.clear_paths()
        for i in range(len(state['game']['heroes'])):
            if ( state['game']['heroes'][i]['id'] != state['hero']['id'] ):
                new_enemy = Hero( state['game']['heroes'][i], False )
                self.enemies[new_enemy.pos] = new_enemy
                self.enemies_list.append( new_enemy )
        self.hero = Hero(state['hero'], True)
        for k,v in self.board.mines.iteritems():
            v.update_owner(state['game']['board']['tiles'],self.hero.ident)
        self.dijkstra()
        for t in self.board.taverns_list:
            t.set_value()
        self.board.taverns_list.sort(key = Tavern.get_value)
        for m in self.board.mines_list:
            m.set_value()
        self.board.mines_list.sort(key = Mine.get_value)
        for e in self.enemies_list:
            e.set_value()
        self.enemies_list.sort(key = Hero.get_value)

    def get_path( self, node ):
        """Return a path from a linked node list"""
        path = []
        distance, loc, this_node = node
        while ( this_node ):
            to_row, to_col = loc
            distance, loc, this_node = this_node
            from_row, from_col = loc
            path.append( REVERSE_AIM[(from_row-to_row,from_col-to_col)] )
        path.reverse()
        return path

    def clear_paths(self):
        """Clear the existing paths between locations"""
        for k,v in self.enemies.iteritems():
            v.path = None
        for k,v in self.board.taverns.iteritems():
            v.path = None
        for k,v in self.board.mines.iteritems():
            v.path = None



        
    def bfs(self):
        """Calculate paths using breadth first search"""
        frontier_queue = deque([])
        frontier_dict = {}
        explored = {}
        frontier_queue.append( (0, self.hero.pos, None) )
        frontier_dict[self.hero.pos] = (0, self.hero.pos, None)

        while ( frontier_queue ):
            node = frontier_queue.popleft()
            distance, loc, parent = node
            
            del frontier_dict[loc]
            explored[loc] = node

            for direction,coords in enumerate(AIM):
                next_loc = self.board.to(loc, coords)
                if next_loc:
                    next_node = ( distance + 1, next_loc, node )
                    if next_loc in self.board.mines:
                        if not self.board.mines[next_loc].path:
                            self.board.mines[next_loc].path = self.get_path(next_node)
                            #print "Path to Mine = ",
                            #print self.board.mines[next_loc].path,
                            #print "  ",
                            #print next_loc
                    elif next_loc in self.enemies:
                        if not self.enemies[next_loc].path:
                            self.enemies[next_loc].path = self.get_path(next_node)
                            #print "Path to enemy = ",
                            #print self.enemies[next_loc].path,
                            #print "  ",
                    elif next_loc in self.board.taverns:
                        if not self.board.taverns[next_loc].path:
                            self.board.taverns[next_loc].path = self.get_path(next_node)
                            #print "Path to Tavern = ",
                            #print self.board.taverns[next_loc].path,
                            #print "  ",
                    elif (next_loc not in explored
                            and next_loc not in frontier_dict
                            and self.board.passable(next_loc)):
                        frontier_queue.append( next_node )
                        frontier_dict[next_loc] = next_node

    def threat_update(self):
        """Change the threat map for new enemy locations"""
        self.threat_map = [ [0 for i in range(self.board.size)] for j in range(self.board.size)]
        enemy_num = 0;
        for pos,enemy in self.enemies.iteritems():
            enemy_num+=1
            threat = 5
            frontier_queue = deque([])
            frontier_dict = {}
            frontier_dict[enemy.pos] = (threat, enemy.pos)
            explored = {}
            frontier_queue.append( (threat, enemy.pos ) )
            self.threat_map[enemy.pos[0]][enemy.pos[1]] = threat
            while threat > 1 and frontier_queue:
                node = frontier_queue.popleft()
                threat, loc = node
                threat -= 1
                del frontier_dict[loc]
                explored[loc] = node
                for direction,coords in enumerate(AIM):
                    next_loc = self.board.to(loc, coords)
                    if next_loc:
                        next_node = ( threat, next_loc )
                        if (next_loc not in explored
                                and next_loc not in frontier_dict
                                and self.board.passable(next_loc)):
                            self.threat_map[next_loc[0]][next_loc[1]] += threat
                            frontier_queue.append( next_node )
                            frontier_dict[next_loc] = next_node
        # Debugging print threat map
        #for m in self.threat_map:
            #for token in m:
                #print token,
            #print "\""

    def dijkstra(self):
        """Claculate paths taking tile threat values into account"""
        self.threat_update()
        frontier_queue = []
        frontier_dict = {}
        explored = {}
        heapq.heappush(frontier_queue, (0, self.hero.pos, None) )
        frontier_dict[self.hero.pos] = (0, self.hero.pos, None)

        while ( frontier_queue ):
            node = heapq.heappop(frontier_queue)
            distance, loc, parent = node
            
            del frontier_dict[loc]
            explored[loc] = node

            for direction,coords in enumerate(AIM):
                next_loc = self.board.to(loc, coords)
                if next_loc:
                    next_node = ( distance + 1 + self.threat_map[next_loc[0]][next_loc[1]], next_loc, node )
                    if next_loc in self.board.mines:
                        if not self.board.mines[next_loc].path:
                            self.board.mines[next_loc].path = self.get_path(next_node)
                            #print "Path to Mine = ",
                            #print self.board.mines[next_loc].path,
                            #print "  ",
                            #print next_loc
                    elif next_loc in self.enemies:
                        if not self.enemies[next_loc].path:
                            self.enemies[next_loc].path = self.get_path(next_node)
                            #print "Path to enemy = ",
                            #print self.enemies[next_loc].path,
                            #print "  ",
                    elif next_loc in self.board.taverns:
                        if not self.board.taverns[next_loc].path:
                            self.board.taverns[next_loc].path = self.get_path(next_node)
                            #print "Path to Tavern = ",
                            #print self.board.taverns[next_loc].path,
                            #print "  ",
                    elif (next_loc not in explored
                            and next_loc not in frontier_dict
                            and self.board.passable(next_loc)):
                        heapq.heappush(frontier_queue, next_node )
                        frontier_dict[next_loc] = next_node

        


class Tavern:
    def __init__(self):
        self.path = None
        self.set_value()
    def set_value(self):
        self.value = 999
        if ( None != self.path ):
            self.value = len(self.path)
    def get_value(self):
        return self.value

class Mine:
    def __init__(self, owner_char_index):
        self.path = None
        self.owner = None
        self.me = False
        self._owner_char_index = owner_char_index
        self.set_value()
        self.neighbor_value = 0

    def update_owner(self, tiles, me_ident):
        """Check the current board string to update mine owner"""
        if '-' == tiles[self._owner_char_index]:
            self.owner = None
        else:
            self.owner = int(tiles[self._owner_char_index])
            if (int(self.owner) == me_ident):
                self.me = True
            else:
                self.me = False

    def set_value(self):
        """Value of a mine is the distance from the player minus that mines value, -2 if it is someone else's mine currently"""
        if ( None == self.path ):
            self.value = 999
        elif ( None == self.owner ):
            self.value = len(self.path) - self.neighbor_value
        elif ( not self.me ):
            self.value = len(self.path) - 1 - self.neighbor_value
        else:
            self.value = 999
        if (self.value < 0 ):
            self.value = 0
    def get_value(self):
        return self.value

class Board:
    def _parseTile(self, row, col, token):
        if (token == '  ' or token[0] == '@'):
            return AIR
        if (token == '##'):
            return WALL
        if (token == '[]'):
            self.taverns[(row,col)] = Tavern()
            self.taverns_list.append( self.taverns[(row,col)] )
            return TAVERN
        if (token[0] == '$'):
            self.mines[(row,col)] = Mine( row*self.size*2 + col*2 + 1 )
            self.mines_list.append( self.mines[(row,col)] )
            return MINE

    def _parseTiles(self, tiles):
        vector = [tiles[i:i+2] for i in range(0, len(tiles), 2)]
        matrix = [vector[i:i+self.size] for i in range(0, len(vector), self.size)]
        self.print_board(tiles)

        return [[self._parseTile(row, col, x) for col, x in enumerate(xs)] for row, xs in enumerate(matrix)]

    def __init__(self, board):
        self.size = board['size']
        self.taverns = {}
        self.taverns_list = []
        self.mines = {}
        self.mines_list = []
        self.tiles = self._parseTiles(board['tiles'])
        self.define_mine_neighbor_value()


    def define_mine_neighbor_value(self):
        """Determine the value of a mine by checking neighboring locations to see if other mines are close by"""
        for pos,mine in self.mines.iteritems():
            distance = 4
            frontier_queue = deque([])
            frontier_dict = {}
            frontier_dict[pos] = (distance, pos)
            explored = {}
            frontier_queue.append( (distance, pos ) )
            while distance > 0 and frontier_queue:
                node = frontier_queue.popleft()
                distance, loc = node
                distance -= 1
                del frontier_dict[loc]
                explored[loc] = node
                for direction,coords in enumerate(AIM):
                    next_loc = self.to(loc, coords)
                    if next_loc:
                        next_node = ( distance, next_loc )
                        if (next_loc not in explored
                                and next_loc not in frontier_dict):
                            if ( self.passable(next_loc)):
                                frontier_queue.append( next_node )
                                frontier_dict[next_loc] = next_node
                            elif ( next_loc in self.mines ):
                                mine.neighbor_value += 1
                                explored[next_loc] = next_node

    def passable(self, loc):
        'true if can walk through'
        x, y = loc
        pos = self.tiles[x][y]
        return pos == AIR

    def to(self, loc, direction):
        'calculate a new location given the direction'
        row, col = loc
        d_row, d_col = AIM[direction]
        n_row = row + d_row
        if (n_row < 0): return None
        if (n_row >= self.size): return None
        n_col = col + d_col
        if (n_col < 0): return None
        if (n_col >= self.size): return None
        return (n_row, n_col)
    def print_board(self, tiles):
        """Print an ascii representation of the game board"""
        vector = [tiles[i:i+2] for i in range(0, len(tiles), 2)]
        matrix = [vector[i:i+self.size] for i in range(0, len(vector), self.size)]
        for m in matrix:
            for token in m:
                print token,
            print "\""

class Hero:
    """Contains all the information for a player"""
    def __init__(self, hero, me):
        self.ident = hero['id']
        self.name = hero['name']
        self.pos = (hero['pos']['x'],hero['pos']['y'])
        self.spawn = (hero['spawnPos']['x'],hero['spawnPos']['y'])
        self.life = hero['life']
        self.gold = hero['gold']
        self.mines = hero['mineCount']
        self.path = None
        self.me = me
        self.set_value()
    def set_value(self):
        """value of a hero is the distance from the player to that hero's position"""
        if ( self.me ):
            self.value = 999
        elif ( None == self.path ):
            self.value = 999
        else:
            self.value = len(self.path)
    def get_value(self):
        return self.value

