# -*- coding: utf-8 -*-

''' Programme d'initialisation de la database ainsi que les metadata dans un fichier SQL '''

### ======================================== INFORMATIONS ======================================== ###
# - TACO = Trash Annotations in COntext
# - 'bnb' = 'batch number' et est un entier entre 0 et 15 inclus.
# - 'litter_box' definie pour chaque dechet est une liste de 4 entiers definissant un rectangle encadrant le dechet sur l'image.
# - litter_box = [x,y,largeur,hauteur] où (x,y) sont les coord du point haut-gauche du rectangle et (largeur,hauteur) ses dimensions
# - Une 'segmentation' est une liste du style [[12,58,15,56],[58,26,58,25]]. On la sauvegarde sous la forme d'une string :
#   '12 58 15 56_58 26 58 25'
### ============================================================================================== ###

from sys import version
PYV = version[0] # python2 donne la str '2' et python3 la str '3'
if PYV=='2':
    import UserDict
elif PYV=='3':
    from collections import UserDict
else:
    print("Problem with Python version : {0}".format(version))
import sqlite3
from PIL import Image, ImageDraw
from os import system, listdir, rename, mkdir
import sys
from useful_code import *


path_to_original_data = "../ORIGINAL_data/" # 'path_to_original_data' doit designer le chemin depuis le repertoire de ce code jusqu'aux images telechargees et le fichier 'metadata.txt'
path_to_data = "../RESIZED_data/" # 'path_to_data' designe le chemin ou vont se trouver les batches des images traitees ainsi que la metadatabase SQL


def get_data_dict(text_file="metadata_TACO.txt"):
    """ Renvoie le dictionnaire contenant toutes les metadata de la database TACO. """
    fichier = open(path_to_original_data+text_file,"r")
    full_txt = fichier.read() #.decode('utf-8')
    fichier.close()
    null = 'NOTHING'
    if PYV=='2':
        dict_data = dict(UserDict.UserDict(eval(full_txt)))
    elif PYV=='3':
        dict_data = dict(UserDict(eval(full_txt)))
    return(dict_data)


def new_coordinates(x_old,y_old,L_x,L_y,rot_angle):
    """ Renvoie la nouvelle valeur des coord (x_old,y_old) apres rotation de l'image de 'rot_angle'
        On suppose que le parametre 'rot_angle' ne peut prendre que les 3 valeurs : 90,270 et 180. """
    if rot_angle == 90:
        return( (y_old,L_x-x_old) )
    elif rot_angle == 180:
        return( (L_x-x_old,L_y-y_old) )
    elif rot_angle == 270:
        return( (L_y-y_old,x_old) )


