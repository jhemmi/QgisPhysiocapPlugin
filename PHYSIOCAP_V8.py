#-*- coding: UTF-8 -*-
#"""
#Created 25/03/2014
#@author: Sebastien Debuisson 
#Modified 12/11/2014
#@author: Anne Belot & Manon Morlet
#Version 8.0
#"""

# ces bibliothèques sont livrées avec winpython
import shutil
import glob
import os
import csv
import sys
import os.path
import time

try :
    import numpy as np
    import matplotlib.pyplot as plt
except :
    print ("Numpy et matplotlib ne sont pas installees ! ")    
    print ("vous pouvez télécharger la suite winpython 3.3 qui contient ces bibliotheques http://winpython.sourceforge.net/")
    print ("sinon vous pouvez installer ces bibliothèques independamment")
    os.system("pause")
    sys.exit()

# Ces bibliothèques doivent être installée indépendamment de winpython http://www.lfd.uci.edu/~gohlke/pythonlibs/#gdal

try :
    from osgeo import osr
except :
    print ("GDAL n'est pas installé ! ")    
    print ("Installer GDAL/osgeo via http://www.lfd.uci.edu/~gohlke/pythonlibs/#gdal ")
    os.system("pause")
    sys.exit()
    
try :
    import shapefile as shp
except :
    print ("la library pyshp n'est pas installee : http://code.google.com/p/pyshp/")
    os.system("pause")
    sys.exit()

#####################################################################################################################
##Definition des fonctions de traitement
#Fonction de traitement. Creation des fichiers pour réaliser les histogrammes
#Lit et traite ligne par ligne le fichier source (src).
#Le résultat est écrit au fur et à mesure dans le
#fichier destination (dst). 

#CONSTANTE :
nb_virg=58

# Fonction pour créer les fichiers histogrammes

def fichierhisto(src, diamet, nbsarment, err):
    
    while True :
        ligne = src.readline() # lit les lignes 1 à 1
        if not ligne: break 
        comptage = ligne.count(",") # compte le nombre de virgules
        result = ligne.split(",") # split en fonction des virgules
        try : # accompli cette fonction si pas d'erreur sinon except
            XY = [float(x) for x in result[1:9]]   # on extrait les XY et on les transforme en float  > Données GPS 
            diams = [float(x) for x in result[9:nb_virg+1]] # on extrait les diams et on les transforme en float 
            diamsF = [i for i in diams if i > 2 and i < 28 ] # on filtre les diams > diamsF correspond aux diams filtrés entre 2 et 28       
            if comptage==nb_virg and len(diamsF)>0 : # si le nombre de diamètre après filtrage != 0 alors mesures
                nbsarm = len(diamsF)/(XY[7]*1000/3600) #8eme donnée du GPS est la vitesse. Dernier terme : distance entre les sarments
                nbsarment.write("%f%s" %(nbsarm,";"))                
                for n in range(len(diamsF)) :
                    diamet.write("%f%s" %(diamsF[n],";"))
        except : # accompli cette fonction si erreur
                        
            err.write("%s%s\n" %("erreur histo",ligne)) # on écrit la ligne dans le fichier ERREUR.csv
#            print (ligne)
#            err.write("erreur %s\n" %(ligne)) # on écrit la ligne dans le fichier ERREUR.csv 
            pass # A DEFINIR


# création de la fonction de traitement des données

