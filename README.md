# Ego3DHands
This repository is for the newest Ego3DHands dataset.

# Introduction
This dataset is for the task of two-hand 3D global pose estimation. Therefore it provides images and corresponding labels with the presence of two hands in egocentric view generated using Blender. This dataset can also be used for the task of hand segmentation, 2D, 3D canonical and 3D global hand pose estimation. For hand tracking in dynamic sequences, we also provide a dynamic version of Ego3DHands.

Each instance provides:
  * hand image with transparent background
  * hand image with background
  * segmentation masks (15 classes for the parts of foreground {1~14} and the background {0})
  * depth image (enocded as RGB images such that Depth = B*1.0 + G*0.01 + R*0.0001)
  * 2D joint locations (represented as percentages, top left is (0.0, 0.0) and bottom right is (1.0, 1.0))
  * 3D global joint locations (normalized such that the bone length from wrist to the mMCP has length of 10.0cm)
  * 3D canonical joint locations (spherically rotated to the center, zero-centered and normalized so the key bone has length of 1.0)
  
# Ego3DHands static & dynamic
Ego3DHands dataset provides 2 different versions for the task of static and dynamic pose estiamtion respectively. The static version includes 50,000 training instances and 5,000 test instances. The dynamic version includes 100 training videos and 10 test videos with 500 frames per video sequence.

# Download
Please use the following link for downloading the dataset:

# Evaluation
For the task of global hand pose estimation, we evaluate in terms of both AUC for the PCK of the 3D canonical hand poses (pose accuracy) and the spherical AUC (directional accuracy & distance accuracy of the root joint). Please see the paper below for more details.

# License
This dataset can only be used for scientific/non-commercial purposes. If you use this dataset for your research, please cite the following paper:
...
