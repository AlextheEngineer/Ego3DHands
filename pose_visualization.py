from PIL import Image

import math
import numpy as np
import global_calculation as gc

import pygame
from pygame.locals import *

from OpenGL.GL import * # "simple" OpenGL functions
from OpenGL.GLU import * # "complex" OpenGL functions

# Virtual camera parameters for OpenGL visualization
WINDOW_WIDTH = 1920//2 # pixels
WINDOW_HEIGHT = 1080//2 # pixels
FOV_Y = 58.5 # degrees, FOV_X = 104 # 67.5 degrees, FOV_X = 120
# With our current focal length (.00924 m), FOV_X should be 104
FAR_PLANE = 36.0 # meters
NEAR_PLANE = .036
GROUND_HEIGHT = -1.10

# Virtual camera position and rotation
camera_x = 0
camera_y = 0
camera_z = 0

# Initial camera view points
INITIAL_POS = [(0,0,0)]
# matches the INITIAL_POS for corresponding view, Y_angle -> horizontal
INITIAL_Y_ANGLE = [(0,0,0)]
# X_angle -> vertical
INITIAL_X_ANGLE = [(0,0,0)]

view = 0

camera_y_angle = 0
camera_x_angle = 0

# Order of coordinates in position matrices
X = 1
Y = 0
Z = 2

proj = None
draw_image_canvas = False#True
changed_instance = True

BONE_BASE_SIZE = .003

# Indexes for the start and end vertices of each edge to be drawn for the hands.
hand_edges = (  
    # LEFT HAND
    # thumb
    (0,1),
    (1,2),
    (2,3),
    (3,4),
    # index
    (0,5),
    (5,6),
    (6,7),
    (7,8),
    # middle
    (0,9),
    (9,10),
    (10,11),
    (11,12),
    # ring
    (0,13),
    (13,14),
    (14,15),
    (15,16),
    # pinky
    (0,17),
    (17,18),
    (18,19),
    (19,20),
   
    # RIGHT HAND
    # thumb
    (21, 22),
    (22, 23),
    (23, 24),
    (24, 25),
    # index
    (21, 26),
    (26, 27),
    (27, 28),
    (28, 29),
    # middle
    (21, 30),
    (30, 31),
    (31,32),
    (32, 33),
    # ring
    (21, 34),
    (34, 35),
    (35, 36),
    (36, 37),
    # pinky
    (21, 38),
    (38, 39),
    (39, 40),
    (40, 41),
    )

# Returns a list of the hand vertices with coordinates [x, y, z] to be drawn.
def get_hand_vertices(globe_coords):
    vertices = []
    _, height, _ = globe_coords.shape
    # sets left hand vertices then right hand
    for hand in globe_coords:
        for r in range(height):
            vertex = []
            # convert from meters to centimeters
            vertex.append(hand[r, X]/100)
            vertex.append(hand[r, Y]/100)
            vertex.append(hand[r, Z]/100)
            vertex[1] *= -1 # flip the y axis so + is down
            vertex[2] *= -1 # flip the z axis, so the hand is in front
            vertices.append(tuple(vertex))
    return tuple(vertices)
    
