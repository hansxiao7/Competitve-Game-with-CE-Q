# Project readme
The objective of this project to repeat the soccer game experiments by Greenwald et al. (2003). The soccer game is a multi-agent, 2-player, zero-sum game. Correlated-Q, foe-Q, friend-Q and Q-learning are the method used.
# Instructions
The codes are included in the **cs7642_p3_soccer_game.py** file. The code has 2 main classes:

- Soccer_game: this class defines the game;
- Multi_Q: this class includes the implementation of all 4 Q-learning methods.

To run the analysis, the instruction is as follows:

1. q = Multi_Q(method): method is a string parameter. Depends on the method used, it can be defined as 'Q-learning', 'ce-Q', 'friend-Q' or 'foe-Q'.
2. q.update_Q(): this step will run 1,000,000 iterations to update Q tables for Player A and Player B.
3. After running, the Q values and policies are stored in the pre-defined q class.

Have fun!
