# -*- coding: utf-8 -*-
"""
/***************************************************************************
 PhysiocapAnalyseurDialog
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
from Physiocap_tools import \
physiocap_log, physiocap_error, physiocap_message_box, physiocap_open_file, \
physiocap_fichierhisto, physiocap_filtrer
from PyQt4 import QtGui, uic
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import *
from qgis.gui import *
import os 
import platform

import csv
#import sys

##if platform.system() == 'Windows':
##    import win32api
    
try :
    import glob
    import shutil
    import time
except :
    # Todo: test si bien dan la log
    physiocap_log(u"Modules glob | shutil ne sont pas installees ! ")    
    physiocap_log(u"vous pouvez télécharger la suite winpython 3.3 qui contient ces bibliotheques http://winpython.sourceforge.net/")
    physiocap_log(u"sinon vous pouvez installer ces bibliothèques independamment")
    
try :
    from osgeo import osr
except :
    physiocap_log(u"GDAL n'est pas installé ! ")    
    physiocap_log(u"Installer GDAL/osgeo via http://www.lfd.uci.edu/~gohlke/pythonlibs/#gdal ")
try :
    import numpy as np
    #import matplotlib.pyplot as plt
except :
    physiocap_log(u"Numpy n'est pas installees ! ")    
    physiocap_log(u"vous pouvez télécharger la suite winpython 3.3 qui contient ces bibliotheques http://winpython.sourceforge.net/")
    physiocap_log(u"sinon vous pouvez installer ces bibliothèques independamment")

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'Physiocap_dialog_base.ui'))



# PARAMETRAGE PHYSIOCAP
# Ces variables sont nommées en Francais par compatibilité avec la version physiocap_V8
# dont les fonctions de calcul sont conservé à l'identique
# Répertoire de base et projet
REPERTOIRE_DONNEES_BRUTES = "/home/jhemmi/Documents/GIS/SCRIPT/QGIS/PhysiocapAnalyseur/data"
NOM_PROJET = "UnProjetPhysiocap"
# Listes de valeurs
CEPAGES = [ "Negrette", "Chardonnay", "Pinot Noir", "Pinot Meunier"]
TAILLES = [ "Chablis", "Guyot simple", "Guyot double", "Cordon de Royat" ]
# Répertoires des sources et de concaténation en fichiers texte
REPERTOIRE_SOURCES = "fichiers_sources"
SUFFIXE_BRUT_CSV = "_RAW.csv"
EXTENSION_MID = "*.MID"
REPERTOIRE_TEXTES = "fichiers_texte"
REPERTOIRE_HISTO = "histogrammes"
REPERTOIRE_SHAPEFILE = "shapefile"
# Nom du fichier de synthèse
FICHIER_RESULTAT = NOM_PROJET +"_resultat.txt"

FICHIER_SAUVE_PARAMETRES = os.path.join(
                    os.path.dirname(__file__), 
                    '.physiocap')
                    
class PhysiocapAnalyseurDialog(QtGui.QDialog, FORM_CLASS):
    def __init__(self, parent=None):
        """Constructor."""
        super(PhysiocapAnalyseurDialog, self).__init__(parent)
        # Set up the user interface from Designer.
        # After setupUI you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)
        self.plugin_dir = os.path.dirname(__file__)  

        # Examples Slot for boutons 
        #self.refreshButton.pressed.connect(self.create_contour_list )
        #self.buttonBox.button( QDialogButtonBox.Ok ).pressed.connect(self.accept)
        #self.buttonBox.button( QDialogButtonBox.Cancel ).pressed.connect(self.reject)
        self.buttonBox.button( QDialogButtonBox.Help ).pressed.connect(self.helpRequested)
        
        # Slot pour données brutes
        self.toolButtonDirectoryPhysiocap.pressed.connect( self.lecture_repertoire_donnees_brutes )  
        
        physiocap_log( u"Votre machine tourne sous " + platform.system())
        # Initialisation des parametres
        # TODO: Reprendre toutes les infos dans le fichier sauvegardé "~plugin/.physiocap"
        self.lineEditProjet.setText( NOM_PROJET)
        self.lineEditDirectoryPhysiocap.setText( REPERTOIRE_DONNEES_BRUTES)
        # Remplissage de la liste de cépage
        if len( CEPAGES) == 0:
            self.fieldComboCepage.clear( )
            physiocap_error( u"Pas de liste de cépage pré défini")
        else:
            self.fieldComboCepage.clear( )
            self.fieldComboCepage.addItems( CEPAGES )
        self.fieldComboCepage.setCurrentIndex( 0)
        # Remplissage de la liste de taille
        if len( TAILLES) == 0:
            self.fieldComboTaille.clear( )
            physiocap_error( u"Pas de liste de mode de taille pré défini")
        else:
            self.fieldComboTaille.clear( )
            self.fieldComboTaille.addItems( TAILLES )
        self.fieldComboTaille.setCurrentIndex( 0)                        
        # TODO: Recherche du projet courant ?
        
    # Slots
    def helpRequested(self):
        """ Help html qui pointe vers gitHub""" 
        help_url = QUrl("file:///%s/help/index.html" % self.plugin_dir)
        QDesktopServices.openUrl(help_url)

    def reject( self ):
        """Close when bouton is Cancel"""
        #self.textEdit.clear()
        QDialog.reject( self)
                
    def accept( self ):
        """Verify when bouton is OK"""
        # currentText pour uns liste de valeur
        if self.lineEditDirectoryPhysiocap.text() == "":
            physiocap_error( u"Pas de répertoire de donnée spécifié")
            return QMessageBox.information( self, "Physiocap",
                                   self.tr( u"Pas de répertoire de donnée spécifié" ) )
        if self.lineEditProjet.text() == "":
            physiocap_error( u"Pas de nom de projet spécifié")
            return QMessageBox.information( self, "Physiocap",
                                   self.tr( u"Pas de nom de projet spécifié" ) )
        # Création des repertoires et des resultats de synthese
        retour = self.creer_donnees_resultats()
                    
    # Repertoire données brutes :
    def lecture_repertoire_donnees_brutes( self):
        """Catch directory for raw data"""
        # TODO: Faire traduction du titre self.?iface.tr("Répertoire des données brutes")
        dirName = QFileDialog.getExistingDirectory( self, u"Répertoire des données brutes",
                                                 REPERTOIRE_DONNEES_BRUTES,
                                                 QFileDialog.ShowDirsOnly
                                                 | QFileDialog.DontResolveSymlinks);
        if len( dirName) == 0:
          return
        self.lineEditDirectoryPhysiocap.setText( dirName )
    
##    def input_textfile( self ):
##        """ Catch name of text file """
##        fileName = QFileDialog.getOpenFileName(None, 
##            "Select your Text File:",
##            "", "*.csv *.txt")
##        if len( fileName) == 0:
##          return
##        self.editOTHERfile.setText( fileName )     
##    
    
    # Creation des repertoires source puis resultats
    def creer_donnees_resultats( self):
        """ Récupération des paramètres saisies et 
        creation de l'arbre "soure" "texte" et du fichier resultats"
        Ce sont les résultats de l'analyse filtration des données brutes"""
        
        # Récupérer les paramètres saisies
        REPERTOIRE_DONNEES_BRUTES = self.lineEditDirectoryPhysiocap.text()
        NOM_PROJET = self.lineEditProjet.text()
        detailParametresVignoble = "y"
        minVitesse = self.doubleSpinBoxMinVitesse.text()
        mindiam = self.spinBoxMinDiametre.text()
        maxdiam = self.spinBoxMaxDiametre.text()
        max_sarments_metre = self.spinBoxMaxSarmentsParMetre.text()
        interrangs = self.spinBoxInterrangs.text()
        interceps = self.spinBoxInterceps.text()
        hauteur = self.spinBoxHauteur.text()
        densite = self.doubleSpinBoxDensite.text()
        leCepage = self.fieldComboCepage.currentText()
        laTaille = self.fieldComboTaille.currentText()
                
