# -*- coding: cp1252 -*-

from sys import version
PYV = version[0]
if PYV=='2':
    import Tkinter as tk
elif PYV=='3':
    import tkinter as tk
else:
    print("Problem with Python version : {0}".format(version))
import ttk
import sqlite3
from PIL import Image,ImageTk
from useful_code import *


path_to_data = "../RESIZED_data/" # 'path_to_data' doit designer le chemin depuis le code jusqu'a la metadatabase SQL.
database = "metadatabase_TACO.db"
path_to_images = "../TO_UPLOAD/" # 'path_to_images' doit designer le chemin vers les images a ajouter
history_file = "new_labels_LIST.txt"


def center_window(w,dimensions):
    """ Centre la fenêtre 'w' au milieu de l'écran. ['dimensions' = "largeurxhauteur"] """
    [l,h] = dimensions.split("x")
    largeur = int(l) ; hauteur = int(h)
    L_ecran = w.winfo_screenwidth() ; H_ecran = w.winfo_screenheight()
    w.geometry( dimensions+"+"+str((L_ecran-largeur)//2)+"+"+str((H_ecran-hauteur)//2) )


## PROGRAMME DE LA FENETRE Tkinter D'AJOUT D'UNE IMAGE

class New_Image_Window():
    """ Fenetre tkinter permettant d'ajouter une image a la database SQL
        L'option 'ajout automatique' dans la database SQL permet a la fois d'ajouter l'image et ses dechets dans la database SQL
        mais aussi de copier l'image dans le batch correspondant. """
    def __init__(self,the_width=2448,the_height=3264,resize_tol=0.1): # Se lance à la création de la fenêtre !
        if already_exists(database,place=path_to_data):
            if not(already_exists(path_to_images[3:-1],"../")):
                mkdir(path_to_images)
            entete = "origin_file_name----image_id----batch_nb----litter_id----supercategory"
            if not(already_exists(history_file,path_to_images)):
                self.the_history = []
                f = open(path_to_images+history_file,'w')
                f.write(entete)
                f.close()
            else:
                self.the_history = get_history(history_file,place=path_to_images)
            
            ## CREATION DE LA FENETRE TKINTER ET DES PARAMETRES GENERAUX
            self.root = tk.Tk()
            self.dim = "1000x740" # "largeurxhauteur"
            center_window(self.root,self.dim)
            self.bg_color = 'light goldenrod' ; self.cat_color = 'orange'
            self.root.configure(bg=self.bg_color)
            self.font = ("arial",15)
            self.root.title("Etiquetage Image Database SQL")
            self.valid_img = get_files_on_type(['.jpg','.JPG','.png'],place=path_to_images)
            self.valid_folder = [" "] + get_files_on_type([],place=path_to_images,folder=True)
            self.nb_max_litter = 5
            self.the_width = the_width ; self.the_height = the_height ; self.resize_tol = resize_tol
            self.WsurH = float(self.the_width)/float(self.the_height)

            ### RECUPERATION DES DONNEES DE LA DATABASE SQL
            conn = sqlite3.connect(path_to_data + database)
            cursor = conn.cursor()
            cursor.execute('''SELECT category_id,supercategory FROM Categories GROUP BY supercategory ORDER BY supercategory ASC''',())
            cat_name_and_id = cursor.fetchall()
            self.list_cat = [] ; self.cat_name_to_id = {}
            for (cat_id,cat_name) in cat_name_and_id:
                self.list_cat.append(cat_name) ; self.cat_name_to_id[cat_name] = cat_id
            if 'Unlabeled litter' in self.list_cat:
                self.list_cat.remove('Unlabeled litter')
            self.list_cat = [" "] + self.list_cat
            cursor.execute('''SELECT image_id FROM Images ORDER BY image_id DESC LIMIT 1''',())
            self.next_img_id = max(cursor.fetchone()[0],get_max(self.the_history,order=1)) + 1
            cursor.execute('''SELECT litter_id FROM Litter ORDER BY litter_id DESC LIMIT 1''',())
            self.next_litt_id = max(cursor.fetchone()[0],get_max(self.the_history,order=3)) + 1
            cursor.execute('''SELECT batch_nb,COUNT(*) FROM Images GROUP BY batch_nb''',())
            b_eff = cursor.fetchall()
            self.dico_batches = {}
            for (bnb,eff) in b_eff:
                self.dico_batches[bnb] = eff
            conn.close()

            ### ORGANISATION DE LA FENETRE TKINTER
            ## Zone image
            self.zone_img = tk.Canvas(self.root, width = 470, height = 620, bg='salmon', highlightthickness=0)
            self.icon_no_img = ImageTk.PhotoImage(Image.open("ANNEXES./no_image_icon.png").resize((200,200)))
            self.zone_img.create_image(235,310, image=self.icon_no_img, tag="no_img_icon") #, anchor = (235,310))
            self.zone_img.grid(row=0,column=5,rowspan=8,columnspan=2,padx=20,pady=20) #,pady=20) sticky='e'
            ## Bouton d'enregistrement IMAGE
            tk.Button(self.root,text="LABEL image",command=self.upload_img,bg='green',font=self.font).grid(row=9,column=5,pady=10)
            ## Bouton d'enregistrement DOSSIER
            tk.Button(self.root,text="LABEL folder",command=self.upload_folder,bg='yellow',font=self.font).grid(row=9,column=6,pady=10)
            ## Titre label
            tk.Label(self.root,text="Etiqueter une image",bg=self.bg_color, font=('impact',36)).grid(row=0,column=0,columnspan=3,pady=16)
            ## Saisie d'un nom d'image
            # 1 - label gauche
            tk.Label(self.root,text="Nom d'image :",bg=self.bg_color, font=self.font).grid(row=1,column=0,sticky='se')
            # 2 - zone de saisie et de choix
            self.img_name = ttk.Combobox(self.root,values=self.valid_img,font=self.font)
            self.img_name.grid(row=1,column=1,sticky='s')
            # 3 - show button
            tk.Button(self.root,text="Show",command=self.show_img,bg='cyan',font=self.font).grid(row=1,column=2,sticky='s')
            ## Saisie d'un nom de dossier
            # 1 - label gauche
            tk.Label(self.root,text="Nom de dossier :",bg=self.bg_color, font=self.font).grid(row=2,column=0,pady=10,sticky='se')
            # 2 - zone de saisie et de choix
            self.folder_name = tk.StringVar() ; self.folder_name.set(" ")
            self.folder_choice = tk.OptionMenu(self.root,self.folder_name,*self.valid_folder)
            self.folder_choice['width']=10 ; self.folder_choice['font'] = self.font
            self.folder_choice.grid(row=2,column=1,pady=8,sticky='s')
            ## Saisie des categories de dechet
            self.list_choice_cat = [] ; self.list_OptMenu = []
            for k in range(0,self.nb_max_litter):
                self.list_choice_cat.append(tk.StringVar())
                tk.Label(self.root,text="Litter "+str(k+1)+" :",bg=self.bg_color, font=self.font).grid(row=k+3,column=0)
                self.list_choice_cat[k].set(self.list_cat[0])
                self.list_OptMenu.append(tk.OptionMenu(self.root,self.list_choice_cat[k],*self.list_cat))
                self.list_OptMenu[k]['width']=20 ; self.list_OptMenu[k]['font'] = self.font ; self.list_OptMenu[k]['bg'] = self.cat_color
                self.list_OptMenu[k].grid(row=k+3,column=1)
            # Bouton ajout automatique dans la database SQL
            self.upload_SQL = tk.IntVar()
            tk.Checkbutton(self.root,text="Ajout automatique à la base SQL",variable=self.upload_SQL,bg=self.bg_color, font=(self.font[0],self.font[1]-2)).grid(row=9,column=0,columnspan=3)
            
            # Ajustement de la grille à la fenêtre
            self.expand_grid(6,10)
            # Boucle principale
            self.root.mainloop()
            print("FIN")
        else:
            print("Database '{0}' n'existe pas à l'emplacement '{1}'.".format(database,path_to_data))

    def expand_grid(self,nb_col,nb_row):
        for k in range(0,nb_col+1): # On étend les colonnes
            self.root.columnconfigure(k, weight=1)
        for k in range(0,nb_row+1): # On étend les lignes
            self.root.rowconfigure(k, weight=1)

    def show_img(self):
        in_string = self.img_name.get()
        if in_string in self.valid_img:
            selected_img = Image.open(path_to_images+in_string) #.resize((450,600))
            # On met l'image sous son orientation EXIF (car elle est a priori la meilleure pour une image)
            EXIF_rot = get_EXIF_rotation(selected_img)
            if EXIF_rot != 0:
                selected_img = selected_img.rotate(360-EXIF_rot,expand=1)
            (width,height) = selected_img.size
            if width>height:
                selected_img = selected_img.rotate(90,expand=1)
            selected_img = selected_img.resize((450,600))
            self.the_img = ImageTk.PhotoImage(selected_img)
            self.zone_img.delete("image")
            self.zone_img.create_image(235,310, image=self.the_img, tag="image") #, anchor = (235,310))
            self.root.update()
        elif in_string.strip(" ") == "":
            self.zone_img.delete("image") ; self.root.update()
            
    def upload_img(self):
        the_litter_cat = []
        for k in range(0,self.nb_max_litter):
            a_cat = self.list_choice_cat[k].get()
            if a_cat != " ":
                the_litter_cat.append(a_cat)
        in_string = self.img_name.get()
        
        if (in_string in self.valid_img) and (the_litter_cat != []): # Donnees rentrees valides
            valid_img = True ; ind = 0
            while (ind < len(self.the_history)) and valid_img:
                if self.the_history[ind][0] == in_string:
                    valid_img = False ; print("# ERREUR : '{0}' deja categorisee dans '{1}' avec image_id={2}".format(in_string,history_file,self.the_history[ind][1]))
                ind += 1
            pil_image = Image.open(path_to_images + in_string)
            (width,height) = pil_image.size
            if width>height:
                pil_image = pil_image.rotate(90,expand=1) ; width,height=height,width
            if is_equal(float(width)/float(height),self.WsurH,self.resize_tol):
                if (width,height) != (self.the_width,self.the_height):
                    pil_image = pil_image.resize((self.the_width,self.the_height),Image.ANTIALIAS)
            else:
                valid_img = False ; print("# ERREUR : '{0}' est de taille {1}x{2}. Ce n'est pas un format {3}".format(in_string,width,height,self.WsurH))
            
            if valid_img: # Sauvegarde des informations
                batch_nb = least_key(self.dico_batches) # On remplit le batch ayant le moins d'images
                self.dico_batches[batch_nb] += 1
                
                if (self.upload_SQL.get() == 1):
                    conn = sqlite3.connect(path_to_data + database) ; cursor = conn.cursor()
                    img_file_name = "batch_"+str(batch_nb)+"/" + "0"*(6-len(str(self.next_img_id)))+str(self.next_img_id) + ".png"
                    img_data = (self.next_img_id,self.the_width,self.the_height,img_file_name,batch_nb,"NOTHING","NOTHING","NOTHING",False,False)
                    cursor.execute('''INSERT INTO Images VALUES (?,?,?,?,?,?,?,?,?,?)''',img_data)
                    f = open(path_to_images+history_file,'a')
                    for a_cat in the_litter_cat:
                        self.the_history.append([in_string,self.next_img_id,batch_nb,self.next_litt_id,a_cat])
                        f.write("\n"+in_string+"----"+str(self.next_img_id)+"----"+str(batch_nb)+"----"+str(self.next_litt_id)+"----"+a_cat)
                        trash_data = (self.next_litt_id,"NOTHING","NOTHING","NOTHING","NOTHING",self.next_img_id,self.cat_name_to_id[a_cat])
                        cursor.execute('''INSERT INTO Litter VALUES (?,?,?,?,?,?,?)''',trash_data)
                        self.next_litt_id += 1
                    f.close()
                    conn.commit() ; conn.close()
                    pil_image.save(path_to_data + img_file_name)
                    print("'{0}' enregistree avec image_id={1} dans '{2}' et '{3}'".format(in_string,self.next_img_id,history_file,database))
                    self.next_img_id+=1
                    
                else:
                    f = open(path_to_images+history_file,'a')
                    for a_cat in the_litter_cat:
                        self.the_history.append([in_string,self.next_img_id,batch_nb,self.next_litt_id,a_cat])
                        f.write("\n"+in_string+"----"+str(self.next_img_id)+"----"+str(batch_nb)+"----"+str(self.next_litt_id)+"----"+a_cat)
                        self.next_litt_id += 1
                    f.close()
                    print("'{0}' enregistree avec image_id={1} dans '{2}'".format(in_string,self.next_img_id,history_file))
                    self.next_img_id+=1
    
    def upload_folder(self):
        the_litter_cat = []
        for k in range(0,self.nb_max_litter):
            a_cat = self.list_choice_cat[k].get()
            if a_cat != " ":
                the_litter_cat.append(a_cat)

        if the_litter_cat != []: # Donnees rentrees valides
            folder_name = self.folder_name.get() + "/"
            in_strings = listdir(path_to_images + folder_name)
            valid_folder = True ; ind = 0
            while (ind < len(self.the_history)) and valid_folder:
                if self.the_history[ind][0] in in_strings:
                    valid_folder = False ; print("# ERREUR : '{0}' deja categorisee dans '{1}' avec image_id={2}".format(self.the_history[ind][0],history_file,self.the_history[ind][1]))
                ind += 1
            for in_string in in_strings:
                valid_img = True
                pil_image = Image.open(path_to_images + folder_name + in_string)
                (width,height) = pil_image.size
                if width>height:
                    pil_image = pil_image.rotate(90,expand=1) ; width,height=height,width
                if not( is_equal(float(width)/float(height),self.WsurH,self.resize_tol) or is_equal(float(width)/float(height),1.0,self.resize_tol) ): # format 4/3 ou carre
                    valid_img = False ; print("# ERREUR : '{0}' est de taille {1}x{2}. Ce n'est pas un format 1 ni {3}".format(in_string,width,height,self.WsurH))
                
                if valid_img: # Sauvegarde des informations
                    batch_nb = least_key(self.dico_batches) # On remplit le batch ayant le moins d'images
                    self.dico_batches[batch_nb] += 1
                    
                    if (self.upload_SQL.get() == 1):
                        conn = sqlite3.connect(path_to_data + database) ; cursor = conn.cursor()
                        img_file_name = "batch_"+str(batch_nb)+"/" + "0"*(6-len(str(self.next_img_id)))+str(self.next_img_id) + ".png"
                        img_data = (self.next_img_id,self.the_width,self.the_height,img_file_name,batch_nb,"NOTHING","NOTHING","NOTHING",False,False)
                        cursor.execute('''INSERT INTO Images VALUES (?,?,?,?,?,?,?,?,?,?)''',img_data)
                        f = open(path_to_images+history_file,'a')
                        for a_cat in the_litter_cat:
                            self.the_history.append([folder_name+in_string,self.next_img_id,batch_nb,self.next_litt_id,a_cat])
                            f.write("\n"+folder_name+in_string+"----"+str(self.next_img_id)+"----"+str(batch_nb)+"----"+str(self.next_litt_id)+"----"+a_cat)
                            trash_data = (self.next_litt_id,"NOTHING","NOTHING","NOTHING","NOTHING",self.next_img_id,self.cat_name_to_id[a_cat])
                            cursor.execute('''INSERT INTO Litter VALUES (?,?,?,?,?,?,?)''',trash_data)
                            self.next_litt_id += 1
                        f.close()
                        conn.commit() ; conn.close()
                        pil_image.save(path_to_data + img_file_name)
                        print("'{0}' --> image_id={1} --> '{2}' AND '{3}'".format(folder_name+in_string,self.next_img_id,history_file,database))
                        self.next_img_id+=1
                        
                    else:
                        f = open(path_to_images+history_file,'a')
                        for a_cat in the_litter_cat:
                            self.the_history.append([folder_name+in_string,self.next_img_id,batch_nb,self.next_litt_id,a_cat])
                            f.write("\n"+folder_name+in_string+"----"+str(self.next_img_id)+"----"+str(batch_nb)+"----"+str(self.next_litt_id)+"----"+a_cat)
                            self.next_litt_id += 1
                        f.close()
                        print("'{0}' --> image_id={1} --> '{2}'".format(folder_name+in_string,self.next_img_id,history_file))
                        self.next_img_id+=1


if __name__ == '__main__':
    New_Image_Window()
