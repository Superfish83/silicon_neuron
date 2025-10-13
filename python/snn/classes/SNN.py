'''
    2025 전국 대학생 AI 반도체 설계 경진대회 2차과제:
    Spiking Neural Network (SNN) controller

    최초작성자: 김연준
'''

import numpy as np

def saturated_add(a, b, min_val, max_val):
    if a + b > max_val:
        return max_val
    elif a + b < min_val:
        return min_val
    else:
        return a + b

class SNN:
    '''
        Spiking Neural Network (SNN) controller
        
        The SNN consists of a single layer:
        - Sensory neurons: 100 neurons receiving sensory input
        - Motor neurons: 8 neurons controlling the motors (4 motors, 이완, 수축)
        
        Neuron model: Izhikevich neuron model
    '''

    def __init__(self, STEPS_PER_SEC, N_SENSORS=100, N_MOTORS=8):
        self.STEPS_PER_SEC = STEPS_PER_SEC
        self.DT = 1.0 / STEPS_PER_SEC
        self.N_SENSORS = N_SENSORS
        self.N_MOTORS = N_MOTORS

        self.V_RESET = -65.0 # reset potential after spike [mV]
        self.V_THRESH = 32.0 # spike threshold [mV]
        self.W_RESET = -15.0 # reset value of recovery variable after spike
        self.W_ADD = 5.0 # increment of recovery variable after spike

        self.WEIGHT_MIN = -2.0
        self.WEIGHT_MAX = 2.0

        self.reset()

    def reset(self):
        # neuron state variables
        self.motor_state = np.zeros((self.N_MOTORS, 2))            # motor neuron states: [V, W]
        self.accumulated_I = np.zeros(self.N_MOTORS)               # accumulated input current for motor neurons

        self.syn_weights = np.random.uniform(self.WEIGHT_MIN, self.WEIGHT_MAX,
                                             (self.N_SENSORS, self.N_MOTORS)) # synaptic weights
        self.syn_fired = np.zeros((self.N_SENSORS, self.N_MOTORS)) # synaptic fired state (1 if fired, else 0)

        self.syn_weights_new = np.copy(self.syn_weights)            # for STDP weight update
        self.syn_weights_new_anti = np.copy(self.syn_weights)       # for anti-STDP weight update

    '''
        SNN step:
        updates neuron states, processes spikes, performs STDP computation

        입력: list of spikes from sensory neurons (indices)
        출력: list of spikes from motor neurons (indices)
    '''
    def step(self, sensory_spikes):
        # (1) process sensory spikes
        for i in sensory_spikes:
            for j in range(self.N_MOTORS):        
                self.accumulated_I[j] += self.syn_weights[i][j]
                self.syn_fired[i][j] = 1

        # (2) update motor neuron states using Izhikevich model
        motor_spikes = []
        for j in range(self.N_MOTORS):
            V = self.motor_state[j][0]
            W = self.motor_state[j][1]
            I = self.accumulated_I[j]

            dVdt = 0.04 * V**2 + 5 * V + 140 - W + I
            dWdt = 0.02 * (0.2 * V - W)

            V += dVdt * self.DT
            W += dWdt * self.DT

            if V >= self.V_THRESH:
                V = self.V_RESET
                W += self.W_ADD
                motor_spikes.append(j)

            self.motor_state[j][0] = V
            self.motor_state[j][1] = W
        
        # (3) STDP weight update
        delta_weights = np.zeros((self.N_SENSORS, self.N_MOTORS))
        for j in motor_spikes:
            for i in range(self.N_SENSORS):
                if self.syn_fired[i][j] == 1:
                    delta_weights[i][j] += 0.5 # potentiation
                    self.syn_fired[i][j] = 0 # reset fired state
                else:
                    delta_weights[i][j] -= 0.25 # depression

        # apply weight updates with clipping
        for j in motor_spikes:
            for i in range(self.N_SENSORS):
                self.syn_weights_new[i][j] = saturated_add(
                    self.syn_weights[i][j], delta_weights[i][j],
                    self.WEIGHT_MIN, self.WEIGHT_MAX)
                self.syn_weights_new_anti[i][j] = saturated_add(
                    self.syn_weights[i][j], -delta_weights[i][j],
                    self.WEIGHT_MIN, self.WEIGHT_MAX)

        return motor_spikes

    def learn_stdp(self):
        self.syn_weights = np.clip(self.syn_weights_new, 0, 1)
        self.syn_weights_new = np.copy(self.syn_weights)

    def learn_anti_stdp(self):
        self.syn_weights = np.clip(self.syn_weights_new_anti, 0, 1)
        self.syn_weights_new_anti = np.copy(self.syn_weights)