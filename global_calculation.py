# Calculate global matrix from 2d and canonical positions
import os
import math
import numpy as np

IS_INITIALIZED = False
# Implicit camera parameters
GLOBAL_HAND_LENGTH = 0 # scaling factor from canonical to global: all shape data is within the canonical position matrix
# Since the focal length cancels out in all the ways we use it (since we only use it for size ratios, angles, and similar triangles), we can make it 1 for simpler calculations
CAMERA_FOCAL_LENGTH = 0

CAMERA_WIDTH = 0
CAMERA_HEIGHT = 0

# Recalculate PXCM when camera parameters change. This was calculated with foc = 1
PXCM = 0 # pixels per centimeter of the camera's sensor: this is the same in the x and y directions

# Joint positions within the positional matrices
WRIST = 0
MIDDLE_FINGER_1 = 9
PINKY_1 = 17

# Ordering of coordinates within the positional matrices
# If you switch these values, make sure to change the rotation matrices accordingly!
# The x, y, z values derived from rotation matrices won't need to change, but the matrices themselves will.
X = 1
Y = 0
Z = 2

# Transforms the global 3D joint locations to canonical 3D joint locations by spherically rotating
# the hand pose to the center of the view, zero-centering and normalizing.
def global_to_canon(global_hand, MIDDLE_FINGER_1 = 9, WRIST = 0):
    X = 1
    Y = 0
    Z = 2
    # For drop-out hands:
    if np.all(global_hand == 0):
       return np.zeros(global_hand.shape)
    ## CHANGE OF BASE 3D
    # The camera's focus is on 0,0,0: the current basis is {[[1],[0],[0]], [[0],[1],[0]], [[0],[0],[1]]}
    # We want it to focus on left_center for the left hand and right_center for the right_hand, with the z 0 value staying on the origin
    # Our basis' z vector for each center will be [[xc],[yc],[zc]]
    affine = np.transpose(global_hand)
    center = affine[:,MIDDLE_FINGER_1]

    # we want to rotate the system such that the vector 0,0,1 is now xc,yc,zc or equivalent
    an_x = math.atan2(center[Y], center[Z])
    rot_x = np.array([[math.cos(an_x),0,-math.sin(an_x)],[0,1,0],[math.sin(an_x),0,math.cos(an_x)]])
    affine = np.dot(rot_x, affine)
    center = affine[:,MIDDLE_FINGER_1]

    an_y = math.atan2(center[X], center[Z])
    rot_y = np.array([[1,0,0],[0,math.cos(an_y),-math.sin(an_y)],[0,math.sin(an_y),math.cos(an_y)]])
    base_changed = np.dot(rot_y, affine)
    
    # Translate to center point (rotation should ensure that center's x and y are close to 0, but z is not)
    pos_canon = np.transpose(base_changed)
    center = pos_canon[MIDDLE_FINGER_1,:]

    pos_canon[:,X] -= center[X]
    pos_canon[:,Y] -= center[Y]
    pos_canon[:,Z] -= center[Z]
    wrist = pos_canon[WRIST, :]#pos_canon[1,:]
    # normalize the matrix
    # the normalizer is the distance between the left hand to the origin (middle finger 1)
    normalizer = math.sqrt((wrist[X] * wrist[X]) + (wrist[Y] * wrist[Y]) + (wrist[Z] * wrist[Z]))
    pos_canon /= normalizer
    return pos_canon

# Transforms the 2D positions and canonical hand orientation into the global hand positions.
# If a global position matrix is provided as ground truth, the difference (prediction - ground truth) will be printed
def canon_to_global(pos_2d, pos_can_3d):
    assert IS_INITIALIZED == True, "Parameters not initialized, call set_params(...) first."
    pos_2d = pos_2d.copy()
    pos_can_3d = pos_can_3d.copy()
    if np.all(pos_2d[0] == 0) or np.all(pos_can_3d[0] == 0):
        calced_left_glob = np.zeros(pos_can_3d[0].shape)
    else:
        calced_left_glob = calculate_global_positions(pos_2d[0], pos_can_3d[0], 0)
    if np.all(pos_2d[1] == 0) or np.all(pos_can_3d[1] == 0):
        calced_right_glob = np.zeros(pos_can_3d[1].shape)
    else:
        calced_right_glob = calculate_global_positions(pos_2d[1], pos_can_3d[1], 1)
    calced_glob = np.zeros(pos_can_3d.shape)
    calced_glob[0] = calced_left_glob
    calced_glob[1] = calced_right_glob

    return calced_glob

