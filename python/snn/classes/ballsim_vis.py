'''
    Ball balancing simulation visualizer (pygame-based)
    
    최초작성자: 김연준
'''

from classes.ballsim import BallSim
import numpy as np
import pygame

class BallSimVis:
    def __init__(self, VIS_FPS):
        self.VIS_FPS = VIS_FPS
        self.SCREEN_SIZE = (700, 400)
        self.SIM_SURF_SIZE = (300, 300)

        # initialize pygame
        pygame.init()
        self.screen = pygame.display.set_mode(self.SCREEN_SIZE)
        pygame.display.set_caption("Ball balancing simulation")
        self.clock = pygame.time.Clock()

        # initialize variables related to simulation visualization
        self.sim_surf = pygame.Surface(self.SIM_SURF_SIZE)
        self.sensor_surf = pygame.Surface(self.SIM_SURF_SIZE)


    def _get_simsurf_coord(self, pos, SIM_SCALE):
        tmp = pos[:2] * SIM_SCALE + np.array(self.SIM_SURF_SIZE) / 2
        return np.array([tmp[0], tmp[1], pos[2]])

    ############### SONSOR SPIKE VISUALIZATION ###############
    def _draw_sensor_surf(self, ballsim: BallSim, SIM_SCALE):
        s_pos = ballsim.sensor.get_sensors_pos()
        s_spike = [False] * len(s_pos)
        for i in ballsim.get_sensory_spikes():
            s_spike[i] = True

        self.sensor_surf.fill((0,0,0))  # clear surface

        SQUARE_SIZE = 0.8 * self.SIM_SURF_SIZE[0]
        OFFSET = self.SIM_SURF_SIZE[0] * 0.1
        pygame.draw.rect(self.sensor_surf, (50,50,50), (OFFSET, OFFSET, SQUARE_SIZE, SQUARE_SIZE))
        
        for i in range(len(s_pos)):
            coord_2d = s_pos[i] * SIM_SCALE + np.array(self.SIM_SURF_SIZE) / 2
            color = (255,100,100) if s_spike[i] else (100,100,100)
            pygame.draw.circle(self.sensor_surf, color, coord_2d, 5)


    ############### SIMULATION MAIN SURFACE DRAWING ###############

    def _draw_plate(self, ballsim: BallSim, SIM_SCALE):
        # plate corners in 3D
        plate_vertices = ballsim._get_plate_vertices()
        coords = [self._get_simsurf_coord(v, SIM_SCALE) \
                                for v in plate_vertices]

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

                c = min(max(int(150 + 20 * (subdiv_z / ballsim.R)), 0), 255)
                subdiv_color = (c, c, c)
                
                pygame.draw.polygon(self.sim_surf, 
                                    subdiv_color,
                                    subdiv_coords_2d, 0)

    def _draw_texts(self, ballsim: BallSim):
        font = pygame.font.SysFont(None, 24)
        img = font.render(f"Simulation Time: {ballsim.time:.2f} s", True, (255,255,255))
        self.screen.blit(img, (10, 10))
        img = font.render(f"Steps: {ballsim.num_steps}", True, (255,255,255))
        self.screen.blit(img, (10, 30))
        img = font.render(f"Sensor spikes fired: {len(ballsim.get_sensory_spikes())}", True, (255,255,255))
        self.screen.blit(img, (340, 20))


    def _draw_ball(self, ballsim: BallSim, SIM_SCALE):
        ball_color = (255, 100, 100)

        coord_2d = self._get_simsurf_coord(ballsim.ball_pos, SIM_SCALE)[:2]
        radius = ballsim.R * SIM_SCALE

        # draw ball
        pygame.draw.circle(self.sim_surf, ball_color, coord_2d, radius)



    ############### MAIN DRAWING & INPUT HANDLING ###############

    def draw(self, ballsim: BallSim):
        self.screen.fill((50, 50, 50))  # clear screen
        self.sim_surf.fill((0,0,0))  # clear surface

        SIM_SCALE = self.SIM_SURF_SIZE[0] / ballsim.PLATE_SIDE * 0.8
        self._draw_plate(ballsim, SIM_SCALE)
        self._draw_ball(ballsim, SIM_SCALE)
        self._draw_texts(ballsim)
        self.screen.blit(self.sim_surf, (20, 50))

        self._draw_sensor_surf(ballsim, SIM_SCALE)
        self.screen.blit(self.sensor_surf, (340, 50))

        pygame.display.flip()
        self.clock.tick(50)  # limit to 50 FPS

    def get_input(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit"
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    return "reset"
        
        return None
    
    def close(self):
        pygame.quit()