def filtrer(src, dst, err, dst0, diamet2):
    #"""Fonction de traitement.
    #Lit et traite ligne par ligne le fichier source (src).
    #Le résultat est écrit au fur et à mesure dans le
    #fichier destination (dst). 
    #"""
    #S'il n'existe pas de données parcellaire, le script travaille avec les données brutes
    if parcellaire == "n" :
        dst.write("%s\n" % ("X ; Y ; XL93 ; YL93 ; NBSARM ; DIAM ; BIOM ; Date ; Vitesse")) # ecriture de l'entête
        dst0.write("%s\n" % ("X ; Y ; XL93 ; YL93 ; NBSARM ; DIAM ; BIOM ; Date ; Vitesse")) # ecriture de l'entête
    #S'il existe des données parcellaire, le script travaille avec les données brutes et les données calculées
    elif parcellaire == "y" :
        dst.write("%s\n" % ("X ; Y ; XL93 ; YL93 ; NBSARM ; DIAM ; BIOM ; Date ; Vitesse ; NBSARMM2 ; NBSARCEP ; BIOMMM2 ; BIOMGM2 ; BIOMGCEP ")) # ecriture de l'entête
        dst0.write("%s\n" % ("X ; Y ; XL93 ; YL93 ; NBSARM ; DIAM ; BIOM ; Date ; Vitesse ; NBSARMM2 ; NBSARCEP ; BIOMMM2 ; BIOMGM2 ; BIOMGCEP ")) # ecriture de l'entête
    mindiam = input("\nEntrer diam min en mm : ")
    mindiam = float(mindiam)
    maxdiam = input("Entrer diam max en mm : ")
    maxdiam = float(maxdiam)
    while maxdiam <= mindiam or maxdiam > 28:
        print ("Diam MAX <= Diam MIN ou Diam MAX > 28 mm : ERREUR !")
        mindiam = input("\nEntrer diam min en mm : ")
        mindiam = float(mindiam)
        maxdiam = input("Entrer diam max en mm : ")
        maxdiam = float(maxdiam)
    #On écrit dans le fichiers résultats les paramètres du modéle
    fichierfinal = open("%s/%s_resultat.txt" %(nom,nom), "a")
    fichierfinal.write("Diamètre minimal : %s mm\n" %mindiam)
    fichierfinal.write("Diamètre maximal : %s mm\n" %maxdiam)
    fichierfinal.close()
    while True :
        ligne = src.readline()
        if not ligne: break 
        comptage = ligne.count(",") # compte le nombre de virgules
        result = ligne.split(",") # split en fonction des virgules
        try : # accompli cette fonction si pas d'erreur sinon except
            XY = [float(x) for x in result[1:9]]   # on extrait les XY et on les transforme en float  
            # On transforme les WGS84 en L93
            WGS84 = osr.SpatialReference()
            WGS84.ImportFromEPSG(4326)
            LAMB93 = osr.SpatialReference()
            LAMB93.ImportFromEPSG(2154)
            transformation1 = osr.CoordinateTransformation(WGS84,LAMB93) 
            L93 = transformation1.TransformPoint(XY[0],XY[1])
            diams = [float(x) for x in result[9:nb_virg+1]] # on extrait les diams et on les transforme en float 
            diamsF = [i for i in diams if i > mindiam and i < maxdiam ] # on filtre les diams avec les paramètres entrés ci-dessus
            if parcellaire == "n" :
                #if comptage==7 : # si le nombre de virgule = 7 alors pas de mesures
                 #   nbsarm = 0
                  #  diam =0
                   # biom = 0
                   # dst0.write("%.7f%s%.7f%s%.7f%s%.7f%s%i%s%i%s%i%s%s%s%0.2f\n" %(XY[1],";",XY[2],";",L93[0],";",L93[1],";",nbsarm,";",diam ,";",biom,";",result[0],";",XY[0])) # on écrit la ligne dans le fichier OUT0.csv 
                if len(diamsF)==0: # si le nombre de diamètre après filtrage = 0 alors pas de mesures
                    nbsarm = 0
                    diam =0
                    biom = 0
                    dst0.write("%.7f%s%.7f%s%.7f%s%.7f%s%i%s%i%s%i%s%s%s%0.2f\n" %(XY[0],";",XY[1],";",L93[0],";",L93[1],";",nbsarm,";",diam ,";",biom,";",result[0],";",XY[7]))  # on écrit la ligne dans le fichier OUT0.csv  
                elif comptage==nb_virg and len(diamsF)>0 : # si le nombre de diamètre après filtrage != 0 alors mesures
                    nbsarm = len(diamsF)/(XY[7]*1000/3600)
                    if nbsarm > 1 and nbsarm < nbsarments and parcellaire == "n" :                   
                        diam =sum(diamsF)/len(diamsF)
                        biom=3.1416*(diam/2)*(diam/2)*nbsarm
                        dst0.write("%.7f%s%.7f%s%.7f%s%.7f%s%0.2f%s%.2f%s%.2f%s%s%s%0.2f\n" %(XY[0],";",XY[1],";",L93[0],";",L93[1],";",nbsarm,";",diam,";",biom,";",result[0],";",XY[7])) # on écrit la ligne dans le fichier OUT0.csv 
                        dst.write("%.7f%s%.7f%s%.7f%s%.7f%s%0.2f%s%.2f%s%.2f%s%s%s%0.2f\n" %(XY[0],";",XY[1],";",L93[0],";",L93[1],";",nbsarm,";",diam,";",biom,";",result[0],";",XY[7])) # on écrit la ligne dans le fichier OUT.csv
                        for n in range(len(diamsF)) :
                            diamet2.write("%f%s" %(diamsF[n],";"))
            elif parcellaire == "y" :
                #if comptage==7 : # si le nombre de virgule = 7 alors pas de mesures
                 #   nbsarm = 0
                 #   diam =0
                  #  biom = 0
                  #  nbsarmm2 = 0
                 #   nbsarcep = 0
                 #   biommm2 = 0
                  #  biomgm2 = 0
                 #   biomgcep = 0
                  #  dst0.write("%.7f%s%.7f%s%.7f%s%.7f%s%i%s%i%s%i%s%s%s%0.2f%s%i%s%i%s%i%s%i%s%i\n" %(XY[1],";",XY[2],";",L93[0],";",L93[1],";",nbsarm,";",diam ,";",biom,";",result[0],";",XY[0],";",nbsarmm2,";",nbsarcep,";",biommm2,";",biomgm2,";",biomgcep)) # on écrit la ligne dans le fichier OUT0.csv 
                if len(diamsF)==0: # si le nombre de diamètre après filtrage = 0 alors pas de mesures
                    nbsarm = 0
                    diam =0
                    biom = 0
                    nbsarmm2 = 0
                    nbsarcep = 0
                    biommm2 = 0
                    biomgm2 = 0
                    biomgcep = 0
                    dst0.write("%.7f%s%.7f%s%.7f%s%.7f%s%i%s%i%s%i%s%s%s%0.2f%s%i%s%i%s%i%s%i%s%i\n" %(XY[0],";",XY[1],";",L93[0],";",L93[1],";",nbsarm,";",diam ,";",biom,";",result[0],";",XY[7],";",nbsarmm2,";",nbsarcep,";",biommm2,";",biomgm2,";",biomgcep))  # on écrit la ligne dans le fichier OUT0.csv  
                elif comptage==nb_virg and len(diamsF)>0 : # si le nombre de diamètre après filtrage != 0 alors mesures
                    nbsarm = len(diamsF)/(XY[7]*1000/3600)
                    if nbsarm > 1 and nbsarm < nbsarments :                   
                        diam =sum(diamsF)/len(diamsF)
                        biom=3.1416*(diam/2)*(diam/2)*nbsarm
                        nbsarmm2 = nbsarm/eer*100
                        nbsarcep = nbsarm*eec/100
                        biommm2 = biom/eer*100
                        biomgm2 = biom*d*hv/eer
                        biomgcep = biom*d*hv*eec/100/100
                        dst0.write("%.7f%s%.7f%s%.7f%s%.7f%s%.2f%s%.2f%s%.2f%s%s%s%.2f%s%.2f%s%.2f%s%.2f%s%.2f%s%.2f\n" %(XY[0],";",XY[1],";",L93[0],";",L93[1],";",nbsarm,";",diam ,";",biom,";",result[0],";",XY[7],";",nbsarmm2,";",nbsarcep,";",biommm2,";",biomgm2,";",biomgcep)) # on écrit la ligne dans le fichier OUT0.csv 
                        dst.write("%.7f%s%.7f%s%.7f%s%.7f%s%.2f%s%.2f%s%.2f%s%s%s%.2f%s%.2f%s%.2f%s%.2f%s%.2f%s%.2f\n" %(XY[0],";",XY[1],";",L93[0],";",L93[1],";",nbsarm,";",diam ,";",biom,";",result[0],";",XY[7],";",nbsarmm2,";",nbsarcep,";",biommm2,";",biomgm2,";",biomgcep)) # on écrit la ligne dans le fichier OUT.csv
                        for n in range(len(diamsF)) :
                            diamet2.write("%f%s" %(diamsF[n],";"))
        except : # accompli cette fonction si erreur
