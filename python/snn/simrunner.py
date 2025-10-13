from classes.ballsim import BallSim
from classes.ballsim_vis import BallSimVis
from classes.SNN import SNN

class SimRunner:
    def __init__(self, STEPS_PER_SEC=1000, M=0.01, NUM_SENSORS=100, verbose=False):
        # simulation
        self.sim = BallSim(STEPS_PER_SEC=STEPS_PER_SEC, M=M, verbose=verbose)
        self.sim.reset_random()

        # SNN controller
        self.snn = SNN(STEPS_PER_SEC=STEPS_PER_SEC)

        # simulation visualizer
        self.vis = BallSimVis(ballsim=self.sim, verbose=verbose)


    def run():
        sim = BallSim(verbose=False)
        vis = BallSimVis(ballsim=sim, verbose=False)

        while True:
            vis.reset_random()
            vis.run()