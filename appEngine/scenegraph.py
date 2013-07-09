'''
    Scene Graph implementation
'''
import os
import xml.etree.ElementTree as ET
from xml.etree.ElementTree import Element, SubElement, ElementTree
import pymunk
from appEngine import rLoader
import pyglet
from pyglet.graphics import OrderedGroup
from pyglet.gl import glColor3f, glColor4f, glLineWidth, glBegin, glVertex3i,\
    glVertex3f, glEnd, glPushMatrix, glPopMatrix, glTranslatef,\
    GL_TRIANGLES, glColorMask, GL_FALSE, GL_TRUE

'''
    z position of layers.
'''
class DrawZPos(object):
    TERRAIN_LINES = 7 #for debug\
    FRONT = 6
    SPRITES = 5
    FOREGROUND = 4


''' 
    class BaseLayer
'''
class BaseLayer(object):
    def setView(self, sceneGraph, x, y):
        self.group.setView(x, y)
        self.viewportWidth = sceneGraph.viewportWidth
        self.viewportHeight = sceneGraph.viewportHeight
    
    def update(self, dt):
        pass
        
class Rect(object):
    def __init__(self, x, y, x2, y2):
        self.x = x
        self.y = y
        self.x2 = x2
        self.y2 = y2
        self.sprite = None
        
    def doesPointIntersect(self, point, threshold):
        x = point[0]
        y = point[1]
        if x > self.x and x < self.x2 and \
            y > self.y and y < self.y2:
            return True
        else:
            return False
            
    def updatePosition(self, x=None, y=None):
        if x is not None:
            self.x = x
        if y is not None:
            self.y = y
        self.x2 = self.x + self.sprite.width
        self.y2 = self.y + self.sprite.height
        self.sprite.x = self.x
        self.sprite.y = self.y
        
'''  
    Aesthetic Layer 
'''
class AestheticGroup(OrderedGroup):
    def __init__(self, z_order):
        super(AestheticGroup, self).__init__(z_order)
        self.focusX = 0
        self.focusY = 0
        self.visible = True
        
    def setFocus(self, x, y):
        self.focusX = x
        self.focusY = y

    def set_state(self):
        glTranslatef(self.focusX, self.focusY, 0)
        if self.visible == False:
            glColorMask(GL_FALSE,GL_FALSE,GL_FALSE,GL_FALSE)
        
    def unset_state(self):
        glTranslatef(-self.focusX, -self.focusY, 0)
        if self.visible == False:
            glColorMask(GL_TRUE,GL_TRUE,GL_TRUE,GL_TRUE)
        
class Visual(Rect):
    def __init__(self, name, (x,y), scale, rot, layerOpacity, sprite):
        x = x
        y = y
        x2 = x + sprite.width
        y2 = y + sprite.height
        super(Visual, self).__init__(x,y,x2,y2)
        self.name = name
        self.sprite = sprite
        self.scale = scale
        self.rot = rot
        self.absOpacity = 255
        self.opacity = self.absOpacity * layerOpacity
        
    def setOpacity(self, layerOpacity, value):
        self.absOpacity = value
        self.opacity = layerOpacity * self.absOpacity
        self.sprite.opacity = self.opacity
        
