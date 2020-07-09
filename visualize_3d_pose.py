import os
import sys
import numpy as np
import cv2
import pose_visualization as vis_3d
import global_calculation as gc

EGO_3D_HAND = "ego_3d_hand"
STEREO_HAND = "stereo_hand"
RENDERED_HAND = "rendered_hand"
output_path = "outputs"

def get_sample_data_from_dataset(dataset_name):
    if dataset_name == EGO_3D_HAND:
        img_path = "samples/ego3dhands/00000/color_new.png"
        kpts_2d_path = "samples/ego3dhands/00000/location_2d.npy"
        kpts_3d_can_path = "samples/ego3dhands/00000/location_3d_canonical.npy"
        kpts_3d_glob_path = "samples/ego3dhands/00000/location_3d_global.npy"
        
        # Load 2D image
        img = cv2.imread(img_path)
        # Load 2D global hand poses
        kpts_2d_glob = np.load(kpts_2d_path)[:,1:,:]        # Ignore elbow joint
        # Load 3D canonical hand poses
        kpts_3d_can = np.load(kpts_3d_can_path)[:,1:,:]
        # Load 3D global hand poses
        kpts_3d_glob_gt = np.load(kpts_3d_glob_path)[:,1:,:]
    else:
        # To visualize other datasets, add paths here. Note that the kpts need to be processed the same way
        # as ego3dhands's kpts in order for the visualization script to function properly.
        print("{} sample not provided. You can add your own samples in the script. Our visualization function currently supports Ego3DHands, STB and RPH.".format(dataset_name))
        sys.exit()
    return img, kpts_2d_glob, kpts_3d_can, kpts_3d_glob_gt

def main():
    print("Visualizing sample 3D hand pose...")
    dataset_set = [EGO_3D_HAND, STEREO_HAND, RENDERED_HAND]
    dataset_name = sys.argv[1]
    assert dataset_name in dataset_set, "Unknown dataset: {}".format(dataset_set)

    # Obtain sample data
    img, kpts_2d_glob, kpts_3d_can, kpts_3d_glob_gt = get_sample_data_from_dataset(dataset_name)

    # Initialize 3D viewer
    vis_3d.init()
    vis_3d.set_dataset(dataset_name)

    # Calculate global 3D joints
    kpts_3d_glob_proj = gc.canon_to_global(kpts_2d_glob, kpts_3d_can)
    # Calculate difference between projected and ground truth 3D global pose 
    L1_error_kpts_3d_glob = np.mean(np.absolute(kpts_3d_glob_gt - kpts_3d_glob_proj))
    print("Mean absolute error between gt and projected 3d global poses: {:.5f} cm".format(L1_error_kpts_3d_glob))

    # Output visualization
    if not os.path.exists(output_path):
        os.makedirs(output_path)
        
    view_idx_list = [0, 1, 2, 3]
    for view_idx in view_idx_list:
        vis_3d.change_view(view_idx)
        vis_3d.draw_global(kpts_3d_glob_proj, canvas_texture = img)
        vis_3d.save_screenshot(os.path.join(output_path, "glob_3d_pose_vis_{}_{}.png".format(view_idx, dataset_name)))
    vis_3d.close()
    print("Visualization output in /{}/".format(output_path))
    
if __name__ == "__main__":
    main()