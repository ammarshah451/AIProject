import random
import math
import copy
import time

row, col = 4, 4
dice = 8

class gamestate:
    def __init__(self, grid=None):
        if grid:
            self.grid = grid
        else:
            self.grid = [[[random.choice(["H","A"]), random.randint(1,dice)] for _ in range(col)] for _ in range(row)]

    def clone(self):
        return gamestate(copy.deepcopy(self.grid))

    def get_valid_moves(self, player):
        moves = []
        directions = [(0,1), (1,0), (-1,0), (0,-1)]

        for i in range(row):
            for j in range(col):
                owner, dice = self.grid[i][j]
                if owner != player or dice < 2:
                    continue
                for dr, dc in directions:
                    nr, nc = i + dr, j + dc
                    if 0 <= nr < row and 0 <= nc < col:
                        realme, _ = self.grid[nr][nc]
                        if realme != player:
                            moves.append(((i,j), (nr,nc)))
                            
        return moves

    def make_move(self, from1, to1):
        i, j = from1
        r, c = to1

        attacker = self.grid[i][j][1]
        defender = self.grid[r][c][1]

        a_sum = sum([random.randint(1,6) for _ in range(attacker)])
        d_sum = sum([random.randint(1,6) for _ in range(defender)])

        if a_sum > d_sum:
            self.grid[i][j][1] = 1
            self.grid[r][c] = [self.grid[i][j][0], attacker-1]
        else:
            self.grid[i][j][1] = 1

    def is_end(self):
        # Check if any player has conquered the entire board
        owners = [self.grid[i][j][0] for i in range(row) for j in range(col)]
        if all(owner == 'H' for owner in owners):
            return 'H'
        elif all(owner == 'A' for owner in owners):
            return 'A'
            
        # Also check if game is actually playable
        h_has_moves = any(len(self.get_valid_moves('H')) > 0 for _ in range(1))
        a_has_moves = any(len(self.get_valid_moves('A')) > 0 for _ in range(1))
        
        if not h_has_moves and not a_has_moves:
            # Return winner based on who controls more cells
            h_count = sum(1 for i in range(row) for j in range(col) if self.grid[i][j][0] == 'H')
            a_count = sum(1 for i in range(row) for j in range(col) if self.grid[i][j][0] == 'A')
            
            if h_count > a_count:
                return 'H'
            elif a_count > h_count:
                return 'A'
            else:
                # In case of tie, randomly choose a winner to avoid stalemate
                return random.choice(['H', 'A'])
                
        return 'None'
            
    def print(self):
        print("\nBoard State:")
        for i in range(row):
            line = ""
            for j in range(col):
                owner, dice = self.grid[i][j]
                line += f"({owner},{dice})  "
            print(line)
        print()


class MCTSNode:
    def __init__(self, state, parent=None, move=None):
        self.state = state
        self.parent = parent
        self.move = move
        self.children = []
        self.visits = 0
        self.wins = 0

    def ucb1(self, total_simulations):
        if self.visits == 0:
            return float('inf')
        return self.wins / self.visits + math.sqrt(2 * math.log(total_simulations) / self.visits)

def mcts(root_state, player, simulations, max_time):
    """
    Monte Carlo Tree Search algorithm with time limit and simulation count limit
    to prevent hanging on larger boards
    """
    start_time = time.time()
    root = MCTSNode(root_state)
    total_simulations = 0
    
    # run simulations until we hit the count or time limit
    while total_simulations < simulations and (time.time() - start_time) < max_time:
        total_simulations += 1
        node = root
        state = root_state.clone()

        # SELECTION
        # choose child with highest UCB score until we reach a leaf node
        while node.children and not state.is_end() != 'None':
            node = max(node.children, key=lambda n: n.ucb1(root.visits + 1))
            if node.move:  # Make sure move exists before applying it
                state.make_move(*node.move)

        # EXPANSION
        # add child nodes if we're not at a terminal state
        if state.is_end() == 'None':
            moves = state.get_valid_moves(player)
            if moves:  
                move = random.choice(moves)
                n_state = state.clone()
                n_state.make_move(*move)
                child = MCTSNode(n_state, node, move)
                node.children.append(child)
                node = child

        # SIMULATION
        simulation = state.clone()
        current_player = player
        
        # limit simulation steps to prevent infinite loops on larger boards
        max_steps = row * col * 4  
        steps = 0
        
        while simulation.is_end() == 'None' and steps < max_steps:
            steps += 1
            moves = simulation.get_valid_moves(current_player)
            if not moves:
                # Switch player if no moves available
                current_player = "H" if current_player == "A" else "A"
                continue
            move = random.choice(moves)
            simulation.make_move(*move)
            current_player = "H" if current_player == "A" else "A"

        # BACKPROPAGATION
        
        w_player = simulation.is_end()
        cur = node
        while cur:
            cur.visits += 1
            if w_player == player:
                cur.wins += 1
            cur = cur.parent

    # Safety check if we have no children 
    if not root.children:
        # Try to get any valid move if MCTS failed
        moves = root_state.get_valid_moves(player)
        if moves:
            return random.choice(moves)
        return None
        
    # Choose the move with the most visits (most reliable)
    best_child = max(root.children, key=lambda c: c.visits)
    
    
    elapsed = time.time() - start_time
    print(f"AI evaluated {total_simulations} simulations in {elapsed:.2f} seconds")
    
    return best_child.move

