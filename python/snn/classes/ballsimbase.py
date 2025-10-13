'''
    2025 전국 대학생 AI 반도체 설계 경진대회 2차과제:
    Ball balancing simulator

    최초작성자: 김연준
'''

import numpy as np


class BallSimBase:
    '''
        Ball balancing simulator
        (1) class parameters:
        * STEPS_PER_SEC: simulation steps per second [s^-1]
        * G: gravitational acceleration [m/s^2]
        * R: radius of the ball [m]
        * M: mass of the ball [kg]
        * MU: friction coefficient between the ball and the plate
        * PLATE_SIDE: length of a side of the square plate [m]

        (2) simulation variables:
        * time: simulation time [s]
        * num_steps

        (3) internal state variables:
        * plate_n[3]: normal vector of the plate
        * ball_pos[3]: position of the ball [m]
        * stball_v[3]: velocity of the ball [m/s]
        * ball_w[3]: angular velocity of the ball [rad/s]
    '''
    def __init__(self, STEPS_PER_SEC, G=9.81, R=0.01, M=0.01, MU=0.1, PLATE_SIDE=0.3, verbose=False):
        # (1) initialize class parameters
        self.STEPS_PER_SEC = STEPS_PER_SEC
        self.DT = 1.0 / self.STEPS_PER_SEC
        self.G = G
        self.R = R
        self.M = M
        self.MU = MU
        self.PLATE_SIDE = PLATE_SIDE
        self.verbose = verbose

        # (2) initialize simulation variables
        self.isRunning = False
        self.time = 0.0
        self.num_steps = 0

        # (3) initialize internal state variables
        self.plate_n = np.array([0,0,1])  # unit vector
        self.ball_pos = np.zeros(3)      # [m]
        self.ball_v = np.zeros(3)      # [m/s]
        self.ball_w = np.zeros(3)      # [rad/s]

        #print("BallSim: initialized.")
        #if verbose:
        #    print(f"self.__dict__:\n{self.__dict__}")

    def reset(self,
              plate_n=np.zeros(3),
              ball_pos=np.zeros(3),
              ball_v=np.zeros(3),
              ball_w=np.zeros(3)):
        self.isRunning = True

        # reset simulation variables
        self.time = 0.0
        self.num_steps = 0

        # reset internal state variables
        self.plate_n = plate_n
        self.ball_pos = ball_pos
        self.ball_v = ball_v
        self.ball_w = ball_w

        print("BallSim: reset complete.")
        if self.verbose:
            print(f"self.__dict__:\n{self.__dict__}")
    
    def reset_random(self,
                     plate_tilt_range=(-0.3, 0.3),
                     ball_pos_range=(-0.05, 0.05),
                     ball_v_range=(-1, 1)):
        # (1) randomly set plate_n
        tmp = np.random.uniform(plate_tilt_range[0], plate_tilt_range[1], size=2)
        plate_n = np.array([tmp[0], tmp[1], np.sqrt(1 - tmp[0]**2 - tmp[1]**2)])

        # (2) randomly set ball_pos, ball_v
        tmp = np.random.uniform(ball_pos_range[0], ball_pos_range[1], size=2)
        ball_pos = np.array([tmp[0], tmp[1], self.R])
        ball_pos += (self.R - np.dot(ball_pos, plate_n)) * plate_n  # keep contact with the plate

        tmp = np.random.uniform(ball_v_range[0], ball_v_range[1], size=2)
        ball_v = np.array([tmp[0], tmp[1], 0])
        ball_v -= np.dot(ball_v, plate_n) * plate_n  # make velocity parallel to the plate
        
        self.reset(
            plate_n=plate_n,
            ball_pos=ball_pos,
            ball_v=ball_v,
            ball_w=np.zeros(3)
        )

    def _get_ball_pos_proj(self):
        # project ball position onto the plate
        p = self.ball_pos - np.dot(self.ball_pos, self.plate_n) * self.plate_n
        return p[:2]

    def _get_forces_to_ball(self):
        # (1) gravitational force
        # f_g: gravitational force [N]
        f_g = np.array([0, 0, -self.M * self.G])

        # (2) normal force from the plate
        # n: normal vector of the plate
        n = self.plate_n
        # f_n: normal force [N]
        f_n = np.dot(-f_g, n) * n 
        
        # (3) frictional force
        # v: velocity of the ball [m/s]
        v = self.ball_v
        # f_f: frictional force [N]
        if np.linalg.norm(v) > 1e-6:
            f_f = -self.MU * np.linalg.norm(f_n) * (v / np.linalg.norm(v)) 
        else:
            f_f = np.zeros(3)

        # (4) total force
        f_total = f_g + f_n + f_f  # [N]

        return (f_total, f_g, f_n, f_f)
    
    def _get_force_torque(self):
        f_total, f_g, f_n, f_f = self._get_forces_to_ball()

        # r: position vector from the center of the ball to the contact point [m]
        r = self.ball_pos - np.dot(self.ball_pos, self.plate_n) * self.plate_n
        # tau: torque [N*m]
        tau = np.cross(r, f_f)

        return (f_total, tau)
    
    def _update_ball(self):
        f, tau = self._get_force_torque()

        # (1) update linear motion
        # a: acceleration of the ball [m/s^2]
        a = f / self.M
        self.ball_v += a * self.DT
        self.ball_v -= np.dot(self.ball_v, self.plate_n) * self.plate_n  # make velocity parallel to the plate
        self.ball_pos += self.ball_v * self.DT
        self.ball_pos += ((self.R-np.dot(self.plate_n, self.ball_pos)) * self.plate_n)  # keep contact with the plate

        # (2) update angular motion
        # I: moment of inertia of the ball [kg*m^2]
        I = (2/5) * self.M * self.R**2
        # alpha: angular acceleration of the ball [rad/s^2]
        alpha = tau / I
        self.ball_w += alpha * self.DT
        # (angular position is not tracked)

    def _get_plate_vertices(self):
        vertices = []
        hs = self.PLATE_SIDE / 2 # half side
        for x in [-hs, hs]:
            for y in [-hs, hs]:
                p = np.array([x, y, 0])
                p -= np.dot(p, self.plate_n) * self.plate_n  # project onto the plate
                vertices.append(p)
        return vertices
    
    def _is_ball_on_plate(self):
        vertices = self._get_plate_vertices()
        xs = [v[0] for v in vertices]
        ys = [v[1] for v in vertices]
        if (min(xs) <= self.ball_pos[0] <= max(xs)) \
            and (min(ys) <= self.ball_pos[1] <= max(ys)):
            return True
        else:
            return False

    # set plate normal vector into a new value (automatically normalized)
    def set_plate_n(self, new_plate_n):
        self.plate_n = new_plate_n / np.linalg.norm(new_plate_n)

    def print_state(self):
        print(f"Sim state at time {self.time:.3f}s (step #{self.num_steps}):")
        print(f"  Plate orientation: {self.plate_n}")
        print(f"  Ball position: {self.ball_pos} [m]")
        print(f"  Ball velocity: {self.ball_v} [m/s]")
        print(f"  Ball angular velocity: {self.ball_w} [rad/s]")

    def step(self):
        if not self.isRunning:
            print("The simulation is not running. Please reset the simulation.")
            return
        
        self._update_ball()

        # update time
        self.time += self.DT
        self.num_steps += 1

        if not self._is_ball_on_plate():
            self.isRunning = False
            print(f"The ball has fallen off the plate!")
            print(f"  At time {self.time:.3f}s (step #{self.num_steps})")
            print(f"  Ball position: {self.ball_pos} [m]")
