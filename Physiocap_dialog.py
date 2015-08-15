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
        physiocap_open_file, physiocap_csv_to_shapefile, physiocap_fichier_histo, \
        physiocap_filtrer       

from PyQt4 import QtGui, uic
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import *
from qgis.gui import *
import os 
import platform

##if platform.system() == 'Windows':
##    import win32api
    
import glob
import shutil
import time  

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
FORMAT_VECTEUR = [ "ESRI Shapefile", "postgres", "memory"]
# Répertoires des sources et de concaténation en fichiers texte
REPERTOIRE_SOURCES = "fichiers_sources"
SUFFIXE_BRUT_CSV = "_RAW.csv"
EXTENSION_MID = "*.MID"
REPERTOIRE_TEXTES = "fichiers_texte"
REPERTOIRE_HISTO = "histogrammes"
REPERTOIRE_SHAPEFILE = "shapefile"
PROJECTION = "L93"
EXTENSION_SHP = "_" + PROJECTION + ".shp"
EXTENSION_POUR_ZERO = "_0"
EXTENSION_PRJ = "_" + PROJECTION + ".prj"

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
        # TODO: V0.2 Reprendre ces infos dans la sauvegarde
        # ou .ini voir configurations ou "~plugin/.physiocap"
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
        # Remplissage de la liste de FORMAT_VECTEUR 
        if len( FORMAT_VECTEUR) == 0:
            self.fieldComboFormats.clear( )
            physiocap_error( u"Pas de liste des formats de vecteurs pré défini")
        else:
            self.fieldComboFormats.clear( )
            self.fieldComboFormats.addItems( FORMAT_VECTEUR )
        self.fieldComboFormats.setCurrentIndex( 0)   
                              
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
                                        
        # Cas détail vignoble
        details = "NO"
        if self.checkBoxInfoVignoble.isChecked():
            details = "YES"
            physiocap_log(u"Les détails du vignoble sont précisées")

        # Todo: V0.2 Assert sur les variables saisies ou QT confiance
