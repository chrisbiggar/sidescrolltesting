import math
import pymunk
import appEngine
from appEngine import actor
from appEngine import rLoader


class Entity(actor.PhysicalActor):
    def __init__(self, focusX, focusY, states, startState, batch=None, mass=5, moment=pymunk.inf):
        super(Entity, self).__init__(states, startState, batch, mass, moment)
        self.focusX = focusX
        self.focusY = focusY
        
    def update(self, dt):
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
        super(Entity, self).update(dt)
        
        
def parseModpaths():
    file = rLoader.file("entities/modpaths")
    paths = dict()
    for line in file:
        parts = line.partition(" = ")
        paths[parts[0]] = parts[2]
    return paths
    
    
def loadClass(paths, name):
    def import_class(cl):
        d = cl.rfind(".")
        classname = cl[d+1:len(cl)]
        m = __import__(cl[0:d], globals(), locals(), [classname])
        return getattr(m, classname)
    classPath = paths[name].strip()
    klass = import_class(classPath)
    return klass