# Instead of drawing fingers as spheres and lines, draw them as pyramids
def draw_hands(hand_pos):
    hand_vertices = get_hand_vertices(hand_pos)
    # print(hand_vertices)

    bone_num = 0
    glColor3f(0,1,0)
    for edge in hand_edges:
        start_v = hand_vertices[edge[0]]
        end_v = hand_vertices[edge[1]]
        if start_v == (0, 0, 0) and end_v == (0, 0, 0):
            continue
        # 1. Find theta (angle between start pt s and end pt e, relative to the normal coordinate system)
        ty = math.atan2(start_v[2]-end_v[2],start_v[0]-end_v[0])
        # 2. Rotate the points by theta, around y axis.
        roty = np.array([[-math.sin(ty), 0, math.cos(ty)],
                         [0, 1, 0],
                         [math.cos(ty), 0, math.sin(ty)]])
        s0 = np.transpose(np.array(start_v) - np.array(end_v))
        
        s1 = np.dot(roty, s0)
        # 3. Repeat 1 and 2 with z axis
        tx = math.atan2(s1[1],s1[2])
        rotx = np.array([[1, 0, 0],
                         [0, math.sin(tx), math.cos(tx)],
                         [0, math.cos(tx), -math.sin(tx)]])
        s2 = np.dot(rotx, s1)
        
        # 3. Add other pts at fixed distance from s
        p1 = s2 + np.array([BONE_BASE_SIZE, 0, BONE_BASE_SIZE])
        p2 = s2 + np.array([-BONE_BASE_SIZE, 0, BONE_BASE_SIZE])
        p3 = s2 + np.array([-BONE_BASE_SIZE, 0, -BONE_BASE_SIZE])
        p4 = s2 + np.array([BONE_BASE_SIZE, 0, -BONE_BASE_SIZE])
        # 4. Rotate all points back by -theta
        # Only do s as a sanity check
        rotx[1,1] *= -1
        rotx[2,2] *= -1
        
        roty[0,0] *= -1
        roty[2,2] *= -1

        e = np.array(end_v)
        p = [p1, p2, p3, p4]
        for i in range(4):
            p[i] = np.dot(roty, np.dot(rotx, p[i]))
            p[i][1:] *= -1
            p[i] += e 
        # 5. Draw: side-pts -> e, side-pts together in a square (s isn't drawn)
        glBegin(GL_LINES)
        for i in range(4):
            glVertex3fv(p[i])
            glVertex3fv(end_v)
            glVertex3fv(p[i])
            glVertex3fv(p[(i+1)%4])
        glEnd()

        bone_num += 1
        if bone_num == 4:
            glColor3f(0, 1, 1)
        elif bone_num == 8:
            glColor3f(0, 0, 1)
        elif bone_num == 12:
            glColor3f(1, 0, 1)
        elif bone_num == 16:
            glColor3f(1, 0, 0)
        elif bone_num == 20:
            glColor3f(0, 1, 0)
            bone_num = 0
    return

# Draws a checkerboard plane as ground to better visualize the 3D space that the hands are in.
def draw_ground():
    h = GROUND_HEIGHT#-1.10
    ss = -10
    se = 10
    load_texture("assets/checker_texture_small.png")
    glColor3f(1, 1, 1)
    glBegin(GL_QUADS)
    glVertex3fv((ss, h, ss))
    glTexCoord2f(0, 0)
    glVertex3fv((ss, h, se))
    glTexCoord2f(0, 1)
    glVertex3fv((se, h, se))
    glTexCoord2f(1, 1)
    glVertex3fv((se, h, ss))
    glTexCoord2f(1, 0)
    glEnd()

# Draws the image on a vertical plane behind the hands
def draw_image(canvas_texture):
    # If no canvas_texture path is provided, don't even draw the image.
    if canvas_texture is None:
        return

    # Draw the rectangle "canvas"
    dist = CANVAS_DISTANCE
    size = CANVAS_SIZE
    aspect_ratio = float(WINDOW_WIDTH)/WINDOW_HEIGHT
    vertices = ((aspect_ratio*size, size, dist),
                (-aspect_ratio*size, size, dist),
                (-aspect_ratio*size, -size, dist),
                (aspect_ratio*size, -size, dist)
                )
    load_texture(canvas_texture)

    glColor3f(1, 1, 1)
    glBegin(GL_QUADS)
    glVertex3fv(vertices[0])
    glTexCoord2f(0, 0)
    glVertex3fv(vertices[1])
    glTexCoord2f(0, 1)
    glVertex3fv(vertices[2])
    glTexCoord2f(1, 1)
    glVertex3fv(vertices[3])
    glTexCoord2f(1, 0)
    glEnd()
    return vertices

def load_texture(texture):
    if type(texture) is str:
        texture_surface = pygame.image.load(texture)
    else:
        texture_surface = pygame.surfarray.make_surface(np.swapaxes(texture[:,:,::-1], 0, 1))
    texture_data = pygame.image.tostring(texture_surface, "RGBA")
    width = texture_surface.get_width()
    height = texture_surface.get_height()

    glEnable(GL_TEXTURE_2D)
    texid = glGenTextures(1)

    glBindTexture(GL_TEXTURE_2D, texid)
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, width, height, 0, GL_RGBA, GL_UNSIGNED_BYTE, texture_data)

    # Not sure if we need these parameters
    glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
    glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
    glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
    glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)

    texture_data = None

    return texid

