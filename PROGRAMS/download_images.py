'''
This script downloads TACO's images from Flickr given an metadata text file
Original code written by Pedro F. Proenza, 2019
'''

from os import path,mkdir,rename,system
import argparse
import json
from PIL import Image
import requests
from io import BytesIO
import sys


parser = argparse.ArgumentParser(description='')
parser.add_argument('--dataset_path', required=False, default= '../ORIGINAL_data/metadata_TACO.txt', help='Path to annotations')
args = parser.parse_args()

dataset_dir = path.dirname(args.dataset_path)

# Download images
print("Telechargement des images :\n")
with open(args.dataset_path, 'r') as f: # open(txt_file_path, 'r') as f:
    annotations = json.loads(f.read())

    nr_images = len(annotations['images'])
    for i in range(0,nr_images):

        image = annotations['images'][i]
        file_name = image['file_name'] ; img_height = image['height'] ; img_width = image['width']
        url_original = image['flickr_url']
        url_resized = image['flickr_640_url']
        file_path = path.join(dataset_dir, file_name)

        # Create the batch (folder) if necessary
        subdir = path.dirname(file_path)
        if not path.isdir(subdir):
            mkdir(subdir)

        if not path.isfile(file_path):
            # Load and Save Image
            response = requests.get(url_original)
            img = Image.open(BytesIO(response.content))
            if img._getexif():
                img.save(file_path, exif=img.info["exif"])
            else:
                img.save(file_path)

        # print("{0}/{1}".format(i+1,nr_images))
        np = int(float(i+1)/75)
        sys.stdout.write("\rCHARGEMENT [" + "X"*np + "-"*(20-np) + "] " + "{0}/1500".format(i+1))
        i+=1

print("\n\nTERMINE ! Toutes les donnees ont ete telechargees dans '../ORIGINAL_data'.")
print(" ") ; system("pause")
