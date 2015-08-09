# -*- coding: utf-8 -*-
"""
/***************************************************************************
 Physiocap_tools
                                 A QGIS plugin
 Physiocap plugin helps analysing raw data from Physiocap in Qgis
                              -------------------
        begin                : 2015-07-31
        git sha              : $Format:%H$
        email                : jean@jhemmi.eu
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 * Physiocap plugin créé par jhemmi.eu et CIVC est issu de :               *
 *- PSPY : PHYSIOCAP SCRIPT PYTHON VERSION 8.0 10/11/2014                  *
 *   CREE PAR LE POLE TECHNIQUE ET ENVIRONNEMENT DU CIVC                   *
 *   MODIFIE PAR LE CIVC ET L'EQUIPE VIGNOBLE DE MOËT & CHANDON            *
 *   AUTEUR : SEBASTIEN DEBUISSON, MODIFIE PAR ANNE BELOT ET MANON MORLET  *
 *   Physiocap plugin comme PSPY sont mis à disposition selon les termes   *
 *   de la licence Creative Commons                                        *
 *   CC-BY-NC-SA http://creativecommons.org/licenses/by-nc-sa/4.0/         *
 *- Plugin builder et Qgis API et à ce titre porte aussi la licence GNU    *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *   http://www.gnu.org/licenses/gpl-2.0.html                              *
 *                                                                         *
***************************************************************************/
"""
from PyQt4 import QtGui, uic  # for Form_class
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import *
from qgis.gui import *

import csv

# Import system & os
import os.path
import sys, string
import platform
if platform.system() == 'Windows':
    import win32api

try :
    from osgeo import osr
except :
    physiocap_log(u"GDAL n'est pas accessible ! ")    
    physiocap_log(u"Installer GDAL/osgeo via http://www.lfd.uci.edu/~gohlke/pythonlibs/#gdal ")

try :
    import numpy as np
    #import matplotlib.pyplot as plt
except :
    physiocap_log(u"Numpy n'est pas installees ! ")    
    physiocap_log(u"vous pouvez télécharger la suite winpython 3.3 qui contient ces bibliotheques http://winpython.sourceforge.net/")
    physiocap_log(u"sinon vous pouvez installer ces bibliothèques independamment")

try :
    import shapefile as shp
except :
    physiocap_log(u"Shapefile n'est pas accessible ! ")    
    physiocap_log(u"la library shapefile n'est pas installee : http://code.google.com/p/pyshp ")

# GLOBAL VARIABLES GLOBALE
PHYSIOCAP_TRACE = "Yes"
NB_VIRGULES = 58

# MESSAGES & LOG
def physiocap_message_box( self, text, level ="warning", title="Physiocap",):
    """Send a message box by default Warning"""
    if level == "about":
        QMessageBox.about( self, title, text)
    elif level == "information":
        QMessageBox.information( self, title, text)
    elif level == "error":
        QMessageBox.error( self, title, text)
    else:
        QMessageBox.warning( self, title, text)

def physiocap_log( aText, level ="WARNING"):
    """Send a text to the Physiocap log"""
    if PHYSIOCAP_TRACE == "Yes":
        QgsMessageLog.logMessage( aText, "Physiocap informations", QgsMessageLog.WARNING)
            
def physiocap_error( aText, level ="WARNING"):
    """Send a text to the Physiocap error"""
    QgsMessageLog.logMessage( aText, "Physiocap erreurs", QgsMessageLog.WARNING)      

def physiocap_write_in_list( self, aText):
    """Write a text in the results list"""
    if platform.system() == "Windows":
        info = aText.split( "\r\n" )        
    else:
        info = aText.split( "\n" )
    for aInfo in info:
        self.textEdit.insertPlainText( aInfo + "\n")   

def get_vector_layers( self ):
    """Create a list of vector """
    layerMap = QgsMapLayerRegistry.instance().mapLayers()
    layerList = []
    for name, layer in layerMap.iteritems():
        if layer.type() == QgsMapLayer.VectorLayer:
            layerList.append( layer.name() )
            
    return layerList
            
        
