'''
Implementation of scene controller and scene manipulation tools.
'''
import pyglet
from editor import rLoader
from pyglet.window import mouse, key
from pyglet.gl import glPopMatrix, glPushMatrix, \
    glScalef, glClearColor, glLineWidth, GL_TRIANGLES, \
    glEnable, GL_BLEND, glTranslatef
import appEngine.scenegraph as scenegraph
from appEngine.scenegraph import SceneGraph


'''
    BaseTool
    abstract. base for all scene tools.
'''
class BaseTool(object):
    NAME = "Base"
    def __init__(self, controller):
    	self.controller = controller
    	
    def activate(self):
        return self
        
    def deactivate(self):
        pass
        
    def screenToSceneCoords(self, x=0, y=0, point=None):
        if point != None:
            x = point[0] - self.controller.graph.focusX
            y = point[1] - self.controller.graph.focusY
            x = x / self.controller.scale
            y = y / self.controller.scale
            return (x,y)
        else:
            x = x - self.controller.graph.focusX
            y = y - self.controller.graph.focusY
            x = x / self.controller.scale
            y = y / self.controller.scale
            return (x,y)
    
    def sceneToScreenCoords(self, x=0, y=0, point=None):
        if point != None:
            x = self.controller.graph.focusX + point[0]
            y = self.controller.graph.focusY + point[1]
            return (x,y)
        else:
            x = self.controller.graph.focusX + x
            y = self.controller.graph.focusY + y
            return (x,y)
            
    # input event handlers 
    def on_mouse_motion(self, x, y, dx, dy):
        pass
    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        pass
    def on_mouse_press(self,x, y, button, modifiers):
        pass
    def on_mouse_scdfroll(self,x, y, scroll_x, scroll_y):
        pass
    def on_mouse_release(self, x, y, button, modifiers):
        pass
    def key_press(self, symbol, modifiers):
        pass
    def key_release(self, symbol, modifiers):
        pass
        

'''
    PanTool
    allows user to pan scene using mouse.
'''
class PanTool(BaseTool):
    NAME = "Pan"
    def __init__(self, controller):
    	super(PanTool, self).__init__(controller)
    
    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        if self.controller.graph != None:
            self.controller.graph.moveFocus(dx, dy)
            

          
'''
    PlotLineTool
    allows user to place a line in the terrain layer. 
'''
class Point(object):
    def __init__(self, x, y):
        self.x = x
        self.y = y
class PlotLineTool(BaseTool):
    NAME = "Line"
    def __init__(self, controller):
    	super(PlotLineTool, self).__init__(controller)
        self.lineStart = (0,0)
        self.mousePoint = (0,0)
        self.snapMode = False
        self.preview = None
    
    def doPreview(self, x2, y2):
        if self.lineStart is None:
            return
        if self.preview is not None:
            self.preview.delete()
            self.preview = None
        x1,y1 = self.lineStart
        x2,y2 = self.screenToSceneCoords(x2,y2)
        # create vl of line preview
        batch = self.controller.graph.batch
        group = self.controller.currentLayer.group
        curColor = self.controller.currentLayer.curColor
        self.preview = batch.add(2, pyglet.gl.GL_LINES, group,
                ('v2f', (x1, y1, x2, y2)),
                ('c3f', (curColor[0],curColor[1],curColor[2])*2))
            
    def closestPointToMouse(self):
        lines = self.controller.graph.layers["terrain"].lines
        mousePos = self.screenToSceneCoords(self.mousePoint[0],self.mousePoint[1])
        closestPoint = None
        
        points = list()
        for line in lines:
            #create list of points
            points.append(Point(line.x1, line.y1))
            points.append(Point(line.x2, line.y2))
        for point in points:
            # calcuate distance between mouse and point
            xDist = abs(mousePos[0] - point.x)
            yDist = abs(mousePos[1] - point.y)
            dist = xDist + yDist
            if closestPoint == None:
                closestDist = dist
                closestPoint = point
            if dist < closestDist:
                closestDist = dist
                closestPoint = point
        return (closestPoint.x, closestPoint.y)
        
    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        self.doPreview(x,y)
    
    def on_mouse_press(self, x, y, button, modifiers):
        if button == mouse.LEFT:
            if self.snapMode == True:
                ''' snap mode causes line start
                    to snap to nearest point '''
                self.mousePoint = (x,y)
                self.lineStart = self.closestPointToMouse()
            else:
                translatedCoords = self.screenToSceneCoords(x,y)
                self.lineStart = translatedCoords

    def on_mouse_release(self, x, y, button, modifiers):
        if button == mouse.LEFT:
            terrain = self.controller.graph.layers['terrain']
            if self.preview is not None:
                self.preview.delete()
                self.preview = None
            mousePos = self.screenToSceneCoords(x,y)
            terrain.addLine(self.lineStart[0], self.lineStart[1], mousePos[0], mousePos[1])
            self.linePreview = None
            self.controller.edited = True
            
