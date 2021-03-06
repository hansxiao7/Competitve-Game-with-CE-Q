# -*- coding: utf-8 -*-
"""CS7642-P3 Soccer Game.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/19YeE1v-2cN7LLhb6ZiOJPCNf9ji6G27w
"""

import numpy as np
import cvxpy as cp
from tqdm.notebook import tqdm

np.random.seed(1)

# Build the soccer game
class Soccer_game:
  def __init__(self):
    # The states include 5 dimensions
    # X_A, Y_A, X_B, Y_B, ball
    # ball = 0 or 1. 0 is for A holding ball. 1 is for B holding ball. 
    # The action space includes 5 discrete elements. 0-N, 1-S, 2-E, 3-W, 4-Stand. 
    # The action space is the same for both players.
    # self.state =  [0, 2, 0, 1, np.random.randint(2)]
    self.state =  [0, 2, 0, 1, 1]
  def take_actions(self, actions):
    done = False
    reward = [0, 0]

    first_mover = np.random.randint(2)
    second_mover = 1 - first_mover
    action_1 = actions[first_mover]
    action_2 = actions[second_mover]

    curr_pos_2 = [self.state[2*second_mover], self.state[2*second_mover+1]]

    new_pos_1 = self.move(first_mover, action_1)
    if new_pos_1 == curr_pos_2: # the move of the 1st mover stops
      if self.state[4] == first_mover: # if the first mover holds the ball, give it to the 2nd mover
        self.state[4] = second_mover
    else: # no collision, the first player moves
      self.state[2*first_mover] = new_pos_1[0]
      self.state[2*first_mover + 1] = new_pos_1[1]
    
    curr_pos_1 = [self.state[2*first_mover], self.state[2*first_mover+1]]

    # Check whether the game finishes
    new_state, reward, done = self.check_goal(first_mover)
    if done == True:
      return new_state, reward, done
    
    # There is no goal, then continue the second mover
    new_pos_2 = self.move(second_mover, action_2)
    if new_pos_2 == curr_pos_1: # the move of the 2nd mover stops
      if self.state[4] == second_mover: # give it to the 1st mover
        self.state[4] = first_mover
    else: # no collision, the second player moves
      self.state[2*second_mover] = new_pos_2[0]
      self.state[2*second_mover + 1] = new_pos_2[1]
    
    # Check whether the game finishes
    new_state, reward, done = self.check_goal(second_mover)
    if done == True:
      return new_state, reward, done
    
    return self.state.copy(), reward, done

  def check_goal(self, player):
    curr_pos = [self.state[2*player], self.state[2*player+1]]
    # If A gets the goal
    if player == 0 and self.state[4] == 0: 
      if curr_pos[1] == 0: 
        reward = [100, -100]
        done = True
        new_state = self.state.copy()
        self.state = [0, 2, 0, 1, 1]
        return new_state, reward, done
      if curr_pos[1] == 3:
        reward = [-100, 100]
        done = True
        new_state = self.state.copy()
        self.state = [0, 2, 0, 1, 1]
        return new_state, reward, done
    # if B gets the goal
    if player == 1 and self.state[4] == 1:
      if curr_pos[1] == 3:
        reward = [-100, 100]
        done = True
        new_state = self.state.copy()
        self.state = [0, 2, 0, 1, 1]
        return new_state, reward, done
      if curr_pos[1] == 0:
        reward = [100, -100]
        done = True
        new_state = self.state.copy()
        self.state = [0, 2, 0, 1, 1]
        return new_state, reward, done
    return self.state.copy(), [0, 0], False

  def move(self, player, action):
    new_pos = [self.state[2*player], self.state[2*player+1]]
    if action == 0: #N
      if new_pos[0] - 1 >= 0:
        new_pos[0] -= 1
    elif action == 1: #S
      if new_pos[0] + 1 <= 1:
        new_pos[0] += 1
    elif action == 2: # E
      if new_pos[1] + 1 <= 3:
        new_pos[1] += 1
    elif action == 3: #W
      if new_pos[1] - 1 >= 0:
        new_pos[1] -= 1

    return new_pos

