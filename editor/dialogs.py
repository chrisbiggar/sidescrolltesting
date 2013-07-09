'''
Editor Dialogs

'''
import os
import pyglet
import kytten
from kytten.frame import Frame, SectionHeader, FoldingSection
from kytten.dialog import Dialog
from kytten.button import Button
from kytten.layout import VerticalLayout, HorizontalLayout, GridLayout
from kytten.widgets import Spacer, Label
from kytten.text_input import Input
from kytten.menu import Menu
from kytten.checkbox import Checkbox
import widgets
import appEngine.scenegraph as scenegraph
from appEngine.scenegraph import FileLoadFailedException


theme = kytten.Theme(os.path.join(os.getcwd(), 'theme'), override={
"gui_color": [64, 128, 255, 255],
"font_size": 16
})
file_ext = scenegraph.SceneGraph.FILE_EXT

def genOkCancelLayout(on_submit, on_cancel):
    return HorizontalLayout([
         Button("Ok", on_click=on_submit),
         Button("Cancel", on_click=on_cancel)
        ], align=kytten.HALIGN_RIGHT)
def on_escape(dialog):
    '''
        tears down specified dialog
    '''
    dialog.teardown()


class MainDialog(Dialog):
    '''
        class MainDialog
        main dialog for application. allows layer navigation and map loading/saving
    '''
    def __init__(self, editor):
        self.controller = editor.controller
        frame = self.createLayout()
        self.lastLayerChoice = None
        super(MainDialog, self).__init__(frame,
            window=editor, batch=editor.dialogBatch, 
            anchor=kytten.ANCHOR_TOP_RIGHT, theme=theme)
        
    def on_layer_update(self):
        options = list()
        keys = self.controller.graph.layers.by_name.iterkeys()
        for key in keys:
            options.append(key)
        self.layerMenu.set_options(options)
        self.metaLayerMenu.set_options(['add layer', 'edit layer', 'edit level'])
        self.fileMenu.set_options(options=["New Level", "Load Level", "Save Level", "Quit"])
        
        
    def layerMenuSelect(self, choice):
        # unselect active layer if clicked
        if choice == self.lastLayerChoice:
            self.layerMenu.options[choice].unselect()
            self.controller.setActiveLayer("none")
            self.lastLayerChoice = None
        else:
            self.controller.setActiveLayer(choice)
            self.lastLayerChoice = choice
        self.controller.tools["placeitem"].setSelectedItem(None)
        self.window.dispatch_event('on_layer_update')
        if self.window.selectedItemDialog.dialog != None:
            self.window.selectedItemDialog.dialog.teardown()
    
    def metaLayerMenuSelect(self, choice):
        if choice == "add layer":
            # add layer to LevelView
            NewLayerDialog(self.window, self.batch, self.controller)
            # unselect new layer button
            if self.layerMenu.selected is not None:
                self.layerMenu.options[self.layerMenu.selected].unselect()
        elif choice == "edit layer":
            EditLayerDialog(self.window, self.batch, self.controller)
        elif choice == "edit level":
            EditLevelDialog(self.window, self.batch, self.controller)

             
    def createLayout(self):
        # layers section
        self.layerMenu = Menu(options=[], on_select=self.layerMenuSelect)
        layersSection = FoldingSection("Layers", VerticalLayout([self.layerMenu]))
        #
        # layers section
        self.metaLayerMenu = widgets.ClickMenu(['-add layer', '-edit layer', '-edit level'], on_select=self.metaLayerMenuSelect)

        self.fileMenu = widgets.ClickMenu(
                options=["New Level", "Load Level", "-Save Level", "Quit"], 
                on_select=self.mapMenuSelect)
        # map section
        mapSection = FoldingSection("Map", self.fileMenu)
        return Frame(VerticalLayout([layersSection, self.metaLayerMenu, mapSection]))
   
    def mapMenuSelect(self, choice):
        if choice == "New Level":
            NewLevelDialog(self.window, self.batch, self.controller)
        elif choice == "Load Level":
            def on_select(filename):
                try:
                    self.controller.loadLevel(filename, self.window)
                    self.window.set_caption("Editor: " + filename)
                except FileLoadFailedException as err:
                    ErrorDialog(self.window, self.batch, err.msg, title="File Load Error")
                on_escape(dialog)
            dialog = kytten.FileLoadDialog(
                        extensions=[file_ext], window=self.window, 
                        theme=self.theme,
                        on_select=on_select, batch=self.batch,
                        on_escape=on_escape)
        elif choice == "Save Level":
            def on_select(filename):
                if filename.endswith(file_ext) == False:
                    filename += file_ext
                self.controller.saveLevelToFile(filename)
                self.window.set_caption("Editor: " + filename)
                on_escape(dialog)
            dialog = kytten.FileSaveDialog(
                extensions=[file_ext], window=self.window,
                batch=self.batch, anchor=kytten.ANCHOR_CENTER,
                theme=self.theme, on_escape=on_escape, on_select=on_select)
        elif choice == "Quit":
            pyglet.app.exit()
            