##        physiocap_log(u"Récup params cepage : " + leCepage + " mindiam : " + mindiam )

        physiocap_log(u"Récup params taille : " + laTaille + " maxdiam : " + maxdiam + " ==" + max_sarments_metre)
        # Vérification de l'existance ou création du répertoire projet
        chemin_projet = os.path.join(REPERTOIRE_DONNEES_BRUTES, NOM_PROJET)
        if not (os.path.exists( chemin_projet)):
            try :
                os.mkdir( chemin_projet)
            except :
                return physiocap_error(u"Problème lors de la création du répertoire projet: " + 
                chemin_projet)
        # Verification de l'existance ou création du répertoire des sources MID et fichier csv
        chemin_sources = os.path.join(chemin_projet, REPERTOIRE_SOURCES)
        if not (os.path.exists( chemin_sources)):
            try :
                os.mkdir( chemin_sources)
            except :
                return physiocap_error(u"Problème lors de la création du répertoire des sources: " + 
                chemin_sources)
        
        # Fichier de concaténations CSV des résultats bruts        
        nom_court_fichier_concat = NOM_PROJET + SUFFIXE_BRUT_CSV
        nom_fichier_concat = os.path.join(chemin_sources, nom_court_fichier_concat)
        if os.path.isfile( nom_fichier_concat):
            physiocap_log(u"Destruction du fichier préexistant :" + nom_fichier_concat) 
            os.remove( nom_fichier_concat)
        try :
            fichier_concat = open(nom_fichier_concat, "w")
        except :
            return physiocap_error(u"Problème lors de la création du fichier concaténé .csv: " + 
            nom_court_fichier_concat)
            
        # Création du fichier concaténé
        nom_fichiers_recherches = os.path.join(REPERTOIRE_DONNEES_BRUTES, EXTENSION_MID)
        physiocap_log(u"Chemin MID: " + nom_fichiers_recherches)
        # Todo: Assert à vérifier le nombre de MID > 0
        # le Tri pour retombé dans l'ordre de Physiocap_V8
        listeTriee = sorted(glob.glob( nom_fichiers_recherches))
        if len( listeTriee) == 0:
            physiocap_log(" Pas de fichier d'entré à traiter...")
            return physiocap_error(" Pas de fichier d'entré à traiter...")
        for mid in listeTriee:
            shutil.copyfileobj(open(mid, "r"), fichier_concat)
            # et copie des MID
            shutil.copy(mid,chemin_sources)
        fichier_concat.close()
            
        # Todo: Assert Trouver les lignes de données invalides (trop longue, sans 58 virgules ... etc...
        # Création la première partie du fichier de synthèse
        nom_fichier_synthese = os.path.join(chemin_projet, FICHIER_RESULTAT)
        try :
            fichier_synthese = open(nom_fichier_synthese, "w")
        except :
            return physiocap_error(u"Problème lors de la création du fichier de synhtese: " + 
            nom_fichier_synthese)
        fichier_synthese.write("SYNTHESE PHYSIOCAP\n\n")
        fichier_synthese.write("Fichier généré le : ")
        a_time = time.strftime("%d/%m/%y %H:%M\n",time.localtime())
        fichier_synthese.write(a_time)
        fichier_synthese.write("\nPARAMETRES SAISIS ")
        
        physiocap_log ( u"Fin de la création csv et synthèse")
       
        # Assert le fichier de données n'est pas vide
        if os.path.getsize(nom_fichier_concat ) == 0 :
            msg =u"Le fichier " + nom_court_fichier_concat + u" a une taille nulle !"
            physiocap_message_box( self, msg)
            return physiocap_error( msg)

        # Verification de l'existance ou création du répertoire textes
        chemin_textes = os.path.join(chemin_projet, REPERTOIRE_TEXTES)
        if not (os.path.exists( chemin_textes)):
            try :
                os.mkdir( chemin_textes)
            except :
                return physiocap_error(u"Problème lors de la création du répertoire des fichiers textes: " + 
                chemin_textes)
                       
        # Ouverture du fichier destination
        # Fichier des diamètres     
        nom_court_fichier_diametre = "diam" + SUFFIXE_BRUT_CSV
        nom_fichier_diametre = os.path.join(chemin_textes, nom_court_fichier_diametre)
        if os.path.isfile( nom_fichier_diametre):
            physiocap_log(u"Destruction du fichier préexistant :" + nom_fichier_diametre) 
            os.remove( nom_fichier_diametre)
        try :
            destination = open(nom_fichier_diametre, "w")
        except :
            return physiocap_error(u"Problème lors de la création du fichier des diamètres: " + 
            nom_fichier_diametre)
        
        # Todo: Appel fonction de creation de fichier
        nom_court_fichier_sarment = "nbsarm" + SUFFIXE_BRUT_CSV
        nom_fichier_sarment = os.path.join(chemin_textes, nom_court_fichier_sarment)
        destination5 = open(nom_fichier_sarment, "w")
        nom_court_fichier_erreur = "erreurs.csv"
        nom_fichier_error = os.path.join(chemin_textes, nom_court_fichier_erreur)
        erreur = open(nom_fichier_error,"w")
        # ouverture du fichier source
        fichier_concat = open(nom_fichier_concat, "r")
 
        # Appeler la fonction de traitement
        #################
        physiocap_fichierhisto( fichier_concat, destination,destination5,erreur)
        #################
        # Fermerture des fichiers
        fichier_concat.close()
        destination.close()
        destination5.close()
        erreur.close()

        physiocap_log ( u"Fin de la création fichier pour histogramme")

        # Todo: Appel fonction de creation de fichier
        nom_court_fichier_out = NOM_PROJET + "_OUT.csv"
        nom_fichier_out = os.path.join(chemin_textes, nom_court_fichier_out)
        destination1 = open(nom_fichier_out, "w")

        nom_court_fichier_out0 = NOM_PROJET + "_OUT0.csv"
        nom_fichier_out0 = os.path.join(chemin_textes, nom_court_fichier_out0)
        destination0 = open(nom_fichier_out0, "w")
        
        nom_court_fichier_diametre_filtre = "diam_FILTERED.csv"
        nom_fichier_diametre_filtre = os.path.join(chemin_textes, nom_court_fichier_diametre_filtre)
        diamet2 = open(nom_fichier_diametre_filtre, "w")

        # ouverture du fichier source
        fichier_concat = open(nom_fichier_concat, "r")       
        erreur = open(nom_fichier_error,"a")

        # Appeler la fonction de traitement
        #################
        physiocap_filtrer( fichier_concat, destination1, erreur, destination0, \
        diamet2, nom_fichier_synthese, \
        float( mindiam), float( maxdiam), float( max_sarments_metre))
        #################
        #On écrit dans le fichiers résultats les paramètres du modéle
        fichier_synthese = open(nom_fichier_synthese, "a")
        fichier_synthese.write("\nAucune information parcellaire saisie\n")
        # Todo: bug %s ou %