'''
    PlaceItemTool
    allows user to place aesthetic or object items into correct layer
'''
class PlaceItemTool(BaseTool):
    NAME="PlaceItem"
    def __init__(self, controller):
        super(PlaceItemTool, self).__init__(controller)
        self.selectedName = None
        self.selectedItem = None
        self.preview = None
        self.active = None
        
    def activate(self):
        self.active = True
        if self.preview is not None:
            self.preview.visible = True
        return self
        
    def deactivate(self):
        self.active = False
        if self.preview is not None:
            self.preview.visible = False
    
    def setSelectedItem(self, path):
        if path is None:
            self.selectedName = None
            self.selectedItem = None 
            self.preview = None
            return
        # extracts the file name without extention
        # f = path[path.rfind("/"):len(path)]
        f = path.__getslice__(path.rfind("/") + 1, len(path))
        self.selectedName = f.__getslice__(0, f.find("."))
        self.selectedItem = pyglet.image.load(path)
        self.preview = pyglet.sprite.Sprite(
                self.selectedItem, batch=self.controller.graph.batch, 
                group=self.controller.currentLayer.group)
        if self.active == False:
            self.preview.visible = False
            
    def key_press(self, symbol, modifiers):
        if self.preview is not None:
            if modifiers & key.MOD_CTRL:
                if symbol == key.MINUS:
                    self.preview.scale -= 0.05
                elif symbol == key.EQUAL:
                    self.preview.scale += 0.05
                elif symbol == key.R:
                    self.preview.rotation += 5
    
    def on_mouse_motion(self, x, y, dx, dy):
        if self.preview is not None and self.active is True:
            self.preview.x, self.preview.y = self.screenToSceneCoords(x,y)

    def on_mouse_release(self, x, y, button, modifiers):
        if self.preview is not None and self.active is True:
            mousePos = self.screenToSceneCoords(x,y)
            self.controller.currentLayer.addItem(self.selectedName, mousePos, self.preview.scale, self.preview.rotation)
            self.controller.edited = True
        
        
'''
    SelectTool
    allows user to select an object.
'''
class SelectTool(BaseTool):
    NAME = "Select"
    def __init__(self, controller, window):
    	super(SelectTool, self).__init__(controller)
    	self.window = window
    	self.selectedItem = None
    	self.highlight = None
    	
    def on_mouse_motion(self, x, y, dx, dy):
        self.mousePoint = self.screenToSceneCoords(x, y)
        if self.controller.currentLayer.isPointOverItem(self.mousePoint, 5) != None:
            cursor = self.window.get_system_mouse_cursor(self.window.CURSOR_HAND)
            self.window.set_mouse_cursor(cursor)
        else:
            cursor = self.window.get_system_mouse_cursor(self.window.CURSOR_DEFAULT)
            self.window.set_mouse_cursor(cursor)
                
    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        currentLayer = self.controller.currentLayer
        if currentLayer.name == "terrain":
            pass
        else:
            if self.selectedItem is not None:
                x = self.selectedItem.x + dx
                y = self.selectedItem.y + dy
                self.selectedItem.updatePosition(x=x, y=y)
                self.controller.edited = True
        
    def on_mouse_press(self, x, y, button, modifiers):
        self.mousePoint = self.screenToSceneCoords(x, y)
        self.selectedItem = self.controller.currentLayer.isPointOverItem(self.mousePoint, 5)
        if self.selectedItem is None:
            return
        currentLayer = self.controller.currentLayer
        if currentLayer.name == "terrain":
            pass
        else:
            sprite = self.selectedItem.sprite
            xy = self.sceneToScreenCoords(sprite.x, sprite.y)
            x = xy[0]
            y = xy[1]
            x2 = x + sprite.width
            y2 = y + sprite.height
            self.highlight = self.controller.batch.add(6, GL_TRIANGLES, self.controller.grid.group,
                ('v2f', (x, y, x2, y, x2, y2, 
                        x, y, x2, y2, x, y2)),
                ('c4f', (1.,1.,1.,0.4)*6))

    def on_mouse_release(self, x, y, button, modifiers):
        if self.highlight is not None:
            self.highlight.delete()
            self.highlight = None
        self.mousePoint = self.screenToSceneCoords(x, y)
        self.selectedItem = self.controller.currentLayer.isPointOverItem(self.mousePoint, 5)
        self.window.dispatch_event('on_select_item')
        