class NewLevelDialog(Dialog):
    '''
        allows user to create new level specifying properties
    '''
    def __init__(self, window, batch, controller):
        self.controller = controller
        super(NewLevelDialog, self).__init__(
            Frame(
                VerticalLayout([
                    SectionHeader("New Level", align=kytten.HALIGN_LEFT),
                    kytten.GridLayout([
                        [Label("Name"), Input("name", "untitled",
                                                max_length=20)],
                        [Label("Height"), Input("height", "1200",
                                                max_length=5)],
                        [Label("Width"), Input("width", "5000",
                                                max_length=5)]                                                
                    ]),
                    SectionHeader("", align=kytten.HALIGN_LEFT),
                    genOkCancelLayout(self.on_submit, self.on_cancel)
                ])),
            window=window, batch=batch,
            anchor=kytten.ANCHOR_CENTER, theme=theme,
            on_enter=self.on_enter, on_escape=on_escape)   
            
    def on_submit(self):
        values = self.get_values()
        name = values["name"]
        width = int(values["width"])
        height = int(values["height"])
        self.controller.newLevel(name, width, height)
        self.window.set_caption("Editor: " + name)
        self.window.dispatch_event('on_layer_update')
        on_escape(self)
    def on_enter(self, dialog):
        self.on_submit()
    def on_cancel(self):
        on_escape(self)
    
class EditLayerDialog(object):
    '''
        allows user to edit the properties of the current layer
    '''
    def __init__(self, window, batch, controller):
        self.layouts = {
            "aesthetic" : self.aestheticLayout,
            "entitylist" : self.entityLayout,
            "switchingentitylist" : self.switchingEntityLayout
        }
        self.controller = controller
        self.dialog = None
        self.window = window
        self.layoutDialog()
        
    def layoutDialog(self, switch=""):
        if self.dialog != None:
            self.dialog.teardown()
        if switch == "entitylist":
            layout = self.layouts["switchingentitylist"]()
        else:
            currentLayer = self.controller.currentLayer
            if currentLayer is not None:
                '''setup the correct layout'''
                if currentLayer.name == "terrain" or \
                    currentLayer.name == "object":
                    layout = self.layouts["entitylist"]()
                else:
                    layout = self.layouts["aesthetic"]()
                layout.add(genOkCancelLayout(self.on_submit, self.on_cancel))
            else:
                #dont show dialog while no layer is selected
                return
        self.dialog = kytten.Dialog(Frame(layout),
            window=self.window, batch=self.window.dialogBatch,
            anchor=kytten.ANCHOR_CENTER, theme=theme)
        
    def aestheticLayout(self):
        def entitylist_click():
            self.layoutDialog(switch="entitylist")
        def delete_click():
            self.controller.graph.deleteLayer(self.controller.currentLayer.name)
            self.window.dispatch_event('on_layer_update')
        def visible_click(value):
            self.controller.setCurrentLayerProperties(visible=value)
        def opacity_on_set(value):
            self.controller.setCurrentLayerProperties(opacity=value)
            
        layer = self.controller.currentLayer
        if layer.name == "foreground":
            disableInputs = True
        else:
            disableInputs = False
        properties = GridLayout([
            [Label("Name"), Input("name", layer.name, max_length=20, abs_width=140, disabled=disableInputs)],
            [Label("Opacity"), kytten.Slider(layer.opacity, 0.0, 1.0, steps=10, on_set=opacity_on_set)],
            [Label("Visible"), Checkbox(is_checked=layer.visible, on_click=visible_click)],
            [Label("Z Order"), Input("z_order", str(layer.z_order), max_length=1, abs_width=35, disabled=disableInputs)],
            [Button("Entity List", on_click=entitylist_click), Button("Delete", on_click=delete_click, disabled=disableInputs)]
        ], padding=10)
        return VerticalLayout([
            SectionHeader("Aesthetic Layer", align=kytten.HALIGN_LEFT),
            properties,
            SectionHeader("", align=kytten.HALIGN_LEFT)
        ])
    
    def entityLayout(self):
        return VerticalLayout([
            SectionHeader("Entity List", align=kytten.HALIGN_LEFT),
            SectionHeader("", align=kytten.HALIGN_LEFT)
        ])
    
    def switchingEntityLayout(self):
        def on_cancel():
            pass
        def on_ok():
            pass
        def on_edit_layer():
            self.layoutDialog()
        if self.dialog != None:
            self.dialog.teardown()
        return VerticalLayout([
            self.entityLayout(),
            HorizontalLayout([
                Button("Edit Layer", on_click=on_edit_layer), 
                Button("Ok", on_click=on_ok), 
                Button("Cancel", on_click=on_cancel)
            ])
        ])
    
    def on_submit(self):
        layer = self.controller.currentLayer
        values = self.dialog.get_values()
        name = values["name"]
        self.controller.renameLayer(layer, name)
        self.window.dispatch_event('on_layer_update')
        self.controller.changeZOrder(layer, value)
        self.dialog.teardown()
    def on_enter(self):
        on_submit()
    def on_cancel(self):
        self.dialog.teardown()
        

