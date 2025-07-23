# Import required libraries
import torch
import cv2
import numpy as np
import matplotlib.pyplot as plt
from sam2.build_sam import build_sam2
from sam2.automatic_mask_generator import SAM2AutomaticMaskGenerator
import supervision as sv
from ultralytics import YOLO
import requests
from config import BASE_URL

all_annotations = {}
  

# SAM2 Model Setup
def setup_sam2_model(model_cfg="sam2_hiera_b+",checkpoint="checkpoints/sam2_hiera_base_plus.pt"):

    device = "cuda" if torch.cuda.is_available() else "cpu"

    # Build SAM2 model - use config name without .yaml extension
    sam2_model = build_sam2(model_cfg, checkpoint, device=device)
    
    # Enable half precision for memory efficiency
    sam2_model.half()
    
    return sam2_model

# SAM2 Mask Generator 
def create_sam2_mask_generator(sam2_model):
    return SAM2AutomaticMaskGenerator(
        model=sam2_model,
        points_per_side=32,
        pred_iou_thresh=0.85,
        stability_score_thresh=0.8,
        crop_n_layers=0,  # Keep 0 for memory efficiency
        crop_overlap_ratio=0.3,
        min_mask_region_area=350,
        points_per_batch=128,
        crop_n_points_downscale_factor=2,
        box_nms_thresh=0.7,
    )

# shrink image to make processing faster
def preprocess_image(image_rgb, target_size=1024):
    height, width = image_rgb.shape[:2]
    
    if max(height, width) > target_size:
        scale = target_size / max(height, width)
        new_width = int(width * scale)
        new_height = int(height * scale)
        image_rgb = cv2.resize(image_rgb, (new_width, new_height), interpolation=cv2.INTER_AREA)
    
    return image_rgb

# decrease number of masks as unlikely to be that many trees
def filter_masks(masks, min_area=500, max_masks=15):
    sorted_masks = sorted(masks, key=lambda x: x['area'] * x['stability_score'], reverse=True)
    filtered_masks = [mask for mask in sorted_masks if mask['area'] >= min_area][:max_masks]
    return filtered_masks


def convert_masks_to_yolo_annotations(masks, image_shape, class_id=0):
    h_img, w_img = image_shape[:2]
    yolo_annotations = []

    for mask in masks:
        # Get bounding box (x_min, y_min, width, height)
        x_min, y_min, width, height = mask['bbox']
        
        # Convert to YOLO format (normalized center x/y, width, height)
        x_center = (x_min + width / 2) / w_img
        y_center = (y_min + height / 2) / h_img
        w_norm = width / w_img
        h_norm = height / h_img

        # Assign class ID (e.g., 0 for “tree”)
        yolo_annotations.append(f"{class_id} {x_center:.6f} {y_center:.6f} {w_norm:.6f} {h_norm:.6f}")
    
    return yolo_annotations


#saves annotations into json format
def save_annotations(annotations,image_path):
    id = image_path.split(".")[0]
    all_annotations[id] = annotations


def save_dataset():
   
    url = BASE_URL+"/createDataset"

    # Send the JSON payload
    response = requests.post(url, json=all_annotations)

    # Check response
    if response.status_code == 200:
        print("Successfully uploaded annotations")
    else:
        print(f"Failed to upload. Status: {response.status_code}, Response: {response.text}")



#determines if image contains a tree
def is_tree(image):

    ################# replace with api request once model deployment is complete ##########
    model = YOLO("best.pt")
    class_name ="idk"
    results = model(image, verbose=False)[0]

    ##############################################

    for box in results.boxes:
        cls = int(box.cls[0])
        conf = float(box.conf[0])
        class_name = model.names[cls]

        if class_name.lower() ==  class_name:
            return True

    return False


def annotate_dataset(image_paths):

    # Setup SAM2 model
    print("Setting up SAM2 model...")
    sam2_model = setup_sam2_model()
    mask_generator = create_sam2_mask_generator(sam2_model)

    #generate annotations for each image 
    for image_path in image_paths:
        print(f"Processing {image_path}")
        # Clear GPU cache
        torch.cuda.empty_cache()
        
        # Load and preprocess image (same as before)
        image = cv2.imread(image_path)
        if image is None:
            print(f"Error: Could not load image {image_path}")
            continue
            
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        original_shape = image_rgb.shape[:2]
        
        # Preprocess image
        image_rgb = preprocess_image(image_rgb, target_size=1024)
        print(f"Image resized from {original_shape} to {image_rgb.shape[:2]}")
        
        # Clear cache before processing
        torch.cuda.empty_cache()
        
        # Generate masks - same API as SAM1!
        print("Generating masks...")
        with torch.cuda.amp.autocast():
            masks = mask_generator.generate(image_rgb)
        
        print(f"Generated {len(masks)} masks")
        
        # Filter masks 
        masks = filter_masks(masks, min_area=300, max_masks=15)
        print(f"Filtered to {len(masks)} masks")

        #extract masks which are trees
        tree_masks = []
        for mask in masks:
            if is_tree(image_rgb):  # Your tree classifier
                tree_masks.append(mask)

        
        annotations = convert_masks_to_yolo_annotations(masks, image_rgb.shape)
        save_annotations(annotations,image_path)
        print(f"Completed processing {image_path}")