import numpy as np

A = np.loadtxt('Results/ce_Q_Q_A.txt')
B = np.loadtxt('Results/foe_Q_Q_A.txt')

x = np.sum((A - np.mean(A)) * (B - np.mean(B))) / np.sqrt(np.sum((A - np.mean(A)) ** 2) * np.sum((B - np.mean(B)) ** 2))
print(x)
# np.savetxt('Results/ce_foe_correlation.txt', np.corrcoef(A, B))