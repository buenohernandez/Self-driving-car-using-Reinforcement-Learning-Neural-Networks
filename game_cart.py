# -*- coding: utf-8 -*-
import pygame
import os
from math import sin, cos, pi, radians, fabs, sqrt, exp, atan
import time
from time import sleep
from random import randint
import numpy as np
from math import ceil
import collections

os.chdir(os.getcwd())

pygame.init()

div = 2
screen = pygame.display.set_mode((1200//div, 800//div))
clock = pygame.time.Clock()
car  = pygame.image.load('car.png').convert_alpha()
car = pygame.transform.scale(car, (48//div, 48//div))
course = pygame.image.load('course.png').convert()
course = pygame.transform.scale(course, (1200//div, 800//div))

RED = (255, 0, 0)
BLACK = (0, 0, 0)
TRACK = (163, 171, 160, 255)
DONE = [[126 // div, 400// div], [260// div, 400 // div], [126// div, 440 // div], [260 // div, 440 // div]]

pygame.font.init() 
myfont = pygame.font.SysFont('Comic Sans MS', 30)


def rot_center(image, angle):  
    orig_rect = image.get_rect()
    rot_image = pygame.transform.rotate(image, angle)
    rot_rect = orig_rect.copy()
    rot_rect.center = rot_image.get_rect().center
    rot_image = rot_image.subsurface(rot_rect).copy()    
    return rot_image
   

class Car:
    def __init__(self):    
        self.x = 168//div
        self.y = 450//div
        self.angle = 0
        self.accel = 0
        self.max_accel = 2
        self.accel_step = 0.1
        self.speed = 100
        self.steer_angle = 0
        self.max_steer_angle = 4
        self.act_labels = ["ACCEL", "LEFT", "RIGHT"]
        self.actions = [range(len(self.act_labels))]
        self.lag = 0.01
        self.times = 0
        self.sensors_length = 50
        self.sensors_angles = range(-30, 31, 60)
        self.sensors = [[0,0,0,0]] * len(self.sensors_angles)
        self.dist = [[0, 0]] * len(self.sensors_angles)
        self.sens_lens = [0] * len(self.sensors_angles)
        self.sens_thres = self.sensors_length
        self.act_size = len(self.act_labels)
        pre_size = np.hstack(self.sens_lens)
        self.state_size = pre_size.reshape(1, pre_size.size).size
        self.pix = TRACK
        self.sp = 0
        self.last_act = "BRAKE"
        

    def check_finish_line(self, x, y):    
        v0 = fabs(DONE[0][1] - y)
        v1 = fabs(DONE[1][1] - y)
        v2 = fabs(DONE[2][1] - y)
        v3 = fabs(DONE[3][1] - y)
        v00 = fabs(DONE[0][1] - DONE[2][1])
        h0 = fabs(DONE[0][0] - x)
        h1 = fabs(DONE[1][0] - x)
        h2 = fabs(DONE[2][0] - x)
        h3 = fabs(DONE[3][0] - x)
        h00 = fabs(DONE[0][0] - DONE[1][0])
        #for i in DONE: pygame.draw.circle(screen, RED,[i[0], i[1]], 1)
        #pygame.draw.rect(screen, RED, (DONE[0], [a-b for a,b in zip(DONE[3], DONE[0])]))
        
        if v0 <= v00 and v2 <= v00  \
        and v1 <= v00 and v3 <= v00 \
        and h0 <= h00 and h1 <= h00 \
        and h2 <= h00 and h3 <= h00:    
            return True     
               
        return False


    def bound_check(self):    
        x = int(self.x) + 24//div
        y = int(self.y) + 24//div        
        self.pix  = course.get_at((x,y))
        self.sp = sum([abs(TRACK[z] - self.pix[z]) for z in range(len(TRACK))])
        
        if self.check_finish_line(x, y):    return 10, True
            
        if self.sp > 50:
            self.__init__()
            return -10, False
            
        if np.count_nonzero(np.array(self.sens_lens)) == 0: return 0, False
        else:   return - round(np.count_nonzero(np.array(self.sens_lens)) / float(len(self.sensors)), 2), False


    def sensors_calc(self, pos, show = True):
    
        for i in range(len(self.sensors_angles)):
            s = sin(radians(self.angle + self.sensors_angles[i]))
            c = cos(radians(self.angle + self.sensors_angles[i]))
            self.sensors[i] = [pos[0] + 24//div, pos[1] + 24//div, pos[0] + 24//div + int((self.sensors_length) * s), int(pos[1] + 24//div + (self.sensors_length) * c)]
            
        self.dist = [[0, 0]] * len(self.sensors_angles)
        self.sens_lens = [0] * len(self.sensors_angles)
        
        for j in range(len(self.sensors_angles)):
            self.vec_x = np.linspace(self.sensors[j][0], self.sensors[j][2], self.sensors_length)
            
            if (self.vec_x[0] - self.vec_x[-1]) < 0: self.vec_x.sort()
            
            self.vec_y = np.linspace(self.sensors[j][1], self.sensors[j][3], self.sensors_length)
            
            if (self.vec_y[0] - self.vec_y[-1]) < 0: self.vec_y.sort()
            
            for i in range(self.sensors_length):
                self.pix2  = course.get_at((int(self.vec_x[i]), int(self.vec_y[i])))
                self.sp2 = sum([abs(TRACK[x] - self.pix2[x]) for x in range(len(TRACK))])
                
                if self.sp2 > 50 and not self.check_finish_line(int(self.vec_x[i]), int(self.vec_y[i])) :
                    self.dist[j] = [int(self.vec_x[i]), int(self.vec_y[i])]
                    self.sens_lens[j] = 1
                    
                    if show:
                        pygame.draw.circle(screen, RED,[int(self.vec_x[i]), int(self.vec_y[i])], 1)
                    break
                    
        if show:
            for i in range(len(self.sensors_angles)):
                pygame.draw.line(screen,RED,(self.sensors[i][0],
                                             self.sensors[i][1]),
                                             (self.sensors[i][2],
                                             self.sensors[i][3]))


    def run(self, action = "BRAKE", lag = None):
    
        if lag == None: lag = self.lag
        
        pygame.event.get()
        self.accel = round(self.accel, 2)
        
        try:
            act = self.act_labels[action]
        except:
            act = action
            
        self.last_act = act
        
        if self.accel != 0:
        
            if act is "LEFT":
                if self.steer_angle < self.max_steer_angle: self.steer_angle  += 1
                
            elif act is "RIGHT":
                if self.steer_angle > -self.max_steer_angle: self.steer_angle  -= 1
                
            else:
                if self.steer_angle > 0: self.steer_angle -= 1
                elif self.steer_angle < 0: self.steer_angle += 1
                
            self.angle += self.steer_angle
            
        if act == "ACCEL" or act == "RIGHT" or act == "LEFT":
        
            if self.accel < self.max_accel:
                self.accel += self.accel_step
                
        elif act == "BRAKE":
            if self.accel < 0:
                self.accel += self.accel_step
            elif self.accel > 0:
                self.accel -= self.accel_step
                
        else:
            if self.accel > 0:
                self.accel -= self.accel_step
            elif self.accel < 0:
                self.accel += self.accel_step
            else:
                self.accel = 0
                                
        self.x += sin(radians(self.angle)) * self.accel * self.speed * lag
        self.y += cos(radians(self.angle)) * self.accel * self.speed * lag
        screen.blit(course, (0,0))
        pos = [int(self.x), int(self.y)]
        self.sensors_calc(pos)
        reward, done = self.bound_check()
        car_ = rot_center(car, self.angle)
        screen.blit(car_, (pos))
        #textsurface = myfont.render(str(reward) + " " + act, False, (0, 0, 0))
        #screen.blit(textsurface,(0,0))
        pygame.display.flip()
        x = int(self.x + 24//div)
        y = int(self.y + 24//div)
        s = sin(radians(self.angle)) * 100
        c = cos(radians(self.angle)) * 100
        pre = np.hstack(self.sens_lens)
        pre = pre.reshape(1, pre.size)        
        return pre, reward, done


if __name__ == "__main__":
    env = Car()
    done = False
    lag = 0.01
        
    while not done:    
        t = time.clock()
        act = "BRAKE"
        pressed = pygame.key.get_pressed()
        
        if pressed[pygame.K_UP]: act = 0
        if pressed[pygame.K_DOWN]: act = "BRAKE"
        if pressed[pygame.K_RIGHT]: act = 2
        if pressed[pygame.K_LEFT]: act = 1
        if pressed[pygame.K_q]: pygame.quit()

        state, reward, done = env.run(act, lag/2)
        print(state,reward, done)
        clock.tick(60)
        lag = time.clock() - t