def ce_solver(new_Q_A, new_Q_B):
  x = cp.Variable(shape=(25, 1), name='x')
  total_reward = cp.sum(cp.multiply(np.reshape(new_Q_A + new_Q_B, newshape=(25, 1)), x))

  # set parameters for contraints
  p_A = []
  for m in range(5):
    for n in range(5):
      if m != n:
        temp = np.zeros(shape=(25))
        for k in range(5):
          temp[m*5 + k] = new_Q_A[m, k] - new_Q_A[n, k]
        p_A.append(temp)

  p_B = []
  for m in range(5):
    for n in range(5):
      if m != n:
        temp = np.zeros(shape=(25))
        for k in range(5):
          temp[m + k *5] = new_Q_B[k, m] - new_Q_B[k, n]
        p_B.append(temp)

  p = np.concatenate([p_A, p_B], axis=0)
  constraints = [cp.matmul(p, x)>=0, x>=0, cp.sum(x) == 1]
  # solve the linear programming problem
  objective = cp.Maximize(total_reward)

  problem = cp.Problem(objective, constraints)
  try:
    solution = problem.solve()
  except:
    return None
  
  if x.value is None:
    return None
    
  x.value = np.abs(x.value)
  x.value = x.value / np.sum(x.value)

  return x.value

def foe_solver(Q_A, Q_B):
  # Set the minimax solver for foe-Q learning
  V_A = 0
  V_B = 0
  # For player A; the first element is the expected reward, the remaining 5 elements are the policy
  x1 = cp.Variable(shape=(6,1), name='x1')
  A1 = np.array([0, 1, 1, 1, 1, 1])
  constraints_1 = [cp.matmul(Q_A.T, x1[1:, 0])>=x1[0], cp.matmul(A1, x1)==1, x1[1:]>=0]

  objective_1 = cp.Maximize(x1[0])
  problem_1 = cp.Problem(objective_1, constraints_1)
  
  # For player B
  x2 = cp.Variable(shape=(6,1), name='x2')
  A2 = np.array([0, 1, 1, 1, 1, 1])
  constraints_2 = [cp.matmul(Q_B, x2[1:, 0])>=x2[0], cp.matmul(A2, x2)==1, x2[1:]>=0]

  objective_2 = cp.Maximize(x2[0])
  problem_2 = cp.Problem(objective_2, constraints_2)

  try:
    solution_1 = problem_1.solve()
  except:
    pi_A = None
  try:
    solution_2 = problem_2.solve()
  except:
    pi_B = None

  if x1.value is None:
    pi_A = None
  else:
    pi_A = list(np.reshape(x1.value[1:], (5,)))
    pi_A = np.absolute(pi_A) / np.sum(np.absolute(pi_A))
    V_A = x1.value[0]
  
  if x2.value is None:
    pi_B = None
  else:
    pi_B = list(np.reshape(x2.value[1:], (5,)))  
    pi_B = np.absolute(pi_B) / np.sum(np.absolute(pi_B))
    V_B = x2.value[0]

  return pi_A, V_A, pi_B, V_B