#            print ("Attention il y a des erreurs dans le fichier !")
#            print (ligne)
            err.write("%s%s\n" %("erreur filtrer",ligne)) # on écrit la ligne dans le fichier ERREUR.csv 
            pass # A DEFINIR

def histo(src):
    #"""Fonction de traitement.
    #Lit et traite ligne par ligne le fichier source (src).
    #Le résultat est écrit au fur et à mesure dans le
    #fichier destination (dst). 
    #"""
#    while True :
    ligne2 = src.readline()
#        if not ligne: break
#        comptage = ligne2.count(",") # compte le nombre de virgules
    histo = ligne2.split(";") # split en fonction des virgules
    XY = [float(x) for x in histo[0:-1]]   # on extrait les XY et on les transforme en float  
    valeur = len(XY)
    print (valeur)
    classes = np.linspace(min, max, bins)
    plt.hist(XY,bins=classes,normed=1, facecolor='green', alpha=0.75) 
    plt.xlabel(label1)
    plt.ylabel(label2)
    plt.title(titre)
    #plt.axis([-10000,3500000, 0, 20])
    plt.grid(True)
    plt.savefig(name)
    plt.show()


######################################################################################################################
print ("***********************************************************")
print ("** PSPY : PHYSIOCAP SCRIPT PYTHON VERSION 8.0 10/11/2014 **")
print ("***********************************************************")
print ("\nCREE PAR LE POLE TECHNIQUE ET ENVIRONNEMENT DU CIVC")
print ("\n MODIFIE PAR LE CIVC ET L'EQUIPE VIGNOBLE DE MOËT & CHANDON")
print ("AUTEUR : SEBASTIEN DEBUISSON, MODIFIE PAR ANNE BELOT ET MANON MORLET")
print ("PSPY est mis à disposition selon les termes de la licence Creative Commons")
print ("CC-BY-NC-SA -> http://creativecommons.org/licenses/by-nc-sa/4.0/\n")


nom = str(input("Donnez un nom au projet : "))
interdit ="//:*?<>|.'"
for i in interdit :
    while i in nom :
        print("Erreur, caractères nom compatibles avec la création d'un dossier (//:*?<>|.')")
        nom = str(input("Donnez un nom au projet : "))

print ("\nconcatenation des fichiers => %s_RAW.csv\n" %nom)


#############################################
# JH Copier dans creer_donnees_resultats 
#############################################

try :
    os.mkdir("%s" %nom)
except FileExistsError as exception_retournee :
        print("Attention ERREUR : " , exception_retournee ,"\n")
try :
    os.mkdir("%s/fichiers_sources" %nom)
except FileExistsError as exception_retournee:
    print("Voici l'erreur :", exception_retournee, "\n")

fichier_concat = open("%s/fichiers_sources/%s_RAW.csv" %(nom,nom), "w")