def normalize_segmentation(coord_list,id_tuple,L_x,L_y,rot_angle=0,resized=False,coef_xy=(1,1)):
    """ Convertit la liste [[12,58,15,56],[58,26,58,25]] en la string '12 58 15 56-58 26 58 25' par exemple.
        Gere une eventuelle rotation d'image et une dilatation/contraction de coefficient 'coef'.
        L_y = hauteur initiale de l'image ; L_x = largeur initiale de l'image
        -> Renvoie la string 'NOTHING' en cas d'erreur lors du traitement. """
    try:
        final_string = ""
        for a_list in coord_list:
            for k in range(0,len(a_list)//2): # 2*k pour les coord des x et 2*k+1 pour les coord des y
                int_x,int_y = int(a_list[2*k]),int(a_list[2*k+1]) # Transforme les 215.0 en 215
                if rot_angle != 0:
                    int_x,int_y = new_coordinates(int_x,int_y,L_x,L_y,rot_angle)
                if resized:
                    int_x,int_y = int(coef_xy[0]*int_x),int(coef_xy[1]*int_y)
                final_string += str(int_x) + " " + str(int_y) + " "
            final_string = final_string[:-1] + "_"
        return(final_string[:-1])
    except:
        print("PROBLEME : Chargement de 'segmentation' avec image_id={0} et litter_id={1}".format(id_tuple[0],id_tuple[1]))
        return("NOTHING")


def normalize_bbox(coord_list,id_tuple,L_x,L_y,rot_angle=0,resized=False,coef_xy=(1,1)):
    """ Convertit la liste [12,58,15,56] en la string '12 58 15 56' par exemple.
        Gere une eventuelle rotation d'image et une dilatation/contraction de coefficient 'coef'.
        -> Renvoie la string 'NOTHING' en cas d'erreur lors du traitement. """
    coord_string = str(coord_list)
    try:
        four_elts = coord_string.strip('][').split(',')
        for k in range(0,4):
            four_elts[k] = int(four_elts[k].strip(" ").split(".")[0])
        [x_box,y_box,larg_box,haut_box] = four_elts
        if rot_angle != 0: # On doit gerer le changement de point de reference haut/gauche (x_bbox,y_bbox)
            if rot_angle == 90:
                x_box,y_box = new_coordinates(x_box+larg_box,y_box,L_x,L_y,90) # On considère le point haut/droit de la box = (x_box+larg_box,y_box)
                larg_box,haut_box = haut_box,larg_box
            elif rot_angle == 180:
                x_box,y_box = new_coordinates(x_box+larg_box,y_box+haut_box,L_x,L_y,180) # On considère le point bas/droit de la box = (x_box+larg_box,y_box+haut_bbox)
            elif rot_angle == 270:
                x_box,y_box = new_coordinates(x_box,y_box+haut_box,L_x,L_y,270) # On considère le point bas/gauche de la box = (x_box,y_box+haut_bbox)
                larg_box,haut_box = haut_box,larg_box
        if resized:
            x_box,y_box = int(coef_xy[0]*x_box),int(coef_xy[1]*y_box)
            larg_box,haut_box = int(coef_xy[0]*larg_box),int(coef_xy[1]*haut_box)
        final_string = str(x_box) + " " + str(y_box) + " " + str(larg_box) + " " + str(haut_box)
        return(final_string)
    except:
        print("PROBLEME : Chargement de 'bbox' avec image_id={0} et litter_id={1}".format(id_tuple[0],id_tuple[1]))
        return("NOTHING")


def create_SQL_database(database_name, dict_data=get_data_dict(), the_width=2448, the_height=3264, resize_tol=0.1):
    """
        Importe les informations de 'dict_data' dans la database SQL 'database_name'.
        Tourne en mode portrait et redimensionne si necessaire les images au passage.
        PARAMETRES :
        - the_width [int] : Largeur desiree pour toutes les images de la database
        - the_height [int] : Hauteur desiree pour toutes les images de la database
        - resize_tol [float] : Une image dont le rapport Largeur/Hauteur est proche de (the_width/the_height)
                               a 'resize_tol' pres est redimensionnee au format (L=the_width,H=the_height)
        # Les donnees dossier 'ORIGINAL_data' ne sont pas modifiees par le programme.
        # Ce dernier produit seulement un dossier 'RESIZED_data' avec les donnees normalisees decrites plus haut.
    """
    if not(already_exists(path_to_data[3:-1],place="../")) and already_exists(path_to_original_data[3:-1],place="../"): # database_name + ".db" , place=path_to_data)):
        print("# CREATION DE LA METADATABASE SQL ET FORMATAGE DES IMAGES #")
        
        ### CREATION DE L'ENVIRONNEMENT (DOSSIER PRINCIPAL ET DOSSIERS BATCHES)
        mkdir(path_to_data[:-1])
        for k in range(1,16):
            mkdir(path_to_data + "batch_" + str(k))
        mkdir(path_to_data + "batch_0") # batch des images qu'on ne peut pas mettre facilement au format (the_width,the_height)
        
        # Create the connexion
        conn = sqlite3.connect(path_to_data + database_name + ".db")
        cursor = conn.cursor()

        ### CREATION DES TABLES
        # Create the table 'Images'
        cursor.execute( '''
                        CREATE TABLE Images(
                            image_id INTEGER PRIMARY KEY,
                            width INTEGER,
                            height INTEGER,
                            file_name TEXT,
                            batch_nb INTEGER,
                            date_captured TEXT,
                            flickr_url TEXT,
                            flickr_640_url TEXT,
                            turned BOOLEAN,
                            resized BOOLEAN)
                        ''')
        # Create the table 'Categories'
        cursor.execute( '''
                        CREATE TABLE Categories(
                            category_id INTEGER PRIMARY KEY,
                            name TEXT,
                            supercategory TEXT)
                        ''')
        # Create the table 'Annotations'
        cursor.execute( '''
                        CREATE TABLE Litter(
                            litter_id INTEGER PRIMARY KEY,
                            segmentation TEXT,
                            litter_box TEXT,
                            area TEXT,
                            iscrowd INTEGER,
                            image_id INTEGER,
                            category_id INTEGER,
                            FOREIGN KEY (image_id) REFERENCES Images(image_id),
                            FOREIGN KEY (category_id) REFERENCES Categories(category_id))
                        ''')
        print("\nTables 'Images'/'Categories'/'Litter' creees dans '{0}.db'".format(database_name))

        ### CHARGEMENT DES DONNEES
        WsurH = float(the_width)/float(the_height) # Rapport desire pour toutes les images
        rotated_images = {} ; resized_images = {} # Permet de retenir les modifications lorsqu'on chargera la table 'Litter'

        print("\nCHARGEMENT des donnees dans la table 'Images'") ; i=0
        ## Chargement de la table 'Images'
        bnb = 1 # On met une image dans chaque batch en passant les batch de 1 a 15 puis on recommence depuis le batch 1
        for img in dict_data['images']:
            # batch_nb = int(img['file_name'].split("_")[1].split("/")[0]) # Récupération num de batch à partir du file_name
            pil_image = Image.open(path_to_original_data + img['file_name'])

            # Prise en compte de l'orientation EXIF
            EXIF_rot = get_EXIF_rotation(pil_image)
            if EXIF_rot != 0: # On met l'image sous son orientation EXIF (car elle est a priori la meilleure pour une image)
                pil_image = pil_image.rotate(360-EXIF_rot,expand=1)
            (img_w,img_h) = pil_image.size # (img_w,img_h) representent alors vraiment les dimensions de l'image telle qu'elle apparait dans le batch => avec d'EXIF !
            new_w,new_h = img_w,img_h # Dimensions qui vont etre celles de l'image apres rotation et redimensionnement

            # Besoin de passer de PAYSAGE en PORTRAIT (+pi/2 dans le sens trigo)
            if img_w>img_h:
                pil_image = pil_image.rotate(90,expand=1) # expand=1 permet de tourner l'image ET de changer son format (le cadre limite)
                new_w,new_h = new_h,new_w
                rotated_images[img['id']] = (True,img_w,img_h,90)
            else:
                rotated_images[img['id']] = (False,img_w,img_h,0) 

            # Besoin de REDIMENSIONNER l'image
            if ((new_w,new_h)!=(the_width,the_height)) and is_equal(float(new_w)/float(new_h),WsurH,resize_tol):
                coef_x = float(the_width)/float(new_w) ; coef_y = float(the_height)/float(new_h)
                new_w,new_h = the_width,the_height
                pil_image = pil_image.resize((the_width,the_height),Image.ANTIALIAS)
                resized_images[img['id']] = (True,coef_x,coef_y)
            else:
                resized_images[img['id']] = (False,1,1)

            # On met dans batch_0 les images qu'on n'a pas reussi a mettre facilement au foramat (the_width,the_height)
            if (new_w,new_h) == (the_width,the_height): # Sauvegarde de l'image dans son batch d'origine
                img_file_name = build_img_file_name(bnb,img['id']) # Format '.jpg' par défaut
                pil_image.save(path_to_data + img_file_name) ; batch_nb=bnb ; bnb=(bnb%15)+1
            else: # Sauvegarde de l'image dans le batch 0 car elle n'a pas le format requis
                img_file_name = build_img_file_name(0,img['id']) # Format '.jpg' par défaut
                pil_image.save(path_to_data + img_file_name) ; batch_nb=0

            # Enregistrement des metadata dans la base SQL
            img_data = (img['id'],new_w,new_h,img_file_name,batch_nb,img['date_captured'],img['flickr_url'],img['flickr_640_url'],rotated_images[img['id']][0],resized_images[img['id']][0])
            cursor.execute('''INSERT INTO Images VALUES (?,?,?,?,?,?,?,?,?,?)''',img_data)

            # Barre de chargement # print(str(i/15)+" %")
            np = int(float(i+1)/75)
            sys.stdout.write("\rCHARGEMENT [" + "X"*np + "-"*(20-np) + "] " + "{0}/1500".format(i+1))
            i+=1
            
        print("Table 'Images' chargee !")

        print("\nCHARGEMENT des donnees dans la table 'Categories'")
        ## Chargement de la table 'Categories'
        for cat in dict_data['categories']:
            cat_data = (cat['id'],cat['name'],cat['supercategory'])
            cursor.execute('''INSERT INTO Categories VALUES (?,?,?)''',cat_data)
        print("Table 'Categories' chargee !")

        print("\nCHARGEMENT des donnees dans la table 'Litter'")
        ## Chargement de la table 'Litter'
        for trash in dict_data['annotations']:
            id_img = trash['image_id'] ; id_litter = trash['id']
            rotated_info,resized_info = rotated_images[id_img],resized_images[id_img] # rotated[1] = GRAND cote / rotated[2] = PETIT cote
            segmentation = normalize_segmentation(trash['segmentation'], (id_img,id_litter), L_x = rotated_info[1], L_y = rotated_info[2],
                                                  rot_angle=rotated_info[3], resized=resized_info[0], coef_xy=(resized_info[1],resized_info[2]))
            bbox = normalize_bbox(trash['bbox'], (id_img,id_litter), L_x = rotated_info[1], L_y = rotated_info[2],
                                                  rot_angle=rotated_info[3], resized=resized_info[0], coef_xy=(resized_info[1],resized_info[2]))
            trash_data = (id_litter,segmentation,bbox,str(trash['area']),trash['iscrowd'],id_img,trash['category_id'])
            cursor.execute('''INSERT INTO Litter VALUES (?,?,?,?,?,?,?)''',trash_data)
        print("Table 'Litter' chargee !")
        
        print("\n-> Base remplie avec succes.")

        # Save (commit) the changes
        conn.commit()
        # Close the connection
        conn.close()
        
    else:
        print("Folder '{0}' already exists or folder '{1}' doesn't exist.".format(path_to_data[:-1],path_to_original_data[:-1]))


if __name__ == '__main__':
    if PYV=='2':
        choice = raw_input("Press (1 + ENTER) to start or (0 + ENTER) to quit : ")
    elif PYV=='3':
        choice = input("Press (1 + ENTER) to start or (0 + ENTER) to quit : ")
    if (choice == "1") or (choice == ""):
        # Creation de la database SQL et formatage des images
        create_SQL_database("metadatabase_TACO")
        print(" ")
        # Normalisation de la database SQL
        create_double_cat()
        print(" ") ; system("pause")
