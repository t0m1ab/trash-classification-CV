# -*- coding: utf-8 -*-

''' Programmes de gestion de la database SQL '''

### ======================================== VOCABULAIRE ======================================== ###
# - TACO = Trash Annotations in COntext
# - 'bnb' = 'batch number' et est un entier entre 0 et 15 inclus.
# - 'litter_box' definie pour chaque dechet est une liste de 4 entiers definissant un rectangle encadrant le dechet sur l'image.
# - litter_box = [x,y,largeur,hauteur] où (x,y) sont les coord du point haut-gauche du rectangle et (largeur,hauteur) ses dimensions
# - Une 'segmentation' est une liste du style [[12,58,15,56],[58,26,58,25]]. On la sauvegarde sous la forme d'une string :
#   '12 58 15 56_58 26 58 25'
### ============================================================================================= ###


import sys
import sqlite3
from PIL import Image, ImageDraw, ImageFont
from os import listdir, rename, mkdir, remove, system
from random import randrange
from useful_code import *


# Parametre a changer si on souhaite executer le code depuis un autre emplacement.
path_to_data = "../RESIZED_data/" # 'path_to_data' doit designer le chemin depuis le code jusqu'a la metadatabase SQL.


### FONCTIONS DE GESTION


def find_litter_cat(image_id,database = "metadatabase_TACO.db"):
    """ Renvoie les 'name' de la table 'Categories' de tous les objets presents sur l'image indiquee. """
    if already_exists(database,place=path_to_data):
        # Create the connexion
        conn = sqlite3.connect(path_to_data + database)
        cursor = conn.cursor()
        # Get the informations
        cursor.execute('''SELECT COUNT(*) FROM Images WHERE (image_id = ?)''',(image_id,))
        x = cursor.fetchone()[0]
        if x == 0: # L'image n'existe pas !
            print("L'image_id {0} n'existe pas.".format(image_id))
            return(None)
        else:
            # Recuperation des identifiants de categories
            cursor.execute('''SELECT category_id FROM Litter WHERE (image_id = ?)''',(image_id,))
            les_cat_id_prov = cursor.fetchall()
            # Suppression des doublons parmi les id de categories et recuperation du nom de la categorie
            les_cat_id = [] ; les_cat_name = []
            for tuple_x in les_cat_id_prov:
                x = tuple_x[0]
                if not(x in les_cat_id): # Nouvelle categorie a ajouter
                    les_cat_id.append(x)
                    cursor.execute('''SELECT name FROM Categories WHERE (category_id = ?)''',(x,))
                    les_cat_name.append(cursor.fetchone()[0])
            return(les_cat_name)
        # Close the connection
        conn.close()
    else:
        print("File {0} doesn't exist.".format(database))
        return(None)

# x = find_litter_cat(115) ; print(x)


def nb_trash_on_img(image_id,database = "metadatabase_TACO.db"):
    """ Donne le nombre de dechets presents sur l'image indiquee. Renvoie 0 si l'image n'existe pas. """
    if already_exists(database,place=path_to_data):
        # Create the connexion
        conn = sqlite3.connect(path_to_data + database)
        cursor = conn.cursor()
        # Get the informations
        cursor.execute('''SELECT COUNT(*) FROM Litter WHERE image_id = ?''',(image_id,))
        tuple_nb = cursor.fetchone()
        return(tuple_nb[0])  
        # Close the connection
        conn.close()
    else:
        print("File {0} doesn't exist.".format(database)) ; return(None)

# x = nb_trash_on_img(18) ; print(x)