# Draw a physical camera and the projection lines to the image canvas
def draw_camera(canvas_vertices):
    glColor3f(0, .5, .5)
    for v in canvas_vertices:
        line_width = 1
        glLineWidth(line_width)
        glBegin(GL_LINES)
        glVertex3fv((0,0,0))
        glVertex3fv(v)
        glEnd()
    for i in range(len(canvas_vertices)):
        v1 = canvas_vertices[i]
        v2 = canvas_vertices[(i+1)%len(canvas_vertices)]
        v1 = (v1[0]/10, v1[1]/10, v1[2]/10)
        v2 = (v2[0]/10, v2[1]/10, v2[2]/10)
        glBegin(GL_TRIANGLES)
        glVertex3fv((0,0,0))
        glVertex3fv(v1)
        glVertex3fv(v2)
        glEnd()
    

# Draws all objects (ground and hands) within the PyGame window.
def draw_objects(hand_pos, canvas_texture=None, do_draw_ground=True):
    if do_draw_ground:
        draw_ground()
    glBindTexture(GL_TEXTURE_2D, 0) # reset texture
    if canvas_texture is not None:
        canvas_vertices = draw_image(canvas_texture)
    glBindTexture(GL_TEXTURE_2D, 0) # reset texture
    draw_hands(hand_pos)
    if view != 0:
        draw_camera(canvas_vertices)

def save_screenshot(path):
    im_bytes = glReadPixels(0, 0, WINDOW_WIDTH, WINDOW_HEIGHT, GL_RGB, GL_UNSIGNED_BYTE)
    im = Image.frombytes("RGB", (WINDOW_WIDTH, WINDOW_HEIGHT), im_bytes)
    im = im.transpose(Image.FLIP_TOP_BOTTOM)
    im.save(path, format="png")

# Process key presses for simple navigation.
# While OpenGL doesn't have an actual camera, this sets the values for all objects to be translated to provide the illusion of a moving camera.
# Returns False if pygame exits, else returns True
def process_input():
    global camera_x, camera_y, camera_z, camera_y_angle, camera_x_angle, view, changed_instance
    yrad = math.radians(camera_y_angle)

    pressed_keys = pygame.key.get_pressed()
    
    ysin = math.sin(yrad)/100
    ycos = math.cos(yrad)/100
    
    # WASD translates the camera in the xz plane (leaving arrow keys free for changing the drawn image in scripts that use this script for visualization)
    if pressed_keys[pygame.K_w]:
        glTranslated(-ysin, 0, ycos)
        camera_x += ysin
        camera_z -= ycos

    if pressed_keys[pygame.K_a]:
        glTranslated(ycos, 0, ysin)
        camera_x -= ycos
        camera_z -= ysin  

    if pressed_keys[pygame.K_s]:
        glTranslated(ysin, 0, -ycos)
        camera_x -= ysin
        camera_z += ycos
            
    if pressed_keys[pygame.K_d]:
        glTranslated(-ycos, 0, -ysin)
        camera_x += ycos
        camera_z += ysin
        
    # Left shift translates the camera upward (+y), while left CTRL translates the camera downward (-y)
    if pressed_keys[pygame.K_LSHIFT]:
        glTranslated(0, -.01, 0)
        camera_y += .01
    
    if pressed_keys[pygame.K_LCTRL]:
        glTranslated(0, .01, 0)
        camera_y -= .01
        
    # Q and E rotate the camera from side to side, around the y axis
    if pressed_keys[pygame.K_q]:
        glTranslated(camera_x, 0, camera_z)
        glRotated(-1, 0, 1, 0)
        glTranslated(-camera_x, 0, -camera_z)
        camera_y_angle -= 1
        
    if pressed_keys[pygame.K_e]:
        glTranslated(camera_x, 0, camera_z)
        glRotated(1, 0, 1, 0)
        glTranslated(-camera_x, 0, -camera_z)
        camera_y_angle += 1

    if pressed_keys[pygame.K_r]:
        glTranslated(0, camera_y, camera_z)
        glRotated(-1, 1, 0, 0)
        glTranslated(0, -camera_y, -camera_z)
        camera_x_angle -= 1
        
    if pressed_keys[pygame.K_f]:
        glTranslated(0, camera_y, camera_z)
        glRotated(1, 1, 0, 0)
        glTranslated(0, -camera_y, -camera_z)
        camera_x_angle += 1

    # Ensures the angle will not overflow and will remain mod 360
    camera_y_angle %= 360
        
    # For non-repeating actions and other events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            return False
        # KEYDOWN events occur when the key is initially pressed, so these actions are not repeated by holding the key
        if event.type == pygame.KEYDOWN:
            # P prints the camera's location and orientation for debugging
            if event.key == pygame.K_p:
                print("Position = " + str((camera_x, camera_y, camera_z)) + ", y angle = " + str(camera_y_angle))
            # The spacebar switches the camera between the camera position and a side view
            if event.key == pygame.K_SPACE:
                change_view()
            # Return takes a screenshot
            if event.key == pygame.K_RETURN:
                save_screenshot("outputs/screenshot.png")
                print("Screenshot saved")
            if event.key == pygame.K_LEFT or event.key == pygame.K_RIGHT:
                changed_instance = True
            # ESC closes the PyGame window.
            if event.key == pygame.K_ESCAPE:
                pygame.quit()
                return False

    return True