def get_input(state):
    valid = state.get_valid_moves("H")
    if not valid:
        print("No valid moves for Human!")
        return None
        
    print("Valid moves: [(from_row, from_col) -> (to_row, to_col)]")
    for move in valid:
        print(f"{move[0]} -> {move[1]}")
        
    while True:
        try:
            move_str = input("Enter move as: from_row from_col to_row to_col: ").strip()
            fr, fc, tr, tc = map(int, move_str.split())
            if ((fr, fc), (tr, tc)) in valid:
                return ((fr, fc), (tr, tc))
        except:
            pass
        print("Invalid move. Try again.")

def main():
    # Option to set custom board size
    global row, col
    try:
        custom_size = input("Enter board size (e.g., '4 4' for 4x4) or press Enter for default: ").strip()
        if custom_size:
            r, c = map(int, custom_size.split())
            if r > 0 and c > 0:
                row, col = r, c
    except:
        pass
    print(f"Using board size: {row}x{col}")
    
    game = gamestate()  
    player = 'H'
    turn_count = 0

    # main game loop
    no_moves_count = 0  # Track consecutive no-move turns
    
    while True:
        game.print()
        turn_count += 1
        print(f"Turn {turn_count} - Current player: {'Human' if player == 'H' else 'AI'}")

        # check for game end
        result = game.is_end()
        if result != 'None':
            print(f"\n\nGame Over! Winner: {'Human' if result == 'H' else 'AI'}")
            break

        # check for stalemate 
        if no_moves_count >= 2:
            print("\n\nGame Over! Stalemate - neither player has valid moves.")
            # determine winner based on territory control
            h_count = sum(1 for i in range(row) for j in range(col) if game.grid[i][j][0] == 'H')
            a_count = sum(1 for i in range(row) for j in range(col) if game.grid[i][j][0] == 'A')
            
            if h_count > a_count:
                print(f"Human wins by territory control! (Human: {h_count}, AI: {a_count})")
            elif a_count > h_count:
                print(f"AI wins by territory control! (AI: {a_count}, Human: {h_count})")
            else:
                print(f"The game ends in a draw! (Human: {h_count}, AI: {a_count})")
            break

        if player == 'H':
            print("Human's turn")
            move = get_input(game)
            if move is None:
                print("Human has no valid moves. Switching to AI.")
                player = 'A'
                no_moves_count += 1
                continue
            else:
                no_moves_count = 0  # Reset counter if a move is made
                print(f"Human moves: {move[0]} -> {move[1]}")
        
        else:
            print("AI's turn... thinking")
            
            # Set AI difficulty based on board size
            if row * col <= 9:  # 3x3 or smaller
                simulations = 100
                max_time = 5.0
            elif row * col <= 16:  # 4x4
                simulations = 75
                max_time = 4.0
            else:  # Larger boards
                simulations = 50
                max_time = 3.0
                
            move = mcts(game, player, simulations, max_time)
            
            if move is None:
                print("AI has no valid moves. Switching to Human.")
                player = 'H'
                no_moves_count += 1
                
                continue
            else:
                no_moves_count = 0  # Reset counter if a move is made
                print(f"AI moves: {move[0]} -> {move[1]}")
        
        if move:
            game.make_move(*move)
            player = 'A' if player == 'H' else 'H'

if __name__ == "__main__":
    main()