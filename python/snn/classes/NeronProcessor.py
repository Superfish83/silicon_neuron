import numpy as np


def saturated_add(a, b, min_val, max_val):
    if a + b > max_val:
        return max_val
    elif a + b < min_val:
        return min_val
    else:
        return a + b


class NeuronProcessor:
    def __init__(
        self,
        hidden_state,
        motor_state,
        accumulated_I_hidden,
        accumulated_I_motor,
        syn_fired_sensor_hidden,
        syn_fired_hidden_motor,
        syn_weights_sensor_hidden,
        syn_weights_hidden_motor,
        syn_weights_sensor_hidden_new,
        syn_weights_hidden_motor_new,
        syn_weights_sensor_hidden_new_anti,
        syn_weights_hidden_motor_new_anti,
        N_SENSORS,
        N_HIDDEN,
        N_MOTORS,
        DT,
        V_THRESH,
        V_RESET,
        W_ADD,
        WEIGHT_MIN,
        WEIGHT_MAX,
    ):
        # np arrays will be shared references
        self.hidden_state = hidden_state
        self.motor_state = motor_state
        self.accumulated_I_hidden = accumulated_I_hidden
        self.accumulated_I_motor = accumulated_I_motor
        self.syn_fired_sensor_hidden = syn_fired_sensor_hidden
        self.syn_fired_hidden_motor = syn_fired_hidden_motor
        self.syn_weights_sensor_hidden = syn_weights_sensor_hidden
        self.syn_weights_hidden_motor = syn_weights_hidden_motor
        self.syn_weights_sensor_hidden_new = syn_weights_sensor_hidden_new
        self.syn_weights_hidden_motor_new = syn_weights_hidden_motor_new
        self.syn_weights_sensor_hidden_new_anti = syn_weights_sensor_hidden_new_anti
        self.syn_weights_hidden_motor_new_anti = syn_weights_hidden_motor_new_anti
        self.N_SENSORS = N_SENSORS
        self.N_HIDDEN = N_HIDDEN
        self.N_MOTORS = N_MOTORS
        self.DT = DT
        self.V_THRESH = V_THRESH
        self.V_RESET = V_RESET
        self.W_ADD = W_ADD
        self.WEIGHT_MIN = WEIGHT_MIN
        self.WEIGHT_MAX = WEIGHT_MAX

        # FIFO queue for two-stage processing (sensor->hidden, hidden->motor)
        self.spike_queue = []

    def queue(self, sensor_spikes):
        """
        FIFO for queuing SNN inputs
        This simulates a hardware FIFO buffer for pipelined processing
        """
        self.spike_queue.append(sensor_spikes)

    def dequeue(self):
        """
        Dequeue the oldest spike set from FIFO
        """
        if len(self.spike_queue) > 0:
            return self.spike_queue.pop(0)
        return []

    def calc_model(self, V, W, I):
        """
        Returns Izhikevich model motor spikes
        """
        dVdt = 0.04 * V**2 + 5 * V + 140 - W + I
        dWdt = 0.02 * (0.2 * V - W)

        V += dVdt * self.DT
        W += dWdt * self.DT

        activation = V >= self.V_THRESH
        if activation:
            V = self.V_RESET
            W += self.W_ADD

        return V, W, activation

    def process_layer(
        self, input_spikes, neuron_state, accumulated_I, weights, syn_fired, n_output
    ):
        """
        Process a layer of neurons

        input_spikes: list of input spike indices
        neuron_state: state of output neurons (np array [n_output, 2] for [V, W])
        accumulated_I: accumulated input current for output neurons (np array)
        weights: synaptic weights from input to output (np array [n_input, n_output])
        syn_fired: synaptic fired state (np array [n_input, n_output])
        n_output: number of output neurons

        Returns: list of output spike indices
        """
        # (1) Accumulate input currents from input spikes
        for i in input_spikes:
            for j in range(n_output):
                accumulated_I[j] += weights[i][j]
                syn_fired[i][j] = 1

        # (2) Update neuron states and detect spikes using Izhikevich model
        output_spikes = []
        for j in range(n_output):
            V = neuron_state[j][0]
            W = neuron_state[j][1]
            I = accumulated_I[j]

            # Update using calc_model
            V, W, activation = self.calc_model(V, W, I)

            neuron_state[j][0] = V
            neuron_state[j][1] = W
            accumulated_I[j] = 0.0  # reset after processing

            if activation:
                output_spikes.append(j)

        return output_spikes

    def update_weights_stdp(
        self, output_spikes, syn_fired, weights, weights_new, weights_new_anti, n_input
    ):
        weights_new[:, :] = weights
        weights_new_anti[:, :] = weights

        for j in output_spikes:
            pre = syn_fired[:, j] == 1
            delta = np.where(pre, 0.5, -0.25)  # A₊=0.5, A₋=0.25

            w_plus = np.clip(weights[:, j] + delta, self.WEIGHT_MIN, self.WEIGHT_MAX)
            w_minus = np.clip(weights[:, j] - delta, self.WEIGHT_MIN, self.WEIGHT_MAX)

            weights_new[:, j] = w_plus
            weights_new_anti[:, j] = w_minus

            syn_fired[:, j] = 0

    def process(self, sensory_spikes):
        """
        Process the entire SNN for one timestep.
        Note that this is processed in two steps via a FIFO.
        (For FPGA implementation)

        Stage 1: Sensor -> Hidden layer (queued)
        Stage 2: Hidden -> Motor layer
        """
        # Queue the sensory spikes for two-stage processing
        self.queue(sensory_spikes)

        # Stage 1: Process sensor -> hidden layer
        if len(self.spike_queue) > 0:
            queued_spikes = self.dequeue()
            hidden_spikes = self.process_layer(
                input_spikes=queued_spikes,
                neuron_state=self.hidden_state,
                accumulated_I=self.accumulated_I_hidden,
                weights=self.syn_weights_sensor_hidden,
                syn_fired=self.syn_fired_sensor_hidden,
                n_output=self.N_HIDDEN,
            )

            # STDP update for sensor->hidden weights
            self.update_weights_stdp(
                output_spikes=hidden_spikes,
                syn_fired=self.syn_fired_sensor_hidden,
                weights=self.syn_weights_sensor_hidden,
                weights_new=self.syn_weights_sensor_hidden_new,
                weights_new_anti=self.syn_weights_sensor_hidden_new_anti,
                n_input=self.N_SENSORS,
            )
        else:
            hidden_spikes = []

        # Stage 2: Process hidden -> motor layer
        motor_spikes = self.process_layer(
            input_spikes=hidden_spikes,
            neuron_state=self.motor_state,
            accumulated_I=self.accumulated_I_motor,
            weights=self.syn_weights_hidden_motor,
            syn_fired=self.syn_fired_hidden_motor,
            n_output=self.N_MOTORS,
        )

        # STDP update for hidden->motor weights
        self.update_weights_stdp(
            output_spikes=motor_spikes,
            syn_fired=self.syn_fired_hidden_motor,
            weights=self.syn_weights_hidden_motor,
            weights_new=self.syn_weights_hidden_motor_new,
            weights_new_anti=self.syn_weights_hidden_motor_new_anti,
            n_input=self.N_HIDDEN,
        )

        return motor_spikes