class AestheticLayer(BaseLayer):
    dir = 'visuals'
    def __init__(self, name, batch, rLoader, z_order, editorMode=False):
        self.batch = batch
        self.rLoader = rLoader
        self.name = name
        self.group = AestheticGroup(z_order)
        self.z_order = z_order
        self.items = []
        self.editorMode = editorMode
        self.visible = True
        self.opacity = 1.0
        
    def unload(self):
        for item in self.items:
            item.sprite.delete()
            
    def reload(self):
        pass
        
    def setVisible(self, value):
        self.visible = value
        self.group.visible = value
        
    def setZOrder(self, value):
        self.z_order = value
        self.group = AestheticGroup(value)
        for item in self.items:
            item.sprite.group = self.group
        
    def setOpacity(self, value):
        self.opacity = value
        for item in self.items:
            item.opacity = item.absOpacity * self.opacity
        
    def addItem(self, item, (x,y), scale, rot):
        file = item + ".png"
        img = rLoader.image(self.dir + "/" + file)
        sprite = pyglet.sprite.Sprite(img, batch=self.batch, group=self.group)
        sprite.x = x
        sprite.y = y
        sprite.scale = scale
        sprite.rotation = rot
        self.items.append(Visual(item, (x,y), scale, rot, self.opacity, sprite))
        
        
    '''
        doesPointIntersect()
        returns boolean based on whether point is over line
        given threshold of width
    '''
    def isPointOverItem(self, point, threshold):
        for item in self.items:
            if item.doesPointIntersect(point, threshold) == True:
                return item
        return None


'''
    Object Layer
'''
class ObjectGroup(OrderedGroup):
    def __init__(self):
        super(ObjectGroup, self).__init__(DrawZPos.SPRITES)
        self.focusX = 0
        self.focusY = 0
        
    def setFocus(self, x, y):
        self.focusX = x
        self.focusY = y

    def set_state(self):
        glTranslatef(self.focusX, self.focusY, 0)
        
    def unset_state(self):
        glTranslatef(-self.focusX, -self.focusY, 0)
        
class Object(Rect):
    def __init__(self, name, (x,y), (x2,y2), scale, rot, opacity, sprite):
        super(Object, self).__init__(x,y,x2,y2)
        self.name = name
        self.sprite = sprite
        self.scale = scale
        self.rot = rot
        
        
class ObjectLayer(BaseLayer):
    dir = 'entities'
    name = 'entities'
    
    def __init__(self, batch, rLoader, editorMode=False):
        self.batch = batch
        self.editorMode = editorMode
        self.items = []
        self.group = ObjectGroup()
        
    def unload(self):
        for item in self.items:
            item.sprite.delete()
            
    def reload(self):
        pass
        
    def addItem(self, item, (x,y), scale, rot):
        file = item + ".png"
        img = rLoader.image(self.dir + "/" + file)
        sprite = pyglet.sprite.Sprite(img, batch=self.batch, group=self.group)
        sprite.x = x
        sprite.y = y
        x2 = x + sprite.width
        y2 = y + sprite.height
        if self.editorMode is True:
            sprite.scale = scale
            sprite.rotation = rot
        else:
            sprite.delete()
            sprite = None
        self.items.append(Object(item, (x,y), (x2,y2), scale, rot, 1.0, sprite))
        
    def isPointOverItem(self, point, threshold):
        for item in self.items:
            if item.doesPointIntersect(point, threshold) == True:
                return item
        return None
        

''' 
    Terrain Layer
    manages the terrain line of sim
'''
''' Class Line
    stores a current terrain layer line and its vertex list 
'''
class Line(object):
    def __init__(self, x1, y1, x2, y2, vl=None):
        self.x1 = x1
        self.y1 = y1
        self.x2 = x2
        self.y2 = y2
        self.vl = vl # gl vertex list
        
    
    def updatePos(self, x1, y1, x2, y2):
        self.x1 = x1
        self.y1 = y1
        self.x2 = x2
        self.y2 = y2
        if self.vl is not None:
            #TODO check that this is right.
            sef.vl.vertices = [x1, y1, x2, y2]
    
    '''
        function doesPointIntersect()
        returns boolean based on whether point is over line
        given threshold of width
    '''
    def doesPointIntersect(self, point, threshold):
        #TODO
        pass
        
class TerrainGroup(OrderedGroup):
    def __init__(self):
        super(TerrainGroup, self).__init__(DrawZPos.TERRAIN_LINES)
        self.focusX = 0
        self.focusY = 0
        
    def setFocus(self, x, y):
        self.focusX = x
        self.focusY = y

    def set_state(self):
        glLineWidth(2)
        glTranslatef(self.focusX, self.focusY, 0)
        
    def unset_state(self):
        glTranslatef(-self.focusX, -self.focusY, 0)
        
