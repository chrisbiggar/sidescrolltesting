import math
import pyglet
from pyglet import *
import pymunk
from pymunk.vec2d import Vec2d
import appEngine
from appEngine import rLoader
from appEngine import actor
from appEngine.actor import centerImgAnchor
from appEngine.entity import Entity

class State(actor.State):
    NORMAL = 10

class Star(Entity):
    def __init__(self, focusX, focusY, batch=None):
        states = dict()
        star = rLoader.image("entities/star.png")
        centerImgAnchor(star)
        states[State.NORMAL] = State(State.NORMAL, star)
        super(Star, self).__init__(focusX, focusY, states, State.NORMAL, batch)
        self.initPhysics()
        
    def initPhysics(self):
        self.shape = pymunk.Circle(self.body, 20)
        self.shape.collisionType = 1 #TODO (magic #)
        self.shape.elasticity = 1.
        
    def addedToScene(self, scene):
        super(Star, self).addedToScene(scene)
        scene.space.add(self.shape)
        
    def setposition(self,x,y):
        self.body.position = x,y
        
    def update(self, dt):
        super(Star, self).update(dt)
        
