'''

'''
import math
import pyglet
import pyglet.sprite as sprite
import pymunk
import appEngine
from appEngine import rLoader

def centerImgAnchor(img):
    img.anchor_x = img.width // 2
    img.anchor_y = img.height // 2


class Actor(object):
    Scene = None

    def update(self, dt):
        pass

    def addedToScene(self, scene):
        self.scene = scene
        
    def removedFromScene(self, scene):
        self.scene = None
    
class Direction(object):
    LEFT = 1
    RIGHT = 2
class State(object):
    STAND = 1
    WALK = 2
    def __init__(self, type, left, right=None):
        self.type = type
        self.left = left
        if right is not None:
            self.right = right
        else:
            self.right = left
    def direction(self, d):
        if d == Direction.LEFT: 
            return self.left
        elif d == Direction.RIGHT:
            return self.right
class VisualActor(sprite.Sprite, Actor):
    def __init__(self, states, startState, batch=None):
        self.states = states
        self.direction = Direction.RIGHT
        self.state = states[startState]
        img = states[startState].direction(self.direction)
        super(VisualActor, self).__init__(img, batch=batch)
        
    def update(self, dt):
        pass
        
    def unload(self):
        self.delete()
        
    def addedToScene(self, scene):
        super(VisualActor, self).addedToScene(scene)
        self.batch = scene.batch
        
    def setState(self, state):
        if state != self.state.type:
            self.state = self.states[state]
            self.image = self.state.direction(self.direction)
        
    def setFacing(self, direction):
        if self.direction != direction:
            self.direction = direction
            self.image = self.state.direction(self.direction)
        
    def loadAnimation(self, imageName, rows, columns, animFreq, loop=False, centerAnchor=False):
        animImg = rLoader.image(imageName)
        tex = animImg.get_texture()
        animGrid = pyglet.image.ImageGrid(tex, rows, columns)
        animGrid = animGrid.get_texture_sequence()
        if centerAnchor == True:
            map(centerImgAnchor, animGrid)
        anim = pyglet.image.Animation.from_image_sequence(animGrid,
                animFreq, loop=loop)
        return anim
            
                
# PhysicalActor - Comprises a pymunk body and the common
# calculations..
#            
class PhysicalActor(VisualActor):
    def __init__(self, states, startState, batch=None, mass=5, moment=pymunk.inf):
        super(PhysicalActor, self).__init__(states, startState, batch=batch)
        self.body = pymunk.Body(mass, moment)
        
    def unload():
        super(PhysicalActor, self).unload()
        
    def update(self, dt):
        self.rotation = math.degrees(self.body.angle)
        
    def addedToScene(self, scene):
        super(PhysicalActor, self).addedToScene(scene)
        if hasattr(scene, 'space'):
            scene.space.add(self.body)


class CompositeActor():
    pass
    
class EffectActor():
    pass
    
    
    
    
    
    
    