### EXTERNAL USE FUNCTIONS ###
# These functions should allow a user to utilize OpenGL from another script

# Initializes the PyGame window. This must be called before the other functions.
def init():
    global camera_x, camera_y, camera_z, camera_y_angle, proj
    pygame.init()
    display = (WINDOW_WIDTH, WINDOW_HEIGHT)
    pygame.display.set_mode(display, OPENGL)
    # sets up the perspective: gluPerspective(fov, aspect_ratio, znear, zfar)
    # znear and zfar create the clipping plane, relative to your perspective: they should always be > 0
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(FOV_Y,float(display[0])/display[1], NEAR_PLANE, FAR_PLANE)
    proj = glGetFloatv(GL_PROJECTION_MATRIX)
    # "typical" pygame event loop
    glMatrixMode(GL_MODELVIEW)
    camera_x, camera_y, camera_z = INITIAL_POS[0]
    camera_y_angle = 0
    glTranslated(-camera_x, -camera_y, -camera_z)

# Draws the global hand without predicting it. This is intended to be used with the ground truth only, but can be used with only the global prediction instead.
def draw_global(kpts_glob, canvas_texture="", draw_ground=True, sky_color=(.7, .7, .7, 1)):
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            return False
    # Process key presses
    if not process_input():
        return False
    # Set bg to gray
    glClearColor(*sky_color)
    # Clear the canvas
    glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT)
    # Draw
    draw_objects(kpts_glob, canvas_texture, draw_ground)
    # Update the display
    pygame.display.flip()
    return True

# Closes the PyGame window and resets the camera values back to 0.
def close():
    global camera_x, camera_y, camera_z, camera_y_angle, camera_x_angle
    camera_x = 0
    camera_y = 0
    camera_z = 0
    camera_y_angle = 0
    camera_x_angle = 0
    pygame.quit()

# view 0 is the basic camera, view 1 is the side view, view -1 toggles the view
def change_view(new_view=-1):
    global view, camera_x, camera_y, camera_z, camera_x_angle, camera_y_angle
    glTranslated(camera_x, camera_y, camera_z)
    glRotated(-camera_x_angle, 1, 0, 0)
    glRotated(-camera_y_angle, 0, 1, 0)
    if new_view == -1:
        view = (view+1)%len(INITIAL_POS)
    else:
        view = new_view
    camera_x, camera_y, camera_z = INITIAL_POS[view]
    camera_y_angle = INITIAL_Y_ANGLE[view]
    camera_x_angle = INITIAL_X_ANGLE[view]
    glRotated(camera_y_angle, 0, 1, 0)
    glRotated(camera_x_angle, 1, 0, 0)
    glTranslated(-camera_x, -camera_y, -camera_z)


