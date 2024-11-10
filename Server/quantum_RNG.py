from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator
from qiskit.visualization import plot_histogram
import numpy as np
import matplotlib.pyplot as plt
import string

def quantum_random_number_generator(num_bits):
  qc = QuantumCircuit(num_bits,num_bits)
  # apply H-gate to each qubit
  for qubit in range(num_bits):
    qc.h(qubit)
  # measure each qubit and store the result in classical bits
  qc.measure(range(num_bits),range(num_bits))
  # Use the Aer's qasm simulator to simulate the circuit
  simulator = AerSimulator()
  # Execute the circuit on the simulator and get the result
  result = simulator.run(qc, shots=100).result()
  counts = result.get_counts()
  plot_histogram(counts)
  plt.show()
  single_result = simulator.run(qc, shots=1).result()
  single_counts = single_result.get_counts()
  # Extract the random bits string from the single outcome
  random_bits = list(single_counts.keys())[0]
  return random_bits

num = quantum_random_number_generator(8)
random_integer = int(num, 2)

print(f"Random integer: {random_integer}")