# Define Q learning model
class Multi_Q:
  def __init__(self, method):
    self.method = method
    if self.method == 'Q-learning':
      self.Q_A = np.zeros(shape=(2, 4, 2, 4, 2, 5))
      self.Q_B = np.zeros(shape=(2, 4, 2, 4, 2, 5))
    else:
      # for Q matrix, the 0th dimension is for different players, 0 for player A and 1 for player B
      self.Q_A = np.zeros(shape=(2, 4, 2, 4, 2, 5, 5))
      self.Q_B = np.zeros(shape=(2, 4, 2, 4, 2, 5, 5))
    self.gamma = 0.9
    self.env = Soccer_game()

    # value for alpha decay
    self.alpha = 0.5
    self.alpha_decay = 0.999994
    self.alpha_min = 0.001

    # value for exploration: epsilon decay
    self.epsilon = 1
    self.epsilon_decay = 0.999995
    self.epsilon_min = 0.001

    # set the initial values for pi
    if self.method == 'foe-Q':
      # this is for foe-Q, friend-Q
      # The first 5 dimensions are states, the last dimension is action space
      self.pi_A = np.ones(shape=(2, 4, 2, 4, 2, 5)) * 1. / 5
      self.pi_B = np.ones(shape=(2, 4, 2, 4, 2, 5)) * 1. / 5

    # set the initial values for pi of ce-Q
    if self.method == 'ce-Q':
      self.pi_AB = np.ones(shape=(2, 4, 2, 4, 2, 25)) * 1. / 25

  def choose_action(self, curr_state):
    if self.method == 'ce-Q': # for ce-Q
      if np.random.random() <= self.epsilon:
        action_A = np.random.randint(5)
        action_B = np.random.randint(5)
      else:
        action_AB = np.random.choice(25, p=self.pi_AB[curr_state[0], curr_state[1], curr_state[2], curr_state[3], curr_state[4], :])
        action_A = int(np.floor(action_AB / 5))
        action_B = int(action_AB % 5)
      return [action_A, action_B]
    elif self.method == 'Q-learning':
      if np.random.random() <= self.epsilon: # exploration
        action_A = np.random.randint(5)
      else:
        action_A = np.argmax(self.Q_A[curr_state[0], curr_state[1], curr_state[2], curr_state[3], curr_state[4], :])
      
      if np.random.random() <= self.epsilon: # exploration
        action_B = np.random.randint(5)
      else:
        action_B = np.argmax(self.Q_B[curr_state[0], curr_state[1], curr_state[2], curr_state[3], curr_state[4], :])
      return [action_A, action_B]

    elif self.method == 'foe-Q': # for foe-Q
      # choose by epsilon-decay scheme
      # for Player_A
      if np.random.random() <= self.epsilon: # exploration
        action_A = np.random.randint(5)
      else:
        action_A = np.random.choice(5, p=self.pi_A[curr_state[0], curr_state[1], curr_state[2], curr_state[3], curr_state[4], :])

      # for Player_B
      if np.random.random() <= self.epsilon: # exploration
        action_B = np.random.randint(5)
      else:
        action_B = np.random.choice(5, p=self.pi_B[curr_state[0], curr_state[1], curr_state[2], curr_state[3], curr_state[4], :])
      return [action_A, action_B]
    
    elif self.method == 'friend-Q':
      # for player A
      if np.random.random() <= self.epsilon: # exploration
        action_A = np.random.randint(5)
      else:
        action_A = np.argmax(self.Q_A[curr_state[0], curr_state[1], curr_state[2], curr_state[3], curr_state[4], :, :])
        action_A = int(np.floor(action_A / 5))
      
      # for player B
      if np.random.random() <= self.epsilon: # exploration
        action_B = np.random.randint(5)
      else:
        action_B = np.argmax(self.Q_B[curr_state[0], curr_state[1], curr_state[2], curr_state[3], curr_state[4], :, :])
        action_B = int(action_B % 5)

      return [action_A, action_B]

  def update_Q(self):
    max_iter = int(1e6)
    V_A = np.zeros(shape=(2, 4, 2, 4, 2))
    V_B = np.zeros(shape=(2, 4, 2, 4, 2))
    prg_bar = tqdm(range(max_iter))
    self.error_A_list = []
    # intialiate the state
    curr_state = self.env.state.copy()
    done = False

    for i in prg_bar:  
      # Correltated-Q
      if self.method == 'ce-Q':
        curr_Q_A = self.Q_A[curr_state[0], curr_state[1], curr_state[2], curr_state[3], curr_state[4], :, :].copy()
        curr_Q_B = self.Q_B[curr_state[0], curr_state[1], curr_state[2], curr_state[3], curr_state[4], :, :].copy()
        curr_pi = ce_solver(curr_Q_A, curr_Q_B)
        
        if curr_pi is not None:
          self.pi_AB[curr_state[0], curr_state[1], curr_state[2], curr_state[3], curr_state[4], :] = np.reshape(curr_pi, (25))
          V_A[curr_state[0], curr_state[1], curr_state[2], curr_state[3], curr_state[4]] = np.sum(np.reshape(curr_Q_A, newshape=(25, 1)) * curr_pi)
          V_B[curr_state[0], curr_state[1], curr_state[2], curr_state[3], curr_state[4]] = np.sum(np.reshape(curr_Q_B, newshape=(25, 1)) * curr_pi)
        
        # record player A at state S take action South before update
        before = self.Q_A[0, 2, 0, 1, 1, 1, 4].copy()

        actions = self.choose_action(curr_state)
        new_state, reward, done = self.env.take_actions(actions)

        # update the Q_table
        ce_Q_A = V_A[new_state[0], new_state[1], new_state[2], new_state[3], new_state[4]]
        ce_Q_B = V_B[new_state[0], new_state[1], new_state[2], new_state[3], new_state[4]]

        error_A = self.alpha * ((1-self.gamma)*reward[0] + self.gamma * ce_Q_A * (1-done) - curr_Q_A[actions[0], actions[1]])
        error_B = self.alpha * ((1-self.gamma)*reward[1] + self.gamma * ce_Q_B * (1-done) - curr_Q_B[actions[0], actions[1]])

        self.Q_A[curr_state[0], curr_state[1], curr_state[2], curr_state[3], curr_state[4], actions[0], actions[1]] += error_A
        self.Q_B[curr_state[0], curr_state[1], curr_state[2], curr_state[3], curr_state[4], actions[0], actions[1]] += error_B

        # Get the error value for figures
        diff = abs(self.Q_A[0, 2, 0, 1, 1, 1, 4] - before)

      if self.method == 'foe-Q':
        if i % 10000 == 0:
          print(i)
        curr_Q_A = self.Q_A[curr_state[0], curr_state[1], curr_state[2], curr_state[3], curr_state[4], :, :].copy()
        curr_Q_B = self.Q_B[curr_state[0], curr_state[1], curr_state[2], curr_state[3], curr_state[4], :, :].copy()
        curr_pi_A, curr_V_A, curr_pi_B, curr_V_B = foe_solver(curr_Q_A, curr_Q_B)

        if curr_pi_A is not None:
          self.pi_A[curr_state[0], curr_state[1], curr_state[2], curr_state[3], curr_state[4], :] = curr_pi_A
          V_A[curr_state[0], curr_state[1], curr_state[2], curr_state[3], curr_state[4]] = curr_V_A
        
        if curr_pi_B is not None:
          self.pi_B[curr_state[0], curr_state[1], curr_state[2], curr_state[3], curr_state[4], :] = curr_pi_B
          V_B[curr_state[0], curr_state[1], curr_state[2], curr_state[3], curr_state[4]] = curr_V_B
        
        # record player A at state S take action South before update
        before = self.Q_A[0, 2, 0, 1, 1, 1, 4].copy()

        actions = self.choose_action(curr_state)
        new_state, reward, done = self.env.take_actions(actions) 

        # update the Q_table
        nash_A = V_A[new_state[0], new_state[1], new_state[2], new_state[3], new_state[4]]
        nash_B = V_B[new_state[0], new_state[1], new_state[2], new_state[3], new_state[4]]

        self.Q_A[curr_state[0], curr_state[1], curr_state[2], curr_state[3], curr_state[4], actions[0], actions[1]] += \
                      self.alpha * ((1-self.gamma)*reward[0] + self.gamma * nash_A * (1-done) - curr_Q_A[actions[0], actions[1]])

        self.Q_B[curr_state[0], curr_state[1], curr_state[2], curr_state[3], curr_state[4], actions[0], actions[1]] += \
                      self.alpha * ((1-self.gamma)*reward[1] + self.gamma * nash_B * (1-done) - curr_Q_B[actions[0], actions[1]])

        # Get the error value for figures
        diff = abs(self.Q_A[0, 2, 0, 1, 1, 1, 4] - before)

      if self.method == 'friend-Q':
        curr_Q_A = self.Q_A[curr_state[0], curr_state[1], curr_state[2], curr_state[3], curr_state[4], :, :].copy()
        curr_Q_B = self.Q_B[curr_state[0], curr_state[1], curr_state[2], curr_state[3], curr_state[4], :, :].copy()

        # record player A at state S take action South before update
        before = self.Q_A[0, 2, 0, 1, 1, 1, 4].copy()

        actions = self.choose_action(curr_state)
        new_state, reward, done = self.env.take_actions(actions) 

        new_Q_A = self.Q_A[new_state[0], new_state[1], new_state[2], new_state[3], new_state[4], :, :].copy()
        new_Q_B = self.Q_B[new_state[0], new_state[1], new_state[2], new_state[3], new_state[4], :, :].copy()

        # update the Q_table
        self.Q_A[curr_state[0], curr_state[1], curr_state[2], curr_state[3], curr_state[4], actions[0], actions[1]] += self.alpha * ((1-self.gamma)*reward[0] + \
                        self.gamma * (1 - done) * np.amax(new_Q_A) - curr_Q_A[actions[0], actions[1]])
        self.Q_B[curr_state[0], curr_state[1], curr_state[2], curr_state[3], curr_state[4], actions[0], actions[1]] += self.alpha * ((1-self.gamma)*reward[1] + \
                        self.gamma * (1 - done) * np.amax(new_Q_B) - curr_Q_B[actions[0], actions[1]])
        
        # Get the error value for figures
        diff = abs(self.Q_A[0, 2, 0, 1, 1, 1, 4] - before)

        

      if self.method == 'Q-learning':
        curr_Q_A = self.Q_A[curr_state[0], curr_state[1], curr_state[2], curr_state[3], curr_state[4], :].copy()
        curr_Q_B = self.Q_B[curr_state[0], curr_state[1], curr_state[2], curr_state[3], curr_state[4], :].copy()

        # record player A at state S take action South before update
        before = self.Q_A[0, 2, 0, 1, 1, 1].copy()

        actions = self.choose_action(curr_state)
        new_state, reward, done = self.env.take_actions(actions)

        new_Q_A = self.Q_A[new_state[0], new_state[1], new_state[2], new_state[3], new_state[4], :].copy()
        new_Q_B = self.Q_B[new_state[0], new_state[1], new_state[2], new_state[3], new_state[4], :].copy()
        
        self.Q_A[curr_state[0], curr_state[1], curr_state[2], curr_state[3], curr_state[4], actions[0]] += self.alpha * ((1-self.gamma)*reward[0] + \
                      self.gamma * (1 - done) * np.amax(new_Q_A) - curr_Q_A[actions[0]])
        self.Q_B[curr_state[0], curr_state[1], curr_state[2], curr_state[3], curr_state[4], actions[1]] += self.alpha * ((1-self.gamma)*reward[1] + \
                      self.gamma * (1 - done) * np.amax(new_Q_B) - curr_Q_B[actions[1]])                                                                                                  

        diff = abs(self.Q_A[0, 2, 0, 1, 1, 1] - before)


      # The same for all methods
      self.error_A_list.append(diff)
      # Update the parameters at each step
      self.alpha = max(self.alpha_min, self.alpha * self.alpha_decay)
      self.epsilon = max(self.epsilon_min, self.epsilon * self.epsilon_decay)

      if done:
        done = False
        curr_state = self.env.state.copy()
      else:
        curr_state = new_state