# Recreates the global positions of a single hand hand, using the 2D image coordinates and the canonical orientation.
# hand_2d and hand_3d should have the positions of a single hand
def calculate_global_positions(hand_2d, hand_3d, hand_side):
    foc = CAMERA_FOCAL_LENGTH
    wrist_2d = hand_2d[WRIST]
    middle_finger_2d = hand_2d[MIDDLE_FINGER_1] # Key joint is usually the 1st joint of the middle finger, where the finger meets the hand
    wrist_3d = hand_3d[WRIST]

    # The x and y angles are "swapped" because a rotation along the x axis changes y and z, not x
    # Since the y angle has to be recalculated after the first x rotation to the origin, there are two y angles:
    #  post_rot_angle_y is the same as the angle between the middle finger and the z-axis in the xz plane
    #   this angle is the angle AFTER rotation around the x-axis, not the angle of rotation around the y-axis
    #  angle_y is the actual angle of y-axis rotation, which must be calculated from post_rot_angle_y
    # These angles (angle_x and post_rot_angle_y) are found from the 2D projection of the middle finger's 1st joint
    midfinger_x_2d = ((middle_finger_2d[X] * CAMERA_WIDTH) - CAMERA_WIDTH/2) / PXCM
    post_rot_angle_y = math.atan2(midfinger_x_2d, foc)
    midfinger_y_2d = ((middle_finger_2d[Y] * CAMERA_HEIGHT) - CAMERA_HEIGHT/2) / PXCM
    angle_x = math.atan2(midfinger_y_2d, foc)
    angle_y = math.atan2(midfinger_x_2d, (midfinger_y_2d * math.sin(angle_x) + (midfinger_x_2d * math.cos(angle_x))/(math.tan(post_rot_angle_y))))

    # Use either wrist or PF1 to MF1 as the edge used to calculate 3d global positions (whichever edge is longer in the image)
    # This prevents an issue where values calculated with 2d distances were off because the points were too close together to get an accurate measurement
    pinky_2d = hand_2d[PINKY_1]

    dist_wm = math.sqrt((CAMERA_WIDTH*(wrist_2d[X]-middle_finger_2d[X]))**2 + (CAMERA_HEIGHT*(wrist_2d[Y]-middle_finger_2d[Y]))**2)
    dist_pm = math.sqrt((CAMERA_WIDTH*(pinky_2d[X]-middle_finger_2d[X]))**2 + (CAMERA_HEIGHT*(pinky_2d[Y]-middle_finger_2d[Y]))**2)

    # For the partner joint, we choose either the wrist or the pinky (even though MF1->PF1 isn't a bone)
    if(dist_wm > dist_pm):
        joint_2d = wrist_2d
        joint_3d = wrist_3d
    else:
        joint_2d = pinky_2d
        joint_3d = hand_3d[PINKY_1]

    # Calculate the radius of the middle finger to the camera in the 3d global coordinates, which is the translation distance zt
    zt = calc_radius(joint_3d, joint_2d, angle_x, angle_y)

    # Reverse the creation of the canonical matrix to turn the canonical matrix into the global matrix
    # rescale the hand
    hand_3d *= GLOBAL_HAND_LENGTH
    # translate in the z direction
    hand_3d[:,Z] +=  zt 

    # rotate the hand in the oposite direction of the canonical's rotation to (0,0,z)    
    affine_3d = np.transpose(hand_3d)
    angle_x = -angle_x
    angle_y = -angle_y

    rot_x = np.array([[math.cos(angle_x),0,-math.sin(angle_x)],[0,1,0],[math.sin(angle_x),0,math.cos(angle_x)]])
    rot_y = np.array([[1,0,0],[0,math.cos(angle_y),-math.sin(angle_y)],[0,math.sin(angle_y),math.cos(angle_y)]])
    rot = np.dot(rot_x, rot_y)

    base_change = np.dot(rot, affine_3d)
    hand_global_3d = np.transpose(base_change)

    return hand_global_3d

