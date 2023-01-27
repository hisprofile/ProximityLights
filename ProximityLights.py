bl_info = {
    "name" : "Proximity Lights",
    "description" : "Disable lights far away from the camera",
    "author" : "hisanimations",
    "version" : (1, 2, 1),
    "blender" : (3, 0, 0),
    "location" : "Properties > Tools > Proximity Lights",
    "support" : "COMMUNITY",
    "category" : "Lighting",
}
# made to help prevent lighting crashes/improve performance in scene's with a high light count
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
        row.prop_search(context.scene, 'prxlightcollection', bpy.data, 'collections', text='Light Collection')
        row=layout.row()
        row.prop(context.scene, 'hisanimlightstats', text='Light Statistics')
        if context.scene.hisanimlightstats:
            layout.label(text=f'Active Lights: {GetActiveLights("ACTIVE")}{"/128 Max" if bpy.context.scene.render.engine=="BLENDER_EEVEE" else ""}') # get amount of lights using each light type
            layout.label(text=f'{str(GetActiveLights("OVERRIDDEN"))+ (" Overridden lights" if GetActiveLights("OVERRIDDEN") !=1 else " Overridden light")}')
            layout.label(text=f'''{str(GetLightTypes("POINT"))+(" point lights" if GetLightTypes("POINT")!=1 else " point light")}''')
            layout.label(text=f'''{str(GetLightTypes("SUN"))+(" sun lights" if GetLightTypes("SUN")!=1 else " sun light")}''')
            layout.label(text=f'''{str(GetLightTypes("SPOT"))+(" spot lights" if GetLightTypes("SPOT")!=1 else " spot light")}''')
            layout.label(text=f'''{str(GetLightTypes("AREA"))+(" area lights" if GetLightTypes("AREA")!=1 else " area light")}''')

# simple function used for filtering. if the object is or intended to be a light, return True.
def IsLight(a):
    if a.type == 'LIGHT':
        return True
    elif a.type == 'EMPTY' and a.get('ISLIGHT'):
        return True


def IsHidden(a): # simple function used for filtering. essentially counts how many lights are visible in the scene.
    if bpy.data.objects[a.name].type != 'LIGHT':
        return False
    else:
        return True

def IsOverridden(a): # simple function used for filtering. if a light is overridden, return True.
    if a.type == 'EMPTY':
        return False
    if a.get('LIGHTOVERRIDE') != None:
        return True
    else:
        return False

def ExcludeLight(a, b, c= None): # multi-purpose light excluder.
    # if a light is given instructions to hide:
    # 1. an empty will take its place
    # 2. the empty will store the light's data,
    # location, rotation, scale, and linked collection
    # in the form of custom property strings
    # 3. the light will be deleted, and its data will be stored.
    
    # if a "light" (empty) is given instructions to show:
    # 1. a new light will be created using the data stored
    # in the empty
    # 2. the light will reuse loc, rot, scale, and collection data
    # 3. the light will be linked to its former collection
    # 4. the empty will be deleted.
    if b == 'SHOW' and a.type != 'LIGHT':
        LIGHT = bpy.data.objects.new(a.name, bpy.data.lights[a.get('DATA')])
        LIGHT.location = a.location
        LIGHT.rotation_euler = a.rotation_euler
        LIGHT.scale = a.scale
        LIGHT.data = bpy.data.lights[a.get('DATA')]
        LIGHT.name = a.get('NAME')
        if bpy.data.collections.get(a.get('COLLECTION')) != None:
            bpy.data.collections[a.get('COLLECTION')].objects.link(LIGHT)
        else:
            bpy.context.scene.collection.objects.link(LIGHT)
        bpy.data.objects.remove(a)
        
    if b == 'HIDE' and a.type != 'EMPTY':
        EMPTYLIGHT = bpy.data.objects.new('PRXLIGHT_PLACEHOLDER', None)
        EMPTYLIGHT.empty_display_type = 'PLAIN_AXES'
        EMPTYLIGHT.use_fake_user = True
        EMPTYLIGHT.location = a.location
        EMPTYLIGHT.rotation_euler = a.rotation_euler
        EMPTYLIGHT.scale = a.scale
        EMPTYLIGHT['ISLIGHT'] = True
        EMPTYLIGHT[a.data.type] = True
        EMPTYLIGHT['DATA'] = a.data.name
        EMPTYLIGHT['NAME'] = a.name
        EMPTYLIGHT['COLLECTION'] = a.users_collection[0].name
        EMPTYLIGHT['HIDDEN'] = True
        if bpy.data.collections.get(EMPTYLIGHT.get('COLLECTION')) != None:
            bpy.data.collections[EMPTYLIGHT.get('COLLECTION')].objects.link(EMPTYLIGHT)
        else:
            bpy.context.scene.collection.objects.link(EMPTYLIGHT)
        if c == True:
            EMPTYLIGHT['PERMHIDDEN'] = True
        if a.data.users == 1:
            a.data.use_fake_user = True
        bpy.data.objects.remove(a)
        
