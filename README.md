# dwmaya
Collection of Maya functions/tools/scripts/helpers/examples.

## playblast:
Uses a temporary floating viewport to avoid messing with your UI and to make sure the correct camera is used.\
Also works in batch mode (mayapy).
```python
dwmaya.playblast.playblast(camera='')
```

## shelf:
Create shelf menu in python. Handy to create non-destructible shelf from userSetup.py and also re-use common part of buttons in multiple shelf tabs.
```python
dwmaya.shelf.create(
    name='example',
    shelf_buttons=[
        dict(
            tooltip="farm_launcher",
            icon="farm_launcher.png",
            command='print("test")'),
        dwmaya.shelf.SEPARATOR,
        dict(
            tooltip="left click menu",
            icon="cube.png",
            command='import maya.cmds as mc;mc.polyCube()',
            menu_button=dwmaya.shelf.RIGHT_BUTTON,
            menu=[
                dict(label='first menu item',
                     command='polyCube',
                     source_type='mel'),
                dict(label='another menu item',
                     command='polyCube',
                     source_type='mel'),
            ]
        )
    ]
)
```