def delete_image(image_id, del_real=False, database = "metadatabase_TACO.db"):
    """ Supprime de la database SQL l'image correspondante. 'del_real = True' signifie qu'on cherche egalement a supprimer l'image de son dossier. """
    if already_exists(database,place=path_to_data):
        # Create the connexion
        conn = sqlite3.connect(path_to_data + database)
        cursor = conn.cursor()
        # Get the informations
        cursor.execute('''SELECT COUNT(*) FROM Images WHERE (image_id = ?)''',(image_id,))
        x = cursor.fetchone()[0]
        if x == 0: # L'image n'existe pas !
            print("L'image_id {0} n'existe pas.".format(image_id))
        else:
            if del_real:
                cursor.execute('''SELECT file_name FROM Images WHERE (image_id = ?)''',(image_id,))
                img_file_name = cursor.fetchone()[0]
                try:
                    remove(path_to_data + img_file_name)
                except:
                    print("L'image '{0}' est introuvable dans les dossiers.".format(img_file_name))
            cursor.execute('''DELETE FROM Litter WHERE image_id = ?''',(image_id,))
            cursor.execute('''DELETE FROM Images WHERE image_id = ?''',(image_id,))
            # Save (commit) the changes
            conn.commit()
            print("Image avec image_id = {0} a ete supprime de la base".format(image_id))
        # Close the connection
        conn.close()
    else:
        print("File {0} doesn't exist.".format(database))

# delete_image(15020,del_real=True)


def show_stat(database = "metadatabase_TACO.db"):
    """ Affiche des statistiques sur la database SQL. """
    if already_exists(database,place=path_to_data):
        # Create the connexion
        conn = sqlite3.connect(path_to_data + database)
        cursor = conn.cursor()
        # Get the information
        sql_request = '''SELECT supercategory,COUNT(*) AS tot
                     FROM (Litter JOIN Categories ON Litter.category_id = Categories.category_id)
                     GROUP BY supercategory
                     ORDER BY tot DESC'''
        cursor.execute(sql_request,())
        the_list = cursor.fetchall()
        for (supercat,nb_tot) in the_list:
            print("- {0} : {1}".format(supercat,nb_tot))
        # Close the connection
        conn.close()
    else:
        print("File {0} doesn't exist.".format(database))
    
# show_stat()


def str_to_int_list(the_string):
    """ Convertit la string "458 125 2961 43_158 689" en la liste [[458,125,2961,43],[15,689]] par exemple. """
    the_list = []
    for sous_liste in the_string.split("_"):
        int_list = []
        for elt in sous_liste.split(" "):
            int_list.append(int(elt))
        the_list.append(int_list)
    return(the_list)


