bl_info = {
    "name" : "Proximity Lights",
    "description" : "Disable lights far away from the camera",
    "author" : "hisanimations",
    "version" : (1, 3),
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
        row.operator('hisanim.mixpower')
        row = layout.row()
        row.prop(context.scene, 'hisanimhardclamp')
        if context.scene.hisanimhardclamp:
            row = layout.row()
            row.prop(context.scene, 'hisanimclamprange')
        if context.scene.hisanimmixpower:
            col = layout.column(align=True)
            col.prop(context.scene, 'hisanimstartfrom')
            col.prop(context.scene, 'hisanimendat')
        row=layout.row()
        row.prop(context.scene, 'hisanimlightstats', text='Light Statistics')
        if context.scene.hisanimlightstats:
            layout.label(text=f'Active Lights: {GetActiveLights("ACTIVE")}{"/128 Max" if bpy.context.scene.render.engine=="BLENDER_EEVEE" else ""}') # get amount of lights using each light type
            layout.label(text=f'{str(GetActiveLights("OVERRIDDEN"))+ (" Overridden lights" if GetActiveLights("OVERRIDDEN") !=1 else " Overridden light")}')
            layout.label(text=f'''{str(GetLightTypes("POINT"))+(" point lights" if GetLightTypes("POINT")!=1 else " point light")} ({len(list(filter(IsHidden, GetLightTypes("POINT", "VERBOSE"))))} active)''')
            layout.label(text=f'''{str(GetLightTypes("SUN"))+(" sun lights" if GetLightTypes("SUN")!=1 else " sun light")}''')
            layout.label(text=f'''{str(GetLightTypes("SPOT"))+(" spot lights" if GetLightTypes("SPOT")!=1 else " spot light")} ({len(list(filter(IsHidden, GetLightTypes("SPOT", "VERBOSE"))))} active)''')
            layout.label(text=f'''{str(GetLightTypes("AREA"))+(" area lights" if GetLightTypes("AREA")!=1 else " area light")} ({len(list(filter(IsHidden, GetLightTypes("AREA", "VERBOSE"))))} active)''')

def MAP(x,a,b,c,d, clamp=None):
   y=(x-a)/(b-a)*(d-c)+c
   
   if clamp:
       return min(max(y, c), d)
   else:
       return y
   
# simple function used for filtering. if the object is or intended to be a light, return True.

def IsLight(a):
    if a.type == 'LIGHT' and a.get('PERMHIDDEN') == None:
        return True
    elif a.type == 'EMPTY' and a.get('ISLIGHT'):
        return True
    
def IsLightNoIgnore(a):
    if a.type == 'LIGHT':
        return True

def IsHidden(a): # simple function used for filtering. essentially counts how many lights are visible in the scene.
    if a.data.energy == 0.0:
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
    if b == 'SHOW' and a.data.get('DEFAULT') != None:
        LIGHT = a
        if bpy.context.scene.hisanimmixpower and a.get('POWER') != None:
            LIGHT.data['POWER'] = a.get('POWER')
            LIGHT.data.energy  = MAP(math.dist(CS.camera.location, LIGHT.location), DIST-(CS.hisanimstartfrom*DIST), DIST-(CS.hisanimendat*DIST), 0, a.get('POWER'), True)
        else:
            LIGHT.data.energy = LIGHT.data['DEFAULT']
            del LIGHT.data['DEFAULT']
        
        
    if b == 'HIDE' and a.data.get('DEFAULT') == None:#(a.data.get('DEFAULT') == None) if c != True else True:
        if a.data.get('POWER') == None:
            a.data['DEFAULT'] = a.data.energy
        else:
            a.data['DEFAULT'] = a.data['POWER']
        a.data.energy = 0.0
        if c == True:
            a['PERMHIDDEN'] = True
            
    if b == 'PERMHIDDEN':
        if a.data.get('DEFAULT') == None:
            a.data['DEFAULT'] = a.data.energy
        a.data.energy = 0
        a['PERMHIDDEN'] = True
    
    return a
        
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

'''strike all of that! i was comPLETELY wrong. i wrote that comment on 1/24/23 i think? it's 2/2/23 now. anyways, the old method was this:
unload lights from the scene by replacing them with an empty that contained all the lights' information when the light
was outside of the range from the camera. once an empty was within range again, a light would be spawned from it using the
information the empty contained, and then the empty was deleted. it was slow, but it worked! until it didn't! blender
still crashed when rendering cause there was just too much to do between every frame. it crashed for a totally different
reason as well. 5 days later, i had found out that when a light's energy is set to 0, the light gets ignored by the scene.
https://cdn.discordapp.com/attachments/723010093033062540/1065294547535540364/image.png mfw
i NEVER knew about that before. so with my newfound knowledge, i rewrote parts of Proximity Lights to make lights get set to 0.
the result? a product that was like 700% more efficient. playing back animation was faster, changing the range was faster,
everything was faster. and with so little that Proximity Lights needs to do, it was a lot more stable. with this new method
now realized, i made a test render of ctf_doublecross without modifying a single light (except through proximity lights of course.)
https://twitter.com/his_animations/status/1619790423849041920 the whole thing rendered without crashing. it was awesome!

For the most part, Proximity Lights is finished.'''
        
def GetLightTypes(a, b=None):
    # 4 functions to determine what kind of light a light is.
    # if an object has a custom property that defines it as a point/sun/spot/area light,
    # return true. however, if the object is an empty but does not have a tag, return false.
    # but if the object is at least a light and is a point/sun/spot/area light, return true.
    POINT = lambda a: a.data.type == 'POINT'
    SUN = lambda a: a.data.type == 'SUN'
    SPOT = lambda a: a.data.type == 'SPOT'
    AREA = lambda a: a.data.type == 'AREA'
    # return the amount of lights under each light type.

    if a == 'POINT':
        if b == 'VERBOSE':
            return list(filter(POINT, list(filter(IsLightNoIgnore, bpy.data.objects))))
        return len(list(filter(POINT, list(filter(IsLightNoIgnore, bpy.data.objects)))))
    if a == 'SUN':
        if b == 'VERBOSE':
            return list(filter(SUN, list(filter(IsLightNoIgnore, bpy.data.objects))))
        return len(list(filter(SUN, list(filter(IsLightNoIgnore, bpy.data.objects)))))
    if a == 'SPOT':
        if b == 'VERBOSE':
            return list(filter(SPOT, list(filter(IsLightNoIgnore, bpy.data.objects))))
        return len(list(filter(SPOT, list(filter(IsLightNoIgnore, bpy.data.objects)))))
    if a == 'AREA':
        if b == 'VERBOSE':
            return list(filter(AREA, list(filter(IsLightNoIgnore, bpy.data.objects))))
        return len(list(filter(AREA, list(filter(IsLightNoIgnore, bpy.data.objects)))))

def GetActiveLights(stats=None):
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

def t(): # get user desired frame modulo
    return bpy.context.scene.hisanimframemodulo

def OptimizeLights(self = None, context = None):
    CS = bpy.context.scene
    LIGHTDICT = {}
    if CS.hisaenablelightdist == False: # if the option to toggle light optimizations is set to False, do nothing
        return None
    if CS.prxlightcollection == None:
        LIGHTS = list(filter(IsLight, bpy.data.objects))
    else:
        LIGHTS = list(filter(IsLight, CS.prxlightcollection.objects))
    l = list(range(0, len(LIGHTS))) # create a list of lights and a range of light amount
    DIST = CS.hisanimdrag.value
    if CS.hisanimhardclamp: # if light clamping is enabled
        GetLight = lambda a: bpy.data.objects[a] # return the object data type of the string
        for i in LIGHTS:
            if i.data.type == 'SUN' or i.get('LIGHTOVERRIDE') != None:
                LIGHTDICT[i.name] = 0.0
                continue
            LIGHTDICT[i.name] = math.dist(CS.camera.location, i.location)
            #LIGHTDICT[i.name] = math.dist(CS.camera.location, i.location) if i.get('LIGHTOVERRIDE') == None else 0.0 # create a dictionary containing the light's name and distance from camera
        CLOSELIGHTS = list(map(GetLight, [*dict(sorted(LIGHTDICT.items(), key=lambda x:x[1])).keys()])) # sort the dictionary based on the keys' values, and turn each string into a blender object type
        if len(CLOSELIGHTS) > CS.hisanimclamprange:
            for i in CLOSELIGHTS[None if len(CLOSELIGHTS) <CS.hisanimclamprange else (len(CLOSELIGHTS)-CS.hisanimclamprange)*-1:]:
                if i.get('LIGHTOVERRIDE') == None or i.data.type != 'SUN':
                    ExcludeLight(i, 'HIDE') # go through every light past the clamp's index in the list and turn it off
        LIGHTS = CLOSELIGHTS[:None if len(CLOSELIGHTS) <CS.hisanimclamprange else (len(CLOSELIGHTS)-CS.hisanimclamprange)*-1] # update the list of lights to only include the lights within the camera's range
    if CS.hisanimenablespread and bpy.context.screen.is_animation_playing and CS.hisanimmodulo:
        # if Spread Out Refresh is enabled and the animation is playing and Refresh Every Amount of Frames is enabled, do this:
        for i in l[int((f() % t())*(len(l) / t())) : None if int(((f() + 1) % t())*(len(l) / t()))== 0 else int(((f() + 1) % t())*(len(l) / t()))]: # good luck figuring that out lol
            # it's a lot to explain. variable "l" contains a range starting from 0 ending at whatever the amount of lights in the scene is.
            # the slicing returns a section of the "l" variable. if frame modulo is set to 30 and there are 120 lights in a scene, then each frame will have 4 different lights Proximity Lights needs to figure out.
            # if the current frame % 30 == 15, it will return the 15th section of the list. i hope that clears things up
            
            if LIGHTS[i].get('LIGHTOVERRIDE') or LIGHTS[i].get('PERMHIDDEN'): # if the light has an override property, skip it
                continue
            if math.dist(CS.camera.location, LIGHTS[i].location) > CS.hisanimdrag.value and LIGHTS[i].data.type != 'SUN': # if the light is outside of the defined distance and is not a sun, hide it 
                ExcludeLight(LIGHTS[i], 'HIDE')
            else: # do the opposite
                ExcludeLight(LIGHTS[i], 'SHOW')
                LIGHT = LIGHTS[i]
                if LIGHT.data.get('POWER') != None:
                    LIGHT.data.energy = MAP(math.dist(CS.camera.location, LIGHT.location), DIST-(CS.hisanimstartfrom*DIST), DIST-(CS.hisanimendat*DIST), 0, LIGHT.data.get('POWER'), True)
                
    elif (f() % t() == 0) if CS.hisanimmodulo and bpy.context.screen.is_animation_playing else True: # refresh all at once, but do it once every other amount of frames when playing if enabled
        for i in LIGHTS:
            if i.get('LIGHTOVERRIDE') or i.get('PERMHIDDEN') or i.data.type == 'SUN':
                continue
            if math.dist(CS.camera.location, i.location) > CS.hisanimdrag.value:# and not i.data.type == 'SUN':
                if i.type == 'LIGHT':
                    if i.data.type == 'SUN':
                        continue
                ExcludeLight(i, 'HIDE')
            else:
                ExcludeLight(i, 'SHOW')
                DIST = CS.hisanimdrag.value
                if i.data.get('POWER') != None:
                    i.data.energy = MAP(math.dist(CS.camera.location, i.location), DIST-(CS.hisanimstartfrom*DIST), DIST-(CS.hisanimendat*DIST), 0, i.data.get('POWER'), True)
class HISANIM_OT_LIGHTOVERRIDE(bpy.types.Operator):
    # make Proximity Lights skip lights that have been told to override
    bl_idname = 'hisanim.lightoverride'
    bl_label = 'Override Optimizer'
    bl_description = 'Lights that have an override property added to them will always show no matter how far away the camera is'

    def execute(self, context):
        for i in bpy.context.selected_objects:
            if i.type != "LIGHT" or i.get('LIGHTOVERRIDE') != None:
                continue
            if GetActiveLights() >= 128:
                self.report({'INFO'}, 'Met max amount of overridden lights!')
                return {'CANCELLED'}
            i['LIGHTOVERRIDE'] = True
            if i.get('PERMHIDDEN') != None:
                del i['PERMHIDDEN']
            if i.data.get('DEFAULT') != None:
                i.data.energy = i.data['DEFAULT']
                del i.data['DEFAULT']
            if i.data.get('POWER') != None:
                i.data.energy = i.data['POWER']
        OptimizeLights()
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
            if i.get('LIGHTOVERRIDE') != None:
                del i['LIGHTOVERRIDE']
            ExcludeLight(i, 'PERMHIDDEN')
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
                del i['PERMHIDDEN']
        return {'FINISHED'}

class HISANIM_OT_REVERTLIGHTS(bpy.types.Operator):
    #show all lights
    bl_idname = 'hisanim.revertlights'
    bl_label = 'Show All Lights'
    bl_description = 'Show all the lights that were left hidden by the optimizer'
    
    bl_options = {'UNDO'}

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
        bpy.data.objects['LIGHTDIST'].scale = Vector((self.value, self.value, self.value))
    else:
        # create an empty shaped as a sphere, scaled to the distanced from the camera defined by the user
        EMPTY = bpy.data.objects.new('LIGHTDIST', None)
        C.scene.collection.objects.link(EMPTY)
        EMPTY.empty_display_type = 'SPHERE'
        EMPTY.scale = Vector((self.value, self.value, self.value))
        EMPTY.location = C.scene.camera.location
        EMPTY.show_in_front = True
        OptimizeLights()
        self.is_dragging = True
        bpy.ops.hisanim.dragsub('INVOKE_DEFAULT')

class HISANIM_LIGHTDIST(bpy.types.PropertyGroup):
    value: bpy.props.FloatProperty(update=hisanimupdates, min=0.0, max=1000.0, step=25, default=25.0)
    is_dragging: bpy.props.BoolProperty()

class HISANIM_OT_MIXPOWER(bpy.types.Operator):
    bl_idname = 'hisanim.mixpower'
    bl_label = 'Mix Power'
    bl_description = 'As lights get too far away from the camera, they will fade away'
    
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        return True
    
        
    def execute(self, context):
        if context.scene.hisanimmixpower != True:
            context.scene.hisanimmixpower = True
            if bpy.context.scene.prxlightcollection == None:
                LIGHTS = list(filter(IsLight, bpy.data.objects))
            else:
                LIGHTS = list(filter(IsLight, bpy.context.scene.prxlightcollection.objects))
            for i in LIGHTS:
                if i.data.type == 'SUN':
                    continue
                if i.data.get('DEFAULT') != None:
                    i.data['POWER'] = i.data['DEFAULT']
                else:
                    i.data['POWER'] = i.data.energy
            return {'FINISHED'}
        else:
            context.scene.hisanimmixpower = False
            if bpy.context.scene.prxlightcollection == None:
                LIGHTS = list(filter(IsLight, bpy.data.objects))
            else:
                LIGHTS = list(filter(IsLight, bpy.context.scene.prxlightcollection.objects))
            for i in LIGHTS:
                if i.data.get('POWER') != None:
                    i.data['DEFAULT'] = i.data['POWER']
                    del i.data['POWER']
            return {'FINISHED'}
    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)
    def draw(self, context):
        if context.scene.hisanimmixpower != True:
            layout = self.layout
            row = self.layout
            layout.label(text='This will make or lights, or lights in a')
            layout.label(text='collection have a fixed amount of power.')
            layout.label(text="Any changes you make to a light's power")
            layout.label(text="will be unsaved.")
            layout.label(text="Executing this will make lights' power")
            layout.label(text="fade in and out based on how")
            layout.label(text="far away the camera is.")
            layout.label(text="Any lights added after this will be unaffected.")
            layout.label(text="Execute?")
        else:
            layout = self.layout
            row = self.layout
            layout.label(text='This will cause lights to no longer fade in and out.')
            layout.label(text='Execute?')
        #bpy.context.scene.hisanimmixpower = False

classes = [HISANIM_PT_LIGHTDIST,
            HISANIM_OT_DRAGSUBSCRIBE,
            HISANIM_LIGHTDIST,
            HISANIM_OT_LIGHTOVERRIDE,
            HISANIM_OT_REMOVEOVERRIDES,
            HISANIM_OT_REVERTLIGHTS,
            HISANIM_OT_HIDELIGHT,
            HISANIM_OT_MIXPOWER]

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
    bpy.types.Scene.hisanimmixpower = bpy.props.BoolProperty(default=False)
    bpy.types.Scene.hisanimstartfrom = bpy.props.FloatProperty(default=0.0, max=1.0, min=0.0, name='Fade Out Range')
    bpy.types.Scene.hisanimendat = bpy.props.FloatProperty(default=0.5, max=1.0, min = 0.01, name='Fade In Range')
    bpy.types.Scene.hisanimhardclamp = bpy.props.BoolProperty(name='Enable Light Culling')
    bpy.types.Scene.hisanimclamprange = bpy.props.IntProperty(default=127, max=127, min=4, name='Light Cull Limit', description='Make it impossible to exceed desired amount of lights')
    
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
