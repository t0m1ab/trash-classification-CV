# -*- coding: cp1252 -*-

import sqlite3
import pandas as pd
from useful_code import *

path_to_data = "../RESIZED_data/" # 'path_to_data' doit designer le chemin depuis le code jusqu'a la metadatabase SQL.
path_to_excel = "../new_labels/"


def upload_new_labels(excel_file="new_labels_ALL.xlsx", database="metadatabase_TACO.db",details = False):
    if already_exists(excel_file,place=path_to_excel):
        df = clean_df(get_dataframe(path_to_excel+excel_file))
        len_df = df.shape[0] # nombre de lignes
        print("Nombre de lignes recuperees dans {0} : {1}".format(excel_file,len_df))
        if already_exists(database,place=path_to_data):
            # Connexion SQL
            conn = sqlite3.connect(path_to_data + database)
            cursor = conn.cursor()
            # Recuperation des donnees
            cursor.execute('''SELECT category_id,supercategory,name FROM Categories''',())
            cat_and_id = cursor.fetchall()
            cat_name_list = [] ; supercat_list = [] ; cat_name_to_id = {}
            for (cat_id,supercat,cat_name) in cat_and_id:
                cat_name_list.append(cat_name.lower()) ; supercat_list.append(supercat.lower())
                cat_name_to_id[cat_name.lower()] = cat_id
            # Iteration sur les lignes de la dataframe (df)
            nb_recat = 0 ; already_labeled = []
            for ind in range(0,len_df):
                (litter_id,supercat,sous_cat) = list(df.iloc[ind,:])
                if supercat != supercat: # nan
                    supercat = "?"
                if sous_cat != sous_cat: # nan
                    sous_cat = "?"
                supercat = str(supercat.strip(" ")).lower()
                sous_cat = str(sous_cat.strip(" ")).lower()
                cursor.execute('''SELECT category_id FROM Litter WHERE litter_id = ?''',(str(litter_id),))
                old_cat_id = cursor.fetchone()[0]
                if old_cat_id == 58: # <=> Unlabeled litter
                    if supercat in supercat_list:
                        if sous_cat in cat_name_list:
                            new_sous_cat = sous_cat
                        else: # Place par defaut dans la categorie doublee
                            if details:
                                print("\nsous_categorie '{0}' inexistante".format(sous_cat))
                                print("-> Dechet (litter_id={0}) place par defaut dans la double_cat : {1}".format(litter_id,supercat))
                            new_sous_cat = supercat
                        cursor.execute('''UPDATE Litter SET category_id = ? WHERE litter_id = ?''',(cat_name_to_id[new_sous_cat] ,str(litter_id)))
                        nb_recat += 1
                    elif supercat != "?":
                        print("\nsupercategory '{0}' inexistante".format(supercat))
                        print("-> Dechet (litter_id={0}) non mis a jour".format(litter_id))

                elif details:
                    print("\n-> Dechet (litter_id={0}) deja labelise : {1} - {2}".format(litter_id,supercat,sous_cat))
                    already_labeled.append(litter_id)
            if nb_recat != 0:
                conn.commit() # Save (commit) the changes
                print("\n=> Nombre total de dechets relabelises = {0}".format(nb_recat))
                if already_labeled != []:
                    print("\n# Dechets deja labelises (id_litter) :")
                    for lit_id in already_labeled:
                        print(" - {0}".format(int(lit_id)))
            else:
                print("AUCUNE MODIFICATION SQL -> Categories inexistantes ou dechets deja labelises")
            conn.close() # Close the connection
                
        else:
            print("Database '{0}' n'existe pas à l'emplacement '{1}'.".format(database,path_to_data))
    else:
        print("Fichier '{0}' n'existe pas.".format(excel_file))


def maj_unlabeled_litter():
    create_double_cat()
    print("---------")
    add_new_cat("Other plastic","Plastic pen")
    add_new_cat("Fabric","Fabric")
    add_new_cat("Chirurgical Mask","Chirurgical Mask")
    print("---------")
    upload_new_labels(details=False)


# maj_unlabeled_litter()




