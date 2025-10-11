'''
    2025 전국 대학생 AI 반도체 설계 경진대회 2차과제:
    Ball balancing simulator

    최초작성자: 김연준
'''

import numpy as np
from ballsimbase import BallSimBase

class BallSim_Motor:
    '''
        Motor neurons
        The motor neurons receive spikes from the SNN controller,
        calculates the position of 'motor', and
        determines the resultant plate normal vector.
        
        Motor는 +x, -x, +y, -y 4개 위치에 하나씩 있으며 각각 2개의 
        neuron(수축, 이완)과 연결되어 있음. (neuron 총 8개)
        각 motor는 spike를 받으면 순간적인 충격을 받은 damped oscillator처럼 작동
        (계산 편의를 위해 각 oscillator는 1kg으로 가정)

        계산된 4개 motor의 위치로부터 평면의 normal vector를 구함.
    '''
    def __init__(self, STEPS_PER_SEC, PLATE_SIDE):
        self.STEPS_PER_SEC = STEPS_PER_SEC
        self.DT = 1.0 / STEPS_PER_SEC
        self.MOTOR_COUNT = 4 # +x, -x, +y, -y
        self.NEURON_COUNT = self.MOTOR_COUNT * 2

        self.PLATE_SIDE = PLATE_SIDE # [m] the plate is square with this side length
        pos = 0.8 * (PLATE_SIDE / 2)
        
        # motor state constants
        self.MOTOR_POS_REST = np.array([
            [ pos, 0, 0], # +x
            [-pos, 0, 0], # -x
            [0,  pos, 0], # +y
            [0, -pos, 0]  # -y
        ])
        self.K = 3 # spring constant [N/m]
        self.D = 3   # damping coefficient [N/(m/s)]
        self.IMPULSE = 0.05 # impulse when a spike is received [N*s]
        self.MAX_DEFLECTION = 0.2*self.PLATE_SIDE # maximum deflection of the motor from the rest position [m]

        self.reset()

    def reset(self):
        self.motor_pos = np.copy(self.MOTOR_POS_REST) # motor position
        self.motor_v_z = np.zeros(4) # motor velocity (z direction only)

    '''
        *** Motor step ***

        입력: spike를 낸 motor neuron들의 인덱스 리스트
            ex: [0, 2, 5, 7] -> +x 수축, +y 수축, -x 이완, -y 이완
        출력: plate의 normal vector
    '''
    def step(self, spikes):
        # (1) apply impulses from spikes
        for neuron_idx in spikes:
            motor_idx = neuron_idx // 2
            is_contract = (neuron_idx % 2 == 0)
            if is_contract:
                self.motor_v_z[motor_idx] -= self.IMPULSE
            else:
                self.motor_v_z[motor_idx] += self.IMPULSE
        
        # (2) update motor positions using damped oscillator model
        for i in range(self.MOTOR_COUNT):
            # calculate forces
            f_spring = -self.K * (self.motor_pos[i,2] - self.MOTOR_POS_REST[i,2]) # spring force
            f_damp   = -self.D * self.motor_v_z[i] # damping force
            f_total  = f_spring + f_damp

            # update velocity and position
            a = f_total
            self.motor_v_z[i] += a * self.DT
            self.motor_pos[i,2] += self.motor_v_z[i] * self.DT

            # limit maximum deflection
            if self.motor_pos[i,2] > self.MOTOR_POS_REST[i,2] + self.MAX_DEFLECTION:
                self.motor_pos[i,2] = self.MOTOR_POS_REST[i,2] + self.MAX_DEFLECTION
            elif self.motor_pos[i,2] < self.MOTOR_POS_REST[i,2] - self.MAX_DEFLECTION:
                self.motor_pos[i,2] = self.MOTOR_POS_REST[i,2] - self.MAX_DEFLECTION

        # (3) calculate plate normal vector from motor positions
        v1 = self.motor_pos[1] - self.motor_pos[0]
        v2 = self.motor_pos[3] - self.motor_pos[2]
        n = np.cross(v1, v2)
        n /= np.linalg.norm(n)

        return n