##        fichier_synthese.write("Nombre de sarments max au mètre linéaire: %s \n" %max_sarments_metre)
##        fichier_synthese.write("Diamètre minimal : %s mm\n" %mindiam)
##        fichier_synthese.write("Diamètre maximal : %s mm\n" %maxdiam)
        fichier_synthese.close()
        # Fermeture du fichier destination
        destination1.close()
        destination0.close()
        diamet2.close()
        erreur.close()
        # Fermerture du fichier source
        fichier_concat.close()      

        # Todo: creation du Shp dans Qgis
        # Verification de l'existance ou création du répertoire des sources MID et fichier csv
        chemin_shapes = os.path.join(chemin_projet, REPERTOIRE_SHAPEFILE)
        if not (os.path.exists( chemin_shapes)):
            try :
                os.mkdir( chemin_shapes)
            except :
                return physiocap_error(u"Problème lors de la création du répertoire des shapes: " + 
                chemin_shapes)
                
        # Création des shapes
        nom_court_fichier_shape_sans_0 = NOM_PROJET + "_L93.shp"
        nom_fichier_out0 = os.path.join(chemin_shapes, nom_court_fichier_shape_sans_0)
        shape_sans_0 = open(nom_fichier_out0, "w")
        
        # Ecriture du fichier shp sans les 0    
        physiocap_log ("Creation du shapefile sans 0 en L93" + nom_court_fichier_shape_sans_0)
        #out_file = ("%s/shapefile/%s_L93.shp" %(nom,nom)) 
        
        #Préparation de la liste d'arguments
        x,y,nbsarmshp,diamshp,biomshp,dateshp,vitesseshp,nbsarmm2,nbsarcep,biommm2,biomgm2,biomgcep=[],[],[],[],[],[],[],[],[],[],[],[]
        diam, nbsarm, vitesse = [], [], []
        #Lecture des data dans le csv et stockage dans une liste
        with open(nom_fichier_out, "rt") as csvfile:
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
                    # Todo: pour calcul de stat à finir
                    vitesse.append(float(row[8]))
                    diam.append(float(row[5]))
                    nbsarm.append(float(row[4]))
                    if len( row) > 8:
                        # On est dans le cas avec info parcellaire
                        pass