'''
    class Keys
    responds to keypresses, notifying an event handler 
    while storing the current state of the keys for querying
'''
class Keys(key.KeyStateHandler):
    def __init__(self, parent):
        self.parent = parent

    def on_key_press(self, symbol, modifiers):
        self.parent.key_press(symbol, modifiers)
        super(Keys, self).on_key_press(symbol, modifiers)

    def on_key_release(self, symbol, modifiers):
        self.parent.key_release(symbol, modifiers)
        super(Keys, self).on_key_release(symbol, modifiers)

class GridGroup(pyglet.graphics.OrderedGroup):
    def __init__(self, controller):
        super(GridGroup, self).__init__(8)
        self.controller = controller
        self.focusX = 0
        self.focusY = 0
        
    def set_state(self):
        glLineWidth(1)
        glEnable(GL_BLEND)
        '''if self.controller.graph is not None:
            glTranslatef(self.controller.graph.focusX, self.controller.graph.focusY, 0)'''
        
    def unset_state(self):
        '''if self.controller.graph is not None:
            glTranslatef(-self.controller.graph.focusX, -self.controller.graph.focusY, 0)'''
        pass
        
class Grid(object):
    def __init__(self, controller, window):
        self.visible = False
        self.snap = False
        self.hSpacing = 50
        self.vSpacing = 50
        self.hOffset = 0
        self.vOffset = 0
        self.batch = pyglet.graphics.Batch()
        self.group = GridGroup(controller)
        self.lines = list()
        self.window = window
                
    def update(self):
        def defLine(x1, y1, x2, y2):
            self.lines.append(self.batch.add(2, pyglet.gl.GL_LINES, self.group,
                ('v2i', (x1, y1, x2, y2)),
                ('c4f', (1.0,1.0,1.0,0.8)*2)))  
        for line in self.lines:
            line.delete()
        self.lines = []
        if self.visible == True:
            hCount = self.window.width / self.hSpacing
            i = 1
            while i <= hCount:
                x = (self.hSpacing * i) + self.hOffset
                y1 = 0
                y2 = self.window.height
                defLine(x, y1, x, y2)
                i = i + 1
            vCount = self.window.height / self.vSpacing
            i = 1
            while i <= vCount:
                y = (self.vSpacing * i) + self.vOffset
                x1 = 0
                x2 = self.window.width
                defLine(x1, y, x2, y)
                i = i + 1
