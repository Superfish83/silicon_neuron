import numpy as np


class NeuronProcessor:
    def __init__(self, motor_state, syn_fired_sensor, syn_weights_sensor,
                 stdp_sensor_new, anti_stdp_sensor_new, params):
        
        self.DT, self.N_SENSORS, self.N_MOTORS, self.V_INIT, self.U_INIT, \
        self.WEIGHT_MIN, self.WEIGHT_MAX, self.STDP_STEP = params
        
        # np arrays will be shared references
        self.motor_state = motor_state
        
        self.syn_fired_sensor = syn_fired_sensor
        self.syn_weights_sensor = syn_weights_sensor

        self.stdp_sensor_new = stdp_sensor_new
        self.anti_stdp_sensor_new = anti_stdp_sensor_new

    def calc_model(self, V, U, I):
        """
        Returns Izhikevich model motor spikes
        """

        THRES_V = 32
        a, b, c, d = 0.1, 0.2, -65, 2

        dVdt = 0.04 * V**2 + 5 * V + 140 - U + I
        dUdt = a * (b * V - U)

        V += dVdt * self.DT
        U += dUdt * self.DT

        spike = V >= THRES_V
        if spike:
            V = c
            U += d

        return V, U, spike

    def process(self, sensory_spikes):
        """
        Process the entire SNN for one timestep.
        (For FPGA implementation)
        """
        motor_spikes = []


        # (1) Collect input spikes
        for i in sensory_spikes:
            for j in range(self.N_MOTORS):
                print(self.syn_weights_sensor[i][j])
                self.motor_state[j][2] += self.syn_weights_sensor[i][j]
                self.syn_fired_sensor[i][j] = 1

        # (2) Update motor neuron states
        for j in range(self.N_MOTORS):
            V = self.motor_state[j][0]
            U = self.motor_state[j][1]
            I = self.motor_state[j][2]

            # Update using calc_model
            V, U, spike = self.calc_model(V, U, I)

            self.motor_state[j][0] = V
            self.motor_state[j][1] = U
            self.motor_state[j][2] = 0.0  # reset after processing

            if spike:
                motor_spikes.append(j)

        # (3) Update STDP weights
        for i in range(self.N_SENSORS):
            for j in range(self.N_MOTORS):
                if self.syn_fired_sensor[i][j] == 1:
                    self.syn_fired_sensor[i][j] = 0

                    self.stdp_sensor_new[i][j] += self.STDP_STEP
                    self.anti_stdp_sensor_new[i][j] -= self.STDP_STEP
                else:
                    self.stdp_sensor_new[i][j] -= self.STDP_STEP
                    self.anti_stdp_sensor_new[i][j] += self.STDP_STEP
        
        return motor_spikes
