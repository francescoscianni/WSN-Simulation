import matplotlib.pyplot as plt
import numpy as np
from wsn_simulation.core import main
from wsn_simulation.results import *

def run_monte_carlo():
    
    loss = [0.5,0.6,0.7]
    max_retransmissions = [1,2,4]
    sim_num = 500
    colors = ['#1f77b4', '#d6612d', '#e7ba52', '#7b3294', '#78ab46']
    
    for i,m in enumerate(max_retransmissions):
        prob = []
        for l in loss:
            cnt = 0
            for j in range(sim_num):
                res = main(max_transmissions=m,
                           loss_rate=l,
                           rng_seed=j,
                           debug_mode=False)
                if res[6]:
                    cnt+=1
            prob.append(cnt/sim_num)
        plt.plot(loss, prob, 
             label=f'tx = {m}', 
             color=colors[i], 
             linewidth=3, 
             marker='o', 
             markersize=10, 
             markerfacecolor='white', 
             markeredgewidth=3,
             zorder=5,          # Higher number = closer to viewer
             clip_on=False)
    
    plt.title("Monte Carlo simulation (500 simulations)")
    plt.xlabel('Single Transmission Loss Rate')
    plt.ylabel('Probability of Successful Flood')
    plt.grid(True, linestyle='-', alpha=0.7)
    plt.ylim([0,1])
    plt.yticks(np.arange(0, 1.05, 0.1))
    plt.xticks(np.arange(0.5, 0.75, 0.05))
    plt.xlim([0.5,0.7])
    plt.legend()
    plt.savefig('Task_2a.png', dpi=300, bbox_inches='tight')
    plt.show()
    

if __name__ == "__main__":
    run_monte_carlo()