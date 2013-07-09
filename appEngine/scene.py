'''
Scene Management
'''
import math
import pyglet
from pyglet import window
from pyglet.gl import *
import pymunk
import appEngine
from appEngine import rLoader
from appEngine.director import Director
import appEngine.scenegraph as scenegraph
from appEngine.scenegraph import SceneGraph
from appEngine import entity as entity


class DuplicateActor(Exception): """actor is already in the world"""
class Scene(window.key.KeyStateHandler, pyglet.event.EventDispatcher):
    def __init__(self, name, viewport):
        self.loaded = False
        self.name = name
        self.batch = pyglet.graphics.Batch()
        self.foregroundGroup = pyglet.graphics.Group()
        self.actors = set()
        self.viewport = viewport
    
    def load(self):
        self.loaded = True

        
    def unload(self, keepState=False):
        for actor in self.actors:
            actor.unload()
            
            
    def reload(self):
        self.graph.reload()
        

    def addActor(self, actor):
        if actor in self.actors:
            raise DuplicateActor("Actor is already in world")
        else:
            self.actors.add(actor)
            actor.addedToScene(self)


    def hasActor(self, actor):
        return actor in self.actors


    def removeActor(self, actor):
        self.actors.remove(actor)


    def clearActors(self):
        self.actors = set()


    def update(self, dt):
        for actor in self.actors:
            actor.update(dt)
            
    
class OrientedCamera(object):
    def __init__(self, scene, xThres=0, yThres=0):
        self.scene = scene
        self.xThres = xThres
        self.yThres = yThres
        
    def update(self):
        avatar = self.scene.avatar
        sceneWidth = self.scene.graph.width
        sceneHeight = self.scene.graph.height
        viewportWidth = self.scene.viewport[0]
        viewportHeight = self.scene.viewport[1]
        
        position = avatar.body.position
        '''horizontal'''
        if position[0] >= self.xThres and\
            position[0] <= (sceneWidth - viewportWidth) + self.xThres:
            fX = position[0] - self.xThres
            self.scene.graph.setFocus(-fX, self.scene.graph.focusY)
        '''vertical'''
        if position[1] >= self.yThres and\
            position[1] <= (sceneHeight - viewportHeight) + self.yThres:
            fY = position[1] - self.yThres
            self.scene.graph.setFocus(self.scene.graph.focusX, -fY)
        

class ContinuousCamera(object):
    def __init__(self, scene, incX=0, incY=0):
        self.scene = scene
        self.incX = -incX
        self.incY = -incY
        
    def update(self):
        self.scene.graph.moveFocus(x=self.incX, y=self.incY)
            

class LevelScene(Scene):
    def __init__(self, name, filename, avatar, viewport, debugMode=False):
        super(LevelScene, self).__init__(name, viewport)
        self.debugMode = debugMode
        self.filename = filename
        self.space = pymunk.Space()
        self.graph = None
        self.avatar = avatar
        self.avatar.setFocus(lambda:self.graph.focusX,lambda:self.graph.focusY)
        self.addActor(self.avatar)
        self.camera = OrientedCamera(self, xThres=800, yThres=300)
        
    def load(self):
        try:
            super(LevelScene, self).load()
            self.graph = SceneGraph.parseMapFile(self.filename, self.batch, rLoader,
                self.viewport, space=self.space, debugMode=self.debugMode)
            self.space.gravity = 0, -1000
            self.parseObjects()
        except scenegraph.FileLoadFailedException as err:
            print "Level Parsing Failed: " + err.msg
        finally:
            self.loaded = False
            
    def parseObjects(self):
        objects = self.graph.layers['object'].items
        focusX = lambda : self.graph.focusX
        focusY = lambda : self.graph.focusY
        paths = entity.parseModpaths()
        for item in objects:
            if item.name == "levelstart":
                self.avatar.setposition(item.x, item.y)
                self.camera.update()
            else:
                actorClass = entity.loadClass(paths, item.name)
                actor = actorClass(focusX, focusY, self.batch)
                actor.setposition(item.x,item.y)
                self.addActor(actor)
        
    def unload(self, keepState=False):
        if self.graph is not None:
            self.graph.delete(keepState)
        super(LevelScene, self).unload(keepState)
        
    def update(self, dt):
        self.space.step(1./60)
        if self.camera is not None:
            self.camera.update()
        super(LevelScene, self).update(dt)
    