class EditLevelDialog(Dialog):
    def __init__(self, window, batch, controller):
        self.controller = controller
        super(EditLevelDialog, self).__init__(
            Frame(
                    VerticalLayout([
                    Button("BG Color", on_click=self.bgColor_click),
                    Button("Source", on_click=self.source_click),
                    Button("Level Size", on_click=self.size_click),
                    SectionHeader("", align=kytten.HALIGN_LEFT),
                    genOkCancelLayout(self.on_submit, self.on_cancel)
                ])),
            window=window, batch=batch,
            anchor=kytten.ANCHOR_CENTER, theme=theme,
            on_enter=self.on_enter, on_escape=on_escape) 
            
    def bgColor_click(self):
        BackgroundColorDialog(self.window, self.batch, self.controller)
    
    def source_click(self):
        SourceDirectoryDialog(self.window, self.batch, self.controller)
        
    def size_click(self):
        LevelSizeDialog(self.window, self.batch, self.controller)
        
    def on_submit(self):
        values = self.get_values()
        #self.controller.graph.sourcePath = values['source']
        on_escape(self)
    
    def on_enter(self, dialog):
        self.on_submit()
    
    def on_cancel(self):
        on_escape(self)
            
            
class SourceDirectoryDialog(Dialog):
    '''
        allows the source directory to be chosen.
    '''
    def __init__(self, window, batch, controller):
        self.controller = controller
        currentPath = self.controller.graph.sourcePath
        super(SourceDirectoryDialog, self).__init__(
            Frame(VerticalLayout([
                Label("Source"),
                HorizontalLayout([
                    Input("source", currentPath,  max_length=20)
                ]),
                Spacer(height=20),
                genOkCancelLayout(self.on_submit, self.on_cancel)
            ])),
            window=window, batch=batch,
            anchor=kytten.ANCHOR_CENTER, theme=theme,
            on_enter=self.on_enter, on_escape=on_escape)
                
    def on_submit(self):
        values = self.get_values()
        self.controller.setSourcePath(values['source'])
        on_escape(self)
    
    def on_enter(self, dialog):
        self.on_submit()
    
    def on_cancel(self):
        on_escape(self)
        
        
class BackgroundColorDialog(Dialog):
    '''
        Allows the background colour of current map
        to be changed.
    '''
    def __init__(self, window, batch, controller):
        self.controller = controller
        bgcolor = self.controller.graph.backColour
        super(BackgroundColorDialog, self).__init__(
            Frame(VerticalLayout([
                Label("Select RGB"),
                HorizontalLayout([
                    Input("r", str(bgcolor[0]),  max_length=4, abs_width=60),
                    Input("g", str(bgcolor[1]),  max_length=4, abs_width=60),
                    Input("b", str(bgcolor[2]),  max_length=4, abs_width=60)
                    
                ]),
                Spacer(height=20),
                genOkCancelLayout(self.on_submit, self.on_cancel)
            ])),
            window=window, batch=batch,
            anchor=kytten.ANCHOR_CENTER, theme=theme,
            on_enter=self.on_enter, on_escape=on_escape)
                
    def on_submit(self):
        values = self.get_values()
        r = float(values['r'])
        g = float(values['g'])
        b = float(values['b'])
        self.controller.changeBackground(r,g,b)
        on_escape(self)
    
    def on_enter(self, dialog):
        self.on_submit()
    
    def on_cancel(self):
        on_escape(self)
        

