import yolo_remover
import blur_detection
import repetitive_images
import photo_upload

def pre_process_and_upload_photos(image_directory):
    
    # remove blurry and repetitive images
    blur_detection.remove_blurry_photos(image_directory)
    repetitive_images.remove_similar_images(image_directory)

    #blur images for privacy
    yolo_remover.blur_privacy(image_directory)

    #upload remaining images to database
    photo_upload.upload_directory(image_directory)

if __name__ == "__main__":
    image_directory = "D:/Database Handler/demo"
    pre_process_and_upload_photos(image_directory)
