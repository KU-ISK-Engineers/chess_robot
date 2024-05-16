import os
import shutil
import sys

def copy_annotations(source_annotations, destination_images):
    # Get all image filenames (without extensions) in the destination directory
    image_files = [os.path.splitext(f)[0] for f in os.listdir(destination_images)
                   if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.tif'))]

    # Copy matching annotation files from the source to the destination directory
    for image_file in image_files:
        source_file = os.path.join(source_annotations, image_file + '.txt')
        destination_file = os.path.join(destination_images, image_file + '.txt')

        if os.path.exists(source_file):
            shutil.copy(source_file, destination_file)
            print(f"Copied {source_file} to {destination_file}")
        else:
            print(f"Annotation for {image_file} not found in source directory")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python script.py <source_annotations_directory> <destination_images_directory>")
        sys.exit(1)

    source_annotations = sys.argv[1]
    destination_images = sys.argv[2]

    if not os.path.isdir(source_annotations):
        print(f"Error: Source directory {source_annotations} does not exist.")
        sys.exit(1)

    if not os.path.isdir(destination_images):
        print(f"Error: Destination directory {destination_images} does not exist.")
        sys.exit(1)

    copy_annotations(source_annotations, destination_images)