# création de la fonction de concaténation
reponse = str()
while reponse !="y" and reponse !="n" :
    reponse = str(input("Voulez-vous changer l'extension *.MID [y/n] : "))
    if reponse == str("n") :
        for i in glob.glob("*.MID"):
            shutil.copyfileobj(open(i, "r"), fichier_concat)
            shutil.copy(i,"%s/fichiers_sources" %nom)
    elif reponse == "y" :
        Typefichier = input("Nouvelle extension (ex : *.TXT ; NAME.EXT...) : ")
        for i in glob.glob(Typefichier):
            shutil.copyfileobj(open(i, "r"), fichier_concat)
            shutil.copy(i,"%s/fichiers_sources" %nom)
fichier_concat.close()
print ("\nCompte rendu : ", fichier_concat, "\n") 


#creation du fichier de synthèse
fichierfinal = open("%s/%s_resultat.txt" %(nom,nom), "w")
fichierfinal.write("SYNTHESE PHYSIOCAP\n\n")
fichierfinal.write("Fichier généré le : ")
time = time.strftime("%d/%m/%y %H:%M",time.localtime())
fichierfinal.write(time)
fichierfinal.write("\nPARAMETRES SAISIS ")
#############################################
# JH FIN Copier dans creer_donnees_resultats 
#############################################
parcellaire = str()
while parcellaire !="y" and parcellaire !="n" :
    parcellaire = str(input("Voulez-vous ajouter des informations parcellaires [y/n] : "))
    if parcellaire == str("y") :
        cepage = str(input("Entrer le cépage : "))
        fichierfinal.write("\nCépage : %s\n" %cepage)
        taille = str(input("Entrer le type de taille : "))
        fichierfinal.write("Type de taille : %s\n" %taille)        
        try :        
            hv=int(input("Entrer la hauteur de végétation en cm : "))    
        except :
            print("Vous devez rentrer un nombre entier")
            hv=int(input("Entrer la hauteur de végétation en cm : "))
        fichierfinal.write("Hauteur de végétation : %s cm\n" %hv)
        try :
            d = float(input("Entrer la densité des bois (ex : 0.9) : "))
        except :
            print("Vous devez rentrer un nombre")
            d = float(input("Entrer la densité des bois (ex : 0.9) : "))
        fichierfinal.write("Densité des bois de taille : %s \n" %d)
        try :
            eer = int(input("Entrer l'ecartement entre rangs en cm : "))
        except :
            print("Vous devez rentrer un nombre entier")
            eer = int(input("Entrer l'ecartement entre rangs en cm : "))
        fichierfinal.write("Ecartement entre rangs : %s cm\n" %eer)
        try :
            eec = int(input("Entrer l'ecartement entre ceps en cm : "))
        except :
            print("Vous devez rentrer un nombre entier")
            eec = int(input("Entrer l'ecartement entre ceps en cm : "))
        fichierfinal.write("Ecartement entre ceps : %s cm\n" %eec)
    if parcellaire == str("n") :
        fichierfinal.write("\nAucune information parcellaire saisie\n")
fichierfinal.close()

        
print ("\nCreation du fichier brut diametre => diam_RAW.csv")
print ("Creation du fichier brut nombre de sarments => nbsarm_RAW.csv")
print ("Creation du fichier d'erreurs => erreurs.csv")
#############################################
# JH Copier 2 dans creer_donnees_resultats
#############################################

if os.path.getsize("%s/fichiers_sources/%s_RAW.csv" %(nom,nom))==0 :
    print ("le fichier %sRAW.csv a une taille nulle, il y a un probleme ! \n" %nom)
    os.system("pause")
    sys.exit()  
elif os.path.getsize("%s/fichiers_sources/%s_RAW.csv" %(nom,nom))!=0 :
    #création du répertoire texte
    try :
        os.mkdir("%s/fichiers_texte" %nom)
    except FileExistsError as exception_retournee :
        print("Attention ERREUR : " , exception_retournee ,"\n")
    # ouverture du fichier source
    source = open("%s/fichiers_sources/%s_RAW.csv" %(nom,nom), "r") 
    # Ouverture du fichier destination
    destination = open("%s/fichiers_texte/diam_RAW.csv" %nom, "w")
    destination5 = open("%s/fichiers_texte/nbsarm_RAW.csv" %nom, "w")
    erreur = open("%s/fichiers_texte/erreurs.csv" %nom,"w")
    # Appeler la fonction de traitement
    fichierhisto(source,destination,destination5,erreur)
    # Fermerture du fichier source
    source.close()
    destination.close()
    destination5.close()
    erreur.close()
    
#############################################
# FIN JH Copier 2 dans creer_donnees_resultats
#############################################

print ("\nCreation de l'histogramme NBSARM AVANT filtration")
# Ouverture du fichier source
source = open("%s/fichiers_texte/nbsarm_RAW.csv" %nom, "r")
# Appeler la fonction de traitement
min = 0
max = 100
bins = input("Nombre de colonnes (suggéré 100) : ")
label1 = "SARMENT au m"
label2 = "FREQUENCE en %"
titre = "HISTOGRAMME NBSARM AVANT TRAITEMENT"
try : 
    os.mkdir("%s/histogrammes" %nom)
except FileExistsError as exception_retournee:
    print("Voici l'erreur :", exception_retournee, "\n")