def show_litter_on_image(image_id,database = "metadatabase_TACO.db",id_litter=True,box=True,polygon=False,fill=False,show=True,save=False,dest="./"):
    """ Affiche la segmentation des dechets presents sur l'image.
        - id_litter [boolean] : True => on affiche les id des dechets sur l'image
        - box [boolean] : True -> affiche un rectangle autour de chaque dechet
        - polygon [boolean] : True -> affiche le contour precis de chaque dechet
        - fill [boolean] : True -> colorie l'interieur de chaque polygone
        - show [boolean] : True -> affiche l'image obtenue
        - save [boolean] : True -> sauvegarde l'image obtenue
        - dest [string] : destination de sauvegarde de l'image """
    if already_exists(database,place=path_to_data):
        # Create the connexion
        conn = sqlite3.connect(path_to_data + database)
        cursor = conn.cursor()
        # Get the informations
        cursor.execute('''SELECT COUNT(*) FROM Images WHERE (image_id = ?)''',(image_id,))
        x = cursor.fetchone()[0]
        if x == 0: # L'image n'existe pas !
            print("L'image_id {0} n'existe pas.".format(image_id))
        else:            
            # Recuperation des informations
            cursor.execute('''SELECT litter_box, segmentation, litter_id FROM Litter WHERE (image_id = ?)''',(image_id,))
            tuple_list = cursor.fetchall()
            print("Nombre de dechets detectes sur l'image : {0}".format(len(tuple_list)))
            cursor.execute('''SELECT file_name FROM Images WHERE (image_id = ?)''',(image_id,))
            file_img_name = cursor.fetchone()[0]
            # Ouverture de l'image et definition de parametres de dessin
            pil_image = Image.open(path_to_data + file_img_name)
            draw = ImageDraw.Draw(pil_image,'RGBA') # 'RGBA' pour dessiner des polygones en couche alpha
            # fill_colors = get_random_colors(len(tuple_list)) # Couleurs opaques
            RED_color = (255,0,0,255) ; RED_color_alpha = (255, 0, 0, 80) # Couleur semi-transparente
            fill_colors = [RED_color for k in range(0,len(tuple_list))]
            line_width = 8 # Largeur du cadre 'box' et du contour 'polygon'
            if id_litter:
                font_size = 60 ; pil_font = ImageFont.truetype("arial.ttf", font_size)
            ### draw.text((300, 200),"Hello World !",(0,0,0),font=font)
            # Iteration sur chaque dechet de l'image
            for indice in range(0,len(tuple_list)):
                (str_box_list,str_segm_list,trash_id) = tuple_list[indice]
                box_list = str_to_int_list(str_box_list)[0]
                list_of_segm_list = str_to_int_list(str_segm_list) # Possiblement plusieurs polygones a dessiner
                if polygon or fill:
                    if list_of_segm_list != "NOTHING":
                        for segm_list in list_of_segm_list:
                            xy_list = [] # On recupere les coordonnees de chaque point de la segmentation
                            for ind in range(0,len(segm_list)//2):
                                xy_list.append( (segm_list[2*ind],segm_list[2*ind+1]) )
                            if polygon:
                                (x1,y1) = xy_list[0]
                                for ind in range(1,len(xy_list)):
                                    (x2,y2) = xy_list[ind]
                                    draw.line((x1,y1,x2,y2),fill=RED_color,width=line_width)
                                    (x1,y1) = (x2,y2)
                                draw.line((x1,y1,xy_list[0][0],xy_list[0][1]),fill=RED_color,width=line_width) # On ferme le polygone
                            if fill:
                                draw.polygon(xy_list, fill=RED_color_alpha)
                    else:
                        print("segmentation = NOTHING pour litter_id = {0}".format(trash_id))
                if box:
                    if box_list != "NOTHING":
                        [xr,yr,larg,haut] = box_list
                        draw.line((xr,yr,xr+larg,yr),fill=fill_colors[indice],width=line_width)
                        draw.line((xr,yr,xr,yr+haut),fill=fill_colors[indice],width=line_width)
                        draw.line((xr+larg,yr,xr+larg,yr+haut),fill=fill_colors[indice],width=line_width)
                        draw.line((xr,yr+haut,xr+larg,yr+haut),fill=fill_colors[indice],width=line_width)
                        if id_litter:
                            draw.text((xr+2,yr-font_size),str(trash_id),fill=(255,0,0),font=pil_font)
                    else:
                        print("litter_box = NOTHING pour litter_id = {0}".format(trash_id))
            if show:
                pil_image.show()
            elif save:
                pil_image = pil_image.save(dest + "image_id_" + str(image_id) + ".jpg")       

        # Close the connection
        conn.close()
    else:
        print("File {0} doesn't exist.".format(database))

# show_litter_on_image(image_id=830, box=True, polygon=True, fill=False)


def random_test_vizu(nb_tot):
    """ Permet de visualiser la segmentation de déchets sur 'nb_tot' photos sélectionnées au hasard. """
    if not(already_exists("random_test")):
        mkdir("random_test")
        for k in range(1,nb_tot+1):
            print("\n{0}/{1}".format(k,nb_tot))
            img_id = randrange(0,1499) ; print("image_id = {0}".format(img_id))
            show_litter_on_image(image_id=img_id, box=True, polygon=False, fill=False, show=False, save=True, dest="random_test/")
    else:
        print("Dossier 'random_test' already exists. Please delete it first.")

# random_test_vizu(10)


def check_SQL_database(database = "metadatabase_TACO.db"):
    """ Verifie si la database SQL est bien a jour par rapport aux images presentes physiquement dans les dossiers. """
    if already_exists(database,place=path_to_data):
        # Create the connexion
        conn = sqlite3.connect(path_to_data + database)
        cursor = conn.cursor()
        # Get the informations
        cursor.execute('''SELECT DISTINCT batch_nb FROM Images''',())
        batch_nb_list_ = cursor.fetchall() ; batch_nb_list = []
        batch_nb_list = sorted(extract_from_tuple(batch_nb_list_))
        del(batch_nb_list_)
        # On check chaque batch 1 a 1
        for batch_nb in batch_nb_list:
            print("\n# Analyse du BATCH {0}".format(batch_nb))
            img_in_folder = listdir(path_to_data + "batch_" + str(batch_nb))
            cursor.execute('''SELECT file_name FROM Images WHERE batch_nb = ?''',(batch_nb,))
            img_in_database = extract_from_tuple(cursor.fetchall())
            not_in_folder = []
            for img_file_name in img_in_database:
                img_name = img_file_name.split("/")[1]
                if img_name in img_in_folder:
                    img_in_folder.remove(img_name)
                else:
                    not_in_folder.append(img_name)
            no_problemo = True
            if not_in_folder != []:
                print("Images enregistrees dans la database mais inexistantes :")
                for img_name in not_in_folder:
                    print(" - " + img_name)
                no_problemo = False
            if img_in_folder != []:
                print("Images existantes mais non-enregistrees dans la database :")
                for img_name in img_in_folder:
                    print(" - " + img_name)
                no_problemo = False
            if no_problemo:
                print("-> Batch {0} is up-to-date with database !".format(batch_nb))            
        # Close the connection
        conn.close()
    else:
        print("Database '{0}' n'existe pas.".format(database))
        
# check_SQL_database()


def move_image(image_id,bnb_dest,database = "metadatabase_TACO.db"):
    """ Deplace une image dans un autre batch. """
    if already_exists(database,place=path_to_data):
        # Create the connexion
        conn = sqlite3.connect(path_to_data + database)
        cursor = conn.cursor()
        # Get the informations
        cursor.execute('''SELECT COUNT(*) FROM Images WHERE (image_id = ?)''',(image_id,))
        x = cursor.fetchone()[0]
        if x == 0: # L'image n'existe pas !
            print("L'image_id {0} n'existe pas.".format(image_id))
        else:
            # Recuperation des numeros de batch existants
            cursor.execute('''SELECT DISTINCT batch_nb FROM Images''',())
            batch_nb_list_ = cursor.fetchall() ; batch_nb_list = []
            batch_nb_list = sorted(extract_from_tuple(batch_nb_list_))
            del(batch_nb_list_)
            cursor.execute('''SELECT file_name,batch_nb FROM Images WHERE (image_id = ?)''',(image_id,))
            (file_img_name,bnb_origin) = cursor.fetchone()
            if (bnb_dest in batch_nb_list) and (bnb_origin != bnb_dest): # Deplacement possible
                new_file_img_name = "batch_" + str(bnb_dest) + "/" + file_img_name.split("/")[1]
                # 1 - Deplacement de l'image dans le nouveau batch
                pil_image = Image.open(path_to_data + file_img_name)
                pil_image.save(path_to_data + new_file_img_name)
                pil_image.close()
                remove(path_to_data + file_img_name)
                # 2 - Actualisation de l'info dans la database SQL
                cursor.execute('''UPDATE Images SET file_name = ?,batch_nb = ? WHERE file_name = ?''',(new_file_img_name,bnb_dest,file_img_name))
                conn.commit()
                print("Image '{0}' moved from batch {1} to batch {2} with success.".format(file_img_name.split("/")[1],bnb_origin,bnb_dest))
            else:
                print("Batch number {0} doesn't exist or image with image_id={1} is already in that batch.".format(bnb_dest,image_id))
        # Close the connection
        conn.close()
    else:
        print("File {0} doesn't exist.".format(database))

# move_image(image_id=8,bnb_dest=0,database = "metadatabase_TACO.db")


def get_pb_images(batch_nb,database = "metadatabase_TACO.db"):
    """ Identifie et copie dans un nouveau dossier les images du batch precise contenant un 'Unlabbeled litter'. """ 
    folder_name = "cat_pb_batch_" + str(batch_nb)
    mkdir(folder_name)
    conn = sqlite3.connect(path_to_data + database)
    cursor = conn.cursor()
    request = ''' SELECT I.image_id,L.litter_id 
                  FROM (Images AS I JOIN Litter AS L ON I.image_id = L.image_id)
                  WHERE (L.category_id = 58 AND batch_nb = ?) '''
    cursor.execute(request,(batch_nb,))
    list_of_ab = cursor.fetchall()
    ind = 1
    for (img_id,litt_id) in list_of_ab:
        show_litter_on_image(image_id=img_id, box=True, polygon=False, fill=False, show=False, save=True, dest=folder_name+"/")
        print("{0}/{1} : image_id = {2}".format(ind,len(list_of_ab),img_id)) ; ind += 1
    conn.close()

# get_pb_images(14)


def get_img_names(bnb,database = "metadatabase_TACO.db"):
    """ Renvoie les noms des images présentes dans le batch de numero 'bnb' selon la database SQL. """
    if already_exists(database,place=path_to_data):
        # Create the connexion
        conn = sqlite3.connect(path_to_data + database)
        cursor = conn.cursor()
        # Get the informations
        cursor.execute('''SELECT file_name FROM Images WHERE batch_nb = ?''',(bnb,))
        tuple_nb = cursor.fetchall()
        la_liste = extract_from_tuple(tuple_nb)
        for k in range(0,len(la_liste)):
            la_liste[k] = la_liste[k].split("/")[1]
        return(la_liste)  
        # Close the connection
        conn.close()
    else:
        print("File {0} doesn't exist.".format(database)) ; return(None)    

# la_liste = get_img_names(bnb=1)


def le_programme(id_categories,batch_nbs,database = "metadatabase_TACO.db"):
    # Create the connexion
    conn = sqlite3.connect(path_to_data + database)
    cursor = conn.cursor()
    les_cat = "(" + str(id_categories)[1:-1] + ")"
    les_bnb = "(" + str(batch_nbs)[1:-1] + ")"
    request = ''' SELECT file_name, MAX(test_binaire) AS x
                  FROM(
                  SELECT DISTINCT I.file_name, (C.category_id IN {0}) AS test_binaire
                  FROM( (Litter AS L JOIN Images AS I ON I.image_id = L.image_id)
                  JOIN Categories AS C ON C.category_id = L.category_id)
                  WHERE (I.batch_nb IN {1})
                  )
                  GROUP BY file_name'''.format(les_cat,les_bnb)
    cursor.execute(request,())
    liste = cursor.fetchall()
    # Close the connection
    conn.close()
    return(liste)

# l = le_programme([4,5,6],[10,11,12,13])


def copy_resize(new_width,new_height,bar_size=20,database='metadatabase_TACO.db'):
    """ Copie la database avec toutes les photos au format [new_width x new_height]. """
    conn = sqlite3.connect(path_to_data + database)
    cursor = conn.cursor()
    cursor.execute('''SELECT COUNT(*) FROM (SELECT image_id FROM Images WHERE batch_nb != 0)''',())
    tot_photos = cursor.fetchone()[0]
    conn.close()
    loading_step = float(tot_photos)/bar_size
    print("Nombre total de photos : {0}".format(tot_photos))
    new_folder = "../RESIZED_data_"+str(new_width)+"x"+str(new_height)
    if not(already_exists(new_folder[3:],place="../")):
        k = 1
        mkdir(new_folder)
        for bnb in range(1,16):
            path_to_old_batch = "../RESIZED_data/batch_" + str(bnb) + "/"
            mkdir(new_folder + "/batch_" + str(bnb))
            path_to_new_batch = new_folder + "/batch_" + str(bnb) + "/"
            img_in_batch = listdir(path_to_old_batch)
            for img_name in img_in_batch:
                pil_image = Image.open(path_to_old_batch + img_name)
                pil_image = pil_image.resize((new_width,new_height))
                pil_image.save(path_to_new_batch + img_name)
                # Affichage barre de chargement
                np = int(float(k+1)/loading_step)
                sys.stdout.write("\rCHARGEMENT [" + "="*np + ">" + "-"*(bar_size-np) + "] " + "{0}/{1}".format(k+1,tot_photos))
                k+=1
        print("Termine.")
    else:
        print("Dossier '{0}' existe deja.".format(new_folder))
    system("pause")

# copy_resize(224,224)


def update_copy_database(new_width,new_height,read_only=True,database='metadatabase_TACO.db'):
    """ Met a jour la copie de la database deja existante avec toutes les photos au format [new_width x new_height]. """
    new_folder = "../RESIZED_data_"+str(new_width)+"x"+str(new_height)
    if already_exists(new_folder[3:],place="../"):
        img_found = []
        for bnb in range(1,16):
            batch_path = "/batch_" + str(bnb) + "/"
            images_in_batch = listdir("../RESIZED_data" + batch_path)
            already_in_batch = listdir(new_folder + batch_path)
            for img_name in images_in_batch:
                if not(img_name in already_in_batch):
                    if not(read_only):
                        pil_image = Image.open("../RESIZED_data" + batch_path + img_name)
                        pil_image = pil_image.resize((new_width,new_height))
                        pil_image.save(new_folder + batch_path + img_name)
                    img_found.append(img_name)
        print("{0} nouvelles images trouvees.".format(len(img_found)))
        return(img_found)
    else:
        print("Dossier '{0}' inexistant.".format(new_folder))
        return([])
    system("pause")

# img_found_list = update_copy_database(224,224) #,read_only=False)


def litter_in_batch(cat_num,database = "metadatabase_TACO.db"):
    """ Donne le nombre de photos et de dechets dont la categorie figure dans 'cat_num' par batch. """
    # Create the connexion
    conn = sqlite3.connect(path_to_data + database)
    cursor = conn.cursor()
    les_cat = "(" + str(cat_num)[1:-1] + ")"
    for bnb in range(1,16):
        request = ''' SELECT COUNT(*) FROM(
                      SELECT DISTINCT I.image_id
                      FROM( (Litter AS L JOIN Images AS I ON I.image_id = L.image_id)
                      JOIN Categories AS C ON C.category_id = L.category_id )
                      WHERE (I.batch_nb = {0}) AND (C.category_id IN {1}) )'''.format(bnb,les_cat)
        cursor.execute(request,())
        nb_img = cursor.fetchone()[0]
        request = ''' SELECT COUNT(*) FROM(
                      SELECT DISTINCT L.litter_id
                      FROM( (Litter AS L JOIN Images AS I ON I.image_id = L.image_id)
                      JOIN Categories AS C ON C.category_id = L.category_id )
                      WHERE (I.batch_nb = {0}) AND (C.category_id IN {1}) )'''.format(bnb,les_cat)
        cursor.execute(request,())
        nb_litter = cursor.fetchone()[0]
        print("Batch_{0} : {1} photos - {2} dechets".format(bnb,nb_img,nb_litter))
    # Close the connection
    conn.close()

# print(litter_in_batch([4,5,6]))


def create_double_cat(database="metadatabase_TACO.db"):
    """ Pour une supercategorie X donnee, la fonction cree dans la database SQL la sous-cat X de X si elle n'existe pas deja.
        Ce processus est itere sur toutes les supercategorie X existantes. """
    if already_exists(database,place=path_to_data):
        # Connexion SQL
        conn = sqlite3.connect(path_to_data + database)
        cursor = conn.cursor()
        # Recuperation des donnees
        cursor.execute('''SELECT supercategory,name FROM Categories''',())
        supercat_cat_list = cursor.fetchall()
        # Construction de la liste des categories doubles a ajouter
        supercat_to_add = []
        for (supercat,_) in supercat_cat_list:
            if supercat not in supercat_to_add:
                cursor.execute('''SELECT COUNT(*) FROM Categories WHERE (name = ?)''',(supercat,))
                x = cursor.fetchone()[0]
                if (x == 0): # La sous_cat n'existe pas
                    supercat_to_add.append(supercat)
        # Ajout des nouvelles categories doubles
        cursor.execute('''SELECT category_id FROM Categories ORDER BY category_id DESC LIMIT 1''',())
        max_cat_id = cursor.fetchone()[0]
        if supercat_to_add != []:
            for supercat in supercat_to_add:
                max_cat_id += 1
                cursor.execute('''INSERT INTO Categories VALUES (?,?,?)''',(max_cat_id,supercat,supercat))
                print("AJOUT SQL -> [category_id : {2}]----[supercategory : {0}]---[NEW sous-categorie : {1}]".format(supercat,supercat,max_cat_id))
            # Save (commit) the changes
            conn.commit()
        else:
            print("AUCUNE MODIFICATION SQL -> Toutes les categories double existent deja.")
        # Close the connection
        conn.close()
    else:
        print("Fichier '{0}' n'existe pas.".format(excel_file))

# create_double_cat()


def add_new_cat(supercategory,sous_categorie,database="metadatabase_TACO.db"):
    """ Ajoute la nouvelle categorie definie par (supercategory,sous_categorie) a la database SQL. """
    if already_exists(database,place=path_to_data):
        # Connexion SQL
        conn = sqlite3.connect(path_to_data + database)
        cursor = conn.cursor()
        # Recuperation des donnees
        cursor.execute('''SELECT category_id FROM Categories ORDER BY category_id DESC LIMIT 1''',())
        max_cat_id = cursor.fetchone()[0]
        # Traitement
        cursor.execute('''SELECT COUNT(*) FROM Categories WHERE (supercategory = ?) AND (name = ?)''',(supercategory,sous_categorie))
        x = cursor.fetchone()[0]
        if (x == 0): # La categorie n'existe pas
            cursor.execute('''SELECT COUNT(*) FROM Categories WHERE (supercategory = ?)''',(supercategory,))
            x = cursor.fetchone()[0]
            if (x == 0): # La supercategory n'existe pas
                max_cat_id += 1
                cursor.execute('''INSERT INTO Categories VALUES (?,?,?)''',(max_cat_id,sous_categorie,supercategory))
                print("AJOUT SQL -> [category_id : {2}]----[supercategory : {0}]---[NEW sous-categorie : {1}]".format(supercategory,sous_categorie,max_cat_id)) 
            else:
                max_cat_id += 1
                cursor.execute('''INSERT INTO Categories VALUES (?,?,?)''',(max_cat_id,sous_categorie,supercategory))
                print("AJOUT SQL -> [category_id : {2}]----[supercategory : {0}]---[NEW sous-categorie : {1}]".format(supercategory,sous_categorie,max_cat_id)) 
            # Save (commit) the changes
            conn.commit()
        else:
            print("AUCUNE MODIFICATION SQL -> Reference deja existante [supercategory : {0}]---[sous-categorie : {1}]".format(supercategory,sous_categorie))
        # Close the connection
        conn.close()
    else:
        print("Fichier '{0}' n'existe pas.".format(excel_file))

# add_new_cat("Mask","Mask")