class LevelSizeDialog(Dialog):
    '''
        allows user to create new level specifying properties
    '''
    def __init__(self, window, batch, controller):
        self.controller = controller
        width = str(self.controller.graph.width)
        height = str(self.controller.graph.height)
        super(LevelSizeDialog, self).__init__(
            Frame(
                VerticalLayout([
                    SectionHeader("Level Size", align=kytten.HALIGN_LEFT),
                    kytten.GridLayout([
                        [Label("Width"), Input("width", width,
                                                max_length=4)],
                        [Label("Height"), Input("height", height,
                                                max_length=4)]                                           
                    ]),
                    SectionHeader("", align=kytten.HALIGN_LEFT),
                    genOkCancelLayout(self.on_submit, self.on_cancel)
                ])),
            window=window, batch=batch,
            anchor=kytten.ANCHOR_CENTER, theme=theme,
            on_enter=self.on_enter, on_escape=on_escape)   
            
    def on_submit(self):
        values = self.get_values()
        #TODO get this to work.
        self.controller.graph.width = values["width"]
        self.controller.graph.height = values["height"]
        on_escape(self)
    def on_enter(self, dialog):
        self.on_submit()
    def on_cancel(self):
        on_escape(self)

 
class NewLayerDialog(Dialog):
    '''
        allows user to create new level specifying properties
    '''
    def __init__(self, window, batch, controller):
        self.controller = controller
        super(NewLayerDialog, self).__init__(
            Frame(
                VerticalLayout([
                    SectionHeader("New Aesthetic Layer", align=kytten.HALIGN_LEFT),
                    kytten.GridLayout([
                        [Label("Name"), Input("name", "untitled",
                                                max_length=20)],
                        [Label("Z Order"), Input("z_order", "3",
                                                max_length=1)]                                            
                    ]),
                    SectionHeader("", align=kytten.HALIGN_LEFT),
                    genOkCancelLayout(self.on_submit, self.on_cancel)
                ])),
            window=window, batch=batch,
            anchor=kytten.ANCHOR_CENTER, theme=theme,
            on_enter=self.on_enter, on_escape=on_escape)   
            
    def on_submit(self):
        values = self.get_values()
        name = values["name"]
        z_order = values["z_order"]
        self.controller.addAestheticLayer(name, z_order)
        self.window.dispatch_event('on_layer_update')
        on_escape(self)
        
    def on_enter(self, dialog):
        self.on_submit()
        
    def on_cancel(self):
        on_escape(self)
        

class StatusPane(Dialog):
    '''
    Controls a dialog that shows the user status information,
    and allows one to change some relevent settings
    '''
    def __init__(self, window, batch, controller):
        frame = self.createLayout()
        super(StatusPane, self).__init__(
            frame, window=window, batch=batch, 
            anchor=kytten.ANCHOR_BOTTOM, theme=theme)
        self.controller = controller
    
    def updateCoords(self):
        x = self.controller.mouseCoord[0]
        y = self.controller.mouseCoord[1]
        if self.controller.graph is not None:
            x = x - self.controller.graph.focusX
            y = y - self.controller.graph.focusY
        strX = "X: " + str(x)
        self.xLabel.set_text(strX)
        strY = "Y: " + str(y)
        self.yLabel.set_text(strY)
        
    def on_update_zoom(self):
        self.zoomLabel.set_text(str(self.controller.scale))
        
    def on_document_update(self):
        if self.controller.edited == True:
            text = "E"
        else:
            text = "U"
        self.editedLabel.set_text(text)

    def createLayout(self):
        def z_minus():
            self.controller.scale = self.controller.scale - 0.1
            self.zoomLabel.set_text(str(self.controller.scale))
        def z_add():
            self.controller.scale = self.controller.scale + 0.1
            self.zoomLabel.set_text(str(self.controller.scale))
        self.xLabel = Label("X:")
        self.yLabel = Label("Y:")
        self.zoomLabel = Label("1.0")
        self.editedLabel = Label("U")
        return Frame(HorizontalLayout([
            Spacer(10, 0),
            self.editedLabel,
            Spacer(10, 0),
            Button("z -", on_click=z_minus),
            self.zoomLabel,
            Button("z +", on_click=z_add),
            Spacer(10, 45),
            VerticalLayout([self.xLabel, self.yLabel]), 
            Spacer(10, 0),
            Button("Grid", on_click=self.gridDialog)
        ]), path=['pane'])
    
    def gridDialog(self):
        GridOptionsDialog(self.window, self.batch, self.controller)
    
    def on_update(self, dt):
        self.updateCoords()
        super(StatusPane, self).on_update(dt)


