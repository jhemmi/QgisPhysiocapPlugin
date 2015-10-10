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
        physiocap_rename_create_dir, physiocap_open_file, \
        physiocap_csv_to_shapefile, physiocap_assert_csv, \
        physiocap_fichier_histo, physiocap_histo, physiocap_filtrer       

from PyQt4 import QtGui, uic
from PyQt4.QtCore import QSettings
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
NOM_PROJET = "VotreProjetPhysiocap"
PHYSIOCAP_NOM = "Physiocap"
PHYSIOCAP_VERSION = PHYSIOCAP_NOM + "_V1_0"

# Listes de valeurs
CEPAGES = [ "CHARDONNAY", "MERLOT", "NEGRETTE", "PINOT NOIR", "PINOT MEUNIER"]
TAILLES = [ "Chablis", "Guyot simple", "Guyot double", "Cordon de Royat", "Cordon libre" ]
FORMAT_VECTEUR = [ "ESRI Shapefile"] #, "postgres", "memory"]

# Répertoires des sources et de concaténation en fichiers texte
FICHIER_RESULTAT = NOM_PROJET +"_resultat.txt"
REPERTOIRE_SOURCES = "fichiers_sources"
SUFFIXE_BRUT_CSV = "_RAW.csv"
EXTENSION_MID = "*.MID"
PROJECTION_MID = "L93"
REPERTOIRE_TEXTES = "fichiers_texte"
TRACE_HISTO = "YES"
REPERTOIRE_HISTOS = "histogrammes"
FICHIER_HISTO_SARMENT = "histogramme_SARMENT_RAW.png"
FICHIER_HISTO_DIAMETRE = "histogramme_DIAMETRE_RAW.png"
FICHIER_HISTO_DIAMETRE_FILTRE = "histogramme_DIAM_FILTERED.png"

REPERTOIRE_SHAPEFILE = "shapefile"
PROJECTION_SHP = "L93"
EXTENSION_SHP = "_" + PROJECTION_SHP + ".shp"
EXTENSION_POUR_ZERO = "_0"
EXTENSION_PRJ = "_" + PROJECTION_SHP + ".prj"

##FICHIER_SAUVE_PARAMETRES = os.path.join(
##                    os.path.dirname(__file__), 
##                    '.physiocap')
##                    
# Exceptions Physiocap 
ERREUR_EXCEPTION = u"Physiocap n'a pas correctement terminé son analyse"
TAUX_LIGNES_ERREUR= 20

class physiocap_exception( Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)
    
class physiocap_exception_rep( physiocap_exception):
    pass
    
class physiocap_exception_fic( physiocap_exception):
    pass

class physiocap_exception_csv( physiocap_exception):
    pass

class physiocap_exception_err_csv( physiocap_exception):
    pass
    
class physiocap_exception_mid( physiocap_exception):
    pass
    
class physiocap_exception_no_mid( ):
    pass
     
