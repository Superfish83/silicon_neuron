"""
2025 전국 대학생 AI 반도체 설계 경진대회 2차과제:
Spiking Neural Network (SNN) controller

최초작성자: 김연준
최종수정자: 임준서
"""

import numpy as np
from .NeuronProcessor import NeuronProcessor


def calc_model(DT, V, U, I):
    """
    Returns Izhikevich model motor spikes
    """

    THRES_V = 32
    a, b, c, d = 0.02, 0.2, -50, 2

    dVdt = 0.04 * V**2 + 5 * V + 140 - U + I
    dUdt = a * (b * V - U)

    V += dVdt * DT
    U += dUdt * DT

    spike = V >= THRES_V
    if spike:
        V = c
        U += d

    return V, U, spike

class SNN:
    """
    Spiking Neural Network (SNN) controller

    The SNN consists of two layers:
    - Sensory neurons: 100 neurons receiving sensory input
    - Hidden neurons: 100 neurons (intermediate layer)
    - Motor neurons: 8 neurons controlling the motors (4 motors, 이완, 수축)

    Neuron model: Izhikevich neuron model
    """

    def __init__(self, STEPS_PER_SEC, N_SENSORS, N_MOTORS):
        # (0) parameters
        self.STEPS_PER_SEC = STEPS_PER_SEC
        self.DT = 1.0 / STEPS_PER_SEC

        self.N_SENSORS = N_SENSORS
        self.N_MOTORS = N_MOTORS

        self.V_INIT = -65.0 
        self.U_INIT = -15.0
        self.WEIGHT_MAX = 32.0
        self.WEIGHT_MIN = 0.0
        self.STDP_STEP = 1.0

        # self.params = (self.DT, self.N_SENSORS, self.N_MOTORS, self.V_INIT, self.U_INIT,
        #                self.WEIGHT_MIN, self.WEIGHT_MAX, self.STDP_STEP)

        # (1) neuron and synapse state variables
        # motor neuron states: [V, U, I (accumulated input current)]
        self.motor_state = np.zeros((self.N_MOTORS, 3))

        # synaptic weights for sensor -> hidden layer
        self.syn_weights_sensor = np.zeros(
            (self.N_SENSORS, self.N_MOTORS),  # Temporary adjustment
        )
        
        # synaptic fired state (1 if fired, else 0) -> used for STDP
        self.syn_fired_sensor = np.zeros(
            (self.N_SENSORS, self.N_MOTORS)
        ) 

        # (2) variables for STDP weight updates
        self.stdp_sensor = np.zeros((self.N_SENSORS, self.N_MOTORS))
        self.anti_stdp_sensor = np.zeros((self.N_SENSORS, self.N_MOTORS))

        
        # (*) Initialize NeuronProcessor
        # self.neuron_processor = NeuronProcessor(
        #     self.motor_state,
        #     self.syn_fired_sensor, self.syn_weights_sensor,
        #     self.stdp_sensor, self.anti_stdp_sensor,
        #     self.params
        # )

        self.reset_weights()
        self.reset_neuron_states()


    def reset_weights(self):
        self.syn_weights_sensor = np.random.uniform(
            self.WEIGHT_MIN, self.WEIGHT_MAX,
            (self.N_SENSORS, self.N_MOTORS)
        )

    def reset_neuron_states(self):
        self.motor_state = np.zeros((self.N_MOTORS, 3))
        self.motor_state[:, 0] += self.V_INIT  # V
        self.motor_state[:, 1] += self.U_INIT  # U
        #self.motor_state[:, 2] *= 0.0          # I
        
        self.syn_fired_sensor[:, :] = 0
        self.stdp_sensor = self.syn_weights_sensor.copy()
        self.anti_stdp_sensor = self.syn_weights_sensor.copy()

    """
        SNN step:
        updates neuron states, processes spikes, performs STDP computation
        Uses queue-based processing through NeuronProcessor

        입력: list of spikes from sensory neurons (indices)
        출력: list of spikes from motor neurons (indices)
    """
    def process(self, sensory_spikes):
        """
        Process the entire SNN for one timestep.
        (For FPGA implementation)
        """
        motor_spikes = []

        # (1) Collect input spikes
        for i in sensory_spikes:
            for j in range(self.N_MOTORS):
                self.motor_state[j][2] += self.syn_weights_sensor[i][j]
                self.syn_fired_sensor[i][j] = 1

        # (2) Update motor neuron states
        for j in range(self.N_MOTORS):
            V = self.motor_state[j][0]
            U = self.motor_state[j][1]
            I = self.motor_state[j][2]

            # Update using calc_model
            V, U, spike = calc_model(self.DT, V, U, I)

            self.motor_state[j][0] = V
            self.motor_state[j][1] = U
            self.motor_state[j][2] = 0.0  # reset after processing

            if spike:
                for k in range(self.N_MOTORS):
                    if k == j:
                        continue
                        # Lateral inhibition:
                    self.motor_state[k][2] = 0.0
                motor_spikes.append(j)

        # (3) Update STDP weights
        for j in motor_spikes:
            for i in range(self.N_SENSORS):
                if self.syn_fired_sensor[i][j] == 1:
                    self.syn_fired_sensor[i][j] = 0

                    self.stdp_sensor[i][j] += self.STDP_STEP
                    self.anti_stdp_sensor[i][j] -= self.STDP_STEP
                else:
                    self.stdp_sensor[i][j] -= self.STDP_STEP
                    self.anti_stdp_sensor[i][j] += self.STDP_STEP
        
        return motor_spikes
    
    def step(self, sensory_spikes):
        motor_spikes = self.process(sensory_spikes)

        return (
            motor_spikes,
            self.motor_state,
        )

    def learn_stdp(self):
        self.syn_weights_sensor = np.clip(
            self.stdp_sensor, self.WEIGHT_MIN, self.WEIGHT_MAX
        )

    def learn_anti_stdp(self):
        self.syn_weights_sensor = np.clip(
            self.anti_stdp_sensor, self.WEIGHT_MIN, self.WEIGHT_MAX
        )