####    NO !    self.assertEqual( "xxx", "xxx")            
        # Création des repertoires et des resultats de synthese
        retour = self.creer_donnees_resultats( details)
        if retour != 0:
            physiocap_error(u"Erreur bloquante : Physiocap n'a pas correctement terminé son analyse")
            QMessageBox.information( self, "Physiocap",
                                   self.tr( u"Physiocap n'a pas correctement terminé son analyse" ) )
            self.reject()
        else:
            physiocap_log(u"Physiocap a terminé son analyse.")
        return 0

    # Repertoire données brutes :
    def lecture_repertoire_donnees_brutes( self):
        """Catch directory for raw data"""
        # TODO: V0.4 Faire traduction du titre self.?iface.tr("Répertoire des données brutes")
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
    def creer_donnees_resultats( self, details = "NO"):
        """ Récupération des paramètres saisies et 
        creation de l'arbre "soure" "texte" et du fichier "resultats"
        Ce sont les résultats de l'analyse filtration des données brutes"""
        
        # Récupérer les paramètres saisies
        REPERTOIRE_DONNEES_BRUTES = self.lineEditDirectoryPhysiocap.text()
        NOM_PROJET = self.lineEditProjet.text()
        minVitesse = float( self.doubleSpinBoxMinVitesse.value())
        mindiam = float( self.spinBoxMinDiametre.value())
        maxdiam = float( self.spinBoxMaxDiametre.value())
        max_sarments_metre = float( self.spinBoxMaxSarmentsParMetre.value())
        physiocap_log(u"Paramètres choisis min diametre : " + str(mindiam) + " max diametre : " + str(maxdiam))

        if details == "YES":
            interrangs = float( self.spinBoxInterrangs.value())
            interceps = float( self.spinBoxInterceps.value())
            hauteur = float( self.spinBoxHauteur.value())
            densite = float( self.doubleSpinBoxDensite.value())
            leCepage = self.fieldComboCepage.currentText()
            laTaille = self.fieldComboTaille.currentText()
            
        # Vérification de l'existance ou création du répertoire projet
        chemin_projet = os.path.join(REPERTOIRE_DONNEES_BRUTES, NOM_PROJET)
        if not (os.path.exists( chemin_projet)):
            try :
                os.mkdir( chemin_projet)
            except :
                return physiocap_error(u"Problème lors de la création du répertoire projet: " + 
                chemin_projet)
        else:
            # le répertoire existant est renommé en ~
            nouveau_chemin_projet = chemin_projet + "~"
            try :
                if os.path.exists( nouveau_chemin_projet):
                    # on détruit le "projet~" pre-existant 
                    shutil.rmtree( nouveau_chemin_projet)
                os.rename( chemin_projet, nouveau_chemin_projet)
                os.mkdir( chemin_projet)
            except :
                return physiocap_error(u"Problème lors du changement de nom du répertoire projet: " + 
                chemin_projet + " avec le suffixe ~" + nouveau_chemin_projet)           
                 
        # Verification de l'existance ou création du répertoire des sources MID et fichier csv
        chemin_sources = os.path.join(chemin_projet, REPERTOIRE_SOURCES)
        if not (os.path.exists( chemin_sources)):
            try :
                os.mkdir( chemin_sources)
            except :
                return physiocap_error(u"Problème lors de la création du répertoire des sources: " + 
                chemin_sources)
        
        # Fichier de concaténations CSV des résultats bruts        
        nom_court_csv_concat = NOM_PROJET + SUFFIXE_BRUT_CSV
        nom_csv_concat = os.path.join(chemin_sources, nom_court_csv_concat)
        if os.path.isfile( nom_csv_concat):
            os.remove( nom_csv_concat)
        try :
            csv_concat = open(nom_csv_concat, "w")
        except :
            return physiocap_error(u"Problème lors de la création du fichier concaténé .csv: " + 
            nom_court_csv_concat)
            
        # Création du fichier concaténé
        nom_fichiers_recherches = os.path.join(REPERTOIRE_DONNEES_BRUTES, EXTENSION_MID)
        #physiocap_log(u"Chemin MID: " + nom_fichiers_recherches)
        
        # Todo: V0.2 ? choisir parmi les MID
        # Assert le nombre de MID > 0
        # le Tri pour retombé dans l'ordre de Physiocap_V8
        listeTriee = sorted(glob.glob( nom_fichiers_recherches))
        if len( listeTriee) == 0:
            aText = u"Erreur génante : pas de fichier MID en entrée à traiter..."
            physiocap_log( aText)
            return physiocap_error( aText)
        for mid in listeTriee:
            shutil.copyfileobj(open(mid, "r"), csv_concat)
            # et copie des MID
            shutil.copy(mid,chemin_sources)
        csv_concat.close()

        # Todo: V0.2 ?Remplacer le fichier synthese par un ecran du plugin           
        # Todo: V0.2 Assert Trouver les lignes de données invalides (trop longue, sans 58 virgules ... etc...
        # Création la première partie du fichier de synthèse
        nom_fichier_synthese = os.path.join(chemin_projet, FICHIER_RESULTAT)
        try :
            fichier_synthese = open(nom_fichier_synthese, "w")
        except :
            return physiocap_error(u"Problème lors de la création du fichier de synthese: " + 
            nom_fichier_synthese)
        fichier_synthese.write("SYNTHESE PHYSIOCAP\n\n")
        fichier_synthese.write("Fichier généré le : ")
        a_time = time.strftime("%d/%m/%y %H:%M\n",time.localtime())
        fichier_synthese.write(a_time)
        fichier_synthese.write("\nPARAMETRES SAISIS ")
        
        physiocap_log ( u"Fin de la création csv et début de synthèse")
       
        # Assert le fichier de données n'est pas vide
        if os.path.getsize(nom_csv_concat ) == 0 :
            msg =u"Le fichier " + nom_court_csv_concat + u" a une taille nulle !"
            physiocap_message_box( self, msg)
            # Todo: V0.4 Assert verifier si fichiers fermés
            return physiocap_error( msg)

        # Verification de l'existance ou création du répertoire textes
        chemin_textes = os.path.join(chemin_projet, REPERTOIRE_TEXTES)
        if not (os.path.exists( chemin_textes)):
            try :
                os.mkdir( chemin_textes)
            except :
                return physiocap_error(u"Problème lors de la création du répertoire des fichiers textes: " + 
                chemin_textes)
                       
        # Ouverture du fichier des diamètres     
        nom_court_fichier_diametre = "diam" + SUFFIXE_BRUT_CSV
        nom_fichier_diametre = os.path.join(chemin_textes, nom_court_fichier_diametre)
        if os.path.isfile( nom_fichier_diametre):
            os.remove( nom_fichier_diametre)
        try :
            histo_diametre = open(nom_fichier_diametre, "w")
        except :
            return physiocap_error(u"Problème lors de la création du fichier des diamètres: " + 
            nom_fichier_diametre)
        
        # Todo: Appel fonction de creation de fichier
        nom_court_fichier_sarment = "nbsarm" + SUFFIXE_BRUT_CSV
        nom_fichier_sarment = os.path.join(chemin_textes, nom_court_fichier_sarment)
        histo_sarment = open(nom_fichier_sarment, "w")
        # Todo: V0.2 ? Supprimer le fichier erreur
        nom_court_fichier_erreur = "erreurs.csv"
        nom_fichier_error = os.path.join(chemin_textes, nom_court_fichier_erreur)
        erreur = open(nom_fichier_error,"w")
        # ouverture du fichier source
        csv_concat = open(nom_csv_concat, "r")
 
        # Appeler la fonction de traitement
        #################
        physiocap_fichier_histo( csv_concat, histo_diametre, \
                                histo_sarment, erreur)
        #################
        # Fermerture des fichiers
        csv_concat.close()
        histo_diametre.close()
        histo_sarment.close()
        erreur.close()

        physiocap_log ( u"Fin de la création fichier pour histogramme")

        # Création des csv
        nom_court_csv_sans_0 = NOM_PROJET + "_OUT.csv"
        nom_csv_sans_0 = os.path.join(chemin_textes, nom_court_csv_sans_0)
        csv_sans_0 = open(nom_csv_sans_0, "w")

        nom_court_csv_avec_0 = NOM_PROJET + "_OUT0.csv"
        nom_csv_avec_0 = os.path.join(chemin_textes, nom_court_csv_avec_0)
        csv_avec_0 = open(nom_csv_avec_0, "w")
        
        nom_court_fichier_diametre_filtre = "diam_FILTERED.csv"
        nom_fichier_diametre_filtre = os.path.join(chemin_textes, nom_court_fichier_diametre_filtre)
        diametre_filtre = open(nom_fichier_diametre_filtre, "w")

        # Ouverture du fichier source
        csv_concat = open(nom_csv_concat, "r")       
        erreur = open(nom_fichier_error,"a")

        # Filtrage des données PHysiocap
        #################
        if details == "NO":
            interrangs = 1
            interceps = 1 
            densite = 1
            hauteur = 1        
        retour = physiocap_filtrer( csv_concat, csv_sans_0, csv_avec_0, \
                    diametre_filtre, nom_fichier_synthese, erreur, \
                    mindiam, maxdiam, max_sarments_metre, details,
                    interrangs, interceps, densite, hauteur)
        #################
        # Fermeture du fichier destination
        csv_sans_0.close()
        csv_avec_0.close()
        diametre_filtre.close()
        erreur.close()
        # Fermerture du fichier source
        csv_concat.close()  
        
        if retour != 0:
            return physiocap_error(u"Erreur bloquante : problème lors du filtrage des données de : " + 
                    nom_court_csv_concat)  
                                       
        # Todo: V0.2 Assert taille du diametre fitré non nulle
        # Todo: V0.2 Assert pour fichiers csv c'est au moins 2 lignes
        
        # On écrit dans le fichiers résultats les paramètres du modéle
        fichier_synthese = open(nom_fichier_synthese, "a")
        if details == "NO":
            fichier_synthese.write("\nAucune information parcellaire saisie\n")
        else:
            fichier_synthese.write("\n")
            fichier_synthese.write("Cepage : %s\n" %leCepage)
            fichier_synthese.write("Type de taille : %s\n" %laTaille)        
            fichier_synthese.write("Hauteur de végétation : %s cm\n" %hauteur)
            fichier_synthese.write("Densité des bois de taille : %s \n" %densite)
            fichier_synthese.write("Ecartement entre rangs : %s cm\n" %interrangs)
            fichier_synthese.write("Ecartement entre ceps : %s cm\n" %interceps)        

        fichier_synthese.write("\n")
        fichier_synthese.write("Nombre de sarments max au mètre linéaire: %s \n" %max_sarments_metre)
        fichier_synthese.write("Diamètre minimal : %s mm\n" %mindiam)
        fichier_synthese.write("Diamètre maximal : %s mm\n" %maxdiam)
        fichier_synthese.close()
    

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
        # Si le shape existe dejà il faut le détruire
        if os.path.isfile( nom_shape_sans_0):
            physiocap_log ( u"Le shape file existant déjà, il est détruit.")
            os.remove( nom_shape_sans_0)            

        # cas sans 0, on demande la synthese en passant le nom du fichier
        retour = physiocap_csv_to_shapefile( nom_csv_sans_0, nom_shape_sans_0, nom_prj_sans_0, 
                nom_fichier_synthese, details)
        if retour != 0:
            return physiocap_error(u"Erreur bloquante : problème lors de la création du shapefile : " + 
                nom_court_shape_sans_0)                
        
        # Création des shapes avec 0
        nom_court_shape_avec_0 = NOM_PROJET + EXTENSION_POUR_ZERO + EXTENSION_SHP
        nom_shape_avec_0 = os.path.join(chemin_shapes, nom_court_shape_avec_0)
        nom_court_prj_avec_0 = NOM_PROJET + EXTENSION_POUR_ZERO + EXTENSION_PRJ
        nom_prj_avec_0 = os.path.join(chemin_shapes, nom_court_prj_avec_0)
        # Si le shape existe dejà il faut le détruire
        if os.path.isfile( nom_shape_avec_0):
            physiocap_log ( u"Le shape file existant déjà, il est détruit.")
            os.remove( nom_shape_avec_0) 
            
        # cas avec 0, pas de demande de synthese
        retour = physiocap_csv_to_shapefile( nom_csv_avec_0, nom_shape_avec_0, nom_prj_avec_0, 
            "NO", details)
        if retour != 0:
            return physiocap_error(u"Erreur bloquante : problème lors de la création du shapefile : " + 
                    nom_court_shape_avec_0) 
                              
        # Affichage des deux shapes dans Qgis
        for s,n in [ (nom_shape_sans_0, nom_court_shape_sans_0) , 
                     (nom_shape_avec_0, nom_court_shape_avec_0)]:
            vector = QgsVectorLayer( s, n, 'ogr')
            QgsMapLayerRegistry.instance().addMapLayer( vector)
            
        # Todo: V0.2 ? Récupérer des styles pour chaque style de shape
        
        # Fin 
        physiocap_log ( u"Fin de la synthèse Physiocap : sans erreur")
        return 0 