'''
    class SceneController
    manages editing of the level controller.
'''
class Controller(object):
    def __init__(self, window):
        self.tools = {
            "pan" : PanTool(self),
            "plotline" : PlotLineTool(self),
            "placeitem" : PlaceItemTool(self),
            "select" : SelectTool(self, window)
        }
        self.window = window
        self.batch = pyglet.graphics.Batch()
        self.graph = None
        self.edited = False
        self.size = (0,0)
        self.scale = 1.0
        self.keys = Keys(self)
        self.mouseCoord = (0,0)
        self.grid = Grid(self, window)
        self.currentLayer = None
        self.currentTool = None
        self.keys = Keys(self)
        window.push_handlers(self)
        window.push_handlers(self.keys)
        
    def _set_edited(self, edited):
        self._edited = edited
        self.window.dispatch_event('on_document_update')
    def _get_edited(self):
        return self._edited
    edited = property(_get_edited, _set_edited)
        
    def addLayer(self, name, z_order):
        self.graph.addAestheticLayer(self, name, z_order)
        self.edited = True
        
    def deleteLayer(self, name):
        if self.currentLayer.name == name:
            self.currentLayer = None
        self.graph.deleteAestheticLayer(name)
        self.edited = True
        
    def renameLayer(self, layer, name):
        if layer.name == name:
            return
        self.graph.layers.delete(layer.name)
        layer.name = name
        self.controller.graph.layers.addNamed(layer, layer.name)
        self.edited = True
            
    def changeLayerZOrder(self, layer, value):
        if layer.group.order == value:
            return
        layer.setZOrder(int(values["z_order"]))
        self.edited = True
        
    def changeBackground(self, r, g, b):
        self.graph.backColour = [r,g,b]
        self.graph.updateBackground()
        self.edited = True
    
    def setSourcePath(self, path):
        self.controller.graph.sourcePath = path
        self.edited = True
    
    def setCurrentLayerProperties(self, visible=None, opacity=None):
        if visible is not None:
            self.currentLayer.setVisible(visible)
            self.edited = True
        if opacity is not None:
            self.currentLayer.setOpacity(opacity)
            self.edited = True
    
        
    def newLevel(self, name, width, height):
        if self.graph is not None:
            self.graph.unload(False)
        self.batch = pyglet.graphics.Batch()
        self.grid.update()
        self.graph = SceneGraph(name, self.batch, rLoader, self.size, width, height, editorMode=True)
        self.levelFilename = None
        self.graph.forceFocus = True
        self.edited = False
    
    def loadLevel(self, filename, window):
        if self.graph is not None:
            self.graph.unload(False)
        self.batch = pyglet.graphics.Batch()
        self.grid.update()
        self.graph = SceneGraph.parseMapFile(filename, self.batch, rLoader, self.size, editorMode=True)
        self.graph.forceFocus = True
        self.levelFilename = filename
        window.dispatch_event('on_layer_update')
        self.edited = False
        
    def saveLevelToFile(self, filename):
        self.graph.saveToFile(filename)
        self.levelFilename = filename
        self.edited = False
        
    def setActiveLayer(self, name):
        # sets the reference to the current layer
        if self.currentTool is not None:
            if self.currentTool.NAME == "PlaceItem":
                self.currentTool.preview = None
        if name == "none":
            self.currentLayer = None
            self.currentTool = None
            return
        try:
            self.currentLayer = self.graph.layers[name]
        except KeyError:
            print "Set Active Layer Key Error"
                    
        
    def setCurrentTool(self, tool):
        for t in self.tools:
            self.tools[t].deactivate()
        # search tool list for name and set
        # tool with given name to current tool.
        try:
            self.currentTool = self.tools[tool].activate()
        except KeyError:
            print "Set Current Tool Key Error"
            
    def resize(self, width, height):
        self.size = (width, height)
        if self.graph:
            self.graph.viewportWidth = width
            self.graph.viewportHeight = height
            
    def update(self, dt):
        if self.graph:
            self.pollPanKeys(dt)
            self.graph.update(dt)
    
    def draw(self):
        if self.batch is not None:
            glPushMatrix()
            glScalef(self.scale, self.scale, 0)
            self.batch.draw()
            glPopMatrix()
        self.grid.batch.draw()
        
    ''' input event handlers '''      
    def pollPanKeys(self, dt):
        moveRate = dt * 400
        if self.keys[key.UP]:
            self.graph.moveFocus(y=-moveRate)
        if self.keys[key.DOWN]:
            self.graph.moveFocus(y=moveRate)
        if self.keys[key.LEFT]:
            self.graph.moveFocus(moveRate)
        if self.keys[key.RIGHT]:
            self.graph.moveFocus(-moveRate)
            
    def key_press(self, symbol, modifiers):
        if symbol == key.HOME:
            if self.graph != None:
                self.graph.setFocus(0,0)
                return
        elif modifiers & key.MOD_CTRL and symbol == key._0:
            self.scale = 1.0
            self.window.dispatch_event('on_update_zoom')
            return
        elif modifiers & key.MOD_CTRL and symbol == key.MINUS:
            self.scale = self.scale - 0.1
            self.window.dispatch_event('on_update_zoom')
            return
        elif modifiers & key.MOD_CTRL and symbol == key.EQUAL:
            self.scale = self.scale + 0.1
            self.window.dispatch_event('on_update_zoom')
            return
        elif modifiers & key.MOD_CTRL and symbol == key.S:
            if self.levelFilename is not None and self.edited is not False:
                self.graph.saveToFile(filename)
        if self.currentTool is not None:
        	self.currentTool.key_press(symbol, modifiers)
    
    def key_release(self, symbol, modifiers):
        if self.currentTool is not None:
        	self.currentTool.key_release(symbol, modifiers)
               
    def on_mouse_motion(self, x, y, dx, dy):
        self.mouseCoord = (x,y)
        if self.currentTool is not None:
        	self.currentTool.on_mouse_motion(x, y, dx, dy)
        
    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        if self.currentTool == None:
            if self.graph != None:
                self.graph.moveFocus(dx, dy)
        if self.currentTool is not None:
        	self.currentTool.on_mouse_drag(x, y, dx, dy, buttons, modifiers)
        
    def on_mouse_press(self,x, y, button, modifiers):
        if self.currentTool is not None:
        	self.currentTool.on_mouse_press(x, y, button , modifiers)
    
    def on_mouse_scdfroll(self,x, y, scroll_x, scroll_y):
        if self.currentTool is not None:
        	self.currentTool.on_mouse_scdfroll(x, y, scroll_x, scroll_y)
    
    def on_mouse_release(self, x, y, button, modifiers):
        if self.currentTool is not None:
        	self.currentTool.on_mouse_release(x, y, button, modifiers)
    

            
