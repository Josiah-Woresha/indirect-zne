import os
from src.modules import *
from src.constraint import *
import matplotlib.pyplot as plt
from scipy.optimize import minimize
from qulacs import QuantumState, DensityMatrix
from qulacsvis import circuit_drawer


# Define ansatz_circuit globally
ansatz_circuit = None

class VQE:
    def __init__(self, n, state, layer, iteration, optimizer, constraint, type, ti, tf, cn, bn, r, noise_status, noise_val, noise_factor, init_param, draw):

        self.n = n
        self.state = state
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
        self.init_param = init_param
        self.draw = draw

        self.xy_ham = create_xy_hamiltonian(n, cn, bn, r)   # XY spin chain Hamiltonian
        self.ising_ham = create_ising_hamiltonian(n, cn, bn)    # Ising spin chain Hamiltonian to be used as observable
    

    # Cost function with noise-less parametric ansatz
    def cost(self, param):
        # Create the quantum state
        if self.state == "DMatrix":
            state = DensityMatrix(self.n)
        else:
            state = QuantumState(self.n)
                    
        global ansatz_circuit  # Access the global ansatz_circuit

        if self.type == "xy":

            if self.noise_status:
                ansatz_circuit = create_noisy_ansatz(self.n, self.layer, self.noise_value, self.noise_factor, self.xy_ham, param)
            else:
                ansatz_circuit = parametric_ansatz(self.n, self.layer, self.xy_ham, param)

        if self.type == "ising":

            if self.noise_status:
                ansatz_circuit = create_noisy_ansatz(self.n, self.layer, self.noise_value, self.noise_factor, self.ising_ham, param)
            else:
                ansatz_circuit = parametric_ansatz(self.n, self.layer, self.ising_ham, param)

        if self.type == "hardware":
            ansatz_circuit = he_ansatz_circuit(self.n, self.layer, param)


        ansatz_circuit.update_quantum_state(state) # type: ignore
        return self.ising_ham.get_expectation_value(state)
    
    def run_vqe(self):
        
        cost_history = []
        min_cost = []
        optimized_params = []  # List to store optimized parameters (solutions)
        param_constraint = None
    

        for _ in range(self.iteration):

            if self.init_param == "random":
                parameters = create_param(self.layer, self.ti, self.tf)
            else:
                parameters = self.init_param

            if self.constraint and self.optimizer == "SLSQP":
                param_constraint =  create_time_constraints(self.layer, len(parameters))
                
            opt = minimize(
                self.cost,
                parameters,
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
        current_dir = os.path.dirname(os.path.abspath(__file__))
        parent_dir = os.path.dirname(current_dir)  # Go up one level
        output_dir = os.path.join(parent_dir, "output")
        os.makedirs(output_dir, exist_ok=True)
        output_file = os.path.join(output_dir, f"circuit_{time_stamp}.png")
        
        circuit_drawer(ansatz_circuit, "mpl") # type: ignore
        plt.savefig(output_file, dpi=dpi)
        plt.close()
        # Print the path of the output file
        print(f"Circuit fig saved to: {os.path.abspath(output_file)}")
    