def get_layer_by_name( self, layerName ):
    layerMap = QgsMapLayerRegistry.instance().mapLayers()
    for name, layer in layerMap.iteritems():
        if layer.type() == QgsMapLayer.VectorLayer and layer.name() == layerName:
            # The layer is found
            break
    if layer.isValid():
        return layer
    else:
        return none
    
def physiocap_open_file( nom_court, chemin, libelle):
    """ Créer ou detruite et crée un fichier"""
    # Fichier des diamètres     
    nom_fichier = os.path.join(chemin, nom_courte)
    if os.path.isfile( nom_fichier_diametre):
        physiocap_log(u"Destruction du fichier préexistant :" + nom_court) 
        os.remove( nom_fichier)
    try :
        fichier_pret = open(nom_fichier, "w")
    except :
        physiocap_error("Problème lors de la création du fichier " + 
        libelle + ": " + 
        nom_court)
    return fichier_pret

# Partie Calcul non modifié
# Definition des fonctions de traitement
# Ces variables sont nommées en Francais par compatibilité avec la version physiocap_V8

def physiocap_shapefile(shape_name, prj_name, csv_name, \
    nom_fichier_synthese = "NO", details="NO"):
    """ Creation de shape file à partir des données des CSV
    Si synthese n'est pas NO, on produit les moyennes dans le fichier synthese
    Selon le niveau de détail du csv, on crée les 5 premiers ou tous les attibuts
    """    

    #Préparation de la liste d'arguments
    x,y,nbsarmshp,diamshp,biomshp,dateshp,vitesseshp= [],[],[],[],[],[],[]
    nbsarmm2,nbsarcep,biommm2,biomgm2,biomgcep=[],[],[],[],[]
  
    #ecriture du fichier shp avec les 0    
    physiocap_log (u"Création du shapefile :" + shape_name)
   
    #Lecture des data dans le csv et stockage dans une liste
    with open(csv_name, "rt") as csvfile:
        r = csv.reader(csvfile, delimiter=";")
        for i,row in enumerate(r):
            if i > 0: #skip header
                x.append(float(row[2]))
                y.append(float(row[3]))
                nbsarmshp.append(float(row[4]))
                diamshp.append(float(row[5]))
                biomshp.append(float(row[6]))
                dateshp.append(str(row[7]))
                vitesseshp.append(float(row[8]))
                if details == "YES":
                    # Niveau de detail demandé
                    # Todo assert sur len row
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
    if details == "YES":
        # Niveau de detail demandé
        w.field('NBSARMM2','F',10,2)
        w.field('NBSARCEP','F',10,2)
        w.field('BIOMM2','F',10,2)
        w.field('BIOMGM2','F',10,2)
        w.field('BIOMGCEP','F',10,2)
    
    #Ecriture du shp
    for j,k in enumerate(x):
        w.point(k,y[j]) #écrit la géométrie
        if details == "YES":
            # Ecrit tous les attributs
            w.record(dateshp[j],vitesseshp[j],nbsarmshp[j], diamshp[j], biomshp[j], \
            nbsarmm2[j], nbsarcep[j], biommm2[j], biomgm2[j], biomgcep[j]) #écrit les attributs
        else:
            # Ecrit les 5 premiers attributs
            w.record(dateshp[j],vitesseshp[j],nbsarmshp[j], diamshp[j], biomshp[j])
            
    #Save shapefile
    w.save(shape_name)
    physiocap_log (u"Fin de création du shapefile :" + shape_name)

    #Create the PRJ file
    prj = open(prj_name, "w")
    epsg = 'PROJCS["RGF93_Lambert_93",GEOGCS["GCS_RGF93",DATUM["D_RGF_1993", \
    SPHEROID["GRS_1980",6378137,298.257222101]],PRIMEM["Greenwich",0], \
    UNIT["Degree",0.017453292519943295]],PROJECTION["Lambert_Conformal_Conic"], \
    PARAMETER["standard_parallel_1",49],PARAMETER["standard_parallel_2",44], \
    PARAMETER["latitude_of_origin",46.5],PARAMETER["central_meridian",3], \
    PARAMETER["false_easting",700000],PARAMETER["false_northing",6600000], \
    UNIT["Meter",1]]'
    prj.write(epsg)
    prj.close()    
    
    # Creation de la synthese
    # Todo: Test des calculs STATISTIQUES
    if nom_fichier_synthese != "NO":
        # Ecriture des resulats
        fichier_synthese = open(nom_fichier_synthese, "a")
        fichier_synthese.write("\n\nSTATISTIQUES\n")
        fichier_synthese.write("vitesse moyenne d'avancement  \n	mean : %0.1f km/h\n" %np.mean(vitesseshp))
        fichier_synthese.write("Section moyenne \n	mean : %0.2f mm	std : %0.1f\n" %(np.mean(diamshp), np.std(diamshp)))
        fichier_synthese.write("Nombre de sarments au m \n	mean : %0.2f	std : %0.1f\n" %(np.mean(nbsarmshp), np.std(nbsarmshp)))
        fichier_synthese.write("Biomasse en mm²/m linéaire \n	mean : %0.1f	std : %0.1f\n" %(np.mean(biomshp), np.std(biomshp)))
        if details == "YES":
            fichier_synthese.write("Nombre de sarments au m² \n	mean : %0.1f	std : %0.1f\n" %(np.mean(nbsarmm2), np.std(nbsarmm2)))
            fichier_synthese.write("Nombre de sarments par cep \n	mean : %0.1f	std : %0.1f\n" %(np.mean(nbsarcep), np.std(nbsarcep)))
            fichier_synthese.write("Biommasse en mm²/m² \n	mean : %0.1f	std : %0.1f\n" %(np.mean(biommm2), np.std(biommm2)))
            fichier_synthese.write("Biomasse en gramme/m² \n	mean : %0.1f	std : %0.1f\n" %(np.mean(biomgm2), np.std(biomgm2)))
            fichier_synthese.write("Biomasse en gramme/cep \n	mean : %0.1f	std : %0.1f\n" %(np.mean(biomgcep), np.std(biomgcep))) 
        fichier_synthese.close()

