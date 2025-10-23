#checks a given file is an image file
def is_image_file(file_path):
    return file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp'))
