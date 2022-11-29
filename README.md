# Proximity Lights
![proxim](https://user-images.githubusercontent.com/41131633/204657765-8ff85f5f-6109-4f50-9950-27a9dad0d695.png)

Buttons are in the Tools section of the property panel.

![image](https://user-images.githubusercontent.com/41131633/204657928-27e283e9-9a65-4d43-878b-55e8c02df8e1.png)

Change the slider to determine how far away lights should be from the camera before they get hidden. Selecting lights and pressing Override or Hide will either have the light permanently show or be hidden.

By default, this will refresh every frame. However, enabling Refresh Every Amount of Frames will refresh the distance between the lights and cameras every amount of frames defined by the user. Enabling Spread Out Refresh will progressively update the lights. All lights will be refreshed once the frame number % amount of frames == 0.

