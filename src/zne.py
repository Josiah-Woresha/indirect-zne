import os
from time import time
from pytest import param
from src.modules import *
from src.constraint import *
from datetime import datetime
import matplotlib
from qulacsvis import circuit_drawer


# Define ansatz_circuit globally
ansatz_circuit = None

class ZNE:
    def __init__(self, n, layer, iteration, optimizer, constraint, type, ti, tf, cn, bn, r, noise_status, noise_val, noise_factor, draw):

        self.n = n
        self.layer = layer
        self.iteration = iteration
        self.optimizer = optimizer
        self.constraint = constraint
        self.type = type
        self.ti = ti
        self.tf = tf
        self.cn = cn
        self.bn = bn
        self.r = r
        self.noise_status = noise_status
        self.noise_value = noise_val
        self.noise_factor = noise_factor
        self.draw = draw

        self.xy_ham = create_xy_hamiltonian(n, cn, bn, r)   # XY spin chain Hamiltonian
        self.ising_ham = create_ising_hamiltonian(n, cn, bn)    # Ising spin chain Hamiltonian to be used as observable

        # Cost function with noise-less parametric ansatz
    def cost(self, param):
        #state = DensityMatrix(self.n)
        state = QuantumState(self.n)
        global ansatz_circuit  # Access the global ansatz_circuit

        if self.type == "xy":

            if not self.noise_status:
                raise ValueError("Noise is not enabled. Aborting the code.")
            else:
                ansatz_circuit = create_noisy_ansatz(self.n, self.layer, self.noise_value, self.noise_factor, self.xy_ham, param)

        if self.type == "ising":

            if not self.noise_status:
                raise ValueError("Noise is not enabled. Aborting the code.")
                
            else:
                ansatz_circuit = create_noisy_ansatz(self.n, self.layer, self.noise_value, self.noise_factor, self.ising_ham, param)

        if self.type == "hardware":
            ansatz_circuit = he_ansatz_circuit(self.n, self.layer, param)


        ansatz_circuit.update_quantum_state(state) # type: ignore
        return self.ising_ham.get_expectation_value(state)
    
    def run_zne(self):
    
        cost_history = []
        min_cost = []
        optimized_params = []  # List to store optimized parameters (solutions)
        
        

        for _ in range(self.iteration):
            init_param = create_param(self.layer, self.ti, self.tf)

            if self.constraint and self.optimizer == "SLSQP":

                param_constraint =  create_time_constraints(self.layer, len(init_param)) # type: ignore
            else:

                param_constraint = None

            opt = minimize(
                self.cost,
                init_param,
                method = self.optimizer,
                constraints = param_constraint,
                callback=lambda x: cost_history.append(self.cost(x))
            )

            min_cost.append(np.min(cost_history))

        optimized_params.append(opt.x)
        exact_eigen_value = exact_sol(self.ising_ham)

        return exact_eigen_value, min_cost, optimized_params
    
    def drawCircuit(self, time_stamp, dpi):
        
        global ansatz_circuit
        output_file = f"circuit_{time_stamp}.png"
        circuit_drawer(ansatz_circuit, "mpl") # type: ignore
        plt.savefig(output_file, dpi = dpi)
        plt.close()
        # Print the path of the output file
        print(f"Output saved to: {os.path.abspath(output_file)}")