# there is a specific reason why i was forced to do this. my 2 other options to go about this were:
# 1. to hide the lights from the viewport and render
# 2. to move the lights into an excluded collection
# doing all of this was fine. manually hiding or excluding lights worked well with blender, and whenever i
# tried to render, the render went through without crashing. obviously, it's preferred to automate this process
# with a script. originally, this script did just that. however, activating the addon in a scene with a high light
# count appeared to hinder the integrity of the .blend file. automatically optimizing the lights would *always* result in a crash.
# the crash logs said this was due to something regarding a "layer_collection_sync" or something like that.
# so automatically hiding or moving lights was not a fit option. my last idea was to unload them by replacing outbound
# lights with an empty. fortunately, this worked! i was no longer needed to search for a solution, and was able to
# move on with the TF2 Map Pack. rendering no longer crashes.

        
def GetLightTypes(a):
    # 4 functions to determine what kind of light a light is.
    # if an object has a custom property that defines it as a point/sun/spot/area light,
    # return true. however, if the object is an empty but does not have a tag, return false.
    # but if the object is at least a light and is a point/sun/spot/area light, return true.
    def POINT(a):
        if a.get('POINT') != None:
            return True
        if a.type != 'LIGHT':
            return False
        if a.data.type == 'POINT':
            return True
    def SUN(a):
        if a.get('SUN') != None:
            return True
        if a.type != 'LIGHT':
            return False
        if a.data.type == 'SUN':
            return True
    def SPOT(a):
        if a.get('SPOT') != None:
            return True
        if a.type != 'LIGHT':
            return False
        if a.data.type == 'SPOT':
            return True
    def AREA(a):
        if a.get('AREA') != None:
            return True
        if a.type != 'LIGHT':
            return False
        if a.data.type == 'AREA':
            return True
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
    if bpy.context.scene.prxlightcollection == None:
        LIGHTS = list(filter(IsLight, bpy.data.objects))
    else:
        LIGHTS = list(filter(IsLight, bpy.context.scene.prxlightcollection.objects))
    l = list(range(0, len(LIGHTS))) # create a list of lights and a range of light amount
    if bpy.context.scene.hisanimenablespread and bpy.context.screen.is_animation_playing and bpy.context.scene.hisanimmodulo:
        # if Spread Out Refresh is enabled and the animation is playing and Refresh Every Amount of Frames is enabled, do this:
        for i in l[int((f() % t())*(len(l) / t())) : None if int(((f() + 1) % t())*(len(l) / t()))== 0 else int(((f() + 1) % t())*(len(l) / t()))]: # good luck figuring that out lol
            # it's a lot to explain. variable "l" contains a range starting from 0 ending at whatever the amount of lights in the scene is.
            # the slicing returns a section of the "l" variable. if frame modulo is set to 30 and there are 120 lights in a scene, then each frame will have 4 different lights Proximity Lights needs to figure out.
            # if the current frame % 30 == 15, it will return the 15th section of the list. i hope that clears things up
            
            # as of the 27th of January, this does not work and i am not sure why.
            
            if LIGHTS[i].get('LIGHTOVERRIDE') or LIGHTS[i].get('PERMHIDDEN'): # if the light has an override property, skip it
                continue
            if math.dist(bpy.context.scene.camera.location, LIGHTS[i].location) > bpy.context.scene.hisanimdrag.value*2 and LIGHTS[i].data.type != 'SUN': # if the light is outside of the defined distance and is not a sun, hide it 
                ExcludeLight(LIGHTS[i], 'HIDE')
            else: # do the opposite
                ExcludeLight(LIGHTS[i], 'SHOW')
    elif (f() % t() == 0) if bpy.context.scene.hisanimmodulo and bpy.context.screen.is_animation_playing else True: # refresh all at once, but do it once every other amount of frames when playing if enabled
        for i in LIGHTS:
            if i.get('LIGHTOVERRIDE') or i.get('PERMHIDDEN'):
                continue
            if math.dist(bpy.context.scene.camera.location, i.location) > bpy.context.scene.hisanimdrag.value*2:# and not i.data.type == 'SUN':
                if i.type == 'LIGHT':
                    if i.data.type == 'SUN':
                        continue
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
            if i.type != "LIGHT" or i.get('LIGHTOVERRIDE') != None:
                continue
            i['LIGHTOVERRIDE'] = True
        return {'FINISHED'}

class HISANIM_OT_HIDELIGHT(bpy.types.Operator):
    # permanently hide lights (of, course this can be reverted)
    bl_idname = 'hisanim.hidelight'
    bl_label = 'Hide Light'
    bl_description = 'Permanently hide lights'

    def execute(self, context):
        for i in bpy.context.selected_objects:
            if i.type != "LIGHT" or i.get('PERMHIDDEN') != None:
                continue
            ExcludeLight(i, 'HIDE', True)
        return {'FINISHED'}

class HISANIM_OT_REMOVEOVERRIDES(bpy.types.Operator):
    # delete any overrides from selected objects
    bl_idname = 'hisanim.removeoverrides'
    bl_label = 'Remove Overrides'
    bl_description = 'Make a light hidable again by the Light Optimizer.'

    def execute(self, context):
        for i in bpy.context.selected_objects:
            if i.type != "LIGHT" or (i.get('LIGHTOVERRIDE') == None and i.get('PERMHIDDEN') == None):
                continue
            if i.get('LIGHTOVERRIDE'):
                del i['LIGHTOVERRIDE']
            if i.get('PERMHIDDEN'):
                i.hide_set(False)
                i.hide_render = False
                del i['PERMHIDDEN']
        return {'FINISHED'}

class HISANIM_OT_REVERTLIGHTS(bpy.types.Operator):
    #show all lights
    bl_idname = 'hisanim.revertlights'
    bl_label = 'Show All Lights'
    bl_description = 'Show all the lights that were left hidden by the optimizer'

    def execute(self, execute):
        for i in list(filter(IsLight, bpy.data.objects)):
            ExcludeLight(i, 'SHOW')
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
    bpy.types.Scene.prxlightcollection = bpy.props.PointerProperty(type=bpy.types.Collection, description='Only iterate through one collection. May improve performance')
    
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
