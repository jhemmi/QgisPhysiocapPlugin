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
from Physiocap_tools import physiocap_message_box, physiocap_question_box,\
        physiocap_log, physiocap_error, \
        physiocap_quelle_projection_demandee, physiocap_get_layer_by_ID
        
##from Physiocap_CIVC import physiocap_csv_vers_shapefile, physiocap_assert_csv, 
##        physiocap_fichier_histo, physiocap_tracer_histo, physiocap_filtrer   

from Physiocap_inter import physiocap_fill_combo_poly_or_point, physiocap_moyenne_InterParcelles

from Physiocap_intra_interpolation import physiocap_interpolation_IntraParcelles

from Physiocap_creer_arbre import physiocap_creer_donnees_resultats

from Physiocap_var_exception import *

from PyQt4 import QtGui, uic
from PyQt4.QtCore import QSettings
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import *
from qgis.gui import *

import glob
#import shutil
import time  

import os

FORM_CLASS, _ = uic.loadUiType(os.path.join( os.path.dirname(__file__), 'Physiocap_dialog_base.ui'))

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

        # Slot for boutons certains sont dans UI
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
        physiocap_log( u"Votre machine tourne sous " + machine)
        
        # Style sheet pour QProgressBar
        self.setStyleSheet( "QProgressBar {color:black; text-align:center; font-weight:bold; padding:2px;}"
           "QProgressBar:chunk {background-color:green; width: 10px; margin-left:1px;}")
