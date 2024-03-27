# Proximity Lights
![proxim](https://user-images.githubusercontent.com/41131633/204657765-8ff85f5f-6109-4f50-9950-27a9dad0d695.png)

Buttons are in the Tools section of the property panel.

<img src="https://github.com/hisprofile/blenderstuff/assets/41131633/01cdc3fd-0c16-4599-b417-0f6425633a56" width=30%>  

# Instructions  
Dragging `Distance Threshold` will create a sphere from the active camera's location, which is then sized based on the distance threshold. Any light inside of the sphere will be enabled, and vice versa.  

Overrides are applied to any selected light. They can be always on (e.g. ignored by proximity lights), or always off.

`Optimize After # of Frames` determines how many frames to skip before updating the lights.

When `Light Collection` is given a collection, only lights inside of that collection will be optimized.

When `Camera Frustrum` is enabled, then any light behind the camera (view plane) is disabled. In other words, only the lights you're facing are enabled.

`Light Culling` ensures the maximum amount of active lights is hard capped at a number. For example; when set to 127, and 144 lights are inside the camera distance threshold, then only the 127 closest lights will be enabled.

`Fade Lights` dims the lights based on distance from the threshold, granting a smooth transition between disabled and enabled.
