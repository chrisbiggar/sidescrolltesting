'''
map editor for appEngine.
'''
import pyglet
from pyglet.window import key
from pyglet.gl import glEnable, glViewport, glMatrixMode, glLoadIdentity, glBlendFunc, \
	gluPerspective, gluLookAt, GL_PROJECTION, GL_MODELVIEW, GL_BLEND, \
	GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA, glClearColor
import controller
import dialogs, toolDialogs


class LevelEditor(pyglet.window.Window):
    '''
    Main Application Class for level editor
    '''
    fpsDisplay = pyglet.clock.ClockDisplay()
    WINDOW_CAPTION = "Editor"
    
    def __init__(self, options):
        for display in pyglet.app.displays:
            screen = display.get_default_screen()
        super(LevelEditor, self).__init__(screen.width, screen.height, self.WINDOW_CAPTION, resizable=True)
        self.set_location(screen.x, screen.y)
        self.dialogBatch = pyglet.graphics.Batch()
        self.keys = key.KeyStateHandler()
        self.push_handlers(self.keys)
        self.controller = controller.Controller(self)
        self.createDialogs()
        # time since program started.
        self.time = 0
        self.showfps = options.showfps

        
    def createDialogs(self):
        self.register_event_type('on_update') # kytten dialogs update internally with this event
        self.register_event_type('on_layer_update') # update layer info
        self.register_event_type('on_update_zoom') # for zoom in status pane
        self.register_event_type('on_update_edited')
        self.register_event_type('on_select_item') # for selected item dialog
        self.register_event_type('on_document_update')
        self.mainDialog = dialogs.MainDialog(self)
        self.push_handlers(self.mainDialog)
        self.statusPane = dialogs.StatusPane(self, self.dialogBatch, self.controller)
        self.push_handlers(self.statusPane)
        self.toolDialog = toolDialogs.ToolDialog(self)
        self.selectedItemDialog = toolDialogs.SelectedItemDialog(self)
        self.push_handlers(self.selectedItemDialog)


    def on_close(self):
        if self.controller.graph != None and self.controller.edited == True:
            ''' if map is open and not saved prompt user
            '''
            dialogs.ConfirmExitDialog(self, self.dialogBatch, self.controller)
        else:
            super(LevelEditor, self).on_close()
        
    def on_resize(self, width, height):
        '''
        calculate perspective matrix
        '''
        v_ar = width/float(height)
        usableWidth = int(min(width, height*v_ar))
        usableHeight = int(min(height, width/v_ar))
        ox = (width - usableWidth) // 2
        oy = (height - usableHeight) // 2
        glViewport(ox, oy, usableWidth, usableHeight)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(60, usableWidth/float(usableHeight), 0.1, 3000.0)
        ''' set camera position on modelview matrix
        '''
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        gluLookAt(width/2.0, height/2.0, height/1.1566,
            width/2.0, height/2.0, 0,
            0.0, 1.0, 0.0)
        ''' update scene controller with size
        '''
        self.controller.resize(width, height)
        #clears to a grey.
        glClearColor(0.4,0.4,0.4,0.)
        return pyglet.event.EVENT_HANDLED
    
    lastClick = 0
    def on_mouse_press(self, x, y, button, modifiers):
        #super(LevelEditor, self).on_mouse_press(x, y, button, modifiers)
        pass
            
    def on_key_release(self, symbol, modifiers):
        #super(LevelEditor, self).on_mouse_release(x, y, button, modifiers)
       	pass
    
    def on_key_press(self, symbol, modifiers):
        if symbol == key.ENTER and modifiers & key.MOD_CTRL:
            ''' toggle fullscreen
            '''
            self.set_fullscreen(not self.fullscreen)
        
    def update(self, dt):
        self.time += (dt * 1000)
        self.controller.update(dt)
        
    def updateKytten(self, dt):
    	self.dispatch_event('on_update', dt)
        
    def on_draw(self):
        self.clear()
        self.controller.draw()
        self.dialogBatch.draw()
        if self.showfps is True:
            self.fpsDisplay.draw()
    
    def run(self):
        pyglet.clock.schedule_interval(self.update, 1/60.)
        pyglet.clock.schedule_interval(self.updateKytten, 1/60.)
        pyglet.app.run()
        