#            "QProgressBar:chunk {background-color: #0088dd; width: 10px; margin-left:1px;}")
        
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
        if (self.settings.value("Affichage/IntraIsos", "YES") == "YES"):
            self.checkBoxIntraIsos.setChecked( Qt.Checked)
        else:
            self.checkBoxIntraIsos.setChecked( Qt.Unchecked)
        if (self.settings.value("Affichage/IntraImages", "YES") == "YES"):
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
            physiocap_error( u"Pas de liste des attribut pour Intra pré défini")
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
                for unFormat in ATTRIBUTS_INTRA:
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
        nom_attribut = self.fieldComboIntra.currentText()
        #physiocap_log(u"Attribut pour Intra >" + nom_attribut )
        nom_complet_point = self.comboBoxPoints.currentText().split( SEPARATEUR_NOEUD)
        if (len( nom_complet_point) !=2):
            return
        nomProjet = nom_complet_point[0] 
        idLayer   = nom_complet_point[1]
        # Eechecher min et max du layer
        layer = physiocap_get_layer_by_ID( idLayer)
        if layer is not None:
            #physiocap_log(u"Todo : Recherche de min et max de l'attribut >" + str( nom_attribut))
            try:
                index_attribut = layer.fieldNameIndex( nom_attribut)
            except:
                # Todo : Attraper cette erreur 
                return
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
            #physiocap_log(u"Look for fields of layer >" + layer.name())
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
            chemin_shapes = os.path.dirname( unicode( layer.dataProvider().dataSourceUri() ) ) ;
            if ( not os.path.exists( chemin_shapes)):
                raise physiocap_exception_rep( chemin_shapes)
            
            chemin_inter = os.path.join( chemin_shapes, VIGNETTES_INTER)
            if (os.path.exists( chemin_inter)):
                # Todo : 1.5 ? On cherche aussi si le groupe inter existe
                # On aiguille vers Intra
                self.groupBoxIntra.setEnabled( True)
                self.ButtonIntra.setEnabled( True)
                self.ButtonInter.setEnabled( False)
                # Retrouver le premier shp de point    
                
                # Todo : JHJHJH Mettre à jour la liste des attributs possibles

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
        # Todo : Vx ? refresh auto avec addedChildrenSignal ?
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
            physiocap_log( u"Votre minimum ne doit pas être plus grand que votre maximum")
            return physiocap_message_box( self,
                self.tr( u"Votre minimum ne doit pas être plus grand que votre maximum"),
                "information")              
        
        
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
            physiocap_error( u"Le shape de points n'est pas choisi." +
              "Lancez le traitement initial - bouton OK - avant de faire votre" +
              "calcul de Moyenne Inter Parcellaire")
            return physiocap_message_box( self,
                self.tr( u"Le shape de points n'est pas choisi." +
                    "Lancez le traitement initial - bouton OK - avant de faire votre" +
                    "calcul de Moyenne Inter Parcellaire" ),
                "information")        

        # Memorisation des saisies
        self.memoriser_saisies_inter_intra_parcelles()
            
        try:
            # Création des répertoires et des résultats de synthèse
            physiocap_interpolation_IntraParcelles(self)
            
        except physiocap_exception_rep as e:
            physiocap_log( ERREUR_EXCEPTION + ". Consultez le journal Physiocap Erreur",
                "WARNING")
            physiocap_error( ERREUR_EXCEPTION)
            physiocap_error(u"Erreur bloquante lors de la création du répertoire : " + str( e),
                "CRITICAL")
            return physiocap_message_box( self, self.tr( ERREUR_EXCEPTION + "\n" + \
                u"Erreur bloquante lors de la création du répertoire : " + str( e)),
                "information" )
        except physiocap_exception_vignette_exists as e:
            physiocap_log( ERREUR_EXCEPTION + ". Consultez le journal Physiocap Erreur",
                "WARNING")
            physiocap_error( ERREUR_EXCEPTION)
            physiocap_error(u"Les moyennes IntraParcellaires " + str( e) + u" existent déjà.",
                "CRITICAL")
            return physiocap_message_box( self, self.tr( ERREUR_EXCEPTION + "\n" + \
                u"Les moyennes IntraParcellaires du projet Physiocap " + str( e) + u" existent déjà. " + \
                u"Vous ne pouvez pas redemander ce calcul : vous devez détruire le groupe ou créer un nouveau projet Physiocap"),
                "information" )
        except physiocap_exception_points_invalid as e:
            physiocap_log( ERREUR_EXCEPTION + ". Consultez le journal Physiocap Erreur",
                "WARNING")
            physiocap_error( ERREUR_EXCEPTION)
            physiocap_error(u"Le fichier de points du projet" + str( e) + "ne contient pas les attributs attendus",
                "CRITICAL")
            return physiocap_message_box( self, self.tr( ERREUR_EXCEPTION + "\n" + \
                u"Le fichier de points du projet" + str( e) + " ne contient pas les attributs attendus"),
                "information" )
        except physiocap_exception_interpolation as e:
            physiocap_log( ERREUR_EXCEPTION + ". Consultez le journal Physiocap Erreur",
                "WARNING")
            physiocap_error( ERREUR_EXCEPTION)
            physiocap_error(u"L'interpolation du fichier : " + str( e) + u" n'a pu s'exécuter",
                "CRITICAL")
            return physiocap_message_box( self, self.tr( ERREUR_EXCEPTION + "\n" + \
                u"L'interpolation du fichier : " + str( e) + u" n'a pu s'exécuter"),
                "information" )
        except:
            raise
        finally:
            pass
        # Fin de capture des erreurs Physiocap        
        physiocap_log(u"Physiocap a terminé les interpolations intra parcelaire.")

                   
    def moyenne_inter_parcelles(self):
        """ Slot qui fait appel au traitement Inter Parcelles et traite exceptions """
       
        nom_complet_point = self.comboBoxPoints.currentText().split( SEPARATEUR_NOEUD)
        if ( len( nom_complet_point) != 2):
            physiocap_error( u"Le shape de points n'est pas choisi. " +
              "Lancez le traitement initial - bouton OK - avant de faire votre " +
              "calcul de Moyenne Inter Parcellaire")
            return physiocap_message_box( self,
                self.tr( u"Le shape de points n'est pas choisi. " +
                    "Lancez le traitement initial - bouton OK - avant de faire votre " +
                    "calcul de Moyenne Inter Parcellaire" ),
                "information")        

        # Eviter les appels multiples
        self.ButtonInter.setEnabled( False)
        # Memorisation des saisies
        self.memoriser_saisies_inter_intra_parcelles()
            
        try:
            # Création des répertoires et des résultats de synthèse
            physiocap_moyenne_InterParcelles(self)
            
        except physiocap_exception_rep as e:
            physiocap_log( ERREUR_EXCEPTION + ". Consultez le journal Physiocap Erreur",
                "WARNING")
            physiocap_error( ERREUR_EXCEPTION)
            physiocap_error(u"Erreur bloquante lors de la création du répertoire : " + str( e),
                "CRITICAL")
            return physiocap_message_box( self, self.tr( ERREUR_EXCEPTION + "\n" + \
                u"Erreur bloquante lors de la création du répertoire : " + str( e)),
                "information" )
        except physiocap_exception_vignette_exists as e:
            physiocap_log(u"Les moyennes InterParcellaires du projet Physiocap " + str( e) + u" existent déjà.",
                "information")
            return physiocap_message_box( self, self.tr( \
                u"Les moyennes InterParcellaires du projet Physiocap " + str( e) + u" existent déjà." + \
                u"Vous ne pouvez pas redemander ce calcul : vous pouvez acceder au calcul Intra Parcellaire"),
                "information" )
        except physiocap_exception_points_invalid as e:
            physiocap_log( ERREUR_EXCEPTION + ". Consultez le journal Physiocap Erreur",
                "WARNING")
            physiocap_error( ERREUR_EXCEPTION)
            physiocap_error(u"Le fichier de points du projet" + str( e) + "ne contient pas les attributs attendus",
                "CRITICAL")
            return physiocap_message_box( self, self.tr( ERREUR_EXCEPTION + "\n" + \
                u"Le fichier de points du projet" + str( e) + " ne contient pas les attributs attendus"),
                "information" )
        except:
            raise
        finally:
            pass
        # Fin de capture des erreurs Physiocap        
        
        self.groupBoxIntra.setEnabled( True)
        self.ButtonIntra.setEnabled( True)
        physiocap_log(u"Physiocap a terminé les moyennes inter parcelaire.")

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

    def reject( self ):
        """Close when bouton is Cancel"""
        #self.textEdit.clear()
        QDialog.reject( self)
                
    def accept( self ):
        """Verify when bouton is OK"""
        # Vérifier les valeurs saisies
        # QT confiance et initilaisation par Qsettings sert d'assert sur la
        # cohérence des variables saisies

        repertoire_data = self.lineEditDirectoryPhysiocap.text()
        if ((repertoire_data == "") or ( not os.path.exists( repertoire_data))):
            physiocap_error( u"Pas de répertoire de donnée spécifié")
            return physiocap_message_box( self, 
                self.tr( u"Pas de répertoire de données brutes spécifié" ),
                "information")
        if self.lineEditProjet.text() == "":
            physiocap_error( u"Pas de nom de projet spécifié")
            return physiocap_message_box( self,
                self.tr( u"Pas de nom de projet spécifié" ),
                "information")
                 
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
            physiocap_log(u"La recherche des MID fouille l'arbre de données")
        self.settings.setValue("Physiocap/recursif", recursif )
            
        laProjection, EXT_SHP, EXT_PRJ, EXT_RASTER, EPSG_NUMBER = physiocap_quelle_projection_demandee( self) 
        self.settings.setValue("Physiocap/laProjection", laProjection)
        physiocap_log(u"Projection des shapefiles demandée en " + laProjection)
           
        #self.settings.setValue("Physiocap/dernier_repertoire", self.lineEditDernierProjet.text() )
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

        # Onglet Histogramme
        TRACE_HISTO = "NO"
        if self.checkBoxHistogramme.isChecked():
            TRACE_HISTO = "YES"
            physiocap_log(u"Les histogrammes sont attendus")
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

            
        # ########################################
        # Gestion de capture des erreurs Physiocap
        # ########################################
        try:
            # Création des répertoires et des résultats de synthèse
            retour = physiocap_creer_donnees_resultats( self, laProjection, EXT_SHP, EXT_PRJ,
                details, TRACE_HISTO, recursif)
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
        except physiocap_exception_stop_user:
            return physiocap_log( u"Arrêt de Physiocap à la demande de l'utilisateur",
                "WARNING")
         # On remonte les autres exceptions
        except:
            raise
        finally:
            pass
            # Todo : Vx ? Se mettre sur l'onglet synthese ou (histo)

        
        # Fin de capture des erreurs Physiocap
        
        physiocap_log(u"Physiocap a terminé son analyse.")
        
    

