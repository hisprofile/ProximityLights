bl_info = {
    "name" : "Proximity Lights",
    "description" : "Disable lights far away from the camera",
    "author" : "hisanimations",
    "version" : (1, 0),
    "blender" : (3, 0, 0),
    "location" : "Properties > Tools > Proximity Lights",
    "support" : "COMMUNITY",
    "category" : "Lighting",
}

import bpy, math
from bpy.types import *
from mathutils import *
class HISANIM_PT_LIGHTDIST(bpy.types.Panel):
    bl_label = "Proximity Lights"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_context = ''
    bl_category = 'Tool'

    def draw(self, context):
        layout = self.layout
        layout.label(text='Optimize lights in a scene')
        row = layout.row()
        row.prop(context.scene, 'hisaenablelightdist', text='Enable Light Optimization')
        row = layout.row()
        row.prop(context.scene.hisanimdrag, 'value', text='Max Distance From Camera')
        row.enabled = True if context.scene.hisaenablelightdist else False
        row = layout.row(align=True)
        row.operator('hisanim.lightoverride')
        row.operator('hisanim.hidelight')
        row.operator('hisanim.removeoverrides')
        row.enabled = True if len(context.selected_objects) >= 1 else False
        row = layout.row()
        row.operator('hisanim.revertlights')
        row.enabled = False if context.scene.hisaenablelightdist else True
        row = layout.row()
        row.prop(context.scene, 'hisanimmodulo', text='Refresh Every Amount of Frames')
        row = layout.row()
        row.prop(context.scene, 'hisanimframemodulo')
        row.enabled = True if context.scene.hisanimmodulo else False
        row=layout.row()
        row.prop(context.scene, 'hisanimenablespread', text='Spread Out Refresh')
        row.enabled = True if context.scene.hisanimmodulo else False
        row=layout.row()
        row.prop(context.scene, 'hisanimexclude', text='Superhide lights')
        row=layout.row()
        row.prop(context.scene, 'hisanimlightstats', text='Light Statistics')
        if context.scene.hisanimlightstats:
            layout.label(text=f'Active Lights: {GetActiveLights("ACTIVE")}{"/128 Max" if bpy.context.scene.render.engine=="BLENDER_EEVEE" else ""}') # get amount of lights using each light type
            layout.label(text=f'{str(GetActiveLights("OVERRIDDEN"))+ (" Overridden lights" if GetActiveLights("OVERRIDDEN") !=1 else " Overridden light")}')
            layout.label(text=f'''{str(GetLightTypes("POINT"))+(" point lights" if GetLightTypes("POINT")!=1 else " point light")}''')
            layout.label(text=f'''{str(GetLightTypes("SUN"))+(" sun lights" if GetLightTypes("SUN")!=1 else " sun light")}''')
            layout.label(text=f'''{str(GetLightTypes("SPOT"))+(" spot lights" if GetLightTypes("SPOT")!=1 else " spot light")}''')
            layout.label(text=f'''{str(GetLightTypes("AREA"))+(" area lights" if GetLightTypes("AREA")!=1 else " area light")}''')

#IsLight = lambda a: a.type=='LIGHT' # simple function used for filtering. if the object is a light, return True.
def IsLight(a):
    if a.type == 'LIGHT':
        return True
    elif a.type == 'EMPTY' and a.get('ISLIGHT'):
        return True


def IsHidden(a): # simple function used for filtering. if a light is hidden, return False.
    if bpy.data.objects[a.name].hide_get() == True:
        return False
    else:
        return True

def IsOverridden(a): # simple function used for filtering. if a light is overridden, return True.
    if a.type == 'EMPTY':
        return False
    if a.data.get('LIGHTOVERRIDE') != None:
        return True
    else:
        return False