##                        nbsarmm2.append(float(row[9]))
##                        nbsarcep.append(float(row[10]))
##                        biommm2.append(float(row[11]))
##                        biomgm2.append(float(row[12]))
##                        biomgcep.append(float(row[13]))
                    
##        # Création du shap et des champs vides
##        w = shp.Writer(shp.POINT)
##        w.autoBalance = 1 #vérifie la geom
##        w.field('DATE','S',25)
##        w.field('VITESSE','F',10,2)
##        w.field('NBSARM','F',10,2)
##        w.field('DIAM','F',10,2)
##        w.field('BIOM','F',10,2)
##        w.field('NBSARMM2','F',10,2)
##        w.field('NBSARCEP','F',10,2)
##        w.field('BIOMM2','F',10,2)
##        w.field('BIOMGM2','F',10,2)
##        w.field('BIOMGCEP','F',10,2)
##        
##        #Ecriture du shp
##        for j,k in enumerate(x):
##            w.point(k,y[j]) #écrit la géométrie
##            w.record(dateshp[j],vitesseshp[j],nbsarmshp[j], diamshp[j], biomshp[j], nbsarmm2[j], nbsarcep[j], biommm2[j], biomgm2[j], biomgcep[j]) #écrit les attributs
##        
##        #Save shapefile
##        w.save(out_file)
##    
### create the PRJ file
##prj = open("%s/shapefile/%s_0_L93.prj" %(nom,nom), "w")
##epsg = 'PROJCS["RGF93_Lambert_93",GEOGCS["GCS_RGF93",DATUM["D_RGF_1993",SPHEROID["GRS_1980",6378137,298.257222101]],PRIMEM["Greenwich",0],UNIT["Degree",0.017453292519943295]],PROJECTION["Lambert_Conformal_Conic"],PARAMETER["standard_parallel_1",49],PARAMETER["standard_parallel_2",44],PARAMETER["latitude_of_origin",46.5],PARAMETER["central_meridian",3],PARAMETER["false_easting",700000],PARAMETER["false_northing",6600000],UNIT["Meter",1]]'
##prj.write(epsg)
##prj.close()
##prj = open("%s/shapefile/%s_L93.prj" %(nom,nom), "w")
##epsg = 'PROJCS["RGF93_Lambert_93",GEOGCS["GCS_RGF93",DATUM["D_RGF_1993",SPHEROID["GRS_1980",6378137,298.257222101]],PRIMEM["Greenwich",0],UNIT["Degree",0.017453292519943295]],PROJECTION["Lambert_Conformal_Conic"],PARAMETER["standard_parallel_1",49],PARAMETER["standard_parallel_2",44],PARAMETER["latitude_of_origin",46.5],PARAMETER["central_meridian",3],PARAMETER["false_easting",700000],PARAMETER["false_northing",6600000],UNIT["Meter",1]]'
##prj.write(epsg)
##prj.close()
        physiocap_log ( u"Fin de la création des shapes")


        # Todo: Calcul de la moyenne
        
        # Ecriture des resulats
        fichier_synthese = open(nom_fichier_synthese, "a")
        fichier_synthese.write("\n\nSTATISTIQUES\n")
        fichier_synthese.write("vitesse moyenne d'avancement  \n	mean : %0.1f km/h\n" %np.mean(vitesse))
        fichier_synthese.write("Section moyenne \n	mean : %0.2f mm	std : %0.1f\n" %(np.mean(diam), np.std(diam)))
        fichier_synthese.write("Nombre de sarments au m \n	mean : %0.2f	std : %0.1f\n" %(np.mean(nbsarm), np.std(nbsarm)))
##        fichier_synthese.write("Biomasse en mm²/m linéaire \n	mean : %0.1f	std : %0.1f\n" %(np.mean(biom), np.std(biom)))
##        if parcellaire == "y" :
##            fichier_synthese.write("Nombre de sarments au m² \n	mean : %0.1f	std : %0.1f\n" %(np.mean(NBSARMM2), np.std(NBSARMM2)))
##            fichier_synthese.write("Nombre de sarments par cep \n	mean : %0.1f	std : %0.1f\n" %(np.mean(NBSARCEP), np.std(NBSARCEP)))
##            fichier_synthese.write("Biommasse en mm²/m² \n	mean : %0.1f	std : %0.1f\n" %(np.mean(BIOMMM2), np.std(BIOMMM2)))
##            fichier_synthese.write("Biomasse en gramme/m² \n	mean : %0.1f	std : %0.1f\n" %(np.mean(BIOMGM2), np.std(BIOMGM2)))
##            fichier_synthese.write("Biomasse en gramme/cep \n	mean : %0.1f	std : %0.1f\n" %(np.mean(BIOMGCEP), np.std(BIOMGCEP))) 
        fichier_synthese.close()

        
        
        # Fin 
        physiocap_log ( u"Fin des shapes")
        return "OK" 

