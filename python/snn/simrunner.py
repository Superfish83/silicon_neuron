from classes.ballsim import BallSim
from classes.ballsim_vis import BallSimVis
from classes.SNN import SNN


class SimRunner:
    def __init__(self, STEPS_PER_SEC, VIS_FPS, M, N_SENSORS=100, verbose=False, MU=0.1):
        # simulation
        self.sim = BallSim(
            STEPS_PER_SEC=STEPS_PER_SEC,
            M=M,
            MU=MU,
            verbose=verbose,
        )
        self.sim.reset_random()

        # SNN controller
        self.snn = SNN(STEPS_PER_SEC=STEPS_PER_SEC, N_SENSORS=N_SENSORS)

        # simulation visualizer
        self.vis = BallSimVis(VIS_FPS=VIS_FPS)

        self.SUCCESS_STEPS = 200

    def update_snn(self):
        if self.sim.num_steps > self.SUCCESS_STEPS and self.sim.get_ball_distfromcenter() < self.sim.PLATE_SIDE / 3:
            #self.SUCCESS_STEPS += 2
            self.snn.learn_stdp()
            print("STDP weight update performed.")
        else:
            #self.SUCCESS_STEPS -= 1
            self.snn.learn_anti_stdp()
            print("Anti-STDP weight update performed.")
        #self.SUCCESS_STEPS = max(200, self.SUCCESS_STEPS)
        #print(f"Current SUCCESS_STEPS: {self.SUCCESS_STEPS}")

    def step(self):
        # (1) get sensory spikes from simulation
        sensory_spikes = self.sim.sensor_step()

        # (2) SNN step: get motor spikes from sensory spikes
        hidden_motor_states = self.snn.step(sensory_spikes)
        motor_spikes = hidden_motor_states[3]
        hidden_spikes = hidden_motor_states[2]

        # (3) simulation step: apply motor spikes to simulation
        self.sim.step(hidden_spikes)

        # (4) visualization step
        if(self.num_episodes > 1000):
            self.vis.draw(self.sim, self.num_episodes, sensory_spikes, hidden_motor_states)

        return motor_spikes

    def run(self):
        # reset simulation and SNN
        self.sim.reset_random()
        self.snn.reset()

        self.num_episodes = 0

        def reset_episode():
            self.num_episodes += 1
            self.update_snn()
            self.snn.neuron_processor.reset_neuron_states()
            self.sim.reset_random()

        while True:
            # (1) handle user input
            cmd = self.vis.get_input()
            if cmd == "quit":
                break
            elif cmd == "reset" or self.sim.num_steps > 300:
                reset_episode()

            # (2) simulation step
            if self.sim.isRunning:
                self.step()
            else:
                reset_episode()

        self.vis.close()


if __name__ == "__main__":
    runner = SimRunner(
        STEPS_PER_SEC=100,
        VIS_FPS=30,
        M=0.01,
        MU=0.01,
        N_SENSORS=100,
        verbose=False,
    )
    runner.run()