def ExcludeLight(a, b):
    '''if bpy.data.collections.get('OFFLIGHTS') == None:
        x = bpy.data.collections.new('OFFLIGHTS')
        x.use_fake_user = True
        bpy.context.view_layer.layer_collection.children['OFFLIGHTS'].exclude = True
        bpy.context.view_layer.layer_collection.children['OFFLIGHTS'].hide_viewport = True
        bpy.data.collections['OFFLIGHTS'].hide_render = True'''
    if b == 'SHOW' and a.type != 'LIGHT':
        LIGHT = bpy.data.objects.new(a.name, bpy.data.lights[a.get('DATA')])
        bpy.context.scene.collection.objects.link(LIGHT)
        LIGHT.location = a.location
        LIGHT.rotation_euler = a.rotation_euler
        LIGHT.scale = a.scale
        LIGHT.data = bpy.data.lights[a.get('DATA')]
        LIGHT.name = a.get('NAME')
        bpy.data.objects.remove(a)
        
    if b == 'HIDE' and a.type != 'EMPTY':
        EMPTYLIGHT = bpy.data.objects.new('PRXLIGHT_PLACEHOLDER', None)
        EMPTYLIGHT.empty_display_type = 'PLAIN_AXES'
        EMPTYLIGHT.use_fake_user = True
        #EMPTYLIGHT = bpy.ops.object.empty_add(type='PLAIN_AXES')
        #EMPTYLIGHT.name = 'PRXLIGHT_PLACEHOLDER'
        EMPTYLIGHT.location = a.location
        EMPTYLIGHT.rotation_euler = a.rotation_euler
        EMPTYLIGHT.scale = a.scale
        EMPTYLIGHT['ISLIGHT'] = True
        EMPTYLIGHT['DATA'] = a.data.name
        EMPTYLIGHT['NAME'] = a.name
        if a.data.users == 1:
            a.data.use_fake_user = True
        bpy.data.objects.remove(a)
        
        
def GetLightTypes(a):
    # 4 lambda functions to determine what kind of light a light is.
    POINT = lambda a: a.data.type == 'POINT'
    SUN = lambda a: a.data.type == 'SUN'
    SPOT = lambda a: a.data.type == 'SPOT'
    AREA = lambda a: a.data.type == 'AREA'

    # return the amount of lights under each light type.

    if a == 'POINT':
        return len(list(filter(POINT, list(filter(IsLight, bpy.data.objects)))))
    if a == 'SUN':
        return len(list(filter(SUN, list(filter(IsLight, bpy.data.objects)))))
    if a == 'SPOT':
        return len(list(filter(SPOT, list(filter(IsLight, bpy.data.objects)))))
    if a == 'AREA':
        return len(list(filter(AREA, list(filter(IsLight, bpy.data.objects)))))

def GetActiveLights(stats):
    # 2 modes. return the amount of lights that are not hidden, return the amount of lights that are overridden
    if stats == 'ACTIVE':
        return len(list(filter(IsHidden, list(filter(IsLight, bpy.data.objects)))))
    else:
        return len(list(filter(IsOverridden, list(filter(IsLight, bpy.data.objects)))))

class HISANIM_OT_DRAGSUBSCRIBE(bpy.types.Operator):

    # taken from https://blender.stackexchange.com/questions/245233/drag-events-of-a-panel-ui-slider

    bl_idname = 'hisanim.dragsub'
    bl_label = ''
    stop: bpy.props.BoolProperty()

    def modal(self, context, event):
        if self.stop:
            context.scene.hisanimdrag.is_dragging = False
            bpy.data.objects.remove(bpy.data.objects['LIGHTDIST'])
            return {'FINISHED'}
        if event.value == 'RELEASE':
            self.stop = True

        return {'PASS_THROUGH'}
    def invoke(self, context, event):
        self.stop = False
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

def f(): # get current frame
    return bpy.context.scene.frame_current

def t(): # get desired frame modulo
    return bpy.context.scene.hisanimframemodulo

