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
        self.SCREEN_SIZE = (950, 450)
        self.SIM_SURF_SIZE = (300, 300)

        # initialize pygame
        pygame.init()
        self.screen = pygame.display.set_mode(self.SCREEN_SIZE)
        pygame.display.set_caption("Ball balancing simulation")
        self.clock = pygame.time.Clock()

        # initialize variables related to simulation visualization
        self.sim_surf = pygame.Surface(self.SIM_SURF_SIZE)
        self.sensor_surf = pygame.Surface(self.SIM_SURF_SIZE)
        self.hidden_motor_surf = pygame.Surface(self.SIM_SURF_SIZE)


    def _get_simsurf_coord(self, pos, SIM_SCALE):
        tmp = pos[:2] * SIM_SCALE + np.array(self.SIM_SURF_SIZE) / 2
        return np.array([tmp[0], tmp[1], pos[2]])


    ############### SURFACE #1: Simulation Visualization ###############

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


    def _draw_ball(self, ballsim: BallSim, SIM_SCALE):
        ball_color = (255, 100, 100)

        coord_2d = self._get_simsurf_coord(ballsim.ball_pos, SIM_SCALE)[:2]
        radius = ballsim.R * SIM_SCALE

        # draw ball
        pygame.draw.circle(self.sim_surf, ball_color, coord_2d, radius)

    def _draw_sim_surf(self, ballsim: BallSim, SIM_SCALE):
        self.sim_surf.fill((0,0,0))  # clear surface

        self._draw_plate(ballsim, SIM_SCALE)
        self._draw_ball(ballsim, SIM_SCALE)


    ############### SURFACE #2: Sensor Spike Visualization ###############
    def _draw_sensor_surf(self, ballsim: BallSim, SIM_SCALE, sensory_spikes):
        s_pos = ballsim.sensor.get_sensors_pos()
        s_spike = [False] * len(s_pos)
        if sensory_spikes is not None:
            for i in sensory_spikes:
                s_spike[i] = True
        
        self.sensor_surf.fill((0,0,0))  # clear surface

        SQUARE_SIZE = 0.8 * self.SIM_SURF_SIZE[0]
        OFFSET = self.SIM_SURF_SIZE[0] * 0.1
        pygame.draw.rect(self.sensor_surf, (50,50,50), (OFFSET, OFFSET, SQUARE_SIZE, SQUARE_SIZE))
        
        for i in range(len(s_pos)):
            coord_2d = s_pos[i] * SIM_SCALE + np.array(self.SIM_SURF_SIZE) / 2
            color = (255,100,100) if s_spike[i] else (100,100,100)
            pygame.draw.circle(self.sensor_surf, color, coord_2d, 5)


    ############### SURFACE #3: Hidden and Motor Spike Visualization ###############
    def _draw_hidden_motor_surf(self, hidden_motor_states):
        hidden_state = hidden_motor_states[0]
        motor_state = hidden_motor_states[1]
        hidden_spikes = hidden_motor_states[2]
        motor_spikes = hidden_motor_states[3]

        self.hidden_motor_surf.fill((30,30,30))  # clear surface
        font = pygame.font.SysFont(None, 22)

        img = font.render(f"Hidden", True, (100, 100, 100))
        self.hidden_motor_surf.blit(img, (20, 20))
        img = font.render(f"Motor", True, (100, 100, 100))
        self.hidden_motor_surf.blit(img, (130, 20))


        # Hidden neurons
        N_HIDDEN = 4
        for i in range(N_HIDDEN):
            x = 20
            y = 60 + (200) / (N_HIDDEN - 1) * i

            color1 = (80, 40, 80)
            color2 = (200, 100, 200)  # activated color
            if hidden_spikes is None:
                color = color1
            elif i in hidden_spikes:
                color = color2
            else:
                color = color1
            pygame.draw.circle(self.hidden_motor_surf, color, (x, y), 8)

            img = font.render(f"{hidden_state[i,0]:0.2f}mV", True, (255,255,255))
            self.hidden_motor_surf.blit(img, (x + 20, y - 10))

        # Motor neurons
        motor_label = [ "Excit +x",
                        "Excit -x",
                        "Excit +y",
                        "Excit -y",
                        "Inhib +x",
                        "Inhib -x",
                        "Inhib +y",
                        "Inhib -y"]
        N_MOTORS = 8
        for i in range(N_MOTORS):
            x = 130
            y = 60 + (200) / (N_HIDDEN - 1) * i

            color1 = (50, 100, 50)
            color2 = (100, 200, 100)  # activated color
            if motor_spikes is None:
                color = color1
            elif i in motor_spikes:
                color = color2
            else:
                color = color1
            pygame.draw.circle(self.hidden_motor_surf, color, (x, y), 8)
            
            # draw motor label
            img = font.render(motor_label[i], True, color)
            self.hidden_motor_surf.blit(img, (x + 90, y - 10))
            img = font.render(f"{motor_state[i,0]:0.2f}mV", True, (255,255,255))
            self.hidden_motor_surf.blit(img, (x + 20, y - 10))


    ############### Draw texts and aggregate the surfaces ###############

    def _draw_texts(self, ballsim: BallSim, num_episodes):
        X1 = 10
        X2 = 320
        X3 = 630

        font = pygame.font.SysFont(None, 24)
        img = font.render(f"Ball-Plate System", True, (255,255,255))
        self.screen.blit(img, (X1,20))
        img = font.render(f"Sensor Spikes", True, (255,255,255))
        self.screen.blit(img, (X2, 20))
        img = font.render(f"Hidden & Motor Spikes", True, (255,255,255))
        self.screen.blit(img, (X3, 20))

        img = font.render(f"Simulation Time: {ballsim.time:.2f} s", True, (255,255,255))
        self.screen.blit(img, (X1, 360))
        img = font.render(f"Steps: {ballsim.num_steps}", True, (255,255,255))
        self.screen.blit(img, (X1, 380))
        img = font.render(f"Episode #{num_episodes}", True, (255,255,255))
        self.screen.blit(img, (X1, 400))

    def _draw_surfs_to_screen(self):
        X1 = 10
        X2 = 320
        X3 = 630

        self.screen.blit(self.sim_surf, (X1, 50))
        self.screen.blit(self.sensor_surf, (X2, 50))
        self.screen.blit(self.hidden_motor_surf, (X3, 50))


    ############### MAIN DRAWING & INPUT HANDLING ###############

    def draw(self, ballsim: BallSim, num_episodes, sensory_spikes, hidden_motor_states=[None, None, None, None]):
        self.screen.fill((30, 30, 30))  # clear screen
        SIM_SCALE = self.SIM_SURF_SIZE[0] / ballsim.PLATE_SIDE * 0.8
        
        self._draw_sim_surf(ballsim, SIM_SCALE)
        self._draw_sensor_surf(ballsim, SIM_SCALE, sensory_spikes)
        self._draw_hidden_motor_surf(hidden_motor_states)

        self._draw_surfs_to_screen()
        self._draw_texts(ballsim, num_episodes)

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