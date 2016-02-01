# -*- coding: utf-8 -*-
"""
/***************************************************************************
 Physiocap_dialog
                                 A QGIS plugin
 Physiocap plugin helps analyse raw data from Physiocap in Qgis and 
 creates a synthesis of Physiocap measures' campaign
 Physiocap plugin permet l'analyse les données brutes de Physiocap dans Qgis et
 crée une synthese d'une campagne de mesures Physiocap
 
 Le module dialog gère la dynamique des dialogues, initialisation 
 et recupération des variables, sauvegarde des parametres.

 Les variables et fonctions sont nommées en Francais
 
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

from Physiocap_CIVC import physiocap_csv_vers_shapefile, physiocap_assert_csv, \
        physiocap_fichier_histo, physiocap_tracer_histo, physiocap_filtrer   

from Physiocap_tools import physiocap_message_box, physiocap_question_box, \
        physiocap_log_for_error, physiocap_log, physiocap_error, \
        physiocap_write_in_synthese, \
        physiocap_rename_existing_file, physiocap_rename_create_dir, physiocap_open_file, \
        physiocap_look_for_MID, physiocap_list_MID, physiocap_quel_uriname, \
        physiocap_get_uri_by_layer, physiocap_tester_uri, \
        physiocap_quelle_projection_demandee, physiocap_get_layer_by_ID

from Physiocap_inter import physiocap_fill_combo_poly_or_point, physiocap_moyenne_InterParcelles

from Physiocap_intra_interpolation import physiocap_interpolation_IntraParcelles

#from Physiocap_creer_arbre import physiocap_creer_donnees_resultats

from Physiocap_var_exception import *

from PyQt4 import QtGui, uic
from PyQt4.QtCore import QSettings
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import *
from qgis.gui import *

import glob
import os
import shutil
import time

# TODO : simplification comme cet example
## from PyQt4 import QtCore, QtGui
##from ui_attributepainter import Ui_AttributePainterForm
##
##
##class attributePainterDialog(QtGui.QWidget, Ui_AttributePainterForm):
##    def __init__(self, iface):
##        QtGui.QWidget.__init__(self)
##        self.setupUi(self)


FORM_CLASS, _ = uic.loadUiType(os.path.join( os.path.dirname(__file__), 'Physiocap_dialog_base.ui'))

class PhysiocapAnalyseurDialog(QtGui.QDialog, FORM_CLASS):
    def __init__(self, parent=None):
        """Constructeur."""
        super(PhysiocapAnalyseurDialog, self).__init__(parent)
        # Set up the user interface from Designer.
        # After setupUI you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)
        self.plugin_dir = os.path.dirname(__file__)  
        self.plugins_dir = os.path.dirname( self.plugin_dir)
        self.python_dir = os.path.dirname( self.plugins_dir)
        self.gis2_dir = os.path.dirname( self.python_dir)
        ## physiocap_log( u"Rep .gis2 " + str( self.gis2_dir))
       
        # Slot for boutons : certains sont dans UI
        ##self.buttonBox.button( QDialogButtonBox.Ok ).pressed.connect(self.accept)
        ##self.buttonBox.button( QDialogButtonBox.Cancel ).pressed.connect(self.reject)
        self.buttonBox.button( QDialogButtonBox.Help ).pressed.connect(self.demander_aide)
        self.buttonContribuer.pressed.connect(self.demander_contribution)
        # Slot pour données brutes
        self.toolButtonDirectoryPhysiocap.pressed.connect( self.lecture_repertoire_donnees_brutes )  
        # Slot pour le groupe vignoble
        self.checkBoxInfoVignoble.stateChanged.connect( self.bascule_details_vignoble)

       
        # Inter
        self.comboBoxPolygone.currentIndexChanged[int].connect( self.update_field_poly_list )
        self.ButtonInter.pressed.connect(self.moyenne_inter_parcelles)
        self.ButtonInterRefresh.pressed.connect(self.liste_inter_parcelles)
        self.groupBoxInter.setEnabled( False)
        
        # Intra        
        self.comboBoxPoints.currentIndexChanged[int].connect( self.update_points_choose_inter_intra )
        self.fieldComboIntra.currentIndexChanged[int].connect( self.min_max_field_intra_list )
        self.ButtonIntra.pressed.connect(self.interpolation_intra_parcelles)
        self.groupBoxIntra.setEnabled( False)
        self.ButtonIntra.setEnabled( False)
        
        # Slot pour les contours
        # self.toolButtonContours.pressed.connect( self.lecture_shape_contours )   
              
        machine = platform.system()
        #physiocap_log( self.trUtf8( "Votre machine tourne sous ") + machine)
        physiocap_log( self.trUtf8( "Votre machine tourne sous {0} ").\
            format( str( machine)))
        
        # Style sheet pour QProgressBar
        self.setStyleSheet( "QProgressBar {color:black; text-align:center; font-weight:bold; padding:2px;}"
           "QProgressBar:chunk {background-color:green; width: 10px; margin-left:1px;}")
        
        ###############
        # Récuperation dans les settings (derniers parametres saisies)
        ###############
        self.settings= QSettings(PHYSIOCAP_NOM, PHYSIOCAP_NOM)
        # Initialisation des parametres à partir des settings
        self.lineEditProjet.setText( self.settings.value("Physiocap/projet", 
            NOM_PROJET ))

##        self.lineEditContours.setText(  self.settings.value("Physiocap/contours",
##            SHAPE_CONTOURS))

        self.lineEditDirectoryPhysiocap.setText(  self.settings.value("Physiocap/repertoire",
            REPERTOIRE_DONNEES_BRUTES))
        if (self.settings.value("Physiocap/recursif") == "YES"):
            self.checkBoxRecursif.setChecked( Qt.Checked)
        else:
            self.checkBoxRecursif.setChecked( Qt.Unchecked)
        
        self.lineEditDernierProjet.setText( self.settings.value("Physiocap/dernier_repertoire",
            ""))    
            
        # Choisir radioButtonL93 ou radioButtonGPS
        laProjection = self.settings.value("Physiocap/laProjection", PROJECTION_L93)
        #physiocap_log( u"Projection récupérée " + laProjection)
        if ( laProjection == PROJECTION_GPS ):
            self.radioButtonGPS.setChecked(  Qt.Checked)
        else:
            #physiocap_log( u"Projection allumé L93 ==? " + laProjection)
            self.radioButtonL93.setChecked(  Qt.Checked)
            
        # Remettre vide le textEditSynthese
        self.textEditSynthese.clear()
        
        # Remplissage de la liste de cépage
        self.fieldComboCepage.setCurrentIndex( 0)
        if len( CEPAGES) == 0:
            self.fieldComboCepage.clear( )
            physiocap_error( self.trUtf8( "Pas de liste de cépage pré défini"))
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
            physiocap_error( self.trUtf8( "Pas de liste de mode de taille pré défini"))
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
            physiocap_error( self.trUtf8( "Pas de liste des formats de vecteurs pré défini"))
        else:
            self.fieldComboFormats.clear( )
            uri = physiocap_get_uri_by_layer( self)
            if uri != None:
                self.fieldComboFormats.addItems( FORMAT_VECTEUR )
            else:
                self.fieldComboFormats.addItem( FORMAT_VECTEUR[ 0] )
                self.fieldComboFormats.setEnabled( False)

             # Retrouver le format de  settings
            i=0
            self.fieldComboFormats.setCurrentIndex( 1)
            leFormat = self.settings.value("Physiocap/leFormat", "xx") 
            for unFormat in FORMAT_VECTEUR:
                if ( unFormat == leFormat):
                    self.fieldComboFormats.setCurrentIndex( i)
                i=i+1        

        # Remplissage de la liste de CHEMIN_TEMPLATES
        self.fieldComboThematiques.setCurrentIndex( 0)   
        if len( CHEMIN_TEMPLATES) == 0:
            self.fieldComboThematiques.clear( )
            aText = self.trUtf8( "Pas de répertoire de thématiques pré défini")
            physiocap_log( aText)
            physiocap_error( aText)
        else:
            leChoixDeThematiques = int( self.settings.value("Physiocap/leChoixDeThematiques", -1)) 
            # Cas inital
            CHEMIN_TEMPLATES_USER = []
            self.fieldComboThematiques.clear( )
            CHEMIN_TEMPLATES_USER.append( os.path.join( self.plugin_dir, CHEMIN_TEMPLATES[0]))
            CHEMIN_TEMPLATES_USER.append( os.path.join( self.gis2_dir, CHEMIN_TEMPLATES[1]))
            self.fieldComboThematiques.addItems( CHEMIN_TEMPLATES_USER )
            if ( leChoixDeThematiques == -1):
                self.fieldComboThematiques.setCurrentIndex( 0)                
            else:
                # Le combo a déjà été rempli, on retrouve le choix
                self.fieldComboThematiques.setCurrentIndex( leChoixDeThematiques)
             
        # Remplissage des autre parametre à partir des settings
        self.spinBoxMinDiametre.setValue( int( self.settings.value("Physiocap/mindiam", 2 )))
        self.spinBoxMaxDiametre.setValue( int( self.settings.value("Physiocap/maxdiam", 28 )))
        self.spinBoxMaxSarmentsParMetre.setValue( int( self.settings.value("Physiocap/max_sarments_metre", 25 )))
        if (self.settings.value("Physiocap/details") == "YES"):
            self.checkBoxInfoVignoble.setChecked( Qt.Checked)
            self.Vignoble.setEnabled( True)
        else:
            self.checkBoxInfoVignoble.setChecked( Qt.Unchecked)
            self.Vignoble.setEnabled( False)
        
        interrang = float( self.settings.value("Physiocap/interrangs", 110 ))
        intercep = float( self.settings.value("Physiocap/interceps", 100 ))
        self.spinBoxInterrangs.setValue( int( interrang))
        self.spinBoxInterceps.setValue( int( intercep))
        # Densité pied /ha
        self.calcul_densite()
##        densite = ""
##        if (interrang !=0) and ( intercep != 0):
##            densite = int (10000 / ((interrang/100) * (intercep/100)))
##        self.lineEditDensite.setText( str( densite))
##        
        self.spinBoxHauteur.setValue( int( self.settings.value("Physiocap/hauteur", 90 )))
        self.doubleSpinBoxDensite.setValue( float( self.settings.value("Physiocap/densite", 0.9 )))


        # Issue 29 : Pour appel de imaging pour comprendre si affichage histo est possible
        try :
            import PIL
            #physiocap_log( u"PIL Path : " + str( PIL.__path__))
            # version PIL n'est pas toujours dispo physiocap_log( u"PIL Version " + str(PIL.VERSION))
            #physiocap_log( u"PILLOW Version " + str(PIL.PILLOW_VERSION))
            #physiocap_log( u"PIL imaging " + str(PIL._imaging))
            from PIL import Image
            from PIL import _imaging
        except ImportError:
            #import sys
            #lePath = sys.path
            aText = self.trUtf8( "Le module image n'est pas accessible. ")
            aText = aText + self.trUtf8( "Vous ne pouvez pas visualiser les histogrammes ")
            physiocap_log( aText)
            physiocap_error( aText)
            self.settings.setValue("Physiocap/histogrammes", "NO")
            self.checkBoxHistogramme.setChecked( Qt.Unchecked)
            self.checkBoxHistogramme.setEnabled( False)
            aText = self.trUtf8( u'Physiocap : Votre installation QGIS ne permet pas du visualisation des histogrammes'\
                )
            physiocap_log( aText)
            physiocap_message_box( self, aText, "information")

        if (self.settings.value("Physiocap/histogrammes") == "YES"):
            self.checkBoxHistogramme.setChecked( Qt.Checked)
        else:
            self.checkBoxHistogramme.setChecked( Qt.Unchecked)
        # Pas d'histo avant calcul
        self.label_histo_sarment.setPixmap( QPixmap( FICHIER_HISTO_NON_CALCULE))
        self.label_histo_diametre_avant.setPixmap( QPixmap( FICHIER_HISTO_NON_CALCULE))
        self.label_histo_diametre_apres.setPixmap( QPixmap( FICHIER_HISTO_NON_CALCULE))
        
        # Les parametres Intra  
        self.spinBoxPower.setValue( float( self.settings.value("Physiocap/powerIntra", 2 )))
        self.spinBoxRayon.setValue( int( self.settings.value("Physiocap/rayonIntra", 12 )))
        self.spinBoxPixel.setValue( float( self.settings.value("Physiocap/pixelIntra", 1 )))
        self.spinBoxIsoMin.setValue( int( self.settings.value("Physiocap/isoMin", 1 )))
        self.spinBoxIsoMax.setValue( int( self.settings.value("Physiocap/isoMax", 1000 )))
        self.spinBoxNombreIso.setValue( int( self.settings.value("Physiocap/isoNombres", 5 )))
        # On initalise le nombre de distance Iso
        self.physiocap_iso_distance()
         
        if (self.settings.value("Physiocap/library") == "SAGA"):
            self.radioButtonSAGA.setChecked(  Qt.Checked)
            self.spinBoxPower.setEnabled( False)
        else:
            self.radioButtonGDAL.setChecked(  Qt.Checked)
            self.spinBoxPixel.setEnabled( False)
        
        # On ne vérifie pas la version SAGA ici
        # Cas Windows : on force SAGA
        if ( machine == "Windows"):
            self.radioButtonSAGA.setChecked(  Qt.Checked)
            # On bloque Gdal
            self.radioButtonGDAL.setEnabled( False)
            self.spinBoxPower.setEnabled( False)
            self.spinBoxPixel.setEnabled( True)

        # Choix d'affichage généraux
        # Toujour le diametre qui est necessaire à "Inter"
        self.checkBoxDiametre.setChecked( Qt.Checked)
        self.checkBoxInterPoints.setChecked( Qt.Checked)
        self.checkBoxInterMoyennes.setChecked( Qt.Checked)

        # Les autres on peut les choisir 
        if (self.settings.value("Affichage/sarment", "YES") == "YES"):
            self.checkBoxSarment.setChecked( Qt.Checked)
        else:
            self.checkBoxSarment.setChecked( Qt.Unchecked)
        if (self.settings.value("Affichage/vitesse", "NO") == "YES"):
            self.checkBoxVitesse.setChecked( Qt.Checked)
        else:
            self.checkBoxVitesse.setChecked( Qt.Unchecked)        
        # Choix d'affichage Inter
        if (self.settings.value("Affichage/InterDiametre", "YES") == "YES"):
            self.checkBoxInterDiametre.setChecked( Qt.Checked)
        else:
            self.checkBoxInterDiametre.setChecked( Qt.Unchecked)
        if (self.settings.value("Affichage/InterBiomasse", "YES") == "YES"):
            self.checkBoxInterBiomasse.setChecked( Qt.Checked)
        else:
            self.checkBoxInterBiomasse.setChecked( Qt.Unchecked)
        if (self.settings.value("Affichage/InterLibelle", "NO") == "YES"):
            self.checkBoxInterLibelle.setChecked( Qt.Checked)
        else:
            self.checkBoxInterLibelle.setChecked( Qt.Unchecked)        

        # Choix d'affichage Intra
        if (self.settings.value("Affichage/IntraUnSeul", "YES") == "YES"):
            self.checkBoxIntraUnSeul.setChecked( Qt.Checked)
        else:
            self.checkBoxIntraUnSeul.setChecked( Qt.Unchecked)
        if (self.settings.value("Affichage/IntraIsos", "NO") == "YES"):
            self.checkBoxIntraIsos.setChecked( Qt.Checked)
        else:
            self.checkBoxIntraIsos.setChecked( Qt.Unchecked)
        if (self.settings.value("Affichage/IntraImages", "NO") == "YES"):
            self.checkBoxIntraImages.setChecked( Qt.Checked)
        else:
            self.checkBoxIntraImages.setChecked( Qt.Unchecked)

        # Calcul dynamique de la densité
        self.spinBoxInterrangs.valueChanged.connect( self.calcul_densite)
        self.spinBoxInterceps.valueChanged.connect( self.calcul_densite)
 
        # Calcul dynamique du intervale Isolignes
        self.spinBoxIsoMin.valueChanged.connect( self.physiocap_iso_distance)
        self.spinBoxIsoMax.valueChanged.connect( self.physiocap_iso_distance)
        self.spinBoxNombreIso.valueChanged.connect( self.physiocap_iso_distance)
 
        # Remplissage de la liste de ATTRIBUTS_INTRA 
        self.fieldComboIntra.setCurrentIndex( 0)   
        if len( ATTRIBUTS_INTRA) == 0:
            self.fieldComboIntra.clear( )
            physiocap_error( self.trUtf8( "Pas de liste des attributs pour Intra pré défini"))
        else:
            self.fieldComboIntra.clear( )
            self.fieldComboIntra.addItems( ATTRIBUTS_INTRA )
            # TEST JH : cas de details ATTRIBUTS_INTRA_DETAIL
            if (self.settings.value("Physiocap/details") == "YES"):
                self.fieldComboIntra.addItems( ATTRIBUTS_INTRA_DETAILS )
            # Retrouver le format de  settings
            i=0
            leFormat = self.settings.value("Physiocap/attributIntra", "xx") 
            for unFormat in ATTRIBUTS_INTRA:
                if ( unFormat == leFormat):
                    self.fieldComboIntra.setCurrentIndex( i)
                i=i+1
            if (self.settings.value("Physiocap/details") == "YES"):
                for unFormat in ATTRIBUTS_INTRA_DETAILS:
                    if ( unFormat == leFormat):
                        self.fieldComboIntra.setCurrentIndex( i)
                    i=i+1


        # Auteurs : Icone
        self.label_jhemmi.setPixmap( QPixmap( os.path.join( REPERTOIRE_HELP, 
            "jhemmi.eu.png")))
        self.label_CIVC.setPixmap( QPixmap( os.path.join( REPERTOIRE_HELP, 
            "CIVC.jpg"))) 
        
        # Init fin 
        return


    
    # ################
    #  Différents SLOT
    # ################

    # FIELDS
    def min_max_field_intra_list( self ):
        """ Create a list of fields for the current vector point in fieldCombo Box"""
        # Todo : V1.4 prefixe Slot et nommage SLOT_Champ_Attibut_Intra     
        nom_attribut = self.fieldComboIntra.currentText()
        #physiocap_log(u"Attribut pour Intra >" + nom_attribut )
        nom_complet_point = self.comboBoxPoints.currentText().split( SEPARATEUR_NOEUD)
        if (len( nom_complet_point) !=2):
            return
        nomProjet = nom_complet_point[0] 
        idLayer   = nom_complet_point[1]
        # Rechecher min et max du layer
        layer = physiocap_get_layer_by_ID( idLayer)
        if layer is not None:
            try:
                index_attribut = layer.fieldNameIndex( nom_attribut)
            except:
                physiocap_log_for_error( self)
                aText = self.trUtf8( "L'attribut %s n'existe pas dans les données à disposition." %\
                     ( str( nom_attribut)))
                aText = aText + \
                    self.trUtf8( \
                    "L'interpolation n'est pas possible. Relancer un calcul de votre projet Physiocap.")
                physiocap_error( aText, "CRITICAL")
                return physiocap_message_box( self, aText, "information")
            valeurs = []
            for un_point in layer.getFeatures():
                 valeurs.append( un_point.attributes()[index_attribut])
##            physiocap_log(u"Min et max de > " + str( nom_attribut) + " sont "  + \
##                str( min(valeurs)) + "==" + str(max(valeurs)))
            self.spinBoxIsoMax.setValue( int( max(valeurs) ))
            self.spinBoxIsoMin.setValue( int( min(valeurs) ))

    def update_field_poly_list( self ):
        """ Create a list of fields for the current vector in fieldCombo Box"""
        nom_complet_poly = self.comboBoxPolygone.currentText().split( SEPARATEUR_NOEUD)
        inputLayer = nom_complet_poly[0] #str(self.comboBoxPolygone.itemText(self.comboBoxPolygone.currentIndex()))
        self.fieldComboContours.clear()
        layer = self.get_layer_by_name( inputLayer )
        self.fieldComboContours.addItem( "NOM_PHY")
        self.fieldComboContours.setCurrentIndex( 0)
        if layer is not None:
            # On exclut les layer qui ne sont pas de type 0 (exemple 1 raster)
            if ( layer.type() == 0):
                i = 1 # Demarre à 1 car NOM_PHY est dejà ajouté
                dernierAttribut = self.settings.value("Physiocap/attributPoly", "xx") 
                for index, field in enumerate(layer.dataProvider().fields()):
                    self.fieldComboContours.addItem( str( field.name()) )
                    if ( str( field.name()) == dernierAttribut):
                        self.fieldComboContours.setCurrentIndex( i)
                    i=i+1
                    
    def update_points_choose_inter_intra( self ):
        """ Verify whether the value autorize Inter or Intra"""
        nom_complet_point = self.comboBoxPoints.currentText().split( SEPARATEUR_NOEUD)
        if ( len( nom_complet_point) != 2):
            return
        
        projet = nom_complet_point[0]
        # Chercher dans arbre si le projet Inter existe
        diametre = nom_complet_point[1] 
        layer = physiocap_get_layer_by_ID( diametre)
        if layer is not None:
            # Avec le diametre, on trouve le repertoire
            pro = layer.dataProvider()
            chemin_shapes = "chemin vers shapeFile"
            if pro.name() != POSTGRES_NOM:
                chemin_shapes = os.path.dirname( unicode( layer.dataProvider().dataSourceUri() ) ) ;
                if ( not os.path.exists( chemin_shapes)):
                    raise physiocap_exception_rep( "chemin vers shapeFile")
            
                chemin_inter = os.path.join( chemin_shapes, VIGNETTES_INTER)
                if (os.path.exists( chemin_inter)):
                    # On aiguille vers Intra
                    self.groupBoxIntra.setEnabled( True)
                    self.ButtonIntra.setEnabled( True)
                    self.ButtonInter.setEnabled( False)

                else:
                    # On aiguille vers Inter
                    self.groupBoxIntra.setEnabled( False)
                    self.ButtonIntra.setEnabled( False)
                    self.ButtonInter.setEnabled( True)
                              


    def get_layer_by_name( self, layerName ):
        layerMap = QgsMapLayerRegistry.instance().mapLayers()
        layer = None
        for name, layer in layerMap.iteritems():
            if layer.type() == QgsMapLayer.VectorLayer and layer.name() == layerName:
                # The layer is found
                break
        if ( layer != None):
            if layer.isValid():
                return layer
            else:
                return None
        else:
            return None



    # Repertoire données brutes :
    def lecture_repertoire_donnees_brutes( self):
        """Catch directory for raw data"""
        # TODO: Vx ? Faire traduction du titre self.?iface.tr("Répertoire des données brutes")
        # Récuperer dans setting le nom du dernier ou sinon REPERTOIRE_DONNEES_BRUTES
        self.settings= QSettings(PHYSIOCAP_NOM, PHYSIOCAP_NOM)
        exampleDirName =  self.settings.value("Physiocap/repertoire", REPERTOIRE_DONNEES_BRUTES)
        
        dirName = QFileDialog.getExistingDirectory( self, u"Répertoire des données brutes",
                                                 exampleDirName,
                                                 QFileDialog.ShowDirsOnly
                                                 | QFileDialog.DontResolveSymlinks);
        if len( dirName) == 0:
          return
        self.lineEditDirectoryPhysiocap.setText( dirName )
 
    def liste_inter_parcelles( self):
        """ Rafraichit les listes avant le calcul inter parcelles"""
        nombre_poly = 0
        nombre_point = 0
        nombre_poly, nombre_point = physiocap_fill_combo_poly_or_point( self)

        if (( nombre_poly > 0) and ( nombre_point > 0)):
            # Liberer le bouton "moyenne"
            self.groupBoxInter.setEnabled( True)
            self.update_field_poly_list()
            self.min_max_field_intra_list()
        else:
            self.groupBoxInter.setEnabled( False)
            
    def physiocap_iso_distance( self):
        """ 
        Recherche du la distance optimale tenant compte de min et max et du nombre d'intervalle
        si erreur rend 3 
        """
        # retrouve sans QT
        min_entier = round( float ( self.spinBoxIsoMin.value()))
        le_max = float ( self.spinBoxIsoMax.value())      
        max_entier = round( le_max)

        if (min_entier >= max_entier):
            aText = self.trUtf8( "Votre minimum ne doit pas être plus grand que votre maximum")
            return physiocap_message_box( self, aText, "information")              
        
        if (max_entier < le_max):
            max_entier = max_entier +1

        if (min_entier >= max_entier):
##            physiocap_log( u"Nombre min " + str(min_entier))
##            physiocap_log( u"Nombre max " + str(max_entier))
##            physiocap_log( u"Nombre d'intervalle d'isoligne forcé à 3")
            self.lineEditDistanceIso.setText( str( 3))
            return 
        
        nombre_iso = round( float ( self.spinBoxNombreIso.value())) 

        distance = max_entier - min_entier
        nombre_intervalles = int( distance / ( nombre_iso + 1))
        if nombre_intervalles < 1:
            nombre_intervalles = 1
            
##        physiocap_log( "Nombre d'intervalle d'iso : " + str(nombre_intervalles) + " min =" + \
##            str( min_entier) + " max =" + str( max_entier) + " nombre iso =" + str( nombre_iso))
        self.lineEditDistanceIso.setText( str( nombre_intervalles))
        return 

    def memoriser_saisies_inter_intra_parcelles(self):
        """ Mémorise les saisies inter et intra """

        # Memorisation des saisies
        self.settings= QSettings( PHYSIOCAP_NOM, PHYSIOCAP_NOM)
        self.settings.setValue("Physiocap/interPoint", self.comboBoxPoints.currentText() )
        self.settings.setValue("Physiocap/interPoly", self.comboBoxPolygone.currentText() )
        self.settings.setValue("Physiocap/attributPoly", self.fieldComboContours.currentText())

        self.settings.setValue("Physiocap/attributIntra", self.fieldComboIntra.currentText())
        self.settings.setValue("Physiocap/powerIntra", float( self.spinBoxPower.value()))
        self.settings.setValue("Physiocap/rayonIntra", float( self.spinBoxRayon.value()))
        self.settings.setValue("Physiocap/pixelIntra", float( self.spinBoxPixel.value()))
        self.settings.setValue("Physiocap/isoMin", float( self.spinBoxIsoMin.value()))
        self.settings.setValue("Physiocap/isoMax", float( self.spinBoxIsoMax.value()))
        self.settings.setValue("Physiocap/isoNombres", float( self.spinBoxNombreIso.value()))
        
        self.settings.setValue("Physiocap/leDirThematiques", self.fieldComboThematiques.currentText())
        self.settings.setValue("Physiocap/leChoixDeThematiques", self.fieldComboThematiques.currentIndex())
        
        # Sauver les affichages Inter
        diametre = "NO"
        if self.checkBoxInterDiametre.isChecked():
            diametre = "YES"
        self.settings.setValue("Affichage/InterDiametre", diametre )
        biomasse = "NO"
        if self.checkBoxInterBiomasse.isChecked():
            biomasse = "YES"
        self.settings.setValue("Affichage/InterBiomasse", biomasse )
        libelle = "NO"
        if self.checkBoxInterLibelle.isChecked():
            libelle = "YES"
        self.settings.setValue("Affichage/InterLibelle", libelle )
        moyennes = "NO"
        if self.checkBoxInterMoyennes.isChecked():
            moyennes = "YES"
        self.settings.setValue("Affichage/InterMoyennes", moyennes )
        points = "NO"
        if self.checkBoxInterPoints.isChecked():
            points = "YES"
        self.settings.setValue("Affichage/InterPoints", points )

        # Sauver les affichages Intra
        unSeul = "NO"
        if self.checkBoxIntraUnSeul.isChecked():
            unSeul = "YES"
        self.settings.setValue("Affichage/IntraUnSeul", unSeul )
        isos = "NO"
        if self.checkBoxIntraIsos.isChecked():
            isos = "YES"
        self.settings.setValue("Affichage/IntraIsos", isos )
        images = "NO"
        if self.checkBoxIntraImages.isChecked():
            images = "YES"
        self.settings.setValue("Affichage/IntraImages", images ) 
        
        # Cas du choix SAGA / GDAL
        LIB = "DO NOT KNOW"
        if self.radioButtonSAGA.isChecked():
            LIB = "SAGA"
        else:
            LIB = "GDAL"
        self.settings.setValue("Physiocap/library", LIB)
        
    def interpolation_intra_parcelles(self):
        """ Slot qui fait appel au interpolation Intra Parcelles et traite exceptions """
       
        nom_complet_point = self.comboBoxPoints.currentText().split( SEPARATEUR_NOEUD)
        if ( len( nom_complet_point) != 2):
            aText = self.trUtf8( "Le shape de points n'est pas choisi. \
Lancez le traitement initial - bouton OK - avant de faire votre \
calcul de Moyenne Inter Parcellaire")   
            physiocap_error( aText, "CRITICAL")
            return physiocap_message_box( self, aText, "information" )

        # Memorisation des saisies
        self.memoriser_saisies_inter_intra_parcelles()
            
        try:
            # Création des répertoires et des résultats de synthèse
            physiocap_interpolation_IntraParcelles(self)
            
        except physiocap_exception_rep as e:
            physiocap_log_for_error( self)
            aText = self.trUtf8( "Erreur bloquante lors de la création du répertoire : %s" % ( str( e)))
            physiocap_error( aText, "CRITICAL")
            return physiocap_message_box( self, aText, "information" )
        except physiocap_exception_vignette_exists as e:
            physiocap_log_for_error( self)
            aText = self.trUtf8( "Des moyennes IntraParcellaires dans %s existent déjà. " % ( str( e)))
            aText = aText + self.trUtf8( "Vous ne pouvez pas redemander ce calcul : vous devez détruire le groupe ") 
            aText = aText + self.trUtf8( "ou mieux créer un nouveau projet Physiocap")
            physiocap_error( aText, "CRITICAL")
            return physiocap_message_box( self, aText, "information" )
        except physiocap_exception_points_invalid as e:
            physiocap_log_for_error( self)
            aText = self.trUtf8( "Le fichier de points du projet %s ne contient pas les attributs attendus" % ( str( e)))
            physiocap_error( aText, "CRITICAL")
            return physiocap_message_box( self, aText, "information" )
        except physiocap_exception_interpolation as e:
            physiocap_log_for_error( self)
            allFile = str(e)
            finFile = '"...' + allFile[-60:-1] + '"'            
            aText = self.trUtf8( "L'interpolation de : %s n'a pu s'exécuter entièrement. " % ( finFile))
            aText = aText + self.trUtf8( "Avez-vous installé et activé la librairie d'interpolation (SAGA ou GDAL) ?")
            physiocap_error( aText, "CRITICAL")
            return physiocap_message_box( self, aText, "information" )
        except:
            raise
        finally:
            pass
        # Fin de capture des erreurs Physiocap        
        physiocap_log( self.trUtf8( "Physiocap a terminé les interpolations intra parcelaire."))

                   
    def moyenne_inter_parcelles(self):
        """ Slot qui fait appel au traitement Inter Parcelles et traite exceptions """
       
        nom_complet_point = self.comboBoxPoints.currentText().split( SEPARATEUR_NOEUD)
        if ( len( nom_complet_point) != 2):
            aText = self.trUtf8( "Le shape de points n'est pas choisi. \
                    Lancez le traitement initial - bouton OK - avant de faire votre \
                    calcul de Moyenne Inter Parcellaire")   
            physiocap_error( aText, "CRITICAL")
            return physiocap_message_box( self, aText, "information" )
        
        # Eviter les appels multiples
        self.ButtonInter.setEnabled( False)
        # Memorisation des saisies
        self.memoriser_saisies_inter_intra_parcelles()
            
        try:
            # Création des répertoires et des résultats de synthèse
            physiocap_moyenne_InterParcelles(self)
            
        except physiocap_exception_rep as e:
            physiocap_log_for_error( self)
            aText = self.trUtf8( "Erreur bloquante lors de la création du répertoire : %s" % ( str( e)))
            physiocap_error( aText, "CRITICAL")
            return physiocap_message_box( self, aText, "information" )
        except physiocap_exception_vignette_exists as e:
            aText1 = self.trUtf8( "Les moyennes InterParcellaires dans %s existent déjà. " % ( str( e)))
            physiocap_log(aText1, "information")
            physiocap_log_for_error( self)
            aText = aText1 + self.trUtf8( "Vous ne pouvez pas redemander ce calcul : vous devez détruire le groupe ") 
            aText = aText + self.trUtf8( "ou mieux créer un nouveau projet Physiocap")
            physiocap_error( aText, "CRITICAL")
            return physiocap_message_box( self, aText, "information" )
        except physiocap_exception_points_invalid as e:
            physiocap_log_for_error( self)
            physiocap_log_for_error( self)
            aText = self.trUtf8( "Le fichier de points du projet %s ne contient pas les attributs attendus" % ( str( e)))
            aText = aText + self.trUtf8( "Lancez le traitement initial - bouton OK - avant de faire votre ")
            aText = aText + self.trUtf8( "calcul de Moyenne Inter Parcellaire" )
            physiocap_error( aText, "CRITICAL")
            return physiocap_message_box( self, aText, "information" )
        except:
            raise
        finally:
            pass
        # Fin de capture des erreurs Physiocap        
        
        self.groupBoxIntra.setEnabled( True)
        self.ButtonIntra.setEnabled( True)
        physiocap_log(self.trUtf8( "Physiocap a terminé les moyennes inter parcelaire."))

    def bascule_details_vignoble(self):
        """ Changement de demande pour les details vignoble : 
        on grise le groupe Vignoble
        """ 
        #physiocap_log( u"Changement de demande pour les details vignoble")
        if self.checkBoxInfoVignoble.isChecked():
            self.Vignoble.setEnabled( True)
        else:
            self.Vignoble.setEnabled( False)         

    def calcul_densite( self):
        # Densité pied /ha

        interrang  = float( self.spinBoxInterrangs.value())
        intercep   = float( self.spinBoxInterceps.value())
        densite = ""
        if (interrang !=0) and ( intercep != 0):
            densite = int (10000 / ((interrang/100) * (intercep/100)))
        self.lineEditDensite.setText( str( densite))
        
    def demander_contribution( self):
        """ Pointer vers payname """ 
        help_url = QUrl("http://plus.payname.fr/jhemmi/?type=9xwqt")
        QDesktopServices.openUrl(help_url)
    
    def demander_aide(self):
        """ Help html qui pointe vers gitHub""" 
        help_url = QUrl("file:///%s/help/index.html" % self.plugin_dir)
        QDesktopServices.openUrl(help_url)


    def physiocap_creer_donnees_resultats( self, laProjection, EXT_CRS_SHP, EXT_CRS_PRJ,
        details = "NO", histogrammes = "NO", recursif = "NO"):
        """ Récupération des paramètres saisies et 
        creation de l'arbre "source" "texte" et du fichier "resultats"
        Ce sont les résultats de l'analyse filtration des données brutes"""
                    
        # Récupérer les paramètres saisies
        REPERTOIRE_DONNEES_BRUTES = self.lineEditDirectoryPhysiocap.text()
        NOM_PROJET = self.lineEditProjet.text()
        mindiam = float( self.spinBoxMinDiametre.value())
        maxdiam = float( self.spinBoxMaxDiametre.value())
        max_sarments_metre = float( self.spinBoxMaxSarmentsParMetre.value())

        physiocap_log( self.trUtf8( "Paramètres pour filtrer les diamètres min : {0} max : {1}").\
            format( str(mindiam), str(maxdiam)))
        if details == "YES":
            interrangs = float( self.spinBoxInterrangs.value())
            interceps = float( self.spinBoxInterceps.value())
            hauteur = float( self.spinBoxHauteur.value())
            densite = float( self.doubleSpinBoxDensite.value())
            leCepage = self.fieldComboCepage.currentText()
            laTaille = self.fieldComboTaille.currentText()
            
        # Vérification de l'existance ou création du répertoire projet
        chemin_projet = os.path.join(REPERTOIRE_DONNEES_BRUTES, NOM_PROJET)
        #physiocap_log(u"Repertoire projet : " + str(chemin_projet))
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
                physiocap_log( self.trUtf8( "Erreur dans fonction creer_donnees_resultats \
                    == %s" % ( str(chemin_projet))))
                raise physiocap_exception_rep( chemin_projet)
        
        
        # Stocker dans la fenetre de synthese le nom du projet
        chemin_base_projet = os.path.basename( chemin_projet)
        self.lineEditDernierProjet.setText( chemin_base_projet)
        self.settings= QSettings( PHYSIOCAP_NOM, PHYSIOCAP_NOM)
        self.settings.value("Physiocap/dernier_repertoire", chemin_base_projet) 
        
        # Progress BAR 2 %
        self.progressBar.setValue( 2)
        
            
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
        
        # Assert le nombre de MID > 0
        # le Tri pour retomber dans l'ordre de Physiocap_V8
        if ( recursif == "YES"):
            # On appelle la fonction de recherche récursive
            listeTriee = physiocap_look_for_MID( REPERTOIRE_DONNEES_BRUTES, "YES", REPERTOIRE_SOURCES)
        else:
            # Non recursif
            listeTriee = sorted(glob.glob( nom_fichiers_recherches))

        if len( listeTriee) == 0:
            raise physiocap_exception_no_mid()
        
        # Verification si plus de 10 MIDs
        if len( listeTriee) >= 15:
            # Beaucoup de MIDs Poser une question si cancel, on stoppe
            uMsg =self.trUtf8( "Plus de 15 fichier MIDs sont à analyser. Temps de traitement > à 1 minute. Voulez-vous continuer ?")
            if ( physiocap_question_box( self, uMsg)):
                pass
            else:
                # Arret demandé
                raise physiocap_exception_stop_user()
            
        for mid in listeTriee:
            try:
                shutil.copyfileobj(open(mid, "r"), csv_concat)
                # et copie des MID
                nom_cible = os.path.join( chemin_sources, os.path.basename(mid))
                if os.path.exists( nom_cible):
                    nouveau_long = physiocap_rename_existing_file( nom_cible)
                    shutil.copyfile( mid, nouveau_long)
                else:
                    shutil.copy( mid, chemin_sources)
            except:
                raise physiocap_exception_mid( mid)
        csv_concat.close()

        # Assert le fichier de données n'est pas vide
        if os.path.getsize( nom_csv_concat ) == 0 :
            uMsg = self.trUtf8( "Le fichier %s a une taille nulle !" % ( str(nom_court_csv_concat))) 
            physiocap_message_box( self, uMsg)
            return physiocap_error( uMsg)
        
        # Création la première partie du fichier de synthèse
        fichier_resultat_analyse = chemin_base_projet + SEPARATEUR_ + FICHIER_RESULTAT
        nom_fichier_synthese, fichier_synthese = physiocap_open_file( fichier_resultat_analyse, chemin_projet , "w")
        fichier_synthese.write( "SYNTHESE PHYSIOCAP\n\n")
        fichier_synthese.write( "Générée le : ")
        a_time = time.strftime( "%d/%m/%y %H:%M\n",time.localtime())
        fichier_synthese.write( a_time)
        fichier_synthese.write( "Répertoire de base ")
        fichier_synthese.write( chemin_base_projet + "\n")
        fichier_synthese.write( "Nom des MID \t\t Date et heures\n=>Nb. Valeurs brutes\tVitesse km/h")
        if (CENTROIDES == "YES"):
            fichier_synthese.write("\nCentroïdes")
        fichier_synthese.write("\n")
        info_mid = physiocap_list_MID( REPERTOIRE_DONNEES_BRUTES, listeTriee)
        for all_info in info_mid:
            info = all_info.split(";")
            fichier_synthese.write( str(info[0]) + "\t" + str(info[1]) + "->" + str(info[2])+ "\n")
            fichier_synthese.write( "=>\t" +str(info[3]) + "\t" + str(info[4]))
            if (CENTROIDES == "YES"):
                # Centroides
                fichier_synthese.write( "\n" + str(info[5]) + "--" + str(info[6]))
            fichier_synthese.write("\n")
    ##        nom_mid = ""
    ##        for fichier_mid in listeTriee:
    ##            nom_mid = nom_mid + os.path.basename( fichier_mid) + " & "
    ##        fichier_synthese.write("Liste des fichiers MID : " + nom_mid[:-3] + "\n")
    ##        physiocap_log( "Liste des MID : " + nom_mid[:-3])
       
        # Progress BAR 5 %
        self.progressBar.setValue( 5)
        physiocap_log ( self.trUtf8( "Fin de la création csv et début de synthèse"))
       
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
                # Todo : question selon le taux de lignes en erreur autorisées
                #raise physiocap_exception_err_csv( pourcentage_erreurs)
        except:
            raise

        # Progress BAR 10 %
        self.progressBar.setValue( 10)        
        fichier_synthese.write("\n\nPARAMETRES SAISIS ")
        
        if os.path.getsize( nom_csv_concat ) == 0 :
            uMsg = self.trUtf8( "Le fichier %s a une taille nulle !" % ( str(nom_court_csv_concat)))
            physiocap_message_box( self, uMsg)
            return physiocap_error( uMsg)

        # ouverture du fichier source
        csv_concat = open(nom_csv_concat, "r")

        # Appeler la fonction de traitement
        if histogrammes == "YES":
            #################
            physiocap_fichier_histo( csv_concat, data_histo_diametre,    
                        data_histo_sarment, erreur)
            #################
            # Fermerture des fichiers
            data_histo_diametre.close()
            data_histo_sarment.close()
        csv_concat.close()
        erreur.close()
        
        # Progress BAR 12 %
        self.progressBar.setValue( 12)
        
        # Verification de l'existance 
        chemin_histos = os.path.join(chemin_projet, REPERTOIRE_HISTOS)
        if not (os.path.exists( chemin_histos)):
            try:
                os.mkdir( chemin_histos)
            except:
                raise physiocap_exception_rep( REPERTOIRE_HISTOS)

        if histogrammes == "YES":
            # creation d'un histo
            nom_data_histo_sarment, data_histo_sarment = physiocap_open_file( nom_court_fichier_sarment, chemin_textes, 'r')
            nom_histo_sarment, histo_sarment = physiocap_open_file( FICHIER_HISTO_SARMENT, chemin_histos)
            name = nom_histo_sarment
            physiocap_tracer_histo( data_histo_sarment, name, 0, 50, "SARMENT au m", "FREQUENCE en %", "HISTOGRAMME NBSARM AVANT TRAITEMENT")
            histo_sarment.close()
            
            nom_data_histo_diametre, data_histo_diametre = physiocap_open_file( nom_court_fichier_diametre, chemin_textes, 'r')
            nom_histo_diametre, histo_diametre = physiocap_open_file( FICHIER_HISTO_DIAMETRE, chemin_histos)
            name = nom_histo_diametre
            physiocap_tracer_histo( data_histo_diametre, name, 0, 30, "DIAMETRE en mm", "FREQUENCE en %", "HISTOGRAMME DIAMETRE AVANT TRAITEMENT")
            histo_diametre.close()        
            
            physiocap_log ( self.trUtf8( "Fin de la création des histogrammes bruts"))
        else:
            physiocap_log ( self.trUtf8( "Pas de création des histogrammes"))

        # Progress BAR 15 %
        self.progressBar.setValue( 15) 
                  
        # Création des csv
        nom_court_csv_sans_0 = NOM_PROJET + SEPARATEUR_ + "OUT.csv"
        nom_csv_sans_0, csv_sans_0 = physiocap_open_file( 
            nom_court_csv_sans_0, chemin_textes)

        nom_court_csv_avec_0 = NOM_PROJET + SEPARATEUR_ + "OUT0.csv"
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
        retour_filtre = physiocap_filtrer( self, csv_concat, csv_sans_0, csv_avec_0, \
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

        # Todo : V1.5 ? Gerer cette erreur par exception
        if retour_filtre != 0:
            uMsg = self.trUtf8( "Erreur bloquante : problème lors du filtrage \
                des données de %s" % ( str(nom_court_csv_concat)))
            return physiocap_error(uMsg)  

        # Progress BAR 60 %
        self.progressBar.setValue( 41)

        if histogrammes == "YES":
            # Histo apres filtatration
            nom_fichier_diametre_filtre, diametre_filtre = physiocap_open_file( 
                nom_court_fichier_diametre_filtre, chemin_textes , "r")
            nom_histo_diametre_filtre, histo_diametre = physiocap_open_file( FICHIER_HISTO_DIAMETRE_FILTRE, chemin_histos)

            physiocap_tracer_histo( diametre_filtre, nom_histo_diametre_filtre, 0, 30, "DIAMETRE en mm", "FREQUENCE en %", "HISTOGRAMME DIAMETRE APRES TRAITEMENT")
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

        # Progress BAR 42%
        self.progressBar.setValue( 42)
        
        # Verification de l'existance ou création du répertoire des sources MID et fichier csv
        chemin_shapes = os.path.join(chemin_projet, REPERTOIRE_SHAPEFILE)
        if not (os.path.exists( chemin_shapes)):
            try :
                os.mkdir( chemin_shapes)
            except :
                raise physiocap_exception_rep( REPERTOIRE_SHAPEFILE)

        # Création des shapes sans 0
        nom_court_shape_sans_0 = NOM_PROJET + NOM_POINTS + EXT_CRS_SHP
        nom_shape_sans_0 = os.path.join(chemin_shapes, nom_court_shape_sans_0)
        nom_court_prj_sans_0 = NOM_PROJET + NOM_POINTS + EXT_CRS_PRJ
        nom_prj_sans_0 = os.path.join(chemin_shapes, nom_court_prj_sans_0)

            
        # Si le shape existe dejà il faut le détruire
        if os.path.isfile( nom_shape_sans_0):
            physiocap_log ( self.trUtf8( "Le shape file existant déjà, il est détruit."))
            os.remove( nom_shape_sans_0)            

        # cas sans 0, on demande la synthese en passant le nom du fichier
        retour = physiocap_csv_vers_shapefile( self, 45, nom_csv_sans_0, nom_shape_sans_0, nom_prj_sans_0, 
                laProjection,
                nom_fichier_synthese, details)
        if retour != 0:
            return physiocap_error(u"Erreur bloquante : problème lors de la création du shapefile : " + 
                nom_court_shape_sans_0)                

        # Progress BAR 65 %
        self.progressBar.setValue( 65)
                
        # Création des shapes avec 0
        nom_court_shape_avec_0 = NOM_PROJET + NOM_POINTS + EXTENSION_POUR_ZERO + EXT_CRS_SHP
        nom_shape_avec_0 = os.path.join(chemin_shapes, nom_court_shape_avec_0)
        nom_court_prj_avec_0 = NOM_PROJET + NOM_POINTS + EXTENSION_POUR_ZERO + EXT_CRS_PRJ
        nom_prj_avec_0 = os.path.join(chemin_shapes, nom_court_prj_avec_0)
        # Si le shape existe dejà il faut le détruire
        if os.path.isfile( nom_shape_avec_0):
            physiocap_log ( self.trUtf8( "Le shape file existant déjà, il est détruit."))
            os.remove( nom_shape_avec_0) 
            
        # cas avec 0, pas de demande de synthese
        retour = physiocap_csv_vers_shapefile( self, 65, nom_csv_avec_0, nom_shape_avec_0, nom_prj_avec_0, laProjection,
            "NO", details)
        if retour != 0:
            return physiocap_error(u"Erreur bloquante : problème lors de la création du shapefile : " + 
                    nom_court_shape_avec_0) 
                              
        # Progress BAR 95%
        self.progressBar.setValue( 95)
        
        # Creer un groupe pour cette analyse
        # Attention il faut qgis > 2.4 metadata demande V2.4 mini
        root = QgsProject.instance().layerTreeRoot( )
        # Nommmer le groupe chemin_base_projet
        sous_groupe = root.addGroup( chemin_base_projet)
        
        # Récupérer des styles pour chaque shape
        dir_template = self.fieldComboThematiques.currentText()
        # Affichage des différents shapes dans Qgis
        SHAPE_A_AFFICHER = []
        qml_is = ""
        if self.checkBoxDiametre.isChecked():
            qml_is = str( self.lineEditThematiqueDiametre.text().strip('"')) + EXTENSION_QML
            SHAPE_A_AFFICHER.append( (nom_shape_sans_0, 'DIAMETRE mm', qml_is))
        if self.checkBoxSarment.isChecked():
            qml_is = str( self.lineEditThematiqueSarment.text().strip('"')) + EXTENSION_QML
            SHAPE_A_AFFICHER.append( (nom_shape_sans_0, 'SARMENT par m', qml_is))
        if self.checkBoxVitesse.isChecked():
            qml_is = str( self.lineEditThematiqueVitesse.text().strip('"')) + EXTENSION_QML
            SHAPE_A_AFFICHER.append(( nom_shape_avec_0, 'VITESSE km/h', qml_is))
        
        for shapename, titre, un_template in SHAPE_A_AFFICHER:
            # Cas Postgres
            if ( self.fieldComboFormats.currentText() == POSTGRES_NOM ):
                uri_nom = physiocap_quel_uriname( self)
                #physiocap_log( u"URI nom : " + str( uri_nom))
                uri_modele = physiocap_get_uri_by_layer( self, uri_nom )
                if uri_modele != None:
                    uri_connect, uri_deb, uri_srid, uri_fin = physiocap_tester_uri( self, uri_modele)            
                    nom_court_shp = os.path.basename( shapename)
                    #TABLES = "public." + nom_court_shp
                    uri = uri_deb +  uri_srid + \
                       " key='gid' type='POINTS' table=" + nom_court_shp[ :-4] + " (geom) sql="            
    ##              "dbname='testpostgis' host='localhost' port='5432'" + \
    ##              " user='postgres' password='postgres' SRID='2154'" + \
    ##              " key='gid' type='POINTS' table=" + nom_court_shp[ :-4] + " (geom) sql="
    ##                physiocap_log ( "Création dans POSTGRES : >>" + uri + "<<")
    ##                vectorPG = QgsVectorLayer( uri, titre, POSTGRES_NOM)
                else:
                    aText = self.trUtf8( "Pas de connecteur vers Postgres : %s. On continue avec des shapefiles"\
                         % (str( uri_nom)))
                    physiocap_log( aText)
                    # Remettre le choix vers ESRI shape file
                    self.fieldComboFormats.setCurrentIndex( 0)

            #physiocap_log( u"Physiocap : Afficher layer ")
            vector = QgsVectorLayer( shapename, titre, 'ogr')
            QgsMapLayerRegistry.instance().addMapLayer( vector, False)
            # Ajouter le vecteur dans un groupe
            vector_node = sous_groupe.addLayer( vector)
            le_template = os.path.join( dir_template, un_template)
            if ( os.path.exists( le_template)):
                #physiocap_log( u"Physiocap le template : " + os.path.basename( le_template))
                vector.loadNamedStyle( le_template)
        
        # Fichier de synthese dans la fenetre resultats   
        fichier_synthese = open(nom_fichier_synthese, "r")
        while True :
            ligne = fichier_synthese.readline() # lit les lignes 1 à 1
            physiocap_write_in_synthese( self, ligne)
            if not ligne: 
                fichier_synthese.close
                break     

        # Progress BAR 95 %
        self.progressBar.setValue( 95)
                    
        # Mettre à jour les histogrammes dans fenetre resultat
        if histogrammes == "YES":
            if ( self.label_histo_sarment.setPixmap( QPixmap( nom_histo_sarment))):
                physiocap_log( self.trUtf8( "Physiocap histogramme sarment chargé"))
            if ( self.label_histo_diametre_avant.setPixmap( QPixmap( nom_histo_diametre))):
                physiocap_log ( self.trUtf8( "Physiocap histogramme diamètre chargé"))                
            if ( self.label_histo_diametre_apres.setPixmap( QPixmap( nom_histo_diametre_filtre))):
                physiocap_log ( self.trUtf8( "Physiocap histogramme diamètre filtré chargé"))    
        else:
            self.label_histo_sarment.setPixmap( QPixmap( FICHIER_HISTO_NON_CALCULE))
            self.label_histo_diametre_avant.setPixmap( QPixmap( FICHIER_HISTO_NON_CALCULE))
            self.label_histo_diametre_apres.setPixmap( QPixmap( FICHIER_HISTO_NON_CALCULE))
            physiocap_log ( self.trUtf8( "Physiocap pas d'histogramme calculé"))    
                           
        # Progress BAR 100 %
        self.progressBar.setValue( 100)
        # Fin 
        
        physiocap_log ( self.trUtf8( "Fin de la synthèse Physiocap : sans erreur"))
        physiocap_fill_combo_poly_or_point( self)
        #physiocap_log ( u"Mise à jour des poly et points")
        return 0 

    def reject( self ):
        """Close when bouton is Cancel"""
        # Todo : V1.4 prefixe Slot et nommage SLOT_Bouton_Cancel      
        #self.textEdit.clear()
        QDialog.reject( self)
                
    def accept( self ):
        """Verify when bouton is OK"""
        # Todo : V1.4 prefixe Slot et nommage SLOT_Bouton_OK
        # Vérifier les valeurs saisies
        # QT confiance et initialisation par Qsettings sert d'assert sur la
        # cohérence des variables saisies

        repertoire_data = self.lineEditDirectoryPhysiocap.text()
        if ((repertoire_data == "") or ( not os.path.exists( repertoire_data))):
            aText = self.trUtf8( "Pas de répertoire de données brutes spécifié")
            physiocap_error( aText)
            return physiocap_message_box( self, aText)
        if self.lineEditProjet.text() == "":
            aText = self.trUtf8( "Pas de nom de projet spécifié")
            physiocap_error( aText)
            return physiocap_message_box( self, aText)                 
        # Remettre vide le textEditSynthese
        self.textEditSynthese.clear()

        # Sauvergarde des saisies dans les settings
        self.settings= QSettings( PHYSIOCAP_NOM, PHYSIOCAP_NOM)
        self.settings.setValue("Physiocap/projet", self.lineEditProjet.text() )
        self.settings.setValue("Physiocap/repertoire", self.lineEditDirectoryPhysiocap.text() )
        #self.settings.setValue("Physiocap/contours", self.lineEditContours.text() )

        # Cas recursif
        recursif = "NO"
        if self.checkBoxRecursif.isChecked():
            recursif = "YES"
            physiocap_log( self.trUtf8( "La recherche des MID fouille l'arbre de données"))
        self.settings.setValue("Physiocap/recursif", recursif )
            
        laProjection, EXT_CRS_SHP, EXT_CRS_PRJ, EXT_CRS_RASTER, EPSG_NUMBER = physiocap_quelle_projection_demandee( self) 
        self.settings.setValue("Physiocap/laProjection", laProjection)
        physiocap_log(self.trUtf8( "Projection des shapefiles demandée en %s"\
            ) % (str( laProjection)))
           
        # Trop tot self.settings.setValue("Physiocap/dernier_repertoire", self.lineEditDernierProjet.text() )
        self.settings.setValue("Physiocap/mindiam", float( self.spinBoxMinDiametre.value()))
        self.settings.setValue("Physiocap/maxdiam", float( self.spinBoxMaxDiametre.value()))


        # Cas détail vignoble
        details = "NO"
        if self.checkBoxInfoVignoble.isChecked():
            details = "YES"
            physiocap_log( self.trUtf8( "Les détails du vignoble sont précisées"))
        self.settings.setValue("Physiocap/details", details)
        self.settings.setValue("Physiocap/max_sarments_metre", float( self.spinBoxMaxSarmentsParMetre.value()))
        self.settings.setValue("Physiocap/interrangs", float( self.spinBoxInterrangs.value()))
        self.settings.setValue("Physiocap/interceps", float( self.spinBoxInterceps.value()))
        self.settings.setValue("Physiocap/hauteur", float( self.spinBoxHauteur.value()))
        self.settings.setValue("Physiocap/densite", float( self.doubleSpinBoxDensite.value()))
        self.settings.setValue("Physiocap/leCepage", self.fieldComboCepage.currentText())
        self.settings.setValue("Physiocap/laTaille", self.fieldComboTaille.currentText())

        # Onglet Histogramme
        TRACE_HISTO = "NO"
        if self.checkBoxHistogramme.isChecked():
            TRACE_HISTO = "YES"
            physiocap_log( self.trUtf8( "Les histogrammes sont attendus"))
        self.settings.setValue("Physiocap/histogrammes", TRACE_HISTO)

        # Sauver les affichages cas généraux
        diametre = "NO"
        if self.checkBoxDiametre.isChecked():
            diametre = "YES"
        self.settings.setValue("Affichage/diametre", diametre )
        sarment = "NO"
        if self.checkBoxSarment.isChecked():
            sarment = "YES"
        self.settings.setValue("Affichage/sarment", sarment )
        vitesse = "NO"
        if self.checkBoxVitesse.isChecked():
            vitesse = "YES"
        self.settings.setValue("Affichage/vitesse", vitesse )

        self.settings.setValue("Physiocap/leFormat", self.fieldComboFormats.currentText())
        self.settings.setValue("Physiocap/leDirThematiques", self.fieldComboThematiques.currentText())

            
        # ########################################
        # Gestion de capture des erreurs Physiocap
        # ########################################
        try:
            # Création des répertoires et des résultats de synthèse
            retour = self.physiocap_creer_donnees_resultats( laProjection, EXT_CRS_SHP, EXT_CRS_PRJ,
                details, TRACE_HISTO, recursif)
        except physiocap_exception_rep as e:
            physiocap_log_for_error( self)
            aText = self.trUtf8( "Erreur bloquante lors de la création du répertoire : %s"\
                 % ( str( e)))
            physiocap_error( aText, "CRITICAL")
            return physiocap_message_box( self, aText, "information" )
        
        except physiocap_exception_err_csv as e:
            physiocap_log_for_error( self)
            aText = self.trUtf8( "Trop d'erreurs %s dans les données brutes"\
                 % ( str( e)))
            physiocap_error( aText, "CRITICAL")
            return physiocap_message_box( self, aText, "information" )
        
        except physiocap_exception_fic as e:
            physiocap_log_for_error( self)
            aText = self.trUtf8( "Erreur bloquante lors de la création du fichier : %s"\
                 % ( str( e)))
            physiocap_error( aText, "CRITICAL")
            return physiocap_message_box( self, aText, "information" )

        except physiocap_exception_csv as e:
            physiocap_log_for_error( self)
            aText = self.trUtf8( "Erreur bloquante lors de la création du fichier csv : %s"\
                 % ( str( e)))
            physiocap_error( aText, "CRITICAL")
            return physiocap_message_box( self, aText, "information" )

        except physiocap_exception_mid as e:
            physiocap_log_for_error( self)
            aText = self.trUtf8( "Erreur bloquante lors de la copie du fichier MID : %s"\
                 % ( str( e)))
            physiocap_error( aText, "CRITICAL")
            return physiocap_message_box( self, aText, "information" )

        except physiocap_exception_no_mid:
            physiocap_log_for_error( self)
            aText = self.trUtf8( "Erreur bloquante : aucun fichier MID à traiter")
            physiocap_error( aText, "CRITICAL")
            return physiocap_message_box( self, aText, "information" )
        
        except physiocap_exception_stop_user:
            return physiocap_log( \
                self.trUtf8( "Arrêt de Physiocap à la demande de l'utilisateur"),
                "WARNING")
         # On remonte les autres exceptions
        except:
            raise
        finally:
            pass

        # Fin de capture des erreurs Physiocap
        # Pour le cas où postgres n'est pas accessible
        self.settings.setValue("Physiocap/leFormat", self.fieldComboFormats.currentText())
        
        physiocap_log( self.trUtf8( "%s a terminé son analyse.") % PHYSIOCAP_UNI)
        