def OptimizeLights(self = None, context = None):
    if bpy.context.scene.hisaenablelightdist == False: # if the option to toggle light optimizations is set to False, do nothing
        return None
    LIGHTS = list(filter(IsLight, bpy.data.objects))
    l = list(range(0, len(LIGHTS))) # create a list of lights and a range of light amount
    if bpy.context.scene.hisanimenablespread and bpy.context.screen.is_animation_playing and bpy.context.scene.hisanimmodulo:
        # if Spread Out Refresh is enabled and the animation is playing and Refresh Every Amount of Frames is enabled, do this:
        for i in l[int((f() % t())*(len(l) / t())) : None if int(((f() + 1) % t())*(len(l) / t()))== 0 else int(((f() + 1) % t())*(len(l) / t()))]: # good luck figuring that out lol
            # it's a lot to explain. variable "l" contains a range starting from 0 ending at whatever the amount of lights in the scene is.
            # the slicing returns a section of the "l" variable. if frame modulo is set to 30 and there are 120 lights in a scene, then each frame will have 4 different lights Proximity Lights needs to figure out.
            # if the current frame % 30 == 15, it will return the 15th section of the list. i hope that clears things up
            '''if LIGHTS[i].data.get('LIGHTOVERRIDE') or LIGHTS[i].data.get('PERMHIDDEN'): # if the light has an override property, skip it
                continue'''
            if math.dist(bpy.context.scene.camera.location, LIGHTS[i].location) > bpy.context.scene.hisanimdrag.value*2 and LIGHTS[i].data.type != 'SUN': # if the light is outside of the defined distance and is not a sun, hide it 
                ExcludeLight(LIGHTS[i], 'HIDE')
            else: # do the opposite
                ExcludeLight(LIGHTS[i], 'SHOW')
    elif (f() % t() == 0) if bpy.context.scene.hisanimmodulo and bpy.context.screen.is_animation_playing else True: # refresh all at once, but do it once every other amount of frames when playing if enabled
        for i in LIGHTS:
            '''if i.data.get('LIGHTOVERRIDE') or i.data.get('PERMHIDDEN'):
                print(i.name, "HIDDEN")
                continue'''
            if math.dist(bpy.context.scene.camera.location, i.location) > bpy.context.scene.hisanimdrag.value*2 and not i.data.type == 'SUN':
                ExcludeLight(i, 'HIDE')
            else:
                ExcludeLight(i, 'SHOW')

class HISANIM_OT_LIGHTOVERRIDE(bpy.types.Operator):
    # make Proximity Lights skip lights that have been told to override
    bl_idname = 'hisanim.lightoverride'
    bl_label = 'Override Optimizer'
    bl_description = 'Lights that have an override property added to them will always show no matter how far away the camera is'

    def execute(self, context):
        for i in bpy.context.selected_objects:
            if i.type != "LIGHT" or i.data.get('LIGHTOVERRIDE') != None:
                continue
            i.data['LIGHTOVERRIDE'] = True
        return {'FINISHED'}

class HISANIM_OT_HIDELIGHT(bpy.types.Operator):
    # permanently hide lights (of, course this can be reverted)
    bl_idname = 'hisanim.hidelight'
    bl_label = 'Hide Light'
    bl_description = 'Permanently hide lights'

    def execute(self, context):
        for i in bpy.context.selected_objects:
            if i.type != "LIGHT" or i.data.get('PERMHIDDEN') != None:
                continue
            i.data['LIGHTOVERRIDE'] = True
            i.data['PERMHIDDEN'] = True
            i.hide_set(True)
            i.hide_render = True
        return {'FINISHED'}

class HISANIM_OT_REMOVEOVERRIDES(bpy.types.Operator):
    # delete any overrides
    bl_idname = 'hisanim.removeoverrides'
    bl_label = 'Remove Overrides'
    bl_description = 'Make a light hidable again by the Light Optimizer.'

    def execute(self, context):
        for i in bpy.context.selected_objects:
            if i.type != "LIGHT" or (i.data.get('LIGHTOVERRIDE') == None and i.data.get('PERMHIDDEN') == None):
                continue
            if i.data.get('LIGHTOVERRIDE'):
                del i.data['LIGHTOVERRIDE']
            if i.data.get('PERMHIDDEN'):
                i.hide_set(False)
                i.hide_render = False
                del i.data['PERMHIDDEN']
        return {'FINISHED'}

