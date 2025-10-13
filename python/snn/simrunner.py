from classes.ballsim import BallSim
from classes.ballsim_vis import BallSimVis
from classes.SNN import SNN

class SimRunner:
    def __init__(self, STEPS_PER_SEC, VIS_FPS, M, N_SENSORS=100, verbose=False):
        # simulation
        self.sim = BallSim(STEPS_PER_SEC=STEPS_PER_SEC, M=M, verbose=verbose)
        self.sim.reset_random()

        # SNN controller
        self.snn = SNN(STEPS_PER_SEC=STEPS_PER_SEC, N_SENSORS=N_SENSORS)

        # simulation visualizer
        self.vis = BallSimVis(VIS_FPS=VIS_FPS)

    def step(self):
        # (1) get sensory spikes from simulation
        sensory_spikes = self.sim.get_sensory_spikes()

        # (2) SNN step: get motor spikes from sensory spikes
        motor_spikes = self.snn.step(sensory_spikes)

        # (3) simulation step: apply motor spikes to simulation
        self.sim.step(None) #(motor_spikes)

        # (4) visualization step
        self.vis.draw(self.sim)

    def run(self):
        # reset simulation and SNN
        self.sim.reset_random()
        self.snn.reset()

        while True:
            # (1) handle user input
            cmd = self.vis.get_input()
            if cmd == "quit":
                break
            elif cmd == "reset":
                self.sim.reset_random()

            # (2) simulation step
            if self.sim.isRunning:
                self.step()
            else:
                self.sim.reset_random() # automatic reset

        self.vis.close()

if __name__ == "__main__":
    runner = SimRunner(STEPS_PER_SEC=100,
                       VIS_FPS=30,
                       M=0.01,
                       N_SENSORS=100,
                       verbose=True)
    runner.run()