# Fonction pour créer les fichiers histogrammes    
def physiocap_fichier_histo(src, diamet, nbsarment, err):
    """Fonction de traitement. Creation des fichiers pour réaliser les histogrammes
    Lit et traite ligne par ligne le fichier source (src).
    Le résultat est écrit au fur et à mesure dans le
    fichier destination (dst)
    """
        
    while True :
        ligne = src.readline() # lit les lignes 1 à 1
        if not ligne: break 
        comptage = ligne.count(",") # compte le nombre de virgules
        result = ligne.split(",") # split en fonction des virgules
        try : # accompli cette fonction si pas d'erreur sinon except
            XY = [float(x) for x in result[1:9]]   # on extrait les XY et on les transforme en float  > Données GPS 
            diams = [float(x) for x in result[9:NB_VIRGULES+1]] # on extrait les diams et on les transforme en float 
            diamsF = [i for i in diams if i > 2 and i < 28 ] # on filtre les diams > diamsF correspond aux diams filtrés entre 2 et 28       
            if comptage==NB_VIRGULES and len(diamsF)>0 : # si le nombre de diamètre après filtrage != 0 alors mesures
                nbsarm = len(diamsF)/(XY[7]*1000/3600) #8eme donnée du GPS est la vitesse. Dernier terme : distance entre les sarments
                nbsarment.write("%f%s" %(nbsarm,";"))                
                for n in range(len(diamsF)) :
                    diamet.write("%f%s" %(diamsF[n],";"))
        except : # accompli cette fonction si erreur
            msg = "%s%s\n" %("erreur histo",ligne)
            physiocap_error( msg )
            err.write( msg ) # on écrit la ligne dans le fichier ERREUR.csv
            pass # A DEFINIR

