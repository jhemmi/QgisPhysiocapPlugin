# -*- coding: utf-8 -*-
"""
/***************************************************************************
 PhysiocapAnalyseurDialog
                                 A QGIS plugin
 Physiocap plugin helps analysing raw data from Physiocap in Qgis & create
 synthesis of Physiocap measures
 Physiocap plugin analyse les données brutes de Physiocap dans Qgis & crée
 une synthese des mesures de Physiocap
 
 Le module Dialogue gere la dynamique des dialogues, initialisation 
 et recupération des variables, sauvegarde des parametres
 nommage et création des fichiers
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
from Physiocap_tools import physiocap_log,physiocap_error,physiocap_message_box, \
        physiocap_open_file, physiocap_shapefile, physiocap_fichier_histo, \
        physiocap_filtrer       

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
    # Todo: ASAP test si bien dans la log
    physiocap_log(u"Modules glob | shutil ne sont pas installees ! ")    
    physiocap_log(u"vous pouvez télécharger la suite winpython 3.3 qui contient ces bibliotheques http://winpython.sourceforge.net/")
    physiocap_log(u"sinon vous pouvez installer ces bibliothèques independamment")
    
try :
    from osgeo import osr
except :
    physiocap_log(u"GDAL n'est pas installé ! ")    
    physiocap_log(u"Installer GDAL/osgeo via http://www.lfd.uci.edu/~gohlke/pythonlibs/#gdal ")

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
EXTENSION_SHP = "_L93.shp"
EXTENSION_POUR_ZERO = "_0"
EXTENSION_PRJ = "_L93.prj"

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
        # TODO: V0.2 Reprendre toutes les infos dans le fichier sauvegardé "~plugin/.physiocap"
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
        # TODO: V0.2 Recherche du projet courant ?
        
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
                                
        # Todo: Assert sur les variables saisies et sur le cas detail ou non                        
        # Création des repertoires et des resultats de synthese
        retour = self.creer_donnees_resultats()
                    
    # Repertoire données brutes :
    def lecture_repertoire_donnees_brutes( self):
        """Catch directory for raw data"""
        # TODO: V0.2 Faire traduction du titre self.?iface.tr("Répertoire des données brutes")
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
        creation de l'arbre "soure" "texte" et du fichier "resultats"
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
##        physiocap_log(u"Récup params taille : " + laTaille + " maxdiam : " + maxdiam + " ==" + max_sarments_metre)
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
        #physiocap_log(u"Chemin MID: " + nom_fichiers_recherches)
        
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
        physiocap_fichier_histo( fichier_concat, destination, \
                                destination5, erreur)
        #################
        # Fermerture des fichiers
        fichier_concat.close()
        destination.close()
        destination5.close()
        erreur.close()

        physiocap_log ( u"Fin de la création fichier pour histogramme")

        # Todo: Appel fonction de creation de fichier
        nom_court_csv_sans_0 = NOM_PROJET + "_OUT.csv"
        nom_csv_sans_0 = os.path.join(chemin_textes, nom_court_csv_sans_0)
        destination1 = open(nom_csv_sans_0, "w")

        nom_court_csv_avec_0 = NOM_PROJET + "_OUT0.csv"
        nom_csv_avec_0 = os.path.join(chemin_textes, nom_court_csv_avec_0)
        destination0 = open(nom_csv_avec_0, "w")
        
        nom_court_fichier_diametre_filtre = "diam_FILTERED.csv"
        nom_fichier_diametre_filtre = os.path.join(chemin_textes, nom_court_fichier_diametre_filtre)
        diamet2 = open(nom_fichier_diametre_filtre, "w")

        # ouverture du fichier source
        fichier_concat = open(nom_fichier_concat, "r")       
        erreur = open(nom_fichier_error,"a")

        # Appeler la fonction de filtraeg des données
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
                
        # Création des shapes sans 0
        nom_court_shape_sans_0 = NOM_PROJET + EXTENSION_SHP
        nom_shape_sans_0 = os.path.join(chemin_shapes, nom_court_shape_sans_0)
        nom_court_prj_sans_0 = NOM_PROJET + EXTENSION_PRJ
        nom_prj_sans_0 = os.path.join(chemin_shapes, nom_court_prj_sans_0)
        # Todo: traiter le cas detail Y
        # cas sans 0, on demande la synthese
        synthese = "YES"
        physiocap_shapefile( nom_shape_sans_0, nom_prj_sans_0, nom_csv_sans_0, synthese)
        physiocap_log ("Creation du shapefile sans 0 en L93" + nom_court_shape_sans_0)

        # Création des shapes avec 0
        nom_court_shape_avec_0 = NOM_PROJET + EXTENSION_POUR_ZERO + EXTENSION_SHP
        nom_shape_avec_0 = os.path.join(chemin_shapes, nom_court_shape_avec_0)
        nom_court_prj_avec_0 = NOM_PROJET + EXTENSION_POUR_ZERO + EXTENSION_PRJ
        nom_prj_avec_0 = os.path.join(chemin_shapes, nom_court_prj_avec_0)
        # Todo: traiter le cas detail Y
        # cas avec 0, pas de demande de synthese
        physiocap_shapefile( nom_shape_avec_0, nom_prj_avec_0, nom_csv_avec_0)
        physiocap_log ("Creation du shapefile avec 0 en L93" + nom_court_shape_avec_0)
        
        physiocap_log ( u"Fin de la création des 2 shapes")
        
        
        # Fin 
        physiocap_log ( u"Fin de la foire")
        return "OK" 

