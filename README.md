# Ego3DHands
<img src="image_sample1.png" width="320">    <img src="image_sample1_sideview.png" width="320">

<img src="image_sample2.png" width="320">    <img src="image_sample2_seg.png" width="320">

Ego3DHands is a large-scale synthetic dataset for the task of two-hand 3D global pose estimation. It provides images and corresponding labels with the presence of two hands in egocentric view generated using Blender. This dataset can also be used for the task of hand segmentation, 2D, 3D canonical and 3D global hand pose estimation. For hand tracking in dynamic sequences, we provide a dynamic version of Ego3DHands.

Each instance provides the following data for both hands:
  * hand image with transparent background
  * hand image with background
  * segmentation masks (15 classes for the parts of foreground {1~14} and the background {0})
  * depth image (enocded as RGB images such that $Depth = 1.0xB_val + 0.01xG_val + 0.0001xR_val cm. Background is represented as 0s)
  * 2D joint locations (represented as percentages in row and column, top left is (0.0, 0.0) and bottom right is (1.0, 1.0))
  * 3D global joint locations (normalized such that the bone length from wrist to the mMCP has length of 10.0cm)
  * 3D canonical joint locations (spherically rotated to the center, zero-centered and normalized so the key bone has length of 1.0)
  
# Ego3DHands static & dynamic
Ego3DHands dataset provides 2 different versions for the task of static and dynamic pose estiamtion respectively. The static version includes 50,000 training instances and 5,000 test instances. The background images for the static version are randomly selected from approximately 20,000 images within 100 different scene categories from online sources. The dynamic version includes 100 training videos and 10 test videos with 500 frames per video sequence. Each sequence has a unique background sequence selected from www.pexels.com.

# Download
Please use the following link for downloading the dataset:

Ego3DHands (static):
https://pan.baidu.com/s/1Z9OSk3WKcUZfYHTJqntLHQ
password: 5a9c

Ego3Dhands (dynamic):
https://pan.baidu.com/s/1Ru2e2Cp9O38GkrrTyAVZyA
password: pmh6

# Evaluation
For the task of global hand pose estimation, we evaluate in terms of both AUC for the PCK of the 3D canonical hand poses (pose accuracy) and the spherical AUC (directional accuracy & distance accuracy of the root joint). Please see the paper below for more details.

# License
This dataset can only be used for scientific/non-commercial purposes. If you use this dataset for your research, please cite the following paper:
...