# Fonction de filtrage et traitement des données
def physiocap_filtrer(src, dst, err, dst0, diamet2, nom_fichier_synthese, mindiam, maxdiam, max_sarments_metre):
    """Fonction de traitement.
    Lit et traite ligne par ligne le fichier source (src).
    Le résultat est écrit au fur et à mesure dans le
    fichier destination (dst). 
    """
    # Todo: traiter les deux cas
    parcellaire = "n"
    
    #S'il n'existe pas de données parcellaire, le script travaille avec les données brutes
    if parcellaire == "n" :
        dst.write("%s\n" % ("X ; Y ; XL93 ; YL93 ; NBSARM ; DIAM ; BIOM ; Date ; Vitesse")) # ecriture de l'entête
        dst0.write("%s\n" % ("X ; Y ; XL93 ; YL93 ; NBSARM ; DIAM ; BIOM ; Date ; Vitesse")) # ecriture de l'entête
    #S'il existe des données parcellaire, le script travaille avec les données brutes et les données calculées
    elif parcellaire == "y" :
        dst.write("%s\n" % ("X ; Y ; XL93 ; YL93 ; NBSARM ; DIAM ; BIOM ; Date ; Vitesse ; NBSARMM2 ; NBSARCEP ; BIOMMM2 ; BIOMGM2 ; BIOMGCEP ")) # ecriture de l'entête
        dst0.write("%s\n" % ("X ; Y ; XL93 ; YL93 ; NBSARM ; DIAM ; BIOM ; Date ; Vitesse ; NBSARMM2 ; NBSARCEP ; BIOMMM2 ; BIOMGM2 ; BIOMGCEP ")) # ecriture de l'entête

    while True :
        ligne = src.readline()
        if not ligne: break 
        comptage = ligne.count(",") # compte le nombre de virgules
        result = ligne.split(",") # split en fonction des virgules
        #physiocap_log("Comptage de virgules : " + str(comptage))

        try : # accompli cette fonction si pas d'erreur sinon except
            XY = [float(x) for x in result[1:9]]   # on extrait les XY et on les transforme en float  
            # On transforme les WGS84 en L93
            WGS84 = osr.SpatialReference()
            WGS84.ImportFromEPSG(4326)
            LAMB93 = osr.SpatialReference()
            LAMB93.ImportFromEPSG(2154)
            transformation1 = osr.CoordinateTransformation(WGS84,LAMB93) 
            L93 = transformation1.TransformPoint(XY[0],XY[1])
            diams = [float(x) for x in result[9:NB_VIRGULES+1]] # on extrait les diams et on les transforme en float 
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
                elif comptage==NB_VIRGULES and len(diamsF)>0 : # si le nombre de diamètre après filtrage != 0 alors mesures
                    nbsarm = len(diamsF)/(XY[7]*1000/3600)
                    if nbsarm > 1 and nbsarm < max_sarments_metre and parcellaire == "n" :                   
                        diam =sum(diamsF)/len(diamsF)
                        biom=3.1416*(diam/2)*(diam/2)*nbsarm
                        dst0.write("%.7f%s%.7f%s%.7f%s%.7f%s%0.2f%s%.2f%s%.2f%s%s%s%0.2f\n" %(XY[0],";",XY[1],";",L93[0],";",L93[1],";",nbsarm,";",diam,";",biom,";",result[0],";",XY[7])) # on écrit la ligne dans le fichier OUT0.csv 
                        dst.write("%.7f%s%.7f%s%.7f%s%.7f%s%0.2f%s%.2f%s%.2f%s%s%s%0.2f\n" %(XY[0],";",XY[1],";",L93[0],";",L93[1],";",nbsarm,";",diam,";",biom,";",result[0],";",XY[7])) # on écrit la ligne dans le fichier OUT.csv
                        for n in range(len(diamsF)) :
                            diamet2.write("%f%s" %(diamsF[n],";"))
            elif parcellaire == "y" :
                physiocap_log("dans parcelle Y : " )
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
                elif comptage==NB_VIRGULES and len(diamsF)>0 : # si le nombre de diamètre après filtrage != 0 alors mesures
                    nbsarm = len(diamsF)/(XY[7]*1000/3600)
                    if nbsarm > 1 and nbsarm < max_sarments_metre :                   
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

 