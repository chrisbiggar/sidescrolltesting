'''

'''
import os
import appEngine
from appEngine import director
from appEngine import actor
from appEngine import scene
import pyglet
from robot import Robot


class Game(object):
    width = 1280
    height = 720
    def __init__(self, options):
        pyglet.clock.set_fps_limit(60)
        appEngine.setResourcePath(["assets", "entities", "assets\avatar"])
        self.director = director.Director((self.width, self.height), True, windowCaption="Game")
        robo = Robot(self.director)
        self.director.push_handlers(robo.keyboard)
        lvlpath = os.path.join("assets", "levels", "level.lvl")
        scene = appEngine.scene.LevelScene("scene", lvlpath, robo, (self.width, self.height))
        self.director.registerScene(scene)
        self.director.switchToScene("scene")
