import math
import pymunk
import appEngine
from appEngine import actor


class Avatar(actor.PhysicalActor):
    def __init__(self, states, startState, batch=None, mass=5, moment=pymunk.inf):
        super(Avatar, self).__init__(states, startState, batch, mass, moment)
        
    def setFocus(self, x, y):
        self.focusX = x
        self.focusY = y
        
    def update(self, dt):
        ''' calculate screen coords '''
        # compensate for pyglet/pymunk anchors
        if hasattr(self, 'get_max_width'):
            avatarWidth = self.get_max_width()/4 #TODO divided into # of rows
            avatarHeight = self.get_max_height()/4 #TODO divied into # of columns
        else:
            avatarWidth = self.width/4
            avatarHeight = self.height/4
        position = self.body.position
        focusX = self.focusX()
        focusY = self.focusY()
        self.x = position[0] + avatarWidth + focusX
        self.y = position[1] + avatarHeight + focusY
        super(Avatar, self).update(dt)