class GridOptionsDialog(Dialog):
    '''
        shows editable grid options.
    '''
    def __init__(self, window, batch, controller):
        self.grid = controller.grid
        self.controller = controller
        super(GridOptionsDialog, self).__init__(
            Frame(
                    VerticalLayout([
                        SectionHeader("Grid Options", align=kytten.HALIGN_LEFT),
                        Checkbox("Show Grid", id="show_grid", is_checked=self.grid.visible),
                        kytten.GridLayout([
                            [Label("H Spacing"), Input("h_spacing", str(self.grid.hSpacing), max_length=3)],
                            [Label("V Spacing"), Input("v_spacing", str(self.grid.vSpacing), max_length=3)],
                            [Label("H Offset"), Input("h_offset", str(self.grid.hOffset), max_length=3)],
                            [Label("V Offset"), Input("v_offset", str(self.grid.vOffset), max_length=3)]
                            ]),
                        SectionHeader("", align=kytten.HALIGN_LEFT),
                        genOkCancelLayout(self.on_submit, self.on_cancel),
                    ])),
                window=window, batch=batch,
                anchor=kytten.ANCHOR_CENTER, theme=theme,
                on_enter=self.on_enter, on_escape=on_escape)
                
    def on_submit(self):
        values = self.get_values()
        self.grid.visible = values["show_grid"]
        self.grid.hSpacing = int(values["h_spacing"])
        self.grid.vSpacing = int(values["v_spacing"])
        self.grid.hOffset = int(values["h_offset"])
        self.grid.vOffset = int(values["v_offset"])
        self.grid.update()
        on_escape(self)
    
    def on_enter(self):
        on_submit()
    
    def on_cancel(self):
        on_escape(self)
        

class ErrorDialog(Dialog):
    '''
        shows a specified error message.
    '''
    def __init__(self, window, batch, msg, title=None, fatal=False):
        if fatal == True:
            title = "Fatal: " + title
        elif title == None:
            title = "Error!"
        super(ErrorDialog, self).__init__(
            Frame(
                    VerticalLayout([
                        SectionHeader(title, align=kytten.HALIGN_LEFT),
                        Label(msg),
                        SectionHeader("", align=kytten.HALIGN_LEFT),
                        Button("Ok", on_click=self.on_submit),
                    ])),
                window=window, batch=batch,
                anchor=kytten.ANCHOR_CENTER, theme=theme,
                on_enter=self.on_enter, on_escape=on_escape)
    def on_submit(self):
        on_escape(self)
    def on_enter(self):
        on_submit()
    def on_cancel(self):
        on_escape(self)

        
        
class ConfirmExitDialog(Dialog):
    '''
    Controls a Dialog prompts User to save the level if edited and not saved
    '''    
    def __init__(self, window, batch, levelView):
        super(ConfirmExitDialog, self).__init__(
            Frame(
                VerticalLayout([
                    SectionHeader("Map Not Saved:", align=kytten.HALIGN_LEFT),
                    HorizontalLayout([
                        Button("Save", on_click=self.save),
                        Button("Dont Save", on_click=self.exitApp),
                        Button("Cancel", on_click=self.cancel)
                    ])
                ])
            ), window=window, batch=batch,
                anchor=kytten.ANCHOR_CENTER, theme=theme,
                on_escape=self.teardownDialog
        )
        self.controller = levelView
    
    def save(self):
        def on_select(filename):
            if filename.endswith(file_ext) == False:
                filename += file_ext
            self.controller.saveLevelToFile(filename)
            self.exitApp()
        kytten.FileSaveDialog(
            extensions=[file_ext], window=self.window,
            batch=self.batch, anchor=kytten.ANCHOR_CENTER,
            theme=theme, on_select=on_select)   
    
    def exitApp(self):
        self.controller.map = None
        pyglet.app.exit()
    
    def cancel(self):
        self.teardownDialog(self)
        
    def teardownDialog(self, dialog):
        super(ConfirmExitDialog, self).teardown()
    
'''        # detect double click and toggle fullscreen
        if self.time - self.lastClick <= 150:
            self.set_fullscreen(not self.fullscreen)
        self.lastClick = self.time'''
            
   
    
