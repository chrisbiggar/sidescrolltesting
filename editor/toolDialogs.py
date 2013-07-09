'''
Tool Dialogs

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
from kytten.checkbox import Checkbox
import widgets
import dialogs
from dialogs import genOkCancelLayout, theme, on_escape
import appEngine.scenegraph as scenegraph

class ToolDialog(object):
    '''
        controls dialog that allows user to manipulate layers
        by dynamically while current type of layer is selected
        showing given controls for type of layer.
    '''   
    def __init__(self, editor):
        self.layouts = {
            "terrain" : self.terrainLayout,
            "aesthetic" : self.itemLayout,
            "object" : self.itemLayout
        }
        editor.push_handlers(self)
        self.controller = editor.controller
        self.dialog = None
        self.window = editor
        self.previousChoice = None
        self.selectedItemLabel = None
    
    def delete(self):
        if self.dialog is not None:
            self.dialog.teardown()
            self.dialog = None
            
    def on_layer_update(self):
        layer = self.controller.currentLayer
        if layer == None:
            self.delete()
            return
        if self.dialog != None:
            self.dialog.teardown()
        # create layout according to editor mode
        if layer.name == "terrain" or layer.name == "object":
            name = layer.name
        else:
            name = "aesthetic"
        self.layout = self.layouts[name]()
        self.dialog = Dialog(Frame(VerticalLayout([self.layout])),
            window=self.window, batch=self.window.dialogBatch,
            anchor=kytten.ANCHOR_TOP_LEFT, theme=theme)
            
    def on_tool_select(self, id):
        self.active_tool = id
        self.controller.setCurrentTool(id)
        # reset the selected item dialog
        if self.window.selectedItemDialog.dialog != None:
            self.window.selectedItemDialog.dialog.teardown()
            
            
    def on_item_select(self, item):
        self.selectedItemLabel.set_text(item)
        path = os.path.join("assets", self.controller.currentLayer.dir, item)
        self.selectedItemImage.setImage(pyglet.image.load(path))
        self.controller.tools['placeitem'].setSelectedItem(path)

    def terrainLayout(self):
        '''
        creates terrain layer manip dialog.
        syncing with current options
        '''
        def on_snapmode_click(is_checked):
            self.controller.tools['plotline'].snapMode = is_checked

        def on_colour_select(choice):
            self.controller.graph.layers['terrain'].setLineColor(choice)
        
        toolSet = []
        toolSet.append(('pan', pyglet.image.load(
            os.path.join('theme', 'tools', 'pan.png'))))
        toolSet.append(('plotline', pyglet.image.load(
            os.path.join('theme', 'tools', 'plotline.png'))))
        toolSet.append(('select',pyglet.image.load(
            os.path.join('theme', 'tools', 'select.png'))))
            
        # Create options from images to pass to Palette
        palette_options = [[]]
        palette_options.append([])
        palette_options.append([])
        for i, pair in enumerate(toolSet):
            option = widgets.PaletteOption(id=pair[0], image=pair[1], padding=4)
            # Build column down, 3 rows
            palette_options[i%2].append(option)
        toolSection = widgets.PaletteMenu(palette_options, on_select=self.on_tool_select)
        
        '''
        sync dropdown colour selection
        '''
        keys = self.controller.currentLayer.colors.items()
        for key in keys:
            if key[1] == self.controller.currentLayer.curColor:
                colour = key[0]
                break
        
        return VerticalLayout([
            toolSection,
            SectionHeader("", align=kytten.HALIGN_LEFT),
            Label("Line Colour"),
            kytten.Dropdown(["White", "Black", "Blue", "Green", "Red"], selected=colour, on_select=on_colour_select),
            Checkbox("Point Snap", is_checked=self.controller.tools["plotline"].snapMode, on_click=on_snapmode_click),
            Checkbox("Grid Snap", id="snap_to", is_checked=True)
        ])
    
    '''
    
    '''
    def itemLayout(self):
        def on_select_item():
            SelectItemDialog(self.window, self.controller.currentLayer, self)
            
        toolSet = []
        toolSet.append(('pan', pyglet.image.load(
            os.path.join('theme', 'tools', 'pan.png'))))
        toolSet.append(('placeitem', pyglet.image.load(
            os.path.join('theme', 'tools', 'object.png'))))
        toolSet.append(('select',pyglet.image.load(
            os.path.join('theme', 'tools', 'select.png'))))
            
        # Create options from images to pass to Palette
        palette_options = [[]]
        palette_options.append([])
        palette_options.append([])
        for i, pair in enumerate(toolSet):
            option = widgets.PaletteOption(id=pair[0], image=pair[1], padding=4)
            # Build column down, 3 rows
            palette_options[i%2].append(option)
        toolSection = widgets.PaletteMenu(palette_options, on_select=self.on_tool_select)
        
        '''
        selected item display
        ''' 
        self.selectedItemLabel = Label("")
        self.selectedItemImage = widgets.Image(None,  maxWidth=128, maxHeight=164)
        
        return VerticalLayout([
            Label(self.controller.currentLayer.name),
            toolSection,
            SectionHeader("Selected Item", align=kytten.HALIGN_LEFT),
            self.selectedItemLabel,
            self.selectedItemImage,
            SectionHeader("", align=kytten.HALIGN_LEFT),
            Checkbox("Grid Snap", id="snap_to", is_checked=True),
            Checkbox("Sticky Mode", id="sticky_mode", is_checked=True),
            SectionHeader("", align=kytten.HALIGN_LEFT),
            kytten.Button("Select Item", on_click=on_select_item)
        ])
        

class SelectItemDialog(Dialog):
    '''
        allows user to select aesthetic or object item
    '''
    def __init__(self, window, currentLayer, layerDialog):
        self.controller = window.controller
        self.layerDialog = layerDialog
        layout = self.createLayout(currentLayer)
        super(SelectItemDialog, self).__init__(
            Frame(layout),
                window=window, batch=window.dialogBatch,
                anchor=kytten.ANCHOR_CENTER, theme=theme,
                on_enter=self.on_enter, on_escape=on_escape)
                
    def createLayout(self, currentLayer):
        '''
        build list of items with name and image
        '''
        path = os.path.join("assets", currentLayer.dir)
        items = list()
        for (path, dirs, files) in os.walk(path):
            for file in files:
                if file.endswith(".png"):
                    items.append([file, pyglet.image.load(os.path.join(path, file))])
        
        if len(items) == 0:
            itemsMenu = Label("No Items Found")
        else:
             itemsMenu = kytten.Scrollable(widgets.ItemMenu(items, on_select=self.layerDialog.on_item_select),
                    height=600)
                
        return VerticalLayout([
            itemsMenu,
            SectionHeader("", align=kytten.HALIGN_LEFT),
            genOkCancelLayout(self.on_submit, self.on_cancel)
        ])
    
    def on_cancel(self):
        on_escape(self)
    def on_submit(self):
        self.on_enter(self)
    def on_enter(self, dialog):
        on_escape(self)


class SelectedItemDialog(object):
    '''
        indicated currently selected and item and displays editable properties
    '''
    currentItem = None
    def __init__(self, editor):
        self.dialog = None
        self.controller = editor.controller
        self.window = editor
        self.updateItem()
        
    def on_select_item(self):
        item = self.controller.tools["select"].selectedItem
        self.updateItem(item)
        
    def updateItem(self, item=None):
        if self.dialog != None:
            self.dialog.teardown()
        if item == None:
            self.currentItem = None
        else:
            self.currentItem = item
            if self.controller.currentLayer.name == "terrain":
                layout = self.lineLayout()
            elif self.controller.currentLayer.name == "object":
                layout = self.objectLayout()
            else:
                layout = self.visualLayout()
            self.dialog = kytten.Dialog(
                Frame(kytten.FoldingSection("Item",layout)),
                window=self.window, batch=self.window.dialogBatch,
                anchor=kytten.ANCHOR_BOTTOM_LEFT, theme=theme)
    
    def objectLayout(self):
        def x_input(text):
            self.currentItem.updatePosition(x=int(text))
            self.controller.edited = True
        def y_input(text):
            self.currentItem.updatePosition(y=int(text))
            self.controller.edited = True
        item = self.currentItem
        return GridLayout([
            [Label("Name"), Input(text=item.name, abs_width=100, disabled=True)],
            [Label("X Pos"), Input(text=str(item.x), abs_width=50, max_length=4, on_input=x_input)],
            [Label("Y Pos"), Input(text=str(item.y), abs_width=50, max_length=4, on_input=y_input)],
            [Label("Width"), Input(text=str(item.x2-item.x), abs_width=50, max_length=4, disabled=True)],
            [Label("Height"), Input(text=str(item.y2-item.y), abs_width=50, max_length=4, disabled=True)]], 
            padding=18)
    
    def visualLayout(self):
        def x_input(text):
            self.currentItem.updatePosition(x=int(text))
            self.controller.edited = True
        def y_input(text):
            self.currentItem.updatePosition(y=int(text))
            self.controller.edited = True
        item = self.currentItem
        return GridLayout([
            [Label("Name"), Input(text=item.name, abs_width=100, disabled=True)],
            [Label("X Pos"), Input(text=str(item.x), abs_width=50, max_length=4, on_input=x_input)],
            [Label("Y Pos"), Input(text=str(item.y), abs_width=50, max_length=4, on_input=y_input)],
            [Label("Width"), Input(text=str(item.x2-item.x), abs_width=50, max_length=4, disabled=True)],
            [Label("Height"), Input(text=str(item.y2-item.y), abs_width=50, max_length=4, disabled=True)]
            ], padding=18)
    
    def lineLayout(self):
        item = self.currentItem
        def x1_input(text):
            item.updatePosition(x1=int(text))
            self.controller.edited = True
        def y1_input(text):
            item.updatePosition(y1=int(text))
            self.controller.edited = True
        def x2_input(text):
            item.updatePosition(x2=int(text))
            self.controller.edited = True
        def y2_input(text):
            item.updatePosition(y2=int(text))
            self.controller.edited = True
        return GridLayout([
            [Label("X1 Pos"), Input("x1_pos", str(item.x1), abs_width=50, max_length=5)],
            [Label("Y1 Pos"), Input("y1_pos", str(item.y1), abs_width=50, max_length=5)],
            [Label("X2 Pos"), Input("x2_pos", str(item.x2), abs_width=50, max_length=5)],
            [Label("Y2 Pos"), Input("y2_pos", str(item.y2), abs_width=50, max_length=5)]
        ], padding=18)
