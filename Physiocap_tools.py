# -*- coding: utf-8 -*-
"""
/***************************************************************************
 Physiocap_tools
                                 A QGIS plugin
 Physiocap plugin helps analysing raw data from Physiocap in Qgis
                              -------------------
        begin                : 2015-07-31
        git sha              : $Format:%H$
        copyright            : (C) 2015 by jhemmi.eu
        email                : jean@jhemmi.eu
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
from PyQt4 import QtGui, uic  # for Form_class
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import *
from qgis.gui import *
# Import system & os
import os.path
import sys, string
import platform
if platform.system() == 'Windows':
    import win32api


try :
    from osgeo import osr
except :
    physiocap_log(u"GDAL n'est pas installé ! ")    
    physiocap_log(u"Installer GDAL/osgeo via http://www.lfd.uci.edu/~gohlke/pythonlibs/#gdal ")


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

# Fonction pour créer les fichiers histogrammes
def physiocap_fichierhisto(src, diamet, nbsarment, err):
    """Fonction de traitement. Creation des fichiers pour réaliser les histogrammes
    Lit et traite ligne par ligne le fichier source (src).
    Le résultat est écrit au fur et à mesure dans le
    fichier destination (dst)"""     
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


# création de la fonction de traitement des données

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
            physiocap_log("dans WGS84 : " )
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
                    physiocap_log("dans diametre 0 : " )
                    nbsarm = 0
                    diam =0
                    biom = 0
                    dst0.write("%.7f%s%.7f%s%.7f%s%.7f%s%i%s%i%s%i%s%s%s%0.2f\n" %(XY[0],";",XY[1],";",L93[0],";",L93[1],";",nbsarm,";",diam ,";",biom,";",result[0],";",XY[7]))  # on écrit la ligne dans le fichier OUT0.csv  
                elif comptage==NB_VIRGULES and len(diamsF)>0 : # si le nombre de diamètre après filtrage != 0 alors mesures
                    nbsarm = len(diamsF)/(XY[7]*1000/3600)
                    if nbsarm > 1 and nbsarm < max_sarments_metre and parcellaire == "n" :                   
                        physiocap_log("dans nb sarments : " + str(nbsarm) )
                        diam =sum(diamsF)/len(diamsF)
                        physiocap_log("dans diam : " + str(diam) )
                        biom=3.1416*(diam/2)*(diam/2)*nbsarm
                        dst0.write("%.7f%s%.7f%s%.7f%s%.7f%s%0.2f%s%.2f%s%.2f%s%s%s%0.2f\n" %(XY[0],";",XY[1],";",L93[0],";",L93[1],";",nbsarm,";",diam,";",biom,";",result[0],";",XY[7])) # on écrit la ligne dans le fichier OUT0.csv 
                        dst.write("%.7f%s%.7f%s%.7f%s%.7f%s%0.2f%s%.2f%s%.2f%s%s%s%0.2f\n" %(XY[0],";",XY[1],";",L93[0],";",L93[1],";",nbsarm,";",diam,";",biom,";",result[0],";",XY[7])) # on écrit la ligne dans le fichier OUT.csv
                        for n in range(len(diamsF)) :
                            diamet2.write("%f%s" %(diamsF[n],";"))
                physiocap_log("fin parcelle N : " )
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

 