"""
2025 전국 대학생 AI 반도체 설계 경진대회 2차과제:
Spiking Neural Network (SNN) controller

최초작성자: 김연준
최종수정자: 임준서
"""

import numpy as np
from .NeronProcessor import NeuronProcessor


class SNN:
    """
    Spiking Neural Network (SNN) controller

    The SNN consists of two layers:
    - Sensory neurons: 100 neurons receiving sensory input
    - Hidden neurons: 100 neurons (intermediate layer)
    - Motor neurons: 8 neurons controlling the motors (4 motors, 이완, 수축)

    Neuron model: Izhikevich neuron model
    """

    def __init__(self, STEPS_PER_SEC, N_SENSORS=100, N_HIDDEN=100, N_MOTORS=8):
        self.STEPS_PER_SEC = STEPS_PER_SEC
        self.DT = 1.0 / STEPS_PER_SEC
        self.N_SENSORS = N_SENSORS
        self.N_MOTORS = N_MOTORS
        self.N_HIDDEN = N_HIDDEN

        self.V_RESET = -65.0  # reset potential after spike [mV]
        self.V_THRESH = 32.0  # spike threshold [mV]
        self.W_RESET = -15.0  # reset value of recovery variable after spike
        self.W_ADD = 5.0  # increment of recovery variable after spike

        self.WEIGHT_MIN = -2.0
        self.WEIGHT_MAX = 2.0

        self.reset()

    def reset(self):
        # neuron state variables
        self.hidden_state = np.zeros((self.N_HIDDEN, 2))  # hidden neuron states: [V, W]
        self.motor_state = np.zeros((self.N_MOTORS, 2))  # motor neuron states: [V, W]
        
        self.accumulated_I_hidden = np.zeros(
            self.N_HIDDEN
        )  # accumulated input current for hidden neurons
        self.accumulated_I_motor = np.zeros(
            self.N_MOTORS
        )  # accumulated input current for motor neurons

        # synaptic weights for sensor -> hidden layer
        self.syn_weights_sensor_hidden = np.random.uniform(
            self.WEIGHT_MIN, self.WEIGHT_MAX, (self.N_SENSORS, self.N_HIDDEN)
        )
        self.syn_fired_sensor_hidden = np.zeros(
            (self.N_SENSORS, self.N_HIDDEN)
        )  # synaptic fired state (1 if fired, else 0)
        
        # synaptic weights for hidden -> motor layer
        self.syn_weights_hidden_motor = np.random.uniform(
            self.WEIGHT_MIN, self.WEIGHT_MAX, (self.N_HIDDEN, self.N_MOTORS)
        )
        self.syn_fired_hidden_motor = np.zeros(
            (self.N_HIDDEN, self.N_MOTORS)
        )  # synaptic fired state (1 if fired, else 0)

        self.syn_weights_sensor_hidden_new = np.copy(self.syn_weights_sensor_hidden)  # for STDP weight update
        self.syn_weights_sensor_hidden_new_anti = np.copy(
            self.syn_weights_sensor_hidden
        )  # for anti-STDP weight update
        
        self.syn_weights_hidden_motor_new = np.copy(self.syn_weights_hidden_motor)  # for STDP weight update
        self.syn_weights_hidden_motor_new_anti = np.copy(
            self.syn_weights_hidden_motor
        )  # for anti-STDP weight update
        
        # Initialize NeuronProcessor
        self.neuron_processor = NeuronProcessor(
            hidden_state=self.hidden_state,
            motor_state=self.motor_state,
            accumulated_I_hidden=self.accumulated_I_hidden,
            accumulated_I_motor=self.accumulated_I_motor,
            syn_fired_sensor_hidden=self.syn_fired_sensor_hidden,
            syn_fired_hidden_motor=self.syn_fired_hidden_motor,
            syn_weights_sensor_hidden=self.syn_weights_sensor_hidden,
            syn_weights_hidden_motor=self.syn_weights_hidden_motor,
            syn_weights_sensor_hidden_new=self.syn_weights_sensor_hidden_new,
            syn_weights_hidden_motor_new=self.syn_weights_hidden_motor_new,
            N_SENSORS=self.N_SENSORS,
            N_HIDDEN=self.N_HIDDEN,
            N_MOTORS=self.N_MOTORS,
            DT=self.DT,
            V_THRESH=self.V_THRESH,
            V_RESET=self.V_RESET,
            W_ADD=self.W_ADD,
            WEIGHT_MIN=self.WEIGHT_MIN,
            WEIGHT_MAX=self.WEIGHT_MAX,
        )

    """
        SNN step:
        updates neuron states, processes spikes, performs STDP computation
        Uses queue-based processing through NeuronProcessor

        입력: list of spikes from sensory neurons (indices)
        출력: list of spikes from motor neurons (indices)
    """

    def step(self, sensory_spikes):
        # Queue-based processing using NeuronProcessor
        # This mimics FPGA FIFO behavior
        motor_spikes = self.neuron_processor.process(sensory_spikes)
        
        print(f"[SNN] Sensory spikes: {len(sensory_spikes)}, Motor spikes: {motor_spikes}")
        
        return motor_spikes

    def learn_stdp(self):
        self.syn_weights_sensor_hidden = np.clip(self.syn_weights_sensor_hidden_new, 0, 1)
        self.syn_weights_sensor_hidden_new = np.copy(self.syn_weights_sensor_hidden)
        
        self.syn_weights_hidden_motor = np.clip(self.syn_weights_hidden_motor_new, 0, 1)
        self.syn_weights_hidden_motor_new = np.copy(self.syn_weights_hidden_motor)

    def learn_anti_stdp(self):
        self.syn_weights_sensor_hidden = np.clip(self.syn_weights_sensor_hidden_new_anti, 0, 1)
        self.syn_weights_sensor_hidden_new_anti = np.copy(self.syn_weights_sensor_hidden)
        
        self.syn_weights_hidden_motor = np.clip(self.syn_weights_hidden_motor_new_anti, 0, 1)
        self.syn_weights_hidden_motor_new_anti = np.copy(self.syn_weights_hidden_motor)