name = ("%s/histogrammes/histogramme_NBSARM_RAW.png" %nom)
print ("\nChoissisez la valeur MAX à filtrer sur le graphique")
print ("Fermer le graphique pour continuer le script")
print ("le nombre de sarments AVANT filtration est de : ")
histo(source)
# Fermerture du fichier source
source.close()
nbsarments = input("\nEntrer le nombre de sarments max au m : ")
nbsarments = float(nbsarments)
#on écrit les paramètres dans le fichier résulat
fichierfinal = open("%s/%s_resultat.txt" %(nom,nom), "a")
fichierfinal.write("Nombre de sarments max au mètre linéaire : %s \n" %nbsarments)
fichierfinal.close()

print ("\nCreation de l'histogramme DIAM AVANT filtration")
print ("Entrez le nombre de colonnes, choissisez les valeurs à filtrer sur le graphique")
# Ouverture du fichier source
source = open("%s/fichiers_texte/diam_RAW.csv" %nom, "r")
# Appeler la fonction de traitement
min = 0
max = 28
bins = input("Nombre de colonnes (suggere 100) : ")
label1 = "DIAMETRE en mm"
label2 = "FREQUENCE en %"
titre = "HISTOGRAMME DIAMETRE AVANT TRAITEMENT"
name = ("%s/histogrammes/histogramme_DIAM_RAW.png" %nom)
print ("Fermer le graphique pour continuer le script")
print ("le nombre de diametres AVANT filtration est de : ")
histo(source)
# Fermerture du fichier source
source.close()
# en pause pour éviter qu'il ne se referme (Windows)

#############################################
# JH Copier 3 dans creer_donnees_resultats
############################################## On met le programme 

# ouverture du fichier source
source = open("%s/fichiers_sources/%s_RAW.csv" %(nom,nom), "r")

# Ouverture du fichier destination
destination1 = open("%s/fichiers_texte/%s_OUT.csv" %(nom,nom), "w")
destination0 = open("%s/fichiers_texte/%s_OUT0.csv" %(nom,nom), "w")
diamet2=open("%s/fichiers_texte/diam_FILTERED.csv" %nom, "w")
erreur = open("%s/fichiers_texte/erreurs.csv" %nom, "a")

# Appeler la fonction de traitement
filtrer(source, destination1, erreur, destination0, diamet2)

# Fermeture du fichier destination
destination1.close()
destination0.close()
diamet2.close()
erreur.close()

# Fermerture du fichier source
source.close()
print ("\nCreation des fichiers => %s_OUT.csv, %s_OUT0.csv, diam_FILTERED.csv et erreurs.csv" %(nom,nom))
print ("\nCreation de l'histogramme APRES filtration")
#############################################
# FIN JH Copier 3 dans creer_donnees_resultats
############################################## On met le programme 


# Ouverture du fichier source
source = open("%s/fichiers_texte/diam_FILTERED.csv" %nom, "r")
# Appeler la fonction de traitement
print ("la valeur bins (colonnes) = {0}".format(bins))
titre = "HISTOGRAMME DIAMETRE APRES TRAITEMENT"
name = ("%s/histogrammes/histogramme_DIAM_FILTERED.png" %nom)
print ("Fermer le graphique pour continuer le script")
print ("le nombre de diametres APRES filtration est de : ")
histo(source)
print("\n")
# Fermerture du fichier source
source.close()

try :
    os.mkdir("%s/shapefile" %nom)
except FileExistsError as exception_retournee:
    print("Voici l'erreur :", exception_retournee, "\n")

# Création du shapefile
#print ("\nCreation du shapefile avec 0 en WGS84 => %s_0_WGS84.shp" %nom)
#ecriture du fichier shp avec les 0
#out_file = ("%s/shapefile/%s_0_WGS84.shp" %(nom,nom))
#Préparation de la liste d'arguments
#x,y,nbsarmshp,diamshp,biomshp,dateshp,vitesseshp=[],[],[],[],[],[],[]
##Lecture des data dans le csv et stockage dans une liste
#with open("%s/fichiers_texte/%s_OUT0.csv" %(nom,nom), "rt") as csvfile:
#    r = csv.reader(csvfile, delimiter=";")
#    for i,row in enumerate(r):
#        if i > 0: #skip header
#            x.append(float(row[0]))
#            y.append(float(row[1]))
#            nbsarmshp.append(row[4])
#            diamshp.append(row[5])
#            biomshp.append(row[6])
#            dateshp.append(str(row[7]))
#            vitesseshp.append(float(row[8]))          
## Création du shap et des champs vides
#w = shp.Writer(shp.POINT)
#w.autoBalance = 1 #vérifie la geom
#w.field('DATE','S',20)
#w.field('VITESSE','F',10,2)
#w.field('NBSARM','F',10,2)
#w.field('DIAM','F',10,2)
#w.field('BIOM','F',10,2)
##Ecriture du shp
#for j,k in enumerate(x):
#    w.point(k,y[j]) #écrit la géométrie
#    w.record(dateshp[j],vitesseshp[j],nbsarmshp[j], diamshp[j], biomshp[j]) #écrit les attributs
##Save shapefile
#w.save(out_file)
## creation du fichier PRJ WG84
#prj = open("%s/shapefile/%s_0_WGS84.prj" %(nom,nom), "w")
#epsg = 'GEOGCS["WGS 84",DATUM["WGS_1984",SPHEROID["WGS 84",6378137,298.257223563]],PRIMEM["Greenwich",0],UNIT["degree",0.0174532925199433]]'
#prj.write(epsg)
#prj.close()