class HISANIM_OT_REVERTLIGHTS(bpy.types.Operator):
    #show all lights
    bl_idname = 'hisanim.revertlights'
    bl_label = 'Show All Lights'
    bl_description = 'Show all the lights that were left hidden by the optimizer'

    def execute(self, execute):
        for i in list(filter(IsLight, bpy.data.objects)):
            i.hide_set(False)
            i.hide_render = False
        return {'FINISHED'}

def hisanimupdates(self, value):
    # taken from https://blender.stackexchange.com/questions/245233/drag-events-of-a-panel-ui-slider
    C = bpy.context
    if self.is_dragging:
        OptimizeLights()
        # scale the empty while dragging
        bpy.data.objects['LIGHTDIST'].scale = Vector((self.value*2, self.value*2, self.value*2))
    else:
        # create an empty shaped as a sphere, scaled to the distanced from the camera defined by the user
        EMPTY = bpy.data.objects.new('LIGHTDIST', None)
        C.scene.collection.objects.link(EMPTY)
        EMPTY.empty_display_type = 'SPHERE'
        EMPTY.scale = Vector((self.value*2, self.value*2, self.value*2))
        EMPTY.location = C.scene.camera.location
        EMPTY.show_in_front = True
        OptimizeLights()
        self.is_dragging = True
        bpy.ops.hisanim.dragsub('INVOKE_DEFAULT')

class HISANIM_LIGHTDIST(bpy.types.PropertyGroup):
    value: bpy.props.FloatProperty(update=hisanimupdates, min=0.0, max=1000.0, step=25, default=25.0)
    is_dragging: bpy.props.BoolProperty()

classes = [HISANIM_PT_LIGHTDIST,
            HISANIM_OT_DRAGSUBSCRIBE,
            HISANIM_LIGHTDIST,
            HISANIM_OT_LIGHTOVERRIDE,
            HISANIM_OT_REMOVEOVERRIDES,
            HISANIM_OT_REVERTLIGHTS,
            HISANIM_OT_HIDELIGHT]

from bpy.app.handlers import persistent

@persistent
def crossover(dummy):
    bpy.app.handlers.frame_change_post.append(OptimizeLights)

def register():
    for i in classes:
        bpy.utils.register_class(i)
    bpy.types.Scene.hisanimlightdist = bpy.props.FloatProperty(min=0.0, default=25.0, step=0.1)
    bpy.types.Scene.hisaenablelightdist = bpy.props.BoolProperty()
    bpy.types.Scene.hisanimdrag = bpy.props.PointerProperty(type=HISANIM_LIGHTDIST)
    bpy.app.handlers.frame_change_post.append(OptimizeLights)
    bpy.app.handlers.load_post.append(crossover)
    bpy.types.Scene.hisanimframemodulo = bpy.props.IntProperty(default=1, min=1, name='Frame Modulo', description='Have all the lights refresh every other amount of frames')
    bpy.types.Scene.hisanimenablespread = bpy.props.BoolProperty()
    bpy.types.Scene.hisanimmodulo = bpy.props.BoolProperty()
    bpy.types.Scene.hisanimlightstats = bpy.props.BoolProperty(default=True)
    bpy.types.Scene.hisanimexclude = bpy.props.BoolProperty(default=True, description='Move lights into an excluded collection. May help prevent crashes')
    
def unregister():
    for i in classes:
        bpy.utils.unregister_class(i)
    del bpy.types.Scene.hisanimframemodulo
    del bpy.types.Scene.hisanimlightdist
    del bpy.types.Scene.hisaenablelightdist
    del bpy.types.Scene.hisanimdrag
    del bpy.types.Scene.hisanimenablespread
    del bpy.types.Scene.hisanimmodulo
    del bpy.types.Scene.hisanimlightstats
    del bpy.types.Scene.hisanimexclude
    try:
        bpy.app.handlers.load_post.remove(crossover)
    except:
        pass
    try:
        bpy.app.handlers.frame_change_post.remove(OptimizeLights)
    except:
        pass

if __name__ == '__main__':
    register()