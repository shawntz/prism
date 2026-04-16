from psychopy.hardware import joystick
from psychopy import visual, event
import numpy as np

joystick.backend='pyglet'  # must match the Window
win = visual.Window([400,400], winType='pyglet')

nJoys = joystick.getNumJoysticks()  # to check if we have any
id = 0
joy = joystick.Joystick(id)  # id must be <= nJoys - 1

nAxes = joy.getNumAxes()  # for interest

ps5_controller_square_id = 0
ps5_controller_circle_id = 2
ps5_controller_triangle_id = 3
ps5_controller_cross_id = 1

while True:  # while presenting stimuli
#    joy.getX()
#    message = visual.TextStim(win=win, colorSpace='rgb255', font='Times', text=str(joy.getAllButtons()))
#    message = visual.TextStim(win=win, colorSpace='rgb255', font='Times', text=str(joy.getAllHats()))
    ps5_button_states = [
        joy.getButton(ps5_controller_square_id), 
        joy.getButton(ps5_controller_circle_id),
        joy.getButton(ps5_controller_triangle_id),
        joy.getButton(ps5_controller_cross_id)
    ]
    
    current_state = np.where(ps5_button_states)[0]
    if len(current_state) == 0:
        message = 'nothing pressed yet...'
    else:
        message = current_state
        
    keys = event.waitKeys()
    button_states = visual.TextStim(win=win, colorSpace='rgb255', font='Times', text=str(keys))
    button_states.draw()
#    square_button = visual.TextStim(win=win, colorSpace='rgb255', font='Times', text='square button: ' + str())
#    circle_button = visual.TextStim(win=win, colorSpace='rgb255', font='Times', text='\n\ncircle button: ' + str())
#    triangle_trigger = visual.TextStim(win=win, colorSpace='rgb255', font='Times', text='\n\n\n\ntriangle trigger: ' + str())
#    cross_trigger = visual.TextStim(win=win, colorSpace='rgb255', font='Times', text='\n\n\n\n\n\ncross (x) trigger: ' + str())
#    message.draw()
#    square_button.draw()
#    circle_button.draw()
#    triangle_trigger.draw()
#    cross_trigger.draw()
    win.flip()  # flipping implicitly updates the joystick info