#Préparation de la liste d'arguments
#x,y,nbsarmshp,diamshp,biomshp,dateshp,vitesseshp=[],[],[],[],[],[],[]   
##ecriture du fichier shp sans les 0    
#print ("Creation du shapefile sans 0 en WGS84 => %s_WGS84.shp" %nom)
#out_file = ("%s/shapefile/%s_WGS84.shp" %(nom,nom))
##Lecture des data dans le csv et stockage dans une liste
#with open("%s/fichiers_texte/%s_OUT.csv" %(nom,nom), "rt") as csvfile:
#    r = csv.reader(csvfile, delimiter=";")
#    for i,row in enumerate(r):
#        if i > 0: #skip header
#            x.append(float(row[0]))
#            y.append(float(row[1]))
#            nbsarmshp.append(row[4])
#            diamshp.append(row[5])
#            biomshp.append(row[6])
#            dateshp.append(str(row[7]))
#            vitesseshp.append(float(row[8]))
## Création du shape et des champs vides
#w = shp.Writer(shp.POINT)
#w.autoBalance = 1 #vérifie la geom
#w.field('DATE','S',20)
#w.field('VITESSE','F',10,2)
#w.field('NBSARM','F',10,2)
#w.field('DIAM','F',10,2)
#w.field('BIOM','F',10,2)
##Ecriture du shp
#for j,k in enumerate(x):
#    w.point(k,y[j]) #écrit la géométrie
#    w.record(dateshp[j],vitesseshp[j],nbsarmshp[j], diamshp[j], biomshp[j]) #écrit les attributs   
##Save shapefile
#w.save(out_file)
## Creation du PRJ L93
#prj = open("%s/shapefile/%s_WGS84.prj" %(nom,nom), "w")
#epsg = 'GEOGCS["WGS 84",DATUM["WGS_1984",SPHEROID["WGS 84",6378137,298.257223563]],PRIMEM["Greenwich",0],UNIT["degree",0.0174532925199433]]'
#prj.write(epsg)
#prj.close()

if parcellaire == "n" :
    #Préparation de la liste d'arguments
    x,y,nbsarmshp,diamshp,biomshp,dateshp,vitesseshp=[],[],[],[],[],[],[]
    
    #ecriture du fichier shp avec les 0    
    print ("\nCréation du shapefile avec 0 en L93 => %s_0_L93.shp" %nom)
    
    
    out_file = ("%s/shapefile/%s_0_L93.shp" %(nom,nom))
    
    #Lecture des data dans le csv et stockage dans une liste
    with open("%s/fichiers_texte/%s_OUT0.csv" %(nom,nom), "rt") as csvfile:
        r = csv.reader(csvfile, delimiter=";")
        for i,row in enumerate(r):
            if i > 0: #skip header
                x.append(float(row[2]))
                y.append(float(row[3]))
                nbsarmshp.append(row[4])
                diamshp.append(row[5])
                biomshp.append(row[6])
                dateshp.append(str(row[7]))
                vitesseshp.append(float(row[8]))
    
    # Création du shap et des champs vides
    w = shp.Writer(shp.POINT)
    w.autoBalance = 1 #vérifie la geom
    w.field('DATE','S',25)
    w.field('VITESSE','F',10,2)
    w.field('NBSARM','F',10,2)
    w.field('DIAM','F',10,2)
    w.field('BIOM','F',10,2)
    
    #Ecriture du shp
    for j,k in enumerate(x):
        w.point(k,y[j]) #écrit la géométrie
        w.record(dateshp[j],vitesseshp[j],nbsarmshp[j], diamshp[j], biomshp[j]) #écrit les attributs
    
    #Save shapefile
    w.save(out_file)
          
    #ecriture du fichier shp sans les 0    
    
    print ("Creation du shapefile sans 0 en L93 => %s_L93.shp" %nom)
    out_file = ("%s/shapefile/%s_L93.shp" %(nom,nom)) 
    
    #Préparation de la liste d'arguments
    x,y,nbsarmshp,diamshp,biomshp,dateshp,vitesseshp=[],[],[],[],[],[],[]
    
    #Lecture des data dans le csv et stockage dans une liste
    with open("%s/fichiers_texte/%s_OUT.csv" %(nom,nom), "rt") as csvfile:
        r = csv.reader(csvfile, delimiter=";")
        for i,row in enumerate(r):
            if i > 0: #skip header
                x.append(float(row[2]))
                y.append(float(row[3]))
                nbsarmshp.append(row[4])
                diamshp.append(row[5])
                biomshp.append(row[6])
                dateshp.append(str(row[7]))
                vitesseshp.append(float(row[8]))
    
    # Création du shap et des champs vides
    w = shp.Writer(shp.POINT)
    w.autoBalance = 1 #vérifie la geom
    w.field('DATE','S',25)
    w.field('VITESSE','F',10,2)
    w.field('NBSARM','F',10,2)
    w.field('DIAM','F',10,2)
    w.field('BIOM','F',10,2)
    
    #Ecriture du shp
    for j,k in enumerate(x):
        w.point(k,y[j]) #écrit la géométrie
        w.record(dateshp[j],vitesseshp[j],nbsarmshp[j], diamshp[j], biomshp[j]) #écrit les attributs
    
    #Save shapefile
    w.save(out_file)
    