class BallSim_Sensor:
    '''
        Sensor neurons
        If the ball passes over the sensor position, it fires a spike.

        무작위로 100개의 센서를 판 위에 배치
        센서는 공이 가까이에 있으면 spike를 내보냄.
        거리에 따라 spike 빈도가 달라짐. (가까울수록 빈도 높음, 3단계로 구분)
    '''
    def __init__(self, N_SENSORS, PLATE_SIDE):
        self.DIST1 = 0.005 # [m]
        self.DIST2 = 0.01 # [m]
        self.DIST3 = 0.02 # [m]
        self.PERIOD1 = 2 # [time steps]
        self.PERIOD2 = 4 # [time steps]
        self.PERIOD3 = 8 # [time steps]
        self.PLATE_SIDE = PLATE_SIDE # [m] the plate is square with this side length

        self.reset_random(N_SENSORS, PLATE_SIDE)

    def reset_random(self, n_sensors, plate_side):
        self.counter = 0 # time step counter. For spike generation at different frequencies
        self.SENSORS_POS = (np.random.rand(n_sensors, 2) - 0.5) * plate_side * 0.8

    '''
        *** Sensor step ***

        입력: 공의 위치 (평면에 대해 projection한 2D 좌표)
        출력: spike를 낸 센서들의 인덱스 리스트 (AER과 비슷한 형식??)
            ex: [0, 3, 5, ..., 97]
    '''
    def step(self, ball_pos_on_plate):
        
        # check if the ball is over any sensor
        dists = np.linalg.norm(self.SENSORS_POS - ball_pos_on_plate, axis=1)
        
        fired_sensors = []
        for i in range(len(self.SENSORS_POS)):
            if dists[i] < self.DIST1:
                if self.counter % self.PERIOD1 == 0:
                    fired_sensors.append(i)
            elif dists[i] < self.DIST2:
                if self.counter % self.PERIOD2 == 0:
                    fired_sensors.append(i)
            elif dists[i] < self.DIST3:
                if self.counter % self.PERIOD3 == 0:
                    fired_sensors.append(i)

        # update counter
        self.counter += 1
        self.counter %= self.PERIOD3

        return fired_sensors


class BallSim(BallSimBase):
    '''
        Ball balancing simulator
        The physical simulation is implemented in the parent class BallSimBase.

        This class implements the input/output interface for SNN-based control.
        (connect with Motor and Sensor)

        class parameters
        * STEPS_PER_SEC: simulation steps per second [s^-1]
        * M: mass of the ball [kg]

        나머지 파라미터는 BallSimBase 클래스에서 default 값으로 초기화됨.
        * M 범위: 0.001 ~ 0.03 [kg]
    '''
    def __init__(self, STEPS_PER_SEC=100, M=0.01, verbose=False):
        # (0) Initialize parent class
        super().__init__(STEPS_PER_SEC=STEPS_PER_SEC, M=M)

        # (1) Initialize Motor and Sensor
        self.motor = BallSim_Motor(STEPS_PER_SEC=STEPS_PER_SEC, PLATE_SIDE=self.PLATE_SIDE)
        self.sensor = BallSim_Sensor(N_SENSORS=100, PLATE_SIDE=self.PLATE_SIDE)

        if verbose:
            print("BallSim: initialized.")
            print(f"self.__dict__:\n{self.__dict__}")

    def reset_random(self):
        super().reset_random()
        self.motor.reset()
        self.sensor.reset_random(n_sensors=100, plate_side=self.PLATE_SIDE)


    def step(self):

        ball_pos_proj = self._get_ball_pos_proj()
        sensor_spike_list = self.sensor.step(ball_pos_proj)

        ## SNN controller logic start ##

        # make random motor spikes for testing
        motor_spike_list = []
        for i in range(self.motor.NEURON_COUNT):
            if np.random.rand() < 0.3:
                motor_spike_list.append(i)
        
        ## SNN controller logic end ##

        self.plate_n = self.motor.step(motor_spike_list)
        super().step()




if __name__ == "__main__":
    sim = BallSim(verbose=True)
    sim.reset_random()

    for _ in range(1000):
        if not sim.isRunning:
            break
        if _ % 10 == 0:
            sim.print_state()
        sim.step()