q = Multi_Q('Q-learning')
q.update_Q()

np.savetxt('Q_learning_Errors.txt', q.error_A_list)

q2 = Multi_Q('friend-Q')
q2.update_Q()

np.savetxt('friend_Q_Q_A.txt', q2.Q_A[0, 2, 0, 1, 1, :, :])
np.savetxt('friend_Q_Q_B.txt', q2.Q_B[0, 2, 0, 1, 1, :, :])
np.savetxt('friend_Q_Errors.txt', q2.error_A_list)

q3 = Multi_Q('ce-Q')
q3.update_Q()

np.savetxt('ce_Q_Q_A.txt', q3.Q_A[0, 2, 0, 1, 1, :, :])
np.savetxt('ce_Q_Q_B.txt', q3.Q_B[0, 2, 0, 1, 1, :, :])
np.savetxt('ce_Q_pi_AB.txt', q3.pi_AB[0, 2, 0, 1, 1, :])
np.savetxt('ce_Q_Errors.txt', q3.error_A_list)

q4 = Multi_Q('foe-Q')
q4.update_Q()

np.savetxt('foe_Q_Q_A.txt', q4.Q_A[0, 2, 0, 1, 1, :, :])
np.savetxt('foe_Q_Q_B.txt', q4.Q_B[0, 2, 0, 1, 1, :, :])
np.savetxt('foe_Q_pi_A.txt', q4.pi_A[0, 2, 0, 1, 1, :])
np.savetxt('foe_Q_pi_B.txt', q4.pi_B[0, 2, 0, 1, 1, :])
np.savetxt('foe_Q_Errors.txt', q4.error_A_list)