elif parcellaire =="y" :
        #Préparation de la liste d'arguments
    x,y,nbsarmshp,diamshp,biomshp,dateshp,vitesseshp,nbsarmm2,nbsarcep,biommm2,biomgm2,biomgcep=[],[],[],[],[],[],[],[],[],[],[],[]
  
    #ecriture du fichier shp avec les 0    
    print ("Creation du shapefile avec 0 en L93 => %s_0_L93.shp" %nom)
    
    
    out_file = ("%s/shapefile/%s_0_L93.shp" %(nom,nom))
    
    #Lecture des data dans le csv et stockage dans une liste
    with open("%s/fichiers_texte/%s_OUT0.csv" %(nom,nom), "rt") as csvfile:
        r = csv.reader(csvfile, delimiter=";")
        for i,row in enumerate(r):
            if i > 0: #skip header
                x.append(float(row[2]))
                y.append(float(row[3]))
                nbsarmshp.append(row[4])
                diamshp.append(row[5])
                biomshp.append(row[6])
                dateshp.append(str(row[7]))
                vitesseshp.append(float(row[8]))
                nbsarmm2.append(float(row[9]))
                nbsarcep.append(float(row[10]))
                biommm2.append(float(row[11]))
                biomgm2.append(float(row[12]))
                biomgcep.append(float(row[13]))
                
    # Création du shap et des champs vides
    w = shp.Writer(shp.POINT)
    w.autoBalance = 1 #vérifie la geom
    w.field('DATE','S',25)
    w.field('VITESSE','F',10,2)
    w.field('NBSARM','F',10,2)
    w.field('DIAM','F',10,2)
    w.field('BIOM','F',10,2)
    w.field('NBSARMM2','F',10,2)
    w.field('NBSARCEP','F',10,2)
    w.field('BIOMM2','F',10,2)
    w.field('BIOMGM2','F',10,2)
    w.field('BIOMGCEP','F',10,2)
    
    #Ecriture du shp
    for j,k in enumerate(x):
        w.point(k,y[j]) #écrit la géométrie
        w.record(dateshp[j],vitesseshp[j],nbsarmshp[j], diamshp[j], biomshp[j], nbsarmm2[j], nbsarcep[j], biommm2[j], biomgm2[j], biomgcep[j]) #écrit les attributs
    
    #Save shapefile
    w.save(out_file)
          
    #ecriture du fichier shp sans les 0    
    
    print ("Creation du shapefile sans 0 en L93 => %s_L93.shp" %nom)
    out_file = ("%s/shapefile/%s_L93.shp" %(nom,nom)) 
    
    #Préparation de la liste d'arguments
    x,y,nbsarmshp,diamshp,biomshp,dateshp,vitesseshp,nbsarmm2,nbsarcep,biommm2,biomgm2,biomgcep=[],[],[],[],[],[],[],[],[],[],[],[]
    
    #Lecture des data dans le csv et stockage dans une liste
    with open("%s/fichiers_texte/%s_OUT.csv" %(nom,nom), "rt") as csvfile:
        r = csv.reader(csvfile, delimiter=";")
        for i,row in enumerate(r):
            if i > 0: #skip header
                x.append(float(row[2]))
                y.append(float(row[3]))
                nbsarmshp.append(row[4])
                diamshp.append(row[5])
                biomshp.append(row[6])
                dateshp.append(str(row[7]))
                vitesseshp.append(float(row[8]))
                nbsarmm2.append(float(row[9]))
                nbsarcep.append(float(row[10]))
                biommm2.append(float(row[11]))
                biomgm2.append(float(row[12]))
                biomgcep.append(float(row[13]))
                
    # Création du shap et des champs vides
    w = shp.Writer(shp.POINT)
    w.autoBalance = 1 #vérifie la geom
    w.field('DATE','S',25)
    w.field('VITESSE','F',10,2)
    w.field('NBSARM','F',10,2)
    w.field('DIAM','F',10,2)
    w.field('BIOM','F',10,2)
    w.field('NBSARMM2','F',10,2)
    w.field('NBSARCEP','F',10,2)
    w.field('BIOMM2','F',10,2)
    w.field('BIOMGM2','F',10,2)
    w.field('BIOMGCEP','F',10,2)
    
    #Ecriture du shp
    for j,k in enumerate(x):
        w.point(k,y[j]) #écrit la géométrie
        w.record(dateshp[j],vitesseshp[j],nbsarmshp[j], diamshp[j], biomshp[j], nbsarmm2[j], nbsarcep[j], biommm2[j], biomgm2[j], biomgcep[j]) #écrit les attributs
    
    #Save shapefile
    w.save(out_file)

