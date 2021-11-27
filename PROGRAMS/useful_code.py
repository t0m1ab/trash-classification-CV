# -*- coding: utf-8 -*-

from PIL import Image, ExifTags
from PIL.ExifTags import TAGS
from os import listdir, rename, mkdir
from random import randrange
import pandas as pd

TAGS_keys = list(TAGS.keys())

# Liste de couleurs
'''
Jaune -> (252,220,18)
Gris -> (132,132,132)
Marron -> (159,85,30)
Ambre -> (240,195,0)
Bleu elec -> (44,117,255)
Rouge -> (247,35,12)
Mauve -> (212,115,212)
Vert Ã©meraude -> (1,215,88)
Vert opaline -> (151,223,198)
Tangerine -> (255,127,0)
'''
dico_COLORS = {'jaune':(252,220,18),'gris':(132,132,132),'marron':(159,85,30),'ambre':(240,195,0),'bleu_elec':(44,117,255),
               'mauve':(215,115,212),'vert_emeraude':(1,215,88),'vert_opaline':(151,223,198),'tangerine':(255,127,0)}

### FONCTIONS UTILES

def already_exists(file_name,place="."):
    """ Renvoie True si 'file_name' existe à l'emplacement 'place' et False sinon. """
    existing_files = listdir(place)
    for a_file in existing_files:
        if a_file == file_name:
            return(True)
    return(False)

def arr(x,p=2):
    """ Arrondit x à p chiffres après la virgule. """
    if p <= 0:
        return(int(x))
    else:
        return( float(int((x*(10**p))))/(10**p) )

def is_equal(a,b,tolerance=0):
    """ Test l'egalite entre a et b avec une tolerance numerique. """
    if abs(a-b)<=tolerance:
        return(True)
    return(False)

def get_random_colors(n):
    """ Renvoie n couleurs au hasard parmi le dico_COLORS. """
    key_colors = list(dico_COLORS.keys())
    the_colors = []
    for k in range(0,min(n,len(key_colors))):
        random_ind = randrange(0,len(key_colors)-1)
        the_colors.append(dico_COLORS[key_colors[random_ind]])
        key_colors.remove(key_colors[random_ind])
    return(the_colors)

def build_img_file_name(bnb,img_id,ext=".jpg"):
    """ (bnb=8,img_id=42,ext=".jpg") => Renvoie 'batch_8/000042.jpg' """
    img_id_str = str(img_id)
    return( "batch_" + str(bnb) + "/" + "0"*(6-len(img_id_str)) + img_id_str + ext )

def get_EXIF_rotation(pil_img):
    """ Retourne l'angle de rotation qu'il faut appliquer à file_name pour trouver l'image
        sauvegardee sans les exif (= img.save(file_name[:-4] + "sans_exif.png")).
        Rotation de image_with_EXIF a image_sans_EXIF."""
    exif = pil_img.getexif()
    if exif == None: # Pas d'exif pour cette image ! Tant mieux !
        return(0)
    else:
        for (exif_code,exif_value) in exif.items():
            if (exif_code in TAGS_keys) and (TAGS[exif_code] == 'Orientation'):
                # print("Image '{0}' has (for 'Orientation') exif_code = {1}".format(pil_img.filename,exif_code))
                if (exif_value == 0) or (exif_value == 1): # No EXIF Orientation
                    return(0)
                elif exif_value == 8:
                    return(270)
                elif exif_value == 3:
                    return(180)
                elif exif_value == 6:
                    return(90)
                else:
                    print("Problem EXIF data with '{0}'".format(pil_img.filename))
                    print("exif_value for 'Orientation' is {0}".format(exif_value))
                    return(0) # Par defaut, on ne touche pas a l'image
        # print("Problem EXIF data with '{0}'".format(pil_img.filename))
        # print("No 'Orientation' found")
        return(0) # Par defaut, on ne touche pas a l'image

def extract_from_tuple(list_in):
    """ [(1,),(2,),(3,)] => Renvoie [1,2,3] """
    list_out = []
    for x in list_in:
        list_out.append(x[0])
    return(list_out)

def get_files_on_type(type_list,place=".",folder=False):
    """ Renvoie la liste des fichiers à l'emplacement 'place' dont l'extension est dans 'type_list'. """
    existing_files = listdir(place) ; the_files = []
    if not(folder):
        for ext in type_list:
            for elt in existing_files:
                if (len(elt)>len(ext)) and (elt[-len(ext):]==ext):
                    try:
                        # unicode(elt) # Plante ici si il y a un accent ds elt
                        the_files.append(elt)
                    except:
                        pass
    else:
        for elt in existing_files:
            if len(elt.split(".")) == 1: # Pas d'extension <=> un dossier
                try:
                    # unicode(elt) # Plante ici si il y a un accent ds elt
                    the_files.append(elt)
                except:
                    pass
    return(the_files)
        

def get_dataframe(nom_fichier):
    """ Renvoie la dataframe associée aux données de 'nom_fichier' et aux 3 champs précisés. """
    input_df = pd.read_excel(nom_fichier, delimiter=';')
    df = input_df[["litter_id","supercategory","sous categorie"]]
    return(df)

# df = get_dataframe("new_labels/"+"new_labels_ALL.xlsx")

def clean_df(dataframe):
    """ Supprime les lignes telles que le premier element de la ligne est vide <=> Nan <=> (x!=x is True)
        ou si c'est une case pleine d'espaces. """
    len_df = dataframe.shape[0] ; ind_to_del = []
    for ind in range(0,len_df):
        x = list(dataframe.iloc[ind,:])[0]
        if (x != x): # Nan
            ind_to_del.append(ind)
    ind_to_del.reverse()
    for ind in ind_to_del:
        dataframe.drop(ind,inplace=True)
    return(dataframe)

# df = clean_df(get_dataframe("new_labels/"+"new_labels_ALL.xlsx"))

def get_history(history_file,place="./",show=False):
    """ Renvoie les informations de 'history_file' sous forme de liste de liste de string. """
    # (df['origin_file_name']==in_string).value_counts()
    f = open(place+history_file, "r")
    the_lines = f.read().split("\n") ; the_history = []
    for line in the_lines[1:]:
        elt = line.split("----")
        if len(elt)==5: # 5 elements attendus
            the_history.append(elt)
        else:
            print("# ANOMALIE : Line '{0}' is strange..".format(line))
    f.close()
    if show:
        for elt in the_history:
            print(elt)
    return(the_history)

# get_history("new_labels_LIST.txt",place="../TO_UPLOAD/",show=True)


def least_key(dico):
    """ Renvoie la clef c qui verifie dico[c]<=dico[k] pour tt k in dico.keys() """
    if dico == {}:
        return(None)
    else:
        the_keys = list(dico.keys()) ; c = the_keys[0]
        for k in the_keys:
            if dico[k]<dico[c]:
                c = k
        return(c)

def get_max(liste,order=0):
    """ Renvoie l'element max parmi tous les elements de liste[k][order] pour k dans [0,len(liste)-1] supposes >= 0.
        Renvoie 0 lorsque 'liste' est vide ou lorsqu'il y a un probleme sur les dimensions. """
    if (liste == []):
        return(0)
    else:
        try:
            the_max = int(liste[0][order])
            for k in range(1,len(liste)):
              elt = int(liste[k][order])
              if elt > the_max:
                  the_max = elt
            return(the_max)
        except:
            return(0)
        
    




    
    

