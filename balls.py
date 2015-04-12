#!/usr/bin/env python
# coding: utf

import pygame
import random

import itertools
import numpy as np
import math

SIZE = 640, 480

def intn(*arg):
    return map(int,arg)

def Init(sz):
    '''Turn PyGame on'''
    global screen, screenrect
    pygame.init()
    screen = pygame.display.set_mode(sz)
    screenrect = screen.get_rect()

class GameMode:
    '''Basic game mode class'''
    def __init__(self):
        self.background = pygame.Color("black")

    def Events(self,event):
        '''Event parser'''
        pass

    def Draw(self, screen):
        screen.fill(self.background)

    def Logic(self, screen):
        '''What to calculate'''
        pass

    def Leave(self):
        '''What to do when leaving this mode'''
        pass

    def Init(self):
        '''What to do when entering this mode'''
        pass

class Ball:
    '''Simple ball class'''

    def __init__(self, filename, pos = (0.0, 0.0), speed = (0.0, 0.0)):
        '''Create a ball from image'''
        self.fname = filename
        self.surface = pygame.image.load(filename)
        self.rect = self.surface.get_rect()
        self.radius = self.rect.height / 2
        self.speed = speed
        self.gravitation = 9.8
        self.pos = pos
        self.newpos = pos
        self.active = True


    def draw(self, surface):
        surface.blit(self.surface, self.rect)

    def action(self):
        '''Proceed some action'''
        if self.active:
            self.pos = self.pos[0]+self.speed[0], self.pos[1]+self.speed[1]

    def logic(self, surface):
        x,y = self.pos
        dx, dy = self.speed
        if x < self.rect.width/2:
            x = self.rect.width/2
            dx = -dx
        elif x > surface.get_width() - self.rect.width/2:
            x = surface.get_width() - self.rect.width/2
            dx = -dx
        if y < self.rect.height/2:
            y = self.rect.height/2
            dy = -dy
        elif y > surface.get_height() - self.rect.height/2:
            y = surface.get_height() - self.rect.height/2
            dy = -dy
        self.pos = x,y
        self.speed = dx, dy + self.gravitation
        self.rect.center = intn(*self.pos)

class RotatingBall(Ball):
    """ Rotating ball """
    def __init__(self, filename, pos = (0.0, 0.0), speed = (0.0, 0.0), speed_angular = 0.0, scale = 1.0):
        """
        Rotating ball
        :param filename: path to file with sprite
        :param pos: initial position
        :param speed: initial speed
        :param speed_angular: initial angular speed degrees per frame
        :return:
        """
        Ball.__init__(self, filename, pos, speed)
        self.scale = scale
        self.speed_angular = speed_angular
        self.original_surface = self.surface
        self.angle = 0
        self.radius *= scale

    def logic(self, surface):
        if self.active:
            self.angle = RotatingBall.limit(self.angle + self.speed_angular, 360)
            self.surface = pygame.transform.rotozoom(self.original_surface, self.angle, self.scale)
            self.rect = self.surface.get_rect()
        Ball.logic(self, surface)

    @staticmethod
    def limit(value, limit):
        """
        Normalize value to range [0, limit)
        :param value: value to normalize
        :param limit: positive limit
        :return: value in range [0, limit)
        """
        return value - limit * int(value / limit)




class Universe:
    '''Game universe'''

    def __init__(self, msec, tickevent = pygame.USEREVENT):
        '''Run a universe with msec tick'''
        self.msec = msec
        self.tickevent = tickevent

    def Start(self):
        '''Start running'''
        pygame.time.set_timer(self.tickevent, self.msec)

    def Finish(self):
        '''Shut down an universe'''
        pygame.time.set_timer(self.tickevent, 0)

class GameWithObjects(GameMode):

    def __init__(self, objects=[]):
        GameMode.__init__(self)
        self.objects = objects

    def locate(self, pos):
        return [obj for obj in self.objects if obj.rect.collidepoint(pos)]

    def Events(self, event):
        GameMode.Events(self, event)
        if event.type == Game.tickevent:
            for obj in self.objects:
                obj.action()

    def Logic(self, surface):
        GameMode.Logic(self, surface)
        for obj in self.objects:
            obj.logic(surface)

        active_objects = filter(lambda obj: obj.active, self.objects)
        for pair in itertools.combinations(active_objects, 2):
            collision = self.collision_detect(*pair)
            if collision:
                for n, ball in enumerate(pair):
                    ball.pos = collision['position'][n]
                    speed = collision['speed'][n]
                    ball.speed = speed[0] * ball.elasticity, speed[1] * ball.elasticity


    def Draw(self, surface):
        GameMode.Draw(self, surface)
        for obj in self.objects:
            obj.draw(surface)


    @staticmethod
    def collision_detect(ball_a, ball_b):
        norm = np.linalg.norm
        a = np.array(ball_a.pos)
        b = np.array(ball_b.pos)
        va = np.array(ball_a.speed)
        vb = np.array(ball_b.speed)
        v = va - vb
        c = b - a
        v_norm = norm(v)
        if norm(c) > (v_norm + ball_a.radius + ball_b.radius):
            return None
        if np.dot(c, v) <= 0:
            return None
        n = v / v_norm
        d = np.dot(n, c)
        f_square = norm(c)**2 - d**2
        sq_distance_smallest = (ball_a.radius + ball_b.radius) ** 2
        if f_square > sq_distance_smallest:
            return None
        distance = d - math.sqrt(sq_distance_smallest - f_square)
        delta = distance / v_norm
        collision_a = a + va * delta
        collision_b = b + vb * delta
        collision_distance = collision_b - collision_a
        collision_c = collision_distance / norm(collision_distance)
        speed_a = - collision_c * norm(va)
        speed_b = collision_c * norm(vb)
        return {
            'delta': delta,
            'position': (tuple(collision_a), tuple(collision_b)),
            'speed': (tuple(speed_a), tuple(speed_b))
        }

class GameWithDnD(GameWithObjects):

    def __init__(self, *argp, **argn):
        GameWithObjects.__init__(self, *argp, **argn)
        self.oldpos = 0,0
        self.drag = None

    def Events(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            click = self.locate(event.pos)
            if click:
                self.drag = click[0]
                self.drag.active = False
                self.oldpos = event.pos
        elif event.type == pygame.MOUSEMOTION and event.buttons[0]:
                if self.drag:
                    self.drag.pos = event.pos
                    self.drag.speed = event.rel
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1 and self.drag:
            self.drag.active = True
            self.drag = None
        GameWithObjects.Events(self, event)

Init(SIZE)
Game = Universe(50)

Run = GameWithDnD()
for i in xrange(5):
    x, y = random.randrange(screenrect.w), random.randrange(screenrect.h)
    dx, dy = 1+random.random()*5, 1+random.random()*5
    #Run.objects.append(Ball("ball.gif",(x,y),(dx,dy)))
    angular = 5 * (random.random() - 0.5)
    scale = random.random() + 0.5
    Run.objects.append(RotatingBall("ball.gif",(x,y),(dx,dy), speed_angular=angular, scale=scale))


Game.Start()
Run.Init()
again = True
while again:
    event = pygame.event.wait()
    if event.type == pygame.QUIT:
        again = False
    Run.Events(event)
    Run.Logic(screen)
    Run.Draw(screen)
    pygame.display.flip()
Game.Finish()
pygame.quit()
