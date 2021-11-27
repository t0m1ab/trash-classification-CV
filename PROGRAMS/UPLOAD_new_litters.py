# -*- coding: cp1252 -*-

from sys import version
PYV = version[0] # python2 donne la str '2' et python3 la str '3'
import sqlite3
from PIL import Image,ImageTk
from useful_code import *


path_to_data = "../RESIZED_data/" # 'path_to_data' doit designer le chemin depuis le code jusqu'a la metadatabase SQL.
database = "metadatabase_TACO.db"
path_to_images = "../TO_UPLOAD/" # 'path_to_images' doit designer le chemin vers les images a ajouter
history_file = "new_labels_LIST.txt"


## PROGRAMME DE CHARGEMENT DES INFORMATIONS DE history_file DANS LA BASE SQL

def upload_litter(the_width=2448,the_height=3264,resize_tol=0.1,read_only = True):
    """
        Charge les images et leurs metadata stockees dans 'history_file' dans la 'database'
        Convention d'ecriture dans 'history_file' : origin_file_name----image_id----batch_nb----litter_id----supercategory
        Formats d'images acceptes : 4/3 et 1/1
    """
    WsurH = float(the_width)/float(the_height)
    if already_exists(database,place=path_to_data):
        if already_exists(history_file,place=path_to_images):
            existing_img = listdir(path_to_images)
            # Recuperation des infos sur les nouveaux dechets
            list_of_litter = get_history(history_file,place=path_to_images)
            # Connexion a la database SQL
            conn = sqlite3.connect(path_to_data + database)
            cursor = conn.cursor()
            # Recuperation des donnees
            cursor.execute('''SELECT category_id,supercategory,name FROM Categories''',())
            cat_and_id = cursor.fetchall()
            cat_name_to_id = {}
            for (cat_id,supercat,cat_name) in cat_and_id:
                cat_name_to_id[cat_name] = cat_id
            cat_name_list = list(cat_name_to_id.keys())
            # Chargement des donnees en SQL (après vérification des erreurs)
            data_to_upload = [] ; nb_litter_on_img = {}
            for [origin_img_file_name,img_id_,batch_nb_,litter_id_,supercat] in list_of_litter:
                img_id = int(img_id_) ; batch_nb = int(batch_nb_) ; litter_id = int(litter_id_)
                cursor.execute('''SELECT COUNT(*) FROM Images WHERE (image_id = ?)''',(img_id,))
                x = cursor.fetchone()[0]
                if x != 0: # Cet image_id existe deja !
                    print("# ERREUR -> L'image_id {0} existe deja dans '{1}'.".format(img_id,database))
                else:
                    cursor.execute('''SELECT COUNT(*) FROM Litter WHERE (litter_id = ?)''',(litter_id,))
                    x = cursor.fetchone()[0]
                    if x != 0: # Cet litter_id existe deja !
                        print("# ERREUR -> Le litter_id {0} existe deja dans '{1}'.".format(litter_id,database))
                    else:
                        ## Test l'existence de l'image
                        is_error = False
                        if not(origin_img_file_name in existing_img) and not(origin_img_file_name.split("/")[0] in existing_img): # Image inexistante
                            is_error = True
                        elif ("/" in origin_img_file_name) and not(origin_img_file_name.split("/")[0] in existing_img): # Sous-dossier inexistant
                            is_error = True
                        elif not(origin_img_file_name.split("/")[1] in listdir(path_to_images + origin_img_file_name.split("/")[0])): # Image inexistante dans sous-dossier
                            is_error = True

                        if is_error:
                            print("# ERREUR -> L'image '{0}' n'existe pas a l'emplacement '{1}'.".format(origin_img_file_name,path_to_images))
                        else:
                            ## PREPARATION enregistrement dans la table 'Images'
                            img_file_name = "batch_" + batch_nb_ + "/" + "0"*(6-len(img_id_)) + img_id_ + ".jpg"
                            # img_data = (img_id,the_width,the_height,img_file_name,batch_nb,'NOTHING','NOTHING','NOTHING',False,False)

                            ## PREPARATION enregistrement dans la table 'Litter'
                            if supercat in cat_name_to_id:
                                trash_data = (litter_id,'NOTHING','NOTHING','NOTHING','NOTHING',img_id,cat_name_to_id[supercat])
                            else:
                                print("ERREUR -> Categorie '{0}' pour image '{1}' inexistante".format(supercat,origin_img_file_name))
                                is_error = True

                            ## PREPARATION copie de l'image dans le bon batch
                            pil_image = Image.open(path_to_images + origin_img_file_name)
                            EXIF_rot = get_EXIF_rotation(pil_image)
                            if EXIF_rot != 0: # On met l'image sous son orientation EXIF (car elle est a priori la meilleure pour une image)
                                pil_image = pil_image.rotate(360-EXIF_rot,expand=1)
                            (width,height) = pil_image.size
                            if width>height:
                                pil_image = pil_image.rotate(90,expand=1) ; width,height = height,width
                            if (width,height) != (the_width,the_height):
                                if is_equal(float(width)/float(height),WsurH,resize_tol):
                                    pil_image = pil_image.resize((the_width,the_height))
                                    width,height = the_width,the_height
                                elif is_equal(float(width)/float(height),1.0,resize_tol): # On autorise le format carre
                                    if width != height: # 1310x1311 par exemple
                                        pil_image = pil_image.resize((width,width))
                                        height = width                                        
                                else:
                                    print("ERREUR -> Image '{0}' a dimensions {1}x{2} (pas un format 1 ni {3})".format(origin_img_file_name,width,height,WsurH))
                                    is_error = True
                            
                            ## AJOUT a la liste de chargement si pas d'erreur
                            if not(is_error):
                                img_data = (img_id,width,height,img_file_name,batch_nb,'NOTHING','NOTHING','NOTHING',False,False)
                                data_to_upload.append( {"img_file_name" : img_file_name ,
                                                        "origin_img_file_name" : origin_img_file_name ,
                                                        "img_data" : img_data ,
                                                        "trash_data" : trash_data ,
                                                        "pil_image" : pil_image} )
                                print("LITTER {0} FROM '{1}' IS {2}.".format(litter_id,origin_img_file_name,supercat))
                            if origin_img_file_name in nb_litter_on_img:
                                nb_litter_on_img[origin_img_file_name] += 1
                            else:
                                nb_litter_on_img[origin_img_file_name] = 1

            nb_errors = len(list_of_litter)-len(data_to_upload)
            if nb_errors != 0: # Il y a eu des erreurs
                if not(read_only):
                    print("\n# ---> Aucune donnee n'a ete chargee. Corrigez les {0} erreurs d'abord.".format(nb_errors))
                else:
                    print("\n# ---> {0} erreur(s) detectee(s) dans les donnees.".format(nb_errors))
            elif len(data_to_upload) != 0:
                if not(read_only):
                    # ENREGISTREMENT SQL et COPIE DES IMAGES
                    img_alrd_loaded = []
                    for data_dico in data_to_upload:
                        if not(data_dico["origin_img_file_name"] in img_alrd_loaded):
                            cursor.execute('''INSERT INTO Images VALUES (?,?,?,?,?,?,?,?,?,?)''',data_dico["img_data"])
                            data_dico["pil_image"].save(path_to_data + data_dico["img_file_name"])
                            img_alrd_loaded.append(data_dico["origin_img_file_name"])
                        cursor.execute('''INSERT INTO Litter VALUES (?,?,?,?,?,?,?)''',data_dico["trash_data"])
                    conn.commit()
                    print("\n# ---> Resume du chargement :")
                    for (name,eff) in list(nb_litter_on_img.items()):
                        print("- Image '{0}' enregistree avec {1} dechets".format(name,eff))
                else:
                    print("\n# ---> Resume du contenu du fichier :")
                    for (name,eff) in list(nb_litter_on_img.items()):
                        print("- Image '{0}' => {1} dechets".format(name,eff))
            else:
                print("\n# ---> Aucune donnee trouvee")
            conn.close()
        else:
            print("File '{0}' n'existe pas à l'emplacement '{1}'.".format(history_file,path_to_images))
    else:
        print("Database '{0}' n'existe pas à l'emplacement '{1}'.".format(database,path_to_data))


if __name__ == '__main__':
    ronly = True
    if PYV=='2':
        choice = raw_input("Ajout réel des images a la base de donnees (oui/non) : ")
    elif PYV=='3':
        choice = input("Ajout réel des images a la base de donnees (oui/non) : ")
    if (choice == "oui"):
        ronly = False
    print(" ")
    upload_litter(read_only = ronly)