# create the PRJ file
prj = open("%s/shapefile/%s_0_L93.prj" %(nom,nom), "w")
epsg = 'PROJCS["RGF93_Lambert_93",GEOGCS["GCS_RGF93",DATUM["D_RGF_1993",SPHEROID["GRS_1980",6378137,298.257222101]],PRIMEM["Greenwich",0],UNIT["Degree",0.017453292519943295]],PROJECTION["Lambert_Conformal_Conic"],PARAMETER["standard_parallel_1",49],PARAMETER["standard_parallel_2",44],PARAMETER["latitude_of_origin",46.5],PARAMETER["central_meridian",3],PARAMETER["false_easting",700000],PARAMETER["false_northing",6600000],UNIT["Meter",1]]'
prj.write(epsg)
prj.close()
prj = open("%s/shapefile/%s_L93.prj" %(nom,nom), "w")
epsg = 'PROJCS["RGF93_Lambert_93",GEOGCS["GCS_RGF93",DATUM["D_RGF_1993",SPHEROID["GRS_1980",6378137,298.257222101]],PRIMEM["Greenwich",0],UNIT["Degree",0.017453292519943295]],PROJECTION["Lambert_Conformal_Conic"],PARAMETER["standard_parallel_1",49],PARAMETER["standard_parallel_2",44],PARAMETER["latitude_of_origin",46.5],PARAMETER["central_meridian",3],PARAMETER["false_easting",700000],PARAMETER["false_northing",6600000],UNIT["Meter",1]]'
prj.write(epsg)
prj.close()

from pylab import *
import shapefile as shp
sf = shp.Reader("%s/shapefile/%s_L93.shp" %(nom,nom))
shapes = sf.shapes()
records = sf.records()
X=[]
Y=[]
diam=[]
biom=[]
nbsarm=[]
vitesse=[]
if parcellaire == "y" :
    NBSARMM2 = []
    NBSARCEP = []
    BIOMMM2 = []
    BIOMGM2 = []
    BIOMGCEP = []    

for i in range(len(records)):
    TX=shapes[i].points[0]
    TXf=float(TX[0])
    TYf=float(TX[1])
    X.append(TXf)
    Y.append(TYf)
    vitesse.append(float(records[i][1]))
    diam.append(float(records[i][3]))
    nbsarm.append(float(records[i][2]))  
    biom.append(float(records[i][4]))
    if parcellaire == "y" :
        NBSARMM2.append(float(records[i][5]))
        NBSARCEP.append(float(records[i][6]))
        BIOMMM2.append(float(records[i][7]))
        BIOMGM2.append(float(records[i][8]))
        BIOMGCEP.append(float(records[i][9]))

fichierfinal = open("%s/%s_resultat.txt" %(nom,nom), "a")
fichierfinal.write("\n\nSTATISTIQUES\n")
fichierfinal.write("vitesse moyenne d'avancement  \n	mean : %0.1f km/h\n" %np.mean(vitesse))
fichierfinal.write("Section moyenne \n	mean : %0.2f mm	std : %0.1f\n" %(np.mean(diam), np.std(diam)))
fichierfinal.write("Nombre de sarments au m \n	mean : %0.2f	std : %0.1f\n" %(np.mean(nbsarm), np.std(nbsarm)))
fichierfinal.write("Biomasse en mm²/m linéaire \n	mean : %0.1f	std : %0.1f\n" %(np.mean(biom), np.std(biom)))
if parcellaire == "y" :
    fichierfinal.write("Nombre de sarments au m² \n	mean : %0.1f	std : %0.1f\n" %(np.mean(NBSARMM2), np.std(NBSARMM2)))
    fichierfinal.write("Nombre de sarments par cep \n	mean : %0.1f	std : %0.1f\n" %(np.mean(NBSARCEP), np.std(NBSARCEP)))
    fichierfinal.write("Biommasse en mm²/m² \n	mean : %0.1f	std : %0.1f\n" %(np.mean(BIOMMM2), np.std(BIOMMM2)))
    fichierfinal.write("Biomasse en gramme/m² \n	mean : %0.1f	std : %0.1f\n" %(np.mean(BIOMGM2), np.std(BIOMGM2)))
    fichierfinal.write("Biomasse en gramme/cep \n	mean : %0.1f	std : %0.1f\n" %(np.mean(BIOMGCEP), np.std(BIOMGCEP))) 
fichierfinal.close()
#print (np.mean(biom))
title("Diamétre en mm")
scatter(X, Y, c=diam)   
plt.colorbar()
grid(True)
show()

efface =str()
while efface !="y" and efface !="n" :
    efface = str(input("\nEffacer les fichiers sources dans le repertoire de travail [y/n] ? : "))
    if efface == str("y") and reponse == "n" :
        for i in glob.glob("*.MID"):
            os.remove(i)  	
    elif efface == str("y") and reponse == "y" :
        for i in glob.glob(Typefichier):
            os.remove(i) 

if os.path.getsize("%s/fichiers_texte/erreurs.csv" %nom)==0 :
    print ("\n*********************************")
    print ("PARFAIT, il n'y a aucune erreur")
    print ("*********************************\n")
elif os.path.getsize("%s/fichiers_sources/%s_RAW.csv" %(nom,nom))!=0 :
    print ("\n*************************************************")
    print ("Il y a quelques erreurs : cf erreurs.csv")
    print ("**************************************************\n")
print ("\nFINI, TRAVAILLEZ BIEN SOUS QGIS !")
os.system("pause")