# Sets all parameters needed for a given dataset
def set_dataset(dataset_name):
    global WINDOW_WIDTH, WINDOW_HEIGHT, GROUND_HEIGHT, FOV_Y, INITIAL_POS, INITIAL_Y_ANGLE, INITIAL_X_ANGLE, CANVAS_DISTANCE, CANVAS_SIZE, X, Y, Z, hand_edges
    if dataset_name == "ego_3d_hand":
        # Virtual camera parameters for OpenGL visualization
        WINDOW_WIDTH = 960          # pixels
        WINDOW_HEIGHT = 540         # pixels
        CANVAS_DISTANCE = -.58

        # Order of coordinates in position matrices
        X = 1
        Y = 0
        Z = 2

        # Set dataset parameters
        key_bone_l = 10.0           # key bone length in cm
        foc_l = 0.924               # focal length
        cam_h = WINDOW_HEIGHT
        cam_w = WINDOW_WIDTH
        PXCM = 406.78               # pixels per cm ratio
        wrist_idx = 0               # index for the wrist joint
        mmcp_idx = 9                # index for the first joint of middle finger
        pmcp_idx = 17               # index for the first joint of pinky finger

        # Initial camera view points
        INITIAL_POS = [
            (0, 0, 0),              # Center view
            (0.679, 0, 0.121),      # Overall view from the right
            (0, 0.8, -0.3),         # top down view
            (0.8, 0, -0.25)         # Close view from the right
        ] 
        # matches the INITIAL_POS for corresponding view, Y_angle -> horizontal
        INITIAL_Y_ANGLE = [0, -41, 0, -60]
        # X_angle -> vertical
        INITIAL_X_ANGLE = [0, 0, 80, 0]

        # Indexes for the start and end vertices of each edge to be drawn for the hands.
        hand_edges = (  
            # LEFT HAND
            # thumb
            (0,1),
            (1,2),
            (2,3),
            (3,4),
            # index
            (0,5),
            (5,6),
            (6,7),
            (7,8),
            # middle
            (0,9),
            (9,10),
            (10,11),
            (11,12),
            # ring
            (0,13),
            (13,14),
            (14,15),
            (15,16),
            # pinky
            (0,17),
            (17,18),
            (18,19),
            (19,20),
        
            # RIGHT HAND
            # thumb
            (21, 22),
            (22, 23),
            (23, 24),
            (24, 25),
            # index
            (21, 26),
            (26, 27),
            (27, 28),
            (28, 29),
            # middle
            (21, 30),
            (30, 31),
            (31,32),
            (32, 33),
            # ring
            (21, 34),
            (34, 35),
            (35, 36),
            (36, 37),
            # pinky
            (21, 38),
            (38, 39),
            (39, 40),
            (40, 41),
            )
    elif dataset_name == "stereo_hand":
        # Virtual camera parameters for OpenGL visualization
        WINDOW_WIDTH = 640          # pixels
        WINDOW_HEIGHT = 480         # pixels
        CANVAS_DISTANCE = -0.8
        #GROUND_HEIGHT

        # Order of coordinates in position matrices
        X = 1
        Y = 0
        Z = 2

        key_bone_l = 3.905
        foc_l = 0.82279041
        cam_h = WINDOW_HEIGHT
        cam_w = WINDOW_WIDTH
        PXCM = 987
        wrist_idx = 0
        mmcp_idx = 9
        pmcp_idx = 17

        # Initial camera view points
        INITIAL_POS = [
            (0, 0, 0),              # Center view
            (0.85, 0, 0.48),        # Overall view from the right
            (0, 1.6, -0.15),        # top down view
            (1.3, 0, -0.25)         # Close view from the right
        ] 
        # matches the INITIAL_POS for corresponding view, Y_angle -> horizontal
        INITIAL_Y_ANGLE = [0, -41, 0, -80]
        # X_angle -> vertical
        INITIAL_X_ANGLE = [0, 0, 80, 0]

        # Indexes for the start and end vertices of each edge to be drawn for the hands.
        hand_edges = (  
            # LEFT HAND
            # thumb
            (0,1),
            (1,2),
            (2,3),
            (3,4),
            # index
            (0,5),
            (5,6),
            (6,7),
            (7,8),
            # middle
            (0,9),
            (9,10),
            (10,11),
            (11,12),
            # ring
            (0,13),
            (13,14),
            (14,15),
            (15,16),
            # pinky
            (0,17),
            (17,18),
            (18,19),
            (19,20),
        
            # RIGHT HAND
            # thumb
            (21, 22),
            (22, 23),
            (23, 24),
            (24, 25),
            # index
            (21, 26),
            (26, 27),
            (27, 28),
            (28, 29),
            # middle
            (21, 30),
            (30, 31),
            (31,32),
            (32, 33),
            # ring
            (21, 34),
            (34, 35),
            (35, 36),
            (36, 37),
            # pinky
            (21, 38),
            (38, 39),
            (39, 40),
            (40, 41),
            )
    elif dataset_name == "rendered_hand":
        # Virtual camera parameters for OpenGL visualization
        WINDOW_WIDTH = 320          # pixels
        WINDOW_HEIGHT = 320         # pixels
        CANVAS_DISTANCE = -0.8

        # Order of coordinates in position matrices
        X = 1
        Y = 0
        Z = 2

        # Need to reset for each instance
        key_bone_l = 10             
        foc_l = 1.0                 
        cam_h = WINDOW_HEIGHT
        cam_w = WINDOW_WIDTH
        PXCM =  1000                
        wrist_idx = 0
        mmcp_idx = 9
        pmcp_idx = 17

        # Initial camera view points
        INITIAL_POS = [
            (0, 0, 0),              # Center view
            (0.85, 0, 0.48),        # Overall view from the right
            (0, 1.1, -0.45),        # top down view
            (1, 0, -0.35)           # Close view from the right
        ] 
        # matches the INITIAL_POS for corresponding view, Y_angle -> horizontal
        INITIAL_Y_ANGLE = [0, -41, 0, -80]
        # X_angle -> vertical
        INITIAL_X_ANGLE = [0, 0, 85, 0]

        # Indexes for the start and end vertices of each edge to be drawn for the hands.
        hand_edges = (  
            # LEFT HAND
            # thumb
            (0,1),
            (1,2),
            (2,3),
            (3,4),
            # index
            (0,5),
            (5,6),
            (6,7),
            (7,8),
            # middle
            (0,9),
            (9,10),
            (10,11),
            (11,12),
            # ring
            (0,13),
            (13,14),
            (14,15),
            (15,16),
            # pinky
            (0,17),
            (17,18),
            (18,19),
            (19,20),
        
            # RIGHT HAND
            # thumb
            (21, 22),
            (22, 23),
            (23, 24),
            (24, 25),
            # index
            (21, 26),
            (26, 27),
            (27, 28),
            (28, 29),
            # middle
            (21, 30),
            (30, 31),
            (31,32),
            (32, 33),
            # ring
            (21, 34),
            (34, 35),
            (35, 36),
            (36, 37),
            # pinky
            (21, 38),
            (38, 39),
            (39, 40),
            (40, 41),
            )

    FOV_Y = calc_fov(cam_h, foc_l, PXCM)
    CANVAS_SIZE = calc_canvas_size(cam_h, foc_l, PXCM, CANVAS_DISTANCE)
    update_perspective_matrix()
    gc.set_params(key_bone_l, foc_l, cam_h, cam_w, PXCM, wrist_idx, mmcp_idx, pmcp_idx, X, Y, Z)
    change_view(0)

