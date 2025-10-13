'''
    Ball balancing simulation visualizer (pygame-based)
    
    최초작성자: 김연준
'''

from ballsim import BallSim
from ballsimbase import BallSimBase
import numpy as np
import pygame

class BallSimVis:
    def __init__(self, ballsim:BallSim, verbose=False):
        self.ballsim = ballsim
        self.screen_size = (400, 400)
        self.verbose = verbose

        # initialize pygame
        pygame.init()
        self.screen = pygame.display.set_mode(self.screen_size)
        pygame.display.set_caption("Ball balancing simulation")
        self.clock = pygame.time.Clock()

        # initialize variables related to simulation visualization
        self.sim_size = (300, 300)
        self.sim_surf = pygame.Surface(self.sim_size)
        self.sim_scale = self.sim_size[0] / self.ballsim.PLATE_SIDE * 0.8

        print("BallSimVis: initialized.")
        if verbose:
            print(f"self.__dict__:\n{self.__dict__}")


    def _get_simsurf_coord(self, pos):
        tmp = pos[:2] * self.sim_scale + np.array(self.sim_size) / 2
        return np.array([tmp[0], tmp[1], pos[2]])

    def _draw_plate(self):
        thickness = 4

        # plate corners in 3D
        plate_vertices = self.ballsim._get_plate_vertices()
        coords = [self._get_simsurf_coord(v) for v in plate_vertices]

        # draw plate: draw multiple subdivided polygons to indicate height(z value)
        num_subdiv = 15
        v1 = (coords[1] - coords[0]) / num_subdiv
        v2 = (coords[2] - coords[0]) / num_subdiv
        for i in range(num_subdiv):
            for j in range(num_subdiv):
                subdiv_coords = [
                    coords[0] + v1*i + v2*j,
                    coords[0] + v1*(i+1) + v2*j,
                    coords[0] + v1*(i+1) + v2*(j+1),
                    coords[0] + v1*i + v2*(j+1)
                ]
                subdiv_coords_2d = [x[:2] for x in subdiv_coords]
                subdiv_z = (subdiv_coords[0][2] + subdiv_coords[2][2]) / 2

                c = min(max(int(150 + 20 * (subdiv_z / self.ballsim.R)), 0), 255)
                subdiv_color = (c, c, c)
                
                pygame.draw.polygon(self.sim_surf, 
                                    subdiv_color,
                                    subdiv_coords_2d, 0)

    def _draw_ball(self):
        ball_color = (255, 100, 100)

        coord_2d = self._get_simsurf_coord(self.ballsim.ball_pos)[:2]
        radius = self.ballsim.R * self.sim_scale

        # draw ball
        pygame.draw.circle(self.sim_surf, ball_color, coord_2d, radius)

    # draw the plate and ball in simulation, viewed from above(z-axis)
    def _draw_simulation(self):
        self.sim_surf.fill((0,0,0))  # clear surface
        self._draw_plate()
        self._draw_ball()
        self.screen.blit(self.sim_surf,
                         ((self.screen_size[0]-self.sim_size[0])//2,
                          (self.screen_size[1]-self.sim_size[1])//2))

    def reset_random(self):
        print("BallSimVis: simulation reset with random initial values.")
        self.ballsim.reset_random()

    def step(self):
        # simulation step
        self.ballsim.step()

        # draw
        self.screen.fill((50, 50, 50))  # clear screen
        self._draw_simulation()
        pygame.display.flip()

        self.clock.tick(30)  # limit to 30 FPS

    def run(self):
        print("BallSimVis: running simulation...")

        while True: # main loop
            # (1) handle input events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r:
                        self.reset_random()
                    if event.key == pygame.K_w:
                        self.ballsim.set_plate_n(self.ballsim.plate_n + np.array([0, -0.1, 0]))
                    if event.key == pygame.K_s:
                        self.ballsim.set_plate_n(self.ballsim.plate_n + np.array([0, 0.1, 0]))
                    if event.key == pygame.K_a:
                        self.ballsim.set_plate_n(self.ballsim.plate_n + np.array([-0.1, 0, 0]))
                    if event.key == pygame.K_d:
                        self.ballsim.set_plate_n(self.ballsim.plate_n + np.array([0.1, 0, 0]))

            # (2) simulation step
            self.step()

            # (3) check if simulation is still running
            if not self.ballsim.isRunning:
                break
        
        print("BallSimVis: simulation ended.")


if __name__ == "__main__":
    sim = BallSim(verbose=False)
    vis = BallSimVis(ballsim=sim, verbose=False)

    while True:
        vis.reset_random()
        vis.run()