class TerrainLayer(BaseLayer):
    name = 'terrain'
    def __init__(self, batch=None, dl=False):
        self.drawLines = dl
        self.batch = batch
        self.initColors()
        self.lines = []
        self.group = TerrainGroup()
        
    def unload(self):
        for line in self.lines:
            line.vl.delete()
            
    def reload(self):
        pass
        
    def initColors(self):
        self.colors = dict()
        self.colors['Blue'] = (0.,0.,255.)
        self.colors['Red'] = (255.,0.,0.)
        self.colors['Green'] = (0.,255.,.0)
        self.colors['White'] = (255.,255.,255.)
        self.colors['Black'] = (0.,0.,0.)
        self.curColor = self.colors['White']
    
    '''
        sets the color of all lines in layer
    '''
    def setLineColor(self, color):
        try:
            color = self.colors[color]
            self.curColor = color
            for line in self.lines:
                line.vl.colors = [color[0],color[1],color[2],color[0],color[1],color[2]]
        except KeyError:
            print "Line Colour Key Error"
    
    '''
        adds a line to the terrain layer upon preview being false,
        while preview is true, line is not stored permanetely and
        just temporarly added to batch
    '''
    def addLine(self, x1, y1, x2, y2):
        vl = None
        if self.drawLines:
            vl = self.batch.add(2, pyglet.gl.GL_LINES, self.group,
                ('v2f', (x1, y1, x2, y2)),
                ('c3f', (self.curColor[0],self.curColor[1],self.curColor[2])*2))
        self.lines.append(Line(x1, y1, x2, y2, vl))
    
    '''
        returns the line that click is over
    '''
    def isPointOverItem(self, point, threshold):
        for line in self.lines:
            if line.doesPointIntersect(point, threshold) == True:
                return line
        return None
            
'''
    Layers
    expands upon list container for named retrieval of items
'''
class Layers(list):
    def __init__(self):
        self.by_name = {}
    
    def addNamed(self, layer, name):
        self.append(layer)
        self.by_name[name] = layer
        self.by_name[name].name = name
        
    def delete(self, name):
        item = self.by_name[name]
        self.by_name.pop(name)
        self.remove(item)
    
    def __getitem__(self, item):
        if isinstance(item, int):
            return self[item]
        return self.by_name[item]
        
class BackgroundGroup(OrderedGroup):
    def __init__(self, z_order):
        self.focusX = 0
        self.focusY = 0
        self.visible = True
        super(BackgroundGroup, self).__init__(z_order)
        
    def setFocus(self, x, y):
        self.focusX = x
        self.focusY = y

    def set_state(self):
        glTranslatef(self.focusX, self.focusY, 0)
        if self.visible == False:
            glColorMask(GL_FALSE,GL_FALSE,GL_FALSE,GL_FALSE)
        
    def unset_state(self):
        glTranslatef(-self.focusX, -self.focusY, 0)
        if self.visible == False:
            glColorMask(GL_TRUE,GL_TRUE,GL_TRUE,GL_TRUE)

'''
    sceneGraph
    
'''
class FileLoadFailedException(Exception): 
    """failed to load level file"""
    def __init__(self, msg):
        self.msg = msg
class SceneGraph(object):
    FILE_EXT = ".lvl"
    def __init__(self, name, batch, resourceLoader, viewportSize, width=0, height=0, space=None, 
        editorMode=False, debugMode=False):
        self.batch = batch
        self.space = space
        #
        self.width = width
        self.height = height
        self.focusX, self.focusY = 0, 0
        self.viewportWidth, self.viewportHeight = viewportSize
        self.backColour = [0.,0.,0.]
        self.name = name
        self.editorMode = editorMode
        self.rLoader = resourceLoader
        self.forceFocus = editorMode
        # layers:
        self.layers = Layers()
        self.layers.addNamed(AestheticLayer("foreground", self.batch, self.rLoader, DrawZPos.FOREGROUND, editorMode=editorMode), "foreground")
        self.layers.addNamed(ObjectLayer(self.batch, self.rLoader, editorMode=editorMode), "object")
        self.layers.addNamed(TerrainLayer(self.batch, dl=editorMode or debugMode), "terrain")
        self.background = None
        self.backgroundGroup = BackgroundGroup(1)
        self.updateBackground()
        
    def unload(self, keepState):
        self.background.delete()
        names = []
        for layer in self.layers:
            names.append(layer.name)
            layer.unload()
        if keepState == False:
            for name in names:
                self.layers.delete(name)
                
    def reload(self):
        for layer in self.layers:
            layer.reload()
        
    def addAestheticLayer(self, name, z_order):
        self.layers.addNamed(AestheticLayer(name, self.batch, self.rLoader, z_order, editorMode=self.editorMode), name)
        
    def deleteAestheticLayer(self, name):
        self.layers[name].delete()
        self.layers.delete(name)
    '''
    returns a scenegraph constructed from specified file
    '''
    @classmethod
    def parseMapFile(cls, fileName, batch, resourceLoader, 
        viewportSize, space=None, editorMode=False, debugMode=False):
        def invalidFile():
            print "invalid file"
        try:  
            tree = ET.parse(fileName)
            root = tree.getroot()
            if root.tag != 'map':
                invalidFile()
                return
            width = int(root.attrib['width'])
            height = int(root.attrib['height'])
            if root[0].tag != 'head':
                invalidFile()
                return
            head = root[0]
            for child in head:
                if child.tag == 'name':
                    mapName = child.text
                #elif child.tag == 'source':
                #    source = child.text
                
            graph = cls(mapName, batch, resourceLoader, viewportSize, width, height, space=space, 
                editorMode=editorMode, debugMode=debugMode)
                
            if root[1].tag != 'layers':
                invalidFile()
                graph = None
                return
            layers = root[1]
            for child in layers:
                if child.tag == 'terrainlayer':
                    layer = graph.layers['terrain']
                    for line in child:
                        x1 = int(line.get('x1'))
                        y1 = int(line.get('y1'))
                        x2 = int(line.get('x2'))
                        y2 = int(line.get('y2'))
                        layer.addLine(x1,y1,x2,y2)
                elif child.tag == 'objectlayer':
                    layer = graph.layers['object']
                    for item in child:
                        name = item.get('name')
                        x = int(item.get('x'))
                        y = int(item.get('y'))
                        rot = 0.0
                        scale = 1.0
                        layer.addItem(name, (x,y), scale, rot)
                else:
                    layer = graph.layers[child.get('name')]
                    for item in child:
                        name = item.get('name')
                        x = int(item.get('x'))
                        y = int(item.get('y'))
                        rot = 0
                        scale = 1.0
                        for c in item:
                            if c.tag == "rotation":
                                rot = int(c.text)
                            if c.tag == "scale":
                                scale = float(c.text)
                        layer.addItem(name, (x,y), scale, rot)
            if space is not None:
                graph.generatePhysics()
            return graph
        except ET.ParseError as err:
            raise FileLoadFailedException(str(err))
        #TODO catch all xml reading exceptions
        
        
    def generatePhysics(self):
        '''terrain layer and visuals with line'''
        layer = self.layers['terrain']
        self.platformSegs = list()
        for line in layer.lines:
            seg = pymunk.Segment(self.space.static_body, (line.x1, line.y1), (line.x2, line.y2), 5)
            self.platformSegs.append(seg)
        '''vertical side lines'''
        self.platformSegs.append(pymunk.Segment(self.space.static_body, (0, 0), (0, self.height), 5))
        self.platformSegs.append(pymunk.Segment(self.space.static_body, (self.width, 0), (self.width, self.height), 5))
        for seg in self.platformSegs:
            seg.friction = 1.
            seg.group = 1
        self.space.add(self.platformSegs)
        
     
    '''
        saves graph to xml file
    '''
    def saveToFile(self, filename):
        root = Element('map')
        root.set('width', str(self.width))
        root.set('height', str(self.height))
        
        head = SubElement(root, 'head')
        name = SubElement(head, 'name')
        name.text = self.name
        #source = SubElement(head, 'source')
        #source.text = self.sourcePath
        
        layers = SubElement(root, 'layers')
        terrainLayer = self.layers["terrain"]
        if len(terrainLayer.lines) > 0:
            terrain_layer = SubElement(layers, 'terrainlayer')
            for line in terrainLayer.lines:
                e = SubElement(terrain_layer, 'line')
                e.set('x1', str(int(line.x1)))
                e.set('y1', str(int(line.y1)))
                e.set('x2', str(int(line.x2)))
                e.set('y2', str(int(line.y2)))
        objectLayer = self.layers["object"]
        if len(objectLayer.items) > 0:
            object_layer = SubElement(layers, 'objectlayer')
            for item in objectLayer.items:
                e = SubElement(object_layer, 'item')
                e.set('name', item.name)
                e.set('x', str(int(item.x)))
                e.set('y', str(int(item.y)))
                if item.scale != 1.0:
                    es = SubElement(e, 'scale')
                    es.text = str(item.scale)
                if item.rot != 0:
                    er = SubElement(e, 'rotation')
                    er.text = str(item.rot)
        for layer in self.layers:
            if layer.name != "terrain" and \
                layer.name != "object" and \
                len(layer.items) > 0:
                aesthetic_layer = SubElement(layers, 'aestheticlayer')
                aesthetic_layer.set('name', layer.name)
                aesthetic_layer.set('visible', str(layer.visible))
                aesthetic_layer.set('opacity', str(layer.opacity))
                for item in layer.items:
                    e = SubElement(aesthetic_layer, 'item')
                    e.set('name', item.name)
                    e.set('x', str(int(item.x)))
                    e.set('y', str(int(item.y)))
                    if item.scale != 1.0:
                        es = SubElement(e, 'scale')
                        es.text = str(item.scale)
                    if item.rot != 0:
                        er = SubElement(e, 'rotation')
                        er.text = str(item.rot)
                        
        tree = ElementTree(root)
        tree.write(filename)
        
    def moveFocus(self, x=0, y=0):
        self.setFocus(self.focusX + x, self.focusY + y)
        
    previousFocus = None
    #forceFocus = True
    def setFocus(self, x, y):
        newFocus = (x, y)
        
        # check for redundant arg
        if self.previousFocus == newFocus:
            return
        self.previousFocus = newFocus
        
        x = int(x)
        y = int(y)
        
        #restrict view to within map size
        if self.forceFocus == False:
            if -x >= self.width - self.viewportWidth:
                x = -(self.width - self.viewportWidth)
            elif -x < 0:
                x = 0
            if -y >= self.height - self.viewportHeight:
                y = -(self.height - self.viewportHeight)
            elif -y < 0:
                y = 0
        
        self.focusX = x
        self.focusY = y
        self.backgroundGroup.setFocus(x,y)
        # update layers
        for layer in self.layers:
            layer.group.setFocus(x, y)
            
    def on_focus_update(self, x, y):
        pass

        
    def update(self, dt):
        for layer in self.layers:
            layer.update(dt)
    
    def updateBackground(self):
        '''adds background to batch'''
        if self.background is not None:
            self.background.delete()
        self.background = self.batch.add(6, GL_TRIANGLES, self.backgroundGroup,
                ('v2i', (0, 0, self.width, 0, self.width, self.height, 
                        0, 0, self.width, self.height, 0, self.height)),
                ('c3f', (self.backColour[0],self.backColour[1],self.backColour[2])*6))