def reset_params(cam_K, cam_h, key_bone_l):
    global PXCM, FOV_Y, CANVAS_SIZE
    foc = 1.0
    PXCM = cam_K[0, 0]
    FOV_Y = calc_fov(cam_h, foc, PXCM)
    CANVAS_SIZE = calc_canvas_size(cam_h, foc, PXCM, CANVAS_DISTANCE)
    update_perspective_matrix()
    gc.set_params(key_bone_l = key_bone_l, foc_l = foc, cam_h = cam_h, pxcm = PXCM)

def update_perspective_matrix():
    display = (WINDOW_WIDTH, WINDOW_HEIGHT)
    pygame.display.set_mode(display, DOUBLEBUF|OPENGL)
    # sets up the perspective: gluPerspective(fov, aspect_ratio, znear, zfar)
    # znear and zfar create the clipping plane, relative to your perspective: they should always be > 0
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(FOV_Y,float(display[0])/display[1], NEAR_PLANE, FAR_PLANE)
    proj = glGetFloatv(GL_PROJECTION_MATRIX)
    # "typical" pygame event loop
    glMatrixMode(GL_MODELVIEW)

# NOTE: cam_h is not necessarily WINDOW_HEIGHT/image_height if the image has been resized like in the Ego3DHand dataset
# fov must be in cm
def calc_fov(cam_h, foc, PXCM):
    foc_pix = foc * PXCM
    h = cam_h/2
    fov = math.degrees(2 * abs(math.atan(h/foc_pix)))
    return fov

def calc_canvas_size(cam_h, foc, PXCM, canvas_distance):
    foc_pix = foc * PXCM
    h = cam_h/2
    size = (h/foc_pix) * abs(canvas_distance)
    return size
