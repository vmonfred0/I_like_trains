import random
from common.base_agent import BaseAgent
from common.move import Move
import heapq
#127.0.0.1
#128.179.154.221
# Student scipers, will be automatically used to evaluate your code
#Repo : 1 étage plus haut; 
#Repo: faire un fork, up_stream, sink forkl
SCIPERS = ["112233", "445566"]

#Refaire des fonctions pour le train ? 
class Agent(BaseAgent):
    def my_train(self):
        #print ( self.all_trains )
        return self.all_trains[self.nickname]     
    def my_direction(self):
        return  Move(tuple(self.my_train()["direction"]))
    def my_wagons(self):
        return self.my_train()["wagons"]
    def my_speed(self,wagon):
        return 0.95**wagon
    def my_possibile_moves(self):
        return [self.my_direction(), self.my_direction().turn_left, self.my_direction().turn_right]
    def my_train_coordinates(self,name):
        return tuple(name["position"])
    def safe_coordinates(self, width,height, cell_size):
        #retourne les coordonnées valables pour demeurer sur la grille du jeu
        return width-cell_size, height-cell_size
    def get_occupied_cases(self):
        #A LA ZOB, RETRAVAILLER
        occupied=[]
        for i,v in self.all_trains.items():
             x,y=self.my_train_coordinates(self.all_trains[i])
             occupied.append((x//self.cell_size,y//self.cell_size))
             wagons= self.all_trains[i]["wagons"]
             for j in wagons:
                x,y=tuple(j)
                occupied.append((x//self.cell_size,y//self.cell_size))
        return occupied
    def get_coordinates_around_players(self, occupied):
        moves=[(0,1),(0,-1),(1,0),(-1,0),(1,1),(-1,1),(1,-1),(-1,-1)]
        zone_around_players=set()
        for i in occupied:
            x_i,y_i = i
            for j in moves:
                x,y =j
                potential_coordinates=x_i+x,y_i+y
                if potential_coordinates not in occupied:
                    zone_around_players.add(potential_coordinates)
        zone_around_players=list(zone_around_players)
        return zone_around_players
    def grid(self):
        #donne une grille pratique à manipuler pour les opérations
        discrete_grid=[[0 for j in range (self.game_width//self.cell_size)]for i in range(self.game_height//self.cell_size)]
        b= self.get_occupied_cases()
        #a=self.get_coordinates_around_players(self.get_occupied_cases())
        occupied=b
        for i in occupied:
            a,b=i
            discrete_grid[a][b]=1
        return discrete_grid
    def get_coordinates_delivery_zone(self):
        #rend les coordonnées de chacun des points de la zone de livraison des passagers 
        all_points=[]
        height=self.delivery_zone['height']
        width=self.delivery_zone['width']
        x_position,y_position=tuple(self.delivery_zone['position'])
        for i in range(0,height,self.cell_size):
            for j in range(0,width,self.cell_size):
                all_points.append((x_position+j,y_position+i))
        return all_points
    def get_coordinates_around_delivery_zone(self, delivery_zone):
        a=self.cell_size
        moves=[(0,a),(0,-a),(a,0),(-a,0),(a,a),(-a,a),(a,-a),(-a,-a)]
        zone_around_delivery=set()
        for i in delivery_zone:
            x_i,y_i = i
            for j in moves:
                x,y =j
                potential_coordinates=x_i+x,y_i+y
                if potential_coordinates not in delivery_zone:
                    zone_around_delivery.add(potential_coordinates)
        zone_around_delivery=list(zone_around_delivery)
        return zone_around_delivery
            

    def dijkstra(self, grid, start, goal, cell,speed):
        #algorithme de Dijkstra, donnant le plus court chemin pour atteindre une case visée (goal)
        #prend en entrée la grille (grid), la case de départ (start), la case visée (goal),
        #  la taille d'une cellule (cell)
        #rend la distance la plus courte, ainsi que le premier déplacement à effectuer
        rows, cols = len(grid), len(grid[0])
        distances = [[float('inf')] * cols for _ in range(rows)] #on initialise la pondération avec infini pour chaque case
        prev = [[None] * cols for _ in range(rows)]

        sx0,sy0=start #coordonnées 'brutes'
        gx0,gy0=goal
        sx, sy = sx0//cell,sy0//cell #coordonnées adaptées à la taille des cellules
        gx, gy = gx0//cell,gy0//cell
        distances[sx][sy] = 0 #initialisation distance
        queue = [(0, (sx, sy))]
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)] #à différencier des directions usuelles
        while queue:
            dist, (x, y) = heapq.heappop(queue) #voir méthode globale heapq

            if (x, y) == (gx, gy):
                break
            for dx, dy in directions:
                nx, ny = x + dx, y + dy
                if 0 <= nx < rows and 0 <= ny < cols and grid[nx][ny] == 0: #condition 0 signifie que la case est libre, pas d'obstacles
                    new_dist = dist + 1
                    if new_dist < distances[nx][ny]:
                        distances[nx][ny] = new_dist
                        prev[nx][ny] = (x, y)
                        heapq.heappush(queue, (new_dist, (nx, ny)))

        # Reconstruction du chemin
        path = []
        x, y = gx, gy
        if distances[x][y] == float('inf'):
            return None, None, None  # Aucun chemin trouvé
        while (x, y) != (sx, sy):
            path.append((x, y))
            x, y = prev[x][y]
        path.append((sx, sy))
        path.reverse()

        # Calcul de la longueur et du premier mouvement
        path_length = len(path)
        if path_length >= 2:
            dx = path[1][0] - path[0][0]
            dy = path[1][1] - path[0][1]
            first_move = dx,dy
        else:
            first_move = None
        time= path_length/speed

        return path_length, first_move, time
    def calculate_best_move_for(self,kind_of_move):
        #pour un type d'opération à effectuer (récolter/déposer des passagers) 
        #trouve le meilleur trajet à prendre 
        #prend en entrée le type d'opération
        #rend le meilleur trajet (distance, premier mouvement)
        optimum=0
        best_move = random.choice(self.my_possibile_moves())
        for i in range (len(kind_of_move)):
            if kind_of_move == self.passengers:
               #si le type d'opération est aller chercher des passagers, on utilise la formule suivante:
               #nombre de passagers sur la case/distance minimale
               #on trouve la case pour laquelle ce rapport est maximal
               x,y=tuple(self.passengers[i]["position"])
               a=self.passengers[i]['value']
            if kind_of_move==self.get_coordinates_delivery_zone():
                #si le type d'opération est aller dépoer des passagers, on utilise la formule suivante:
                #nombre de passagers pris en charge/distance minimale
                #on vérifie s'il est possible et intéressant de déposer des passagers; si oui on trouve
                #la case la plus proche
                x,y= self.get_coordinates_delivery_zone()[i]
                a=len(self.my_wagons())
            speed=self.my_speed(len(self.my_wagons()))
            path_length,first_move, time_spent =self.dijkstra(self.grid(),(self.my_train_coordinates(self.my_train())),(x,y), self.cell_size, speed) 
            if time_spent is None:
                print('x')
                value=0
            else:
                value=a/time_spent
            if optimum < value:
                optimum=value
                best_move=first_move
        return optimum, best_move
    def calculate_absolute_best_move(self):
        #on regarde pour notre situation, la meilleure opération à faire
        #rend le meilleur chemin à effectuer, et le premier déplacement à faire
        kind_of_moves=[self.passengers,self.get_coordinates_delivery_zone()]
        optimum=0
        best_move= random.choice(self.my_possibile_moves())

        for i in kind_of_moves:
            value, move = self.calculate_best_move_for(i)
            if value > optimum:
                optimum, best_move= value, move
        return optimum, best_move
    def bastard_move(self):
        a=self.get_coordinates_around_delivery_zone(self.get_coordinates_delivery_zone())
        while self.my_wagons == len(a)-1:
            if self.my_train_coordinates not in a:
                path_length, first_move= self.dijkstra(self.grid, self.my_train_coordinates, a[0], self.cell_size)
                return first_move
    #fonctions à implémenter ?  
    # -déterminer mouvement du joueur, s'il va sur des passagers, qu'il y sera avant moi, -> abandonner cette option
    # FAIT -trouver la vitesse du machin, essayer de faire un algo prenant en compte le temps à mettre. 
    # -Voir quelle combinaison mettra le moins de temps à être effectuée: 
    # exemple: best_move = déposer passager, problème passagers pas loin, qu'y a t'il de mieux à faire
    #si l'adversaire effectue un mouvement périodique (période max), déterminer ensuite ses prochains mouvements
    def get_authorized_moves(self,position,safe,direction,a):
        x_train,y_train=position
        x_safe,y_safe=safe
        possible_moves=[direction, direction.turn_left(), direction.turn_right()]
        authorized_moves=[]
        for i in (possible_moves):
            x0, y0=i.value
            x_move,y_move=x0*self.cell_size, y0*self.cell_size
            sum_x= x_move +x_train
            sum_y=y_move +y_train
            if 0 <=sum_x <=x_safe and 0<=sum_y <=y_safe and  ([sum_x, sum_y] not in self.get_occupied_cases()):
                authorized_moves.append(i)
                #améliorer effectuer une itération !
            
        return authorized_moves

    def get_move(self):
        """
        Called regularly called to get the next move for your train. Implement
        an algorithm to control your train here. You will be handing in this file.
        This method must return one of moves.MOVE
        """

        coordinates= self.my_train_coordinates(self.my_train())
        s_coordinates= self.safe_coordinates(self.game_width, self.game_height, self.cell_size )
        direction= Move(tuple(self.my_train()["direction"]))
        opt, best= self.calculate_absolute_best_move()
        authorized_moves=self.get_authorized_moves(coordinates,s_coordinates,direction, 0)

        for i in authorized_moves:
            if i.value == best:
                return i
        return random.choice(authorized_moves) 

   