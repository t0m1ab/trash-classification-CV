# -*- coding: cp1252 -*-

''' Programme pour ajouter toutes les images de la database TIDY a la database TACO '''

from os import listdir
from PIL import Image,ImageTk
import sqlite3
from useful_code import *


path_to_TIDY = "../../Database_TIDY/" # 'path_to_TIDY' doit désigner le chemin jusqu'aux sous-dossiers de la database TIDY
path_to_data = "../RESIZED_data/" # 'path_to_data' designe le chemin jusqu'aux batches d'images TACO ainsi que la database SQL

folder_names = ["Bottle cap","Broken glass","Can","Cigarette","Cup","Glass bottle","Normal paper","Plastic bag & wrapper","Clear plastic bottle"]


### ======================================================== PRE-TRAITEMENT MANUEL ======================================================== ###
# Placer un dossier 'Database_TIDY' à l'emplacement 'path_to_TIDY' contenant 10 sous-dossiers dont les noms sont listes dans 'folder_name'
# Dans chacun de ses sous-dossiers doit se trouver des images de TIDY contenant un dechet correspondant au nom du sous-dossier dans lequel
# est l'image
# Les categories de folder_names correspondent au 'name' de la table 'Categories" de la database SQL, il est donc possible de reorganiser
# plus finement les dechets au sein de ces categories manuellement avant de charger les informations via le programme 'upload_TIDY_database'.
### ======================================================================================================================================= ###


def auto_turn_images(folder_name,the_width,the_height,act=False):
    """ Tourne et redimensionne automatiquement les images contenues dans 'folder' """
    list_of_imgs = listdir(path_to_TIDY + folder_name)
    print("{0} images found in '{1}':".format(len(list_of_imgs),folder_name))
    for img_name in list_of_imgs:
        pil_image = Image.open(path_to_TIDY + folder_name + img_name)
        (w,h) = pil_image.size
        if (the_width<the_height) and (w>h):
            pil_image = pil_image.rotate(90,expand=1) ; w,h=h,w ; need_to_act = True
        elif (the_width>the_height) and (w<h):
            pil_image = pil_image.rotate(90,expand=1) ; w,h=h,w ; need_to_act = True
        if (the_width,the_height) != (w,h):
            pil_image = pil_image.resize((the_width,the_height),Image.ANTIALIAS) ; need_to_act = True
        if act and need_to_act:
            pil_image.save(path_to_TIDY + folder_name + img_name)
        print(img_name)
    print("Termine.")

# auto_turn_images("cigarette/",3000,4000,act=False)


def upload_TIDY_database(database='metadatabase_TACO.db'):
    """ Charge les images de la database TIDY dans la database TACO. """
    conn = sqlite3.connect(path_to_data + database)
    cursor = conn.cursor()
    
    ### RECUPERATION DES DONNEES DE LA DATABASE SQL
    dico_link = {}
    for fname in folder_names:
        cursor.execute('''SELECT category_id FROM Categories WHERE name=?''',(fname,))
        dico_link[fname] = cursor.fetchone()[0]
    print(dico_link)
    cursor.execute('''SELECT image_id FROM Images ORDER BY image_id DESC LIMIT 1''',())
    next_img_id = cursor.fetchone()[0]+1
    cursor.execute('''SELECT litter_id FROM Litter ORDER BY litter_id DESC LIMIT 1''',())
    next_litt_id = cursor.fetchone()[0]+1
    cursor.execute('''SELECT batch_nb,COUNT(*) FROM Images GROUP BY batch_nb''',())
    b_eff = cursor.fetchall()
    dico_batches = {}
    for (bnb,eff) in b_eff:
        dico_batches[bnb] = eff

    list_of_folders = listdir(path_to_TIDY) ; tot_photos = 0
    for folder_name in list_of_folders:
        list_of_imgs = listdir(path_to_TIDY + folder_name)
        print("\nChargement du dossier '{0}' ({1} photos)".format(folder_name,len(list_of_imgs)))
        for img_name in list_of_imgs:
            path_to_image = path_to_TIDY + folder_name + "/" + img_name

            ## PREPARATION copie de l'image dans le bon batch
            pil_image = Image.open(path_to_image)
            EXIF_rot = get_EXIF_rotation(pil_image)
            if EXIF_rot != 0: # On met l'image sous son orientation EXIF (car elle est a priori la meilleure pour une image)
                pil_image = pil_image.rotate(360-EXIF_rot,expand=1)
            (width,height) = pil_image.size
            if width>height:
                pil_image = pil_image.rotate(90,expand=1) ; width,height = height,width
            if (width,height) != (3000,4000):
                print("PROBLEME : {0}".format(folder_name + "/" + img_name))
            
            ## ENREGISTREMENT SQL
            bnb = least_key(dico_batches)
            img_file_name = "batch_" + str(bnb) + "/" + "0"*(6-len(str(next_img_id))) + str(next_img_id) + ".png"
            # Chargement dans la table IMAGES
            img_data = (next_img_id,width,height,img_file_name,bnb,'NOTHING','NOTHING','NOTHING',False,False)
            cursor.execute('''INSERT INTO Images VALUES (?,?,?,?,?,?,?,?,?,?)''',img_data)
            # Chargement dans la table LITTER
            trash_data = (next_litt_id,'NOTHING','NOTHING','NOTHING','NOTHING',next_img_id,dico_link[folder_name])
            cursor.execute('''INSERT INTO Litter VALUES (?,?,?,?,?,?,?)''',trash_data)

            ## COPIE DE L'IMAGE
            pil_image.save(path_to_data + img_file_name)
            print("- {0} --> image_id = {1} --> batch {2}".format(img_name,next_img_id,bnb))
            dico_batches[bnb] += 1 ; next_img_id += 1 ; next_litt_id += 1
        tot_photos += len(list_of_imgs)
         
    conn.commit()
    conn.close()
    print("\n-> Database TIDY chargee dans Database TACO ({0} photos).".format(tot_photos))

upload_TIDY_database()
    