class physiocap_exception_params( physiocap_exception):
    pass
    
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

        ###############
        # Récuperation dans les settings (derniers parametres saisies)
        ###############
        self.settings= QSettings(PHYSIOCAP_NOM, PHYSIOCAP_VERSION)
        # Initialisation des parametres à partir des settings
        self.lineEditProjet.setText( self.settings.value("Physiocap/projet", 
            NOM_PROJET ))
        self.lineEditDirectoryPhysiocap.setText(  self.settings.value("Physiocap/repertoire",
            REPERTOIRE_DONNEES_BRUTES))
        
        # Remplissage de la liste de cépage
        self.fieldComboCepage.setCurrentIndex( 0)
        if len( CEPAGES) == 0:
            self.fieldComboCepage.clear( )
            physiocap_error( u"Pas de liste de cépage pré défini")
        else:
            self.fieldComboCepage.clear( )
            self.fieldComboCepage.addItems( CEPAGES )
            # Retrouver le cépage de  settings
            i=0
            leCepage = self.settings.value("Physiocap/leCepage", "xx")
            for cepage in CEPAGES:
                if ( cepage == leCepage):
                    self.fieldComboCepage.setCurrentIndex( i)
                i=i+1
                
        # Remplissage de la liste de taille
        self.fieldComboTaille.setCurrentIndex( 0)        
        if len( TAILLES) == 0:
            self.fieldComboTaille.clear( )
            physiocap_error( u"Pas de liste de mode de taille pré défini")
        else:
            self.fieldComboTaille.clear( )
            self.fieldComboTaille.addItems( TAILLES )
            # Retrouver la taille de  settings
            i=0
            laTaille = self.settings.value("Physiocap/laTaille", "xx") 
            for taille in TAILLES:
                if ( taille == laTaille):
                    self.fieldComboTaille.setCurrentIndex( i)
                i=i+1
        
        # Remplissage de la liste de FORMAT_VECTEUR 
        self.fieldComboFormats.setCurrentIndex( 0)   
        if len( FORMAT_VECTEUR) == 0:
            self.fieldComboFormats.clear( )
            physiocap_error( u"Pas de liste des formats de vecteurs pré défini")
        else:
            self.fieldComboFormats.clear( )
            self.fieldComboFormats.addItems( FORMAT_VECTEUR )
            # Retrouver le format de  settings
            i=0
            leFormat = self.settings.value("Physiocap/leFormat", "xx") 
            for unFormat in FORMAT_VECTEUR:
                if ( unFormat == leFormat):
                    self.fieldComboTaille.setCurrentIndex( i)
                i=i+1
                            
        # Remplissage des autre parametre à partir des settings
        self.doubleSpinBoxMinVitesse.setValue( float( self.settings.value("Physiocap/minVitesse", 1 )))
        self.spinBoxMinDiametre.setValue( int( self.settings.value("Physiocap/mindiam", 2 )))
        self.spinBoxMaxDiametre.setValue( int( self.settings.value("Physiocap/maxdiam", 28 )))
        self.spinBoxMaxSarmentsParMetre.setValue( int( self.settings.value("Physiocap/max_sarments_metre", 25 )))
        if (self.settings.value("Physiocap/details") == "YES"):
            self.checkBoxInfoVignoble.setChecked( Qt.Checked)
        else:
            self.checkBoxInfoVignoble.setChecked( Qt.Unchecked)

        self.spinBoxInterrangs.setValue( int( self.settings.value("Physiocap/interrangs", 110 )))
        self.spinBoxInterceps.setValue( int( self.settings.value("Physiocap/interceps", 100 )))
        self.spinBoxHauteur.setValue( int( self.settings.value("Physiocap/hauteur", 90 )))
        self.doubleSpinBoxDensite.setValue( float( self.settings.value("Physiocap/densite", 0.9 )))
 
       # TODO: V1.5 ? Recherche du projet courant ?
        
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
        # Vérifier les valeurs saisies
        # QT confiance et initilaisation par Qsettings sert d'assert sur la
        # cohérence des variables saisies

        if self.lineEditDirectoryPhysiocap.text() == "":
            physiocap_error( u"Pas de répertoire de donnée spécifié")
            return physiocap_message_box( self, 
                self.tr( u"Pas de répertoire de données brutes spécifié" ),
                "information")
        if self.lineEditProjet.text() == "":
            physiocap_error( u"Pas de nom de projet spécifié")
            return physiocap_message_box( self,
                self.tr( u"Pas de nom de projet spécifié" ),
                "information")
                                        

        # Sauvergarde des saisies dans les settings
        self.settings= QSettings( PHYSIOCAP_NOM, PHYSIOCAP_VERSION)
        self.settings.setValue("Physiocap/projet", self.lineEditProjet.text() )
        self.settings.setValue("Physiocap/repertoire", self.lineEditDirectoryPhysiocap.text() )
        self.settings.setValue("Physiocap/minVitesse", float( self.doubleSpinBoxMinVitesse.value()))
        self.settings.setValue("Physiocap/mindiam", float( self.spinBoxMinDiametre.value()))
        self.settings.setValue("Physiocap/maxdiam", float( self.spinBoxMaxDiametre.value()))

        # Cas détail vignoble
        details = "NO"
        if self.checkBoxInfoVignoble.isChecked():
            details = "YES"
            physiocap_log(u"Les détails du vignoble sont précisées")
        self.settings.setValue("Physiocap/details", details)
        self.settings.setValue("Physiocap/max_sarments_metre", float( self.spinBoxMaxSarmentsParMetre.value()))
        self.settings.setValue("Physiocap/interrangs", float( self.spinBoxInterrangs.value()))
        self.settings.setValue("Physiocap/interceps", float( self.spinBoxInterceps.value()))
        self.settings.setValue("Physiocap/hauteur", float( self.spinBoxHauteur.value()))
        self.settings.setValue("Physiocap/densite", float( self.doubleSpinBoxDensite.value()))
        self.settings.setValue("Physiocap/leCepage", self.fieldComboCepage.currentText())
        self.settings.setValue("Physiocap/laTaille", self.fieldComboTaille.currentText())



        # ########################################
        # Gestion de capture des erreurs Physiocap
        # ########################################
        try:
            # Création des répertoires et des résultats de synthèse
            retour = self.creer_donnees_resultats( details)
        except physiocap_exception_rep as e:
            physiocap_log( ERREUR_EXCEPTION + ". Consultez le journal Physiocap Erreur",
                "WARNING")
            physiocap_error( ERREUR_EXCEPTION)
            physiocap_error(u"Erreur bloquante lors de la création du répertoire : " + str( e),
                "CRITICAL")
            return physiocap_message_box( self, self.tr( ERREUR_EXCEPTION + "\n" + \
                u"Erreur bloquante lors de la création du répertoire : " + str( e)),
                "information" )
        
        except physiocap_exception_err_csv as e:
            physiocap_log( ERREUR_EXCEPTION + ". Consultez le journal Physiocap Erreur",
                "WARNING")
            physiocap_error( ERREUR_EXCEPTION)
            physiocap_error(u"Trop d'erreurs " + str( e) + u" dans les données brutes",
                "CRITICAL")
            return physiocap_message_box( self, self.tr( ERREUR_EXCEPTION + "\n" + \
                u"Trop d'erreurs " + str( e) + u" dans les données brutes"),
                "information" )
        
        except physiocap_exception_fic as e:
            physiocap_log( ERREUR_EXCEPTION + ". Consultez le journal Physiocap Erreur",
                "WARNING")
            physiocap_error( ERREUR_EXCEPTION)
            physiocap_error(u"Erreur bloquante lors de la création du fichier : " + str( e),
                "CRITICAL")
            return physiocap_message_box( self, self.tr( ERREUR_EXCEPTION + "\n" + \
                u"Erreur bloquante lors de la création du fichier : " + str( e)),
                "information" )
        except physiocap_exception_csv as e:
            physiocap_log( ERREUR_EXCEPTION + ". Consultez le journal Physiocap Erreur",
                "WARNING")
            physiocap_error( ERREUR_EXCEPTION)
            physiocap_error(u"Erreur bloquante lors de la création du fichier csv : " + str( e),
                "CRITICAL")
            return physiocap_message_box( self, self.tr( ERREUR_EXCEPTION + "\n" + \
                u"Erreur bloquante lors de la création du fichier cvs : " + str( e)),
                "information" )

        except physiocap_exception_mid as e:
            physiocap_log( ERREUR_EXCEPTION + ". Consultez le journal Physiocap Erreur",
                "WARNING")
            physiocap_error( ERREUR_EXCEPTION)
            physiocap_error(u"Erreur bloquante lors de la copie du fichier mid : " + str( e),
                "CRITICAL")
            return physiocap_message_box( self, self.tr( ERREUR_EXCEPTION + "\n" + \
                u"Erreur bloquante lors de la copie du fichier mid : " + str( e)),
                "information" )
        except physiocap_exception_no_mid:
            physiocap_log( ERREUR_EXCEPTION + ". Consultez le journal Physiocap Erreur",
                "WARNING")
            physiocap_error( ERREUR_EXCEPTION)
            physiocap_error(u"Erreur bloquante : aucun fichier mid à traiter",
                "CRITICAL")
            return physiocap_message_box( self, self.tr( ERREUR_EXCEPTION + "\n" + \
                u"Erreur bloquante : aucun fichier mid à traiter"),
                "information" )
        # On remonte les autres exceptions
        except:
            raise
        finally:
            self.reject()
        # ########################################
        # Fin de capture des erreurs Physiocap
        # #########################################
        
        physiocap_log(u"Physiocap a terminé son analyse.")

    
    # Repertoire données brutes :
    def lecture_repertoire_donnees_brutes( self):
        """Catch directory for raw data"""
        # TODO: Vx ? Faire traduction du titre self.?iface.tr("Répertoire des données brutes")
        dirName = QFileDialog.getExistingDirectory( self, u"Répertoire des données brutes",
                                                 REPERTOIRE_DONNEES_BRUTES,
                                                 QFileDialog.ShowDirsOnly
                                                 | QFileDialog.DontResolveSymlinks);
        if len( dirName) == 0:
          return
        self.lineEditDirectoryPhysiocap.setText( dirName )
        
    
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
            try:
                os.mkdir( chemin_projet)
            except:
                raise physiocap_exception_rep( NOM_PROJET)
        else:
            # Le répertoire existant est renommé en (+1)
            try: 
                chemin_projet = physiocap_rename_create_dir( chemin_projet)
            except:
                return
            
        # Verification de l'existance ou création du répertoire des sources MID et fichier csv
        chemin_sources = os.path.join(chemin_projet, REPERTOIRE_SOURCES)
        if not (os.path.exists( chemin_sources)):
            try:
                os.mkdir( chemin_sources)
            except:
                raise physiocap_exception_rep( REPERTOIRE_SOURCES)
                    
        # Fichier de concaténations CSV des résultats bruts        
        nom_court_csv_concat = NOM_PROJET + SUFFIXE_BRUT_CSV
        try:
            nom_csv_concat, csv_concat = physiocap_open_file( nom_court_csv_concat, chemin_sources, "w")
        except physiocap_exception_fic as e:
            raise physiocap_exception_csv( nom_court_csv_concat)
            
        # Création du fichier concaténé
        nom_fichiers_recherches = os.path.join(REPERTOIRE_DONNEES_BRUTES, EXTENSION_MID)
        
        # Todo: Vx ? choisir parmi les MID
        # Assert le nombre de MID > 0
        # le Tri pour retomber dans l'ordre de Physiocap_V8
        listeTriee = sorted(glob.glob( nom_fichiers_recherches))
        if len( listeTriee) == 0:
            raise physiocap_exception_no_mid()
        for mid in listeTriee:
            try:
                shutil.copyfileobj(open(mid, "r"), csv_concat)
                # et copie des MID
                shutil.copy(mid,chemin_sources)
            except :
                raise physiocap_exception_mid( mid)
        csv_concat.close()

        # Assert le fichier de données n'est pas vide
        if os.path.getsize( nom_csv_concat ) == 0 :
            uMsg =u"Le fichier " + nom_court_csv_concat + u" a une taille nulle !"
            physiocap_message_box( self, uMsg)
            return physiocap_error( uMsg)
        

        # Todo: Vx ? Remplacer le fichier synthese par un ecran du plugin           
        # Création la première partie du fichier de synthèse
        nom_fichier_synthese, fichier_synthese = physiocap_open_file( FICHIER_RESULTAT, chemin_projet , "w")
        fichier_synthese.write("SYNTHESE PHYSIOCAP\n\n")
        fichier_synthese.write("Fichier généré le : ")
        a_time = time.strftime("%d/%m/%y %H:%M\n",time.localtime())
        fichier_synthese.write(a_time)
        physiocap_log ( u"Fin de la création csv et début de synthèse")
       
        # Verification de l'existance ou création du répertoire textes
        chemin_textes = os.path.join(chemin_projet, REPERTOIRE_TEXTES)
        if not (os.path.exists( chemin_textes)):
            try :
                os.mkdir( chemin_textes)
            except :
                raise physiocap_exception_rep( REPERTOIRE_TEXTES)
                       
        # Ouverture du fichier des diamètres     
        nom_court_fichier_diametre = "diam" + SUFFIXE_BRUT_CSV
        nom_data_histo_diametre, data_histo_diametre = physiocap_open_file( nom_court_fichier_diametre, 
            chemin_textes)
        
        # Appel fonction de creation de fichier
        nom_court_fichier_sarment = "nbsarm" + SUFFIXE_BRUT_CSV
        nom_data_histo_sarment, data_histo_sarment = physiocap_open_file( nom_court_fichier_sarment, 
            chemin_textes)

        # Todo: V1.5 ? Supprimer le fichier erreur
        nom_fichier_erreur, erreur = physiocap_open_file( "erreurs.csv" , chemin_textes)
    
        # ouverture du fichier source
        csv_concat = open(nom_csv_concat, "r")
        # Appeler la fonction de vérification du format du fichier csv
        # Si plus de 20 % d'erreur exception est monté
        try:
            pourcentage_erreurs = physiocap_assert_csv( csv_concat, erreur)
            if ( pourcentage_erreurs > TAUX_LIGNES_ERREUR):
                fichier_synthese.write("\nTrop d'erreurs dans les données brutes")
                raise physiocap_exception_err_csv( pourcentage_erreurs)
        except:
            raise
        
        fichier_synthese.write("\nPARAMETRES SAISIS ")
        
        if os.path.getsize( nom_csv_concat ) == 0 :
            uMsg =u"Le fichier " + nom_court_csv_concat + u" a une taille nulle !"
            physiocap_message_box( self, uMsg)
            return physiocap_error( uMsg)

        # ouverture du fichier source
        csv_concat = open(nom_csv_concat, "r")

        # Appeler la fonction de traitement
        #################
        physiocap_fichier_histo( csv_concat, data_histo_diametre,    
                        data_histo_sarment, erreur)
        #################
        # Fermerture des fichiers
        csv_concat.close()
        data_histo_diametre.close()
        data_histo_sarment.close()
        erreur.close()

        # Verification de l'existance ou création du répertoire des sources MID et fichier csv
        chemin_histos = os.path.join(chemin_projet, REPERTOIRE_HISTOS)
        if not (os.path.exists( chemin_histos)):
            try:
                os.mkdir( chemin_histos)
            except:
                raise physiocap_exception_rep( REPERTOIRE_HISTOS)

        # creation d'un histo
        nom_data_histo_sarment, data_histo_sarment = physiocap_open_file( nom_court_fichier_sarment, chemin_textes, 'r')
        nom_histo_sarment, histo_sarment = physiocap_open_file( FICHIER_HISTO_SARMENT, chemin_histos)
        name = nom_histo_sarment
        if (TRACE_HISTO == "YES"):
            physiocap_histo( data_histo_sarment, name, 0, 80, "SARMENT au m", "FREQUENCE en %", "HISTOGRAMME NBSARM AVANT TRAITEMENT")
        histo_sarment.close()
        
        nom_data_histo_diametre, data_histo_diametre = physiocap_open_file( nom_court_fichier_diametre, chemin_textes, 'r')
        nom_histo_diametre, histo_diametre = physiocap_open_file( FICHIER_HISTO_DIAMETRE, chemin_histos)
        name = nom_histo_diametre
        if (TRACE_HISTO == "YES"):
            physiocap_histo( data_histo_diametre, name, 0, 30, "DIAMETRE en mm", "FREQUENCE en %", "HISTOGRAMME DIAMETRE AVANT TRAITEMENT")
        histo_diametre.close()        
        
        physiocap_log ( u"Fin de la création des histogrammes bruts")

        # Création des csv
        nom_court_csv_sans_0 = NOM_PROJET + "_OUT.csv"
        nom_csv_sans_0, csv_sans_0 = physiocap_open_file( 
            nom_court_csv_sans_0, chemin_textes)

        nom_court_csv_avec_0 = NOM_PROJET + "_OUT0.csv"
        nom_csv_avec_0, csv_avec_0 = physiocap_open_file( 
            nom_court_csv_avec_0, chemin_textes)
       
        nom_court_fichier_diametre_filtre = "diam_FILTERED.csv"
        nom_fichier_diametre_filtre, diametre_filtre = physiocap_open_file( 
            nom_court_fichier_diametre_filtre, chemin_textes )

        # Ouverture du fichier source et re ouverture du ficheir erreur
        csv_concat = open(nom_csv_concat, "r")       
        erreur = open(nom_fichier_erreur,"a")

        # Filtrage des données Physiocap
        #################
        if details == "NO":
            interrangs = 1
            interceps = 1 
            densite = 1
            hauteur = 1        
        retour_filtre = physiocap_filtrer( csv_concat, csv_sans_0, csv_avec_0, \
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

        if retour_filtre != 0:
            return physiocap_error(u"Erreur bloquante : problème lors du filtrage des données de : " + 
                    nom_court_csv_concat)  

        # Histo apres filtatration
        nom_fichier_diametre_filtre, diametre_filtre = physiocap_open_file( 
            nom_court_fichier_diametre_filtre, chemin_textes , "r")
        nom_histo_diametre_filtre, histo_diametre = physiocap_open_file( FICHIER_HISTO_DIAMETRE_FILTRE, chemin_histos)

        if (TRACE_HISTO == "YES"):
            physiocap_histo( diametre_filtre, nom_histo_diametre_filtre, 0, 30, "DIAMETRE en mm", "FREQUENCE en %", "HISTOGRAMME DIAMETRE APRES TRAITEMENT")
        diametre_filtre.close()        
                                              
        # On écrit dans le fichiers résultats les paramètres du modéle
        fichier_synthese = open(nom_fichier_synthese, "a")
        if details == "NO":
            fichier_synthese.write("\nAucune information parcellaire saisie\n")
        else:
            fichier_synthese.write("\n")
            msg = "Cépage : " + str( leCepage) + "\n"
            fichier_synthese.write( msg)
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
                raise physiocap_exception_rep( REPERTOIRE_SHAPEFILE)
               
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
                              
        # Récupérer des styles pour chaque shape
        dirTemplate = os.path.join( os.path.dirname(__file__), 'modeleQgis')       
        # Affichage des deux shapes dans Qgis
        for s,ti,te in [(nom_shape_sans_0, 'DIAMETRE', 'Diametre 6 quantilles.qml') , 
                        (nom_shape_sans_0, 'SARMENT', 'Sarments 4 Jenks.qml') , 
                        (nom_shape_avec_0, 'VITESSE', 'Vitesse.qml')]:
            vector = QgsVectorLayer( s, ti, 'ogr')
            QgsMapLayerRegistry.instance().addMapLayer( vector)
            leTemplate = os.path.join( dirTemplate, te)
            physiocap_log ( u"Physiocap le template : " + leTemplate )
            vector.loadNamedStyle( leTemplate)
            #self.vectorlayer_name.loadNamedStyle('path_to_qml_file')
            #layer.readSymbology(myDocRoot,errmsg)  
            
        # Fin 
        physiocap_log ( u"Fin de la synthèse Physiocap : sans erreur")
        return 0 