# Maybe we need to rotate bone_len_2d somehow?
def calc_radius(joint_canon, j_2d, angle_x, angle_y):
    # reverse angles of rotation
    angle_x *= -1
    angle_y *= -1
    # rotate middle finger and partner joint, just as the global was rotated to become the canonical
    foc = CAMERA_FOCAL_LENGTH
    rot_x = np.array([[math.cos(angle_x),0,-math.sin(angle_x)],[0,1,0],[math.sin(angle_x),0,math.cos(angle_x)]])
    rot_y = np.array([[1,0,0],[0,math.cos(angle_y),-math.sin(angle_y)],[0,math.sin(angle_y),math.cos(angle_y)]])
    # The 2d points have foc as their z position
    j_2d = np.array([((j_2d[0] * CAMERA_HEIGHT) - CAMERA_HEIGHT/2) / PXCM, ((j_2d[1] * CAMERA_WIDTH) - CAMERA_WIDTH/2) / PXCM, foc])
    # After this rotation, mf_2d should be [0, 0, rotated_foc]
    j_2d = np.dot(j_2d,rot_x)
    j_2d = np.dot(j_2d,rot_y)
    # Get the sides of the triangle formed by the canonical bone, in the XY / Z plane
    h = GLOBAL_HAND_LENGTH * (joint_canon[X]**2 + joint_canon[Y]**2)**.5
    w = GLOBAL_HAND_LENGTH * joint_canon[Z]
    bone_len_2d = (j_2d[0]**2 + j_2d[1]**2)**.5
    foc = j_2d[2]
    # Get r, which is the z distance to the partner joint's canonical point
    r = h * foc / bone_len_2d
    # R is the radius to the middle finger (also the z portion of the scaled and translated middle finger)
    R = r-w
    return R

### PARAMETER CALCULATION ###

# use the ground truth to calculate the camera's pxcm
# recalculate pxcm when the camera (virtual or real) has been changed
def calculate_pxcm(pos_2d, glob):
    middle_finger_2d = pos_2d[0,MIDDLE_FINGER_1,:]
    middle_finger_3d = glob[0,MIDDLE_FINGER_1,:]
    y2d = middle_finger_3d[X]*CAMERA_FOCAL_LENGTH/middle_finger_3d[Z]
    # print("Actual y2d = " + str(y2d))
    y_screen = middle_finger_2d[X]
    # print("2D y coordinate = " + str(y_screen))
    y_pix = y_screen * CAMERA_WIDTH - (CAMERA_WIDTH/2)
    pxcm = y_pix/y2d # pixels/cm
    print("PXCM = " + str(pxcm) + " pixels per cm")
    return pxcm

### SET DATASET ###

# Sets all parameters needed for a given dataset. New dataset parameters can be added
def set_params(key_bone_l, foc_l, cam_h, cam_w, pxcm, wrist_idx, mmcp_idx, pmcp_idx, x_idx, y_idx, z_idx):
    global IS_INITIALIZED, GLOBAL_HAND_LENGTH, CAMERA_FOCAL_LENGTH, CAMERA_WIDTH, CAMERA_HEIGHT, PXCM, WRIST, MIDDLE_FINGER_1, PINKY_1, X, Y, Z
    IS_INITIALIZED = True
    GLOBAL_HAND_LENGTH = key_bone_l
    CAMERA_FOCAL_LENGTH = foc_l
    CAMERA_HEIGHT = cam_h
    CAMERA_WIDTH = cam_w
    PXCM = pxcm
    WRIST = wrist_idx
    MIDDLE_FINGER_1 = mmcp_idx
    PINKY_1 = pmcp_idx
    X = x_idx
    Y = y_idx
    Z = z_idx
    
