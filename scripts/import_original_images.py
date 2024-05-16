import os
import shutil
import sys

def import_original_images(source_dir, target_dir):
    # Ensure the target directory exists
    os.makedirs(target_dir, exist_ok=True)

    # Iterate over all files in the source directory
    for filename in os.listdir(source_dir):
        if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.tif')) and "_rotated_" not in filename:
            source_path = os.path.join(source_dir, filename)
            target_path = os.path.join(target_dir, filename)
            
            # Copy the original image to the target directory
            shutil.copy(source_path, target_path)
            print(f"Copied {source_path} to {target_path}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python import_original_images.py <source_directory> <target_directory>")
        sys.exit(1)

    source_directory = sys.argv[1]
    target_directory = sys.argv[2]

    if not os.path.isdir(source_directory):
        print(f"Error: Source directory {source_directory} does not exist.")
        sys.exit(1)

    if not os.path.isdir(target_directory):
        os.makedirs(target_directory)

    import_original_images(source_directory, target_directory)
