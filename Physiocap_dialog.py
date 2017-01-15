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
 Les slots sont définis et activés.
 La gestion des assert avant traitement et des retours d'exception se trouve 
 dans ce module 

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

from Physiocap_tools import physiocap_message_box, \
        physiocap_log_for_error, physiocap_log, physiocap_error, \
        physiocap_quelle_projection_demandee, physiocap_get_layer_by_ID
#        physiocap_get_uri_by_layer, \

from Physiocap_creer_arbre import PhysiocapFiltrer
from Physiocap_inter import PhysiocapInter, physiocap_fill_combo_poly_or_point
from Physiocap_intra_interpolation import PhysiocapIntra #, physiocap_fill_combo_poly_or_point

from Physiocap_var_exception import *

from PyQt4 import QtGui, uic
from PyQt4.QtCore import QSettings, Qt, QUrl
from PyQt4.QtGui import QDialogButtonBox, QDialog, QPixmap, QFileDialog, QDesktopServices
from qgis.core import QGis, QgsProject, QgsMapLayerRegistry, QgsMapLayer, \
    GEOSRID, GEO_EPSG_CRS_ID

if platform.system() == 'Windows':
    import win32api
    
FORM_CLASS, _ = uic.loadUiType(os.path.join( os.path.dirname(__file__), 'Physiocap_dialog_base.ui'))

class PhysiocapAnalyseurDialog( QtGui.QDialog, FORM_CLASS):
    def __init__(self, parent=None):
        """Constructeur du dialogue Physiocap 
        Initialisation et recupération des variables, sauvegarde des parametres.
        Les slots sont définis et activés.
        """
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
       
        # Slot for boutons : ces deux sont déjà sont dans UI
        ##self.buttonBox.button( QDialogButtonBox.Ok ).pressed.connect(self.accept)
        ##self.buttonBox.button( QDialogButtonBox.Cancel ).pressed.connect(self.reject)
        self.buttonBox.button( QDialogButtonBox.Help ).pressed.connect(self.slot_demander_aide)
        self.buttonContribuer.pressed.connect(self.slot_demander_contribution)
        # Slot pour données brutes et pour données cibles
        self.toolButtonDirectoryPhysiocap.pressed.connect( self.slot_lecture_repertoire_donnees_brutes )  
        self.toolButtonDirectoryFiltre.pressed.connect( self.slot_lecture_repertoire_donnees_cibles)  
        # Slot pour le groupe vignoble
        self.checkBoxInfoVignoble.stateChanged.connect( self.slot_bascule_details_vignoble)

       
        # Inter
        self.comboBoxPolygone.currentIndexChanged[int].connect( self.slot_maj_champ_poly_liste )
        self.ButtonInter.pressed.connect(self.slot_moyenne_inter_parcelles)
        self.ButtonInterRefresh.pressed.connect(self.slot_liste_inter_parcelles)
        self.groupBoxInter.setEnabled( False)
        
        # Intra        
        self.comboBoxPoints.currentIndexChanged[int].connect( self.slot_maj_points_choix_inter_intra )
        self.fieldComboIntra.currentIndexChanged[int].connect( self.slot_min_max_champ_intra )
        self.ButtonIntra.pressed.connect(self.slot_interpolation_intra_parcelles)
        self.groupBoxIntra.setEnabled( False)
        self.ButtonIntra.setEnabled( False)
        
        # Slot pour les contours
        # self.toolButtonContours.pressed.connect( self.lecture_shape_contours )   
              
        machine = platform.system()
        physiocap_log( self.trUtf8( "Votre machine tourne sous QGIS {0} et {1} ").\
            format( QGis.QGIS_VERSION, machine))        
##        physiocap_log( self.trUtf8( "Test 1 et 2 : {0} <===> {1} ").\
##            format( PHYSIOCAP_TEST1, PHYSIOCAP_TEST2))
##        physiocap_log( self.trUtf8( "Test 3 et 4 : {0} <===> {1} ").\
##            format( PHYSIOCAP_TEST3, PHYSIOCAP_TEST4))
##        physiocap_log( self.trUtf8( "Qgis attend des couches de projection SRID {0} CRS_ID {1} ").\
##            format( GEOSRID, GEO_EPSG_CRS_ID ))
        
        
        # Style sheet pour QProgressBar
        self.setStyleSheet( "QProgressBar {color:black; text-align:center; font-weight:bold; padding:2px;}"
           "QProgressBar:chunk {background-color:green; width: 10px; margin-left:1px;}")
        
        ###############
        # Récuperation dans les settings (derniers parametres saisies)
        ###############
        self.settings= QSettings(PHYSIOCAP_NOM, PHYSIOCAP_NOM)
        # Initialisation des parametres à partir des settings
        nom_projet = self.settings.value("Physiocap/projet", NOM_PROJET)
        self.lineEditProjet.setText( nom_projet)
        
        if (self.settings.value("Physiocap/recursif") == "YES"):
            self.checkBoxRecursif.setChecked( Qt.Checked)
        else:
            self.checkBoxRecursif.setChecked( Qt.Unchecked)
        
        # Nom du projet et des répertoires
        repertoire_brut = self.settings.value("Physiocap/repertoire",
            REPERTOIRE_DONNEES_BRUTES)
        self.lineEditDirectoryPhysiocap.setText( repertoire_brut )
        self.lineEditDernierProjet.setText( self.settings.value("Physiocap/dernier_repertoire",
            ""))    
        # Répertoire cibles apres filtre
        repertoire_cible = self.settings.value("Physiocap/cible_repertoire", "VIDE")
        if ( repertoire_cible == "VIDE"):
            repertoire_cible = repertoire_brut
        self.lineEditDirectoryFiltre.setText( repertoire_cible)
                
        # Consolidation
        if (self.settings.value("Physiocap/consolidation") == "YES"):
            self.checkBoxConsolidation.setChecked( Qt.Checked)
        else:
            self.checkBoxConsolidation.setChecked( Qt.Unchecked)
        
            
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
            physiocap_error( self, self.trUtf8( "Pas de liste de cépage pré défini"))
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
            physiocap_error( self, self.trUtf8( "Pas de liste de mode de taille pré défini"))
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
            physiocap_error( self, self.trUtf8( "Pas de liste des formats de vecteurs pré défini"))
        else:
            self.fieldComboFormats.clear( )
            #uri = physiocap_get_uri_by_layer( self)
            uri = None
            if uri != None:
                self.fieldComboFormats.addItems( FORMAT_VECTEUR )
            else:
                self.fieldComboFormats.addItem( FORMAT_VECTEUR[ 0] )
                self.fieldComboFormats.setEnabled( False)
             # Retrouver le format de  settings
            i=0
            self.fieldComboFormats.setCurrentIndex( 0)
            leFormat = self.settings.value("Physiocap/leFormat", "xx") 
            for unFormat in FORMAT_VECTEUR:
                if ( unFormat == leFormat):
                    self.fieldComboFormats.setCurrentIndex( i)
                    #physiocap_log( self.trUtf8( "Format retrouvé")) 
                i=i+1        

        # Remplissage de la liste de SHAPE Filtre
        # DIAMETRE : Cas unique
        self.fieldComboShapeDiametre.clear( )
        self.fieldComboShapeDiametre.addItem( "Sans vitesse nulle **")
        self.fieldComboShapeDiametre.setCurrentIndex( 0)                
 
        # SARMENT
        self.fieldComboShapeSarment.setCurrentIndex( 0)   
        if len( CHEMIN_SHAPES_FILTRATION) == 0:
            self.fieldComboShapeSarment.clear( )
            aText = self.trUtf8( "Pas de liste de shapefiles à afficher apres filtration")
            physiocap_log( aText)
            physiocap_error( self, aText)
        else:
            leChoixDeShape = int( self.settings.value("Physiocap/leChoixShapeSarment", -1)) 
            # Cas initial
            self.fieldComboShapeSarment.clear( )
            self.fieldComboShapeSarment.addItems( CHEMIN_SHAPES_FILTRATION )
            if ( leChoixDeShape == -1):
                self.fieldComboShapeSarment.setCurrentIndex( 0)                
            else:
                # Le combo a déjà été rempli, on retrouve le choix
                self.fieldComboShapeSarment.setCurrentIndex( leChoixDeShape)
 
        # BIOMASSE
        self.fieldComboShapeBiomasse.setCurrentIndex( 0)   
        if len( CHEMIN_SHAPES_FILTRATION) == 0:
            self.fieldComboShapeBiomasse.clear( )
            aText = self.trUtf8( "Pas de liste de shapefiles à afficher apres filtration")
            physiocap_log( aText)
            physiocap_error( self, aText)
        else:
            leChoixDeShape = int( self.settings.value("Physiocap/leChoixShapeBiomasse", -1)) 
            # Cas initial
            self.fieldComboShapeBiomasse.clear( )
            self.fieldComboShapeBiomasse.addItems( CHEMIN_SHAPES_FILTRATION )
            if ( leChoixDeShape == -1):
                self.fieldComboShapeBiomasse.setCurrentIndex( 0)                
            else:
                # Le combo a déjà été rempli, on retrouve le choix
                self.fieldComboShapeBiomasse.setCurrentIndex( leChoixDeShape)
 
        # VITESSE
        self.fieldComboShapeVitesse.setCurrentIndex( 0)   
        if len( CHEMIN_SHAPES_FILTRATION) == 0:
            self.fieldComboShapeVitesse.clear( )
            aText = self.trUtf8( "Pas de liste de shapefiles à afficher apres filtration")
            physiocap_log( aText)
            physiocap_error( self, aText)
        else:
            leChoixDeShape = int( self.settings.value("Physiocap/leChoixShapeVitesse", -1)) 
            # Cas initial
            self.fieldComboShapeVitesse.clear( )
            self.fieldComboShapeVitesse.addItems( CHEMIN_SHAPES_FILTRATION )
            if ( leChoixDeShape == -1):
                self.fieldComboShapeVitesse.setCurrentIndex( 1)                
            else:
                # Le combo a déjà été rempli, on retrouve le choix
                self.fieldComboShapeVitesse.setCurrentIndex( leChoixDeShape)
 
        # Remplissage du choix de calcul isoligne
        self.fieldComboAideIso.setCurrentIndex( 0)   
        if len( CHOIX_ISO) == 0:
            self.fieldComboAideIso.clear( )
            aText = self.trUtf8( "Pas d'option de choix d'aide au calcul iso")
            physiocap_log( aText)
            physiocap_error( self, aText)
        else:
            leChoixAideIso = int( self.settings.value("Physiocap/leChoixAideIso", -1)) 
            # Cas inital
            self.fieldComboAideIso.clear( )
            self.fieldComboAideIso.addItems( CHOIX_ISO )
            if ( leChoixAideIso == -1):
                self.fieldComboAideIso.setCurrentIndex( 0)                
            else:
                # Le combo a déjà été rempli, on retrouve le choix
                self.fieldComboAideIso.setCurrentIndex( leChoixAideIso) 

        # Remplissage de la liste de CHEMIN_TEMPLATES
        self.fieldComboThematiques.setCurrentIndex( 0)   
        if len( CHEMIN_TEMPLATES) == 0:
            self.fieldComboThematiques.clear( )
            aText = self.trUtf8( "Pas de répertoire de thématiques pré défini")
            physiocap_log( aText)
            physiocap_error( self, aText)
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
                if ( leChoixDeThematiques == 1): 
                    # On est dans le cas où l'utilisateur a pri sla main sur ces qml
                    # autorisation de modifier les nom de qml
                    self.groupBoxThematiques.setEnabled( True)
                    themeDiametre = self.settings.value("Physiocap/themeDiametre", "x Diametre 4 Jenks")
                    self.lineEditThematiqueDiametre.setText( themeDiametre )
                    themeSarment = self.settings.value("Physiocap/themeSarment", "x Sarment 4 Jenks")
                    self.lineEditThematiqueSarment.setText( themeSarment )
                    themeBiomasse = self.settings.value("Physiocap/themeBiomasse", "Biomasse 4 Jenks")
                    self.lineEditThematiqueBiomasse.setText( themeBiomasse )
                    themeVitesse = self.settings.value("Physiocap/themeVitesse", "Vitesse")
                    self.lineEditThematiqueVitesse.setText( themeVitesse )
                    # Inter
                    themeDiametre = self.settings.value("Physiocap/themeInterDiametre", "Diametre")
                    self.lineEditThematiqueInterDiametre.setText( themeDiametre )
                    themeSarment = self.settings.value("Physiocap/themeInterSarment", "Sarment")
                    self.lineEditThematiqueInterSarment.setText( themeSarment )
                    themeBiomasse = self.settings.value("Physiocap/themeInterBiomasse", "Biomasse")
                    self.lineEditThematiqueInterBiomasse.setText( themeBiomasse )
                    themeLibelle = self.settings.value("Physiocap/themeInterLibelle", "Moyenne Inter")
                    self.lineEditThematiqueInterLibelle.setText( themeLibelle )
                    # inter moyenne et points
                    themeMoyenne = self.settings.value("Physiocap/themeInterMoyenne", "Moyenne Inter")
                    self.lineEditThematiqueInterMoyenne.setText( themeMoyenne )
                    themePoints = self.settings.value("Physiocap/themeInterPoints", "Diametre 4 Jenks")
                    self.lineEditThematiqueInterPoints.setText( themePoints )
                    # intra
                    themeIso = self.settings.value("Physiocap/themeIntraIso", "Isolignes")
                    self.lineEditThematiqueIntraIso.setText( themeIso )
                    themeImage = self.settings.value("Physiocap/themeIntraImage", "Intra")
                    self.lineEditThematiqueIntraImage.setText( themeImage )
                else:
                    # Cas repertoire du plugin
                    self.groupBoxThematiques.setEnabled( False)
                    # Remettre les nom de thematiques par defaut 
                    self.lineEditThematiqueDiametre.setText("Diametre 4 Jenks")
                    self.settings.setValue("Physiocap/themeDiametre", "Diametre 4 Jenks")
                    self.lineEditThematiqueSarment.setText("Sarment 4 Jenks")
                    self.settings.setValue("Physiocap/themeSarment", "Sarment 4 Jenks")
                    self.lineEditThematiqueBiomasse.setText("Biomasse 4 Jenks")
                    self.settings.setValue("Physiocap/themeBiomasse", "Biomasse 4 Jenks")
                    self.lineEditThematiqueVitesse.setText("Vitesse")
                    self.settings.setValue("Physiocap/themeVitesse", "Vitesse")
                    # Inter
                    self.lineEditThematiqueInterDiametre.setText("Diametre")
                    self.settings.setValue("Physiocap/themeInterDiametre", "Diametre")
                    self.lineEditThematiqueInterSarment.setText("Sarment")
                    self.settings.setValue("Physiocap/themeInterSarment", "Sarment")
                    self.lineEditThematiqueInterBiomasse.setText("Biomasse")
                    self.settings.setValue("Physiocap/themeInterBiomasse", "Biomasse")
                    self.lineEditThematiqueInterLibelle.setText("Moyenne Inter")
                    self.settings.setValue("Physiocap/themeInterLibelle", "Moyenne Inter")
                    # inter moyenne et points
                    self.lineEditThematiqueInterMoyenne.setText("Moyenne Inter")
                    self.settings.setValue("Physiocap/themeInterMoyenne", "Moyenne Inter")
                    self.lineEditThematiqueInterPoints.setText("Diametre 4 Jenks")
                    self.settings.setValue("Physiocap/themeInterPoints", "Diametre 4 Jenks")     
                    # Intra
                    self.lineEditThematiqueIntraIso.setText("Isolignes")
                    self.settings.setValue("Physiocap/themeIntraIso", "Isolignes")
                    self.lineEditThematiqueIntraImage.setText("Intra")
                    self.settings.setValue("Physiocap/themeIntraImage", "Intra")
                    
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
        self.slot_calcul_densite()
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
            physiocap_error( self, aText)
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
        self.spinBoxPixel.setValue( float( self.settings.value("Physiocap/pixelIntra", 0.5 )))
        self.spinBoxDoubleRayon.setValue( float( self.settings.value("Physiocap/rayonIntra", 12 )))
        self.slot_rayon()
        self.spinBoxIsoMin.setValue( int( self.settings.value("Physiocap/isoMin", 1 )))
        self.spinBoxIsoMax.setValue( int( self.settings.value("Physiocap/isoMax", 1000 )))
        self.spinBoxNombreIso.setValue( int( self.settings.value("Physiocap/isoNombres", 5 )))
        # On initalise le nombre de distance Iso
        self.slot_iso_distance()
         
        if (self.settings.value("Physiocap/library") == "SAGA"):
            self.radioButtonSAGA.setChecked(  Qt.Checked)
            self.spinBoxPower.setEnabled( False)
        else:
            self.radioButtonGDAL.setChecked(  Qt.Checked)
        
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
        if (self.settings.value("Affichage/biomasse", "NO") == "YES"):
            self.checkBoxBiomasse.setChecked( Qt.Checked)
        else:
            self.checkBoxBiomasse.setChecked( Qt.Unchecked)
        if (self.settings.value("Affichage/vitesse", "NO") == "YES"):
            self.checkBoxVitesse.setChecked( Qt.Checked)
        else:
            self.checkBoxVitesse.setChecked( Qt.Unchecked)        
        # Choix d'affichage Inter
        if (self.settings.value("Affichage/InterDiametre", "YES") == "YES"):
            self.checkBoxInterDiametre.setChecked( Qt.Checked)
        else:
            self.checkBoxInterDiametre.setChecked( Qt.Unchecked)
        if (self.settings.value("Affichage/InterSarment", "NO") == "YES"):
            self.checkBoxInterSarment.setChecked( Qt.Checked)
        else:
            self.checkBoxInterSarment.setChecked( Qt.Unchecked)
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
        self.spinBoxInterrangs.valueChanged.connect( self.slot_calcul_densite)
        self.spinBoxInterceps.valueChanged.connect( self.slot_calcul_densite)
 
        # Calcul du commentaire sur pixel et rayon en unite de carte
        self.radioButtonSAGA.toggled.connect( self.slot_rayon)
        #self.radioButtonGDAL.toggled.connect( self.slot_rayon)
        self.radioButtonGPS.toggled.connect( self.slot_rayon)
        #self.radioButtonL93.toggled.connect( self.slot_rayon)
      
        # Calcul dynamique du intervale Isolignes
        self.spinBoxIsoMin.valueChanged.connect( self.slot_iso_distance)
        self.spinBoxIsoMax.valueChanged.connect( self.slot_iso_distance)
        self.spinBoxNombreIso.valueChanged.connect( self.slot_iso_distance)
        
        # Alerte GPS
        self.radioButtonGPS.toggled.connect( self.slot_GPS_alert)

 
        # Remplissage de la liste de ATTRIBUTS_INTRA 
        self.fieldComboIntra.setCurrentIndex( 0)   
        if len( ATTRIBUTS_INTRA) == 0:
            self.fieldComboIntra.clear( )
            physiocap_error( self, self.trUtf8( "Pas de liste des attributs pour Intra pré défini"))
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
        
        # Appel à contrib
        self.slot_Contrib_alert()
        # Contributeurs : Icone
        self.label_IFVV.setPixmap( QPixmap( os.path.join( REPERTOIRE_HELP, 
            "Logo_IFV.png"))) 
        self.label_Moet.setPixmap( QPixmap( os.path.join( REPERTOIRE_HELP, 
            "Logo_Moet.png"))) 
        
        # Init fin 
        return


    
    # ################
    #  Différents SLOT
    # ################

    # FIELDS
    def slot_min_max_champ_intra( self ):
        """ Create a list of fields for the current vector point in fieldCombo Box"""
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
                aText = self.trUtf8( "L'attribut {0} n'existe pas dans les données à disposition.").\
                format( nom_attribut)
                aText = aText + \
                    self.trUtf8( "L'interpolation n'est pas possible. Recréer un nouveau projet Physiocap.")
                physiocap_error( self, aText, "CRITICAL")
                return physiocap_message_box( self, aText, "information")
            valeurs = []
            for un_point in layer.getFeatures():
                 valeurs.append( un_point.attributes()[index_attribut])
##            physiocap_log(u"Min et max de > " + str( nom_attribut) + " sont "  + \
##                str( min(valeurs)) + "==" + str(max(valeurs)))
            self.spinBoxIsoMax.setValue( int( max(valeurs) ))
            self.spinBoxIsoMin.setValue( int( min(valeurs) ))

    def slot_maj_champ_poly_liste( self ):
        """ Create a list of fields having unique values for the current vector in fieldCombo Box"""
        nom_complet_poly = self.comboBoxPolygone.currentText().split( SEPARATEUR_NOEUD)
        inputLayer = nom_complet_poly[0] 
        self.fieldComboContours.clear()
        layer = self.lister_nom_couches( inputLayer)
        self.fieldComboContours.addItem( "NOM_PHY")
        self.fieldComboContours.setCurrentIndex( 0)
        if layer is not None:
            # On exclut les layer qui ne sont pas de type 0 (exemple 1 raster)
            if ( layer.type() == 0):
                i = 1 # Demarre à 1 car NOM_PHY est dejà ajouté
                dernierAttribut = self.settings.value("Physiocap/attributPoly", "xx") 
                # OLD for index, field in enumerate(layer.dataProvider().fields()):
                for index, field in enumerate(layer.dataProvider().fields()):
                    # Vérifier si les valeurs du field name sont unique
                    valeur_unique = "YES"
                    valeur_dic = {}
                    mon_nom = field.name()
                    #idx = layer.fieldNameIndex(mon_nom)
                    k = 0
                    iter = layer.getFeatures()
                    for feature in iter:
                        try:
                            if feature.attributes()[index] == None:
                                valeur_unique = "NO"
                            elif valeur_dic.has_key( feature.attributes()[index]) ==1:
                                valeur_unique = "NO"
                            else:
                                valeur_dic[ feature.attributes()[index]] = k
                        except:
                            valeur_unique = "NO"
                        if valeur_unique == "NO":
                            break
                        k = k+1
                    
                    if valeur_unique == "YES":
                        self.fieldComboContours.addItem( mon_nom )
                        if ( str( mon_nom) == dernierAttribut):
                            self.fieldComboContours.setCurrentIndex( i)
                        i=i+1
                    
    def slot_maj_points_choix_inter_intra( self ):
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
                              


    def lister_nom_couches( self, layerName ):
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
    def slot_lecture_repertoire_donnees_brutes( self):
        """Catch directory for raw data"""
        # Récuperer dans setting le nom du dernier ou sinon REPERTOIRE_DONNEES_BRUTES
        self.settings= QSettings(PHYSIOCAP_NOM, PHYSIOCAP_NOM)
        exampleDirName =  self.settings.value("Physiocap/repertoire", REPERTOIRE_DONNEES_BRUTES)
        
        dirName = QFileDialog.getExistingDirectory( self, self.trUtf8 ("Choisir le répertoire de vos données Physiocap brutes (MID)"),
                                                 exampleDirName,
                                                 QFileDialog.ShowDirsOnly
                                                 | QFileDialog.DontResolveSymlinks);
        if len( dirName) == 0:
          return
        self.lineEditDirectoryPhysiocap.setText( dirName )
        
     # Repertoire données brutes :
    def slot_lecture_repertoire_donnees_cibles( self):
        """Catch directory for new filtered data"""
        # Récuperer dans setting le nom du dernier ou sinon REPERTOIRE_DONNEES_BRUTES
        self.settings= QSettings(PHYSIOCAP_NOM, PHYSIOCAP_NOM)
        exampleDirName =  self.settings.value("Physiocap/cible_repertoire", "Vide")
        # Cas vraiment inital
        if exampleDirName == "Vide":
            exampleDirName =  self.settings.value("Physiocap/repertoire", REPERTOIRE_DONNEES_BRUTES)
            
        dirName = QFileDialog.getExistingDirectory( self, self.trUtf8 ("Choisir le répertoire qui contiendra les résultats les données filtrées par Physiocap"),
                                                 exampleDirName,
                                                 QFileDialog.ShowDirsOnly
                                                 | QFileDialog.DontResolveSymlinks);
        if len( dirName) == 0:
          return
        self.lineEditDirectoryFiltre.setText( dirName )
 
    def slot_liste_inter_parcelles( self):
        """ Rafraichit les listes avant le calcul inter parcelles"""
        nombre_poly = 0
        nombre_point = 0
        nombre_poly, nombre_point = physiocap_fill_combo_poly_or_point( self)

        if (( nombre_poly > 0) and ( nombre_point > 0)):
            # Liberer le bouton "moyenne"
            self.groupBoxInter.setEnabled( True)
            self.slot_maj_champ_poly_liste()
            self.slot_min_max_champ_intra()
        else:
            self.groupBoxInter.setEnabled( False)
        
        # Mise à jour du commentaire pour le rayon
        self.slot_rayon()
            
    def slot_Contrib_alert( self):
        """ 
        Toute les x utilisations, rappeler à l'utilisateur qu'il est bien de contribuer
        """
        # Vérifier si le nombre d'utilisation est atteint
        self.settings= QSettings( PHYSIOCAP_NOM, PHYSIOCAP_NOM)
        niveau_utilisation = int( self.settings.value("Affichage/Contrib_alert", 0))
        if ( niveau_utilisation < 10):
            self.settings.setValue("Affichage/Contrib_alert", \
                niveau_utilisation + 1)
            return 
          
        aText = self.trUtf8( "{0} vous rapelle que ce logiciel ouvert et libre n'est pas exempt de besoins. ").\
                    format( PHYSIOCAP_UNI)
        aText = aText + self.trUtf8( "L'extension est diffusée gratuitement par le biais de la distribution ")
        aText = aText + self.trUtf8( "QGIS pour vous faciliter son utilisation. Ce choix est lié à la grande importance ")
        aText = aText + self.trUtf8( "de rester maître de ses données. L'extension a besoin de votre aide. ")
        aText = aText + self.trUtf8( "Contribuez simplement à la hauteur du service rendu. ")
        aText = aText + self.trUtf8( 'Trois clics : Onglet "A Propos" puis bouton "Contribuer" et passez par votre navigateur')
        # Mémoriser que le message a été donné
        self.settings.setValue("Affichage/Contrib_alert", 0)
        return physiocap_message_box( self, aText, "information")
    
    def slot_GPS_alert( self):
        """ 
        Quand GPS est choisi, on monte une alerte
        """
        # Vérifier si le message a déjà été donné
        self.settings= QSettings( PHYSIOCAP_NOM, PHYSIOCAP_NOM)
        if (self.settings.value("Affichage/GPSalertIntra", "NO") == "YES"):
            return
            
        #physiocap_message_box( self, "Dans slot_GPS_alert", "information")   
        aText = self.trUtf8( "{0} ne conseille le choix GPS si vous souhaitez réaliser").\
                    format( PHYSIOCAP_UNI)
        aText = aText + self.trUtf8( "une interpolatioin INTRA parcellaire. ")
        aText = aText + self.trUtf8( "Il n'est pas conseillé d'interpoler dans un systeme non plan. ")
        aText = aText + self.trUtf8( "En effet, selon votre lattitude, l'unite des coordonnées X et Y ")
        aText = aText + self.trUtf8( "peuvent varier. L'interpolation basée sur l'inverse des distances ")
        aText = aText + self.trUtf8( "pourra donc être déformée par rapport à un calcul dans un systeme ")
        aText = aText + self.trUtf8( "plan (comme L93).")
        # Mémoriser que le message a été donné
        self.settings.setValue("Affichage/GPSalertIntra", "YES")
        
        return physiocap_message_box( self, aText, "information")
            
    def slot_rayon( self):
        """ 
        Selon GPS ou L93 et SAGA ou GDAL mise en place du x=commentaire pour le
        rayon en unite de carte
        """
        # retrouve sans QT
        #physiocap_message_box( self, "Dans slot Rayon", "information")   
        self.lineEditDoubleRayon.setText( "Etrange et bizarre")
                
        self.spinBoxDoubleRayon.setEnabled( True)
        
        if self.radioButtonSAGA.isChecked():
            self.spinBoxPixel.setEnabled( True)
            if self.radioButtonL93.isChecked():
                aText = self.trUtf8( "{0} conseille un rayon d'interpolation entre 5 et 15").\
                    format( PHYSIOCAP_UNI)
                self.lineEditDoubleRayon.setText( aText)
            if self.radioButtonGPS.isChecked():
                aText = self.trUtf8( "{0} conseille un rayon d'interpolation proche de 0.000085 (8.85E-5)").\
                    format( PHYSIOCAP_UNI)
                self.lineEditDoubleRayon.setText( aText)
                
        if self.radioButtonGDAL.isChecked():
            self.spinBoxPixel.setEnabled( False)
            if self.radioButtonL93.isChecked():
                # Proposer un texte
                aText = self.trUtf8( "{0} conseille un rayon d'interpolation proche de 5").\
                    format( PHYSIOCAP_UNI)
                self.lineEditDoubleRayon.setText( aText)
            if self.radioButtonGPS.isChecked():
                # Proposer un texte
                aText = self.trUtf8( "{0} conseille un rayon d'interpolation proche de 0.00015 (1.5E-4)").\
                    format( PHYSIOCAP_UNI)
                self.lineEditDoubleRayon.setText( aText)

        return 0

    def slot_iso_distance( self):
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
        self.settings.setValue("Physiocap/rayonIntra", float( self.spinBoxDoubleRayon.value()))
        self.settings.setValue("Physiocap/pixelIntra", float( self.spinBoxPixel.value()))
        self.settings.setValue("Physiocap/isoMin", float( self.spinBoxIsoMin.value()))
        self.settings.setValue("Physiocap/isoMax", float( self.spinBoxIsoMax.value()))
        self.settings.setValue("Physiocap/isoNombres", float( self.spinBoxNombreIso.value()))

        self.settings.setValue("Physiocap/leChoixAideIso", self.fieldComboAideIso.currentIndex())
        
        self.settings.setValue("Physiocap/leDirThematiques", self.fieldComboThematiques.currentText())
        self.settings.setValue("Physiocap/leChoixDeThematiques", self.fieldComboThematiques.currentIndex())
        
        # Sauver les affichages Inter
        diametre = "NO"
        if self.checkBoxInterDiametre.isChecked():
            diametre = "YES"
        self.settings.setValue("Affichage/InterDiametre", diametre )
        sarment = "NO"
        if self.checkBoxInterSarment.isChecked():
            sarment = "YES"
        self.settings.setValue("Affichage/InterSarment", sarment )
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
        
    def slot_interpolation_intra_parcelles(self):
        """ Slot qui fait appel au interpolation Intra Parcelles et traite exceptions """
       
        nom_complet_point = self.comboBoxPoints.currentText().split( SEPARATEUR_NOEUD)
        if ( len( nom_complet_point) != 2):
            aText = self.trUtf8( "Le shape de points n'est pas choisi. ")
            aText = aText + self.trUtf8( "Créer une nouvelle instance de projet - bouton OK - ")
            aText = aText + self.trUtf8( "avant de faire votre calcul de Moyenne Inter puis Intra Parcellaire")   
            physiocap_error( self, aText, "CRITICAL")
            return physiocap_message_box( self, aText, "information" )

        # Memorisation des saisies
        self.memoriser_saisies_inter_intra_parcelles()
            
        try:
            # Création des répertoires et des résultats de synthèse
            intra = PhysiocapIntra( self)
            intra.physiocap_interpolation_IntraParcelles( self)
            
        except physiocap_exception_rep as e:
            physiocap_log_for_error( self)
            aText = self.trUtf8( "Erreur bloquante lors de la création du répertoire : {0}").\
                format( e)
            physiocap_error( self, aText, "CRITICAL")
            return physiocap_message_box( self, aText, "information" )
        except physiocap_exception_vignette_exists as e:
            physiocap_log_for_error( self)
            aText = self.trUtf8( "Les moyennes IntraParcellaires dans {0} existent déjà. ").\
                format( e)
            aText = aText + self.trUtf8( "Vous ne pouvez pas redemander ce calcul :\n")
            aText = aText + self.trUtf8( "- Vous pouvez détruire le groupe dans le panneau des couches\n- ou ") 
            aText = aText + self.trUtf8( "créer une nouvelle instance de projet Physiocap")
            physiocap_error( self, aText, "CRITICAL")
            return physiocap_message_box( self, aText, "information" )
        except physiocap_exception_points_invalid as e:
            physiocap_log_for_error( self)
            aText = self.trUtf8( "Le fichier de points du projet {0} ne contient pas les attributs attendus").\
                format( e)
            physiocap_error( self, aText, "CRITICAL")
            return physiocap_message_box( self, aText, "information" )
        except physiocap_exception_interpolation as e:
            physiocap_log_for_error( self)
            allFile = str(e)   # avec str(e) on edite du garbage
            finFile = '"...' + allFile[-60:-1] + '"'            
            aText = self.trUtf8( "L'interpolation de : {0} n'a pu s'exécuter entièrement. ").\
                format( finFile)
            aText = aText + self.trUtf8( "\n - Si la librairie d'interpolation (SAGA ou GDAL) ")
            aText = aText + self.trUtf8( "est bien installée et activée dans {0}. ").\
                format( self.trUtf8( "Traitement"))
            aText = aText + self.trUtf8( "\n - Si vous n'avez pas des contours bizarres.")
            aText = aText + self.trUtf8( "\n - Si vous n'avez pas détruit de couches récemment...")
            aText = aText + self.trUtf8( "\n - Si vous n'avez pas modifié de contexte L93/GPS.")
            aText = aText + self.trUtf8( "\nAlors vous pouvez contacter le support avec vos traces et données brutes")
            physiocap_error( self, aText, "CRITICAL")
            return physiocap_message_box( self, aText, "information" )
        except physiocap_exception_no_processing:
            physiocap_log_for_error( self)
            aText = self.trUtf8( "L'extension {0} n'est pas accessible. ").\
                format( self.trUtf8( "Traitement"))
            aText = aText + self.trUtf8( "Pour réaliser l'interpolation intra parcellaire, vous devez")
            aText = aText + self.trUtf8( " installer l'extension {0} (menu Extension => Installer une extension)").\
                format( self.trUtf8( "Traitement"))
            physiocap_error( self, aText)
            return physiocap_message_box( self, aText, "information")
        except physiocap_exception_no_saga:
            physiocap_log_for_error( self)
            aText = self.trUtf8( "SAGA n'est pas accessible. ")
            aText = aText + self.trUtf8( "Pour réaliser l'interpolation intra parcellaire, vous devez")
            aText = aText + self.trUtf8( " installer SAGA")
            physiocap_error( self, aText)
            return physiocap_message_box( self, aText, "information")
        except physiocap_exception_project_contour_incoherence as e:
            physiocap_log_for_error( self)
            aText = self.trUtf8( "Le polygone de contour {0} n'est pas retrouvé. ").\
                format( e)
            aText = aText + self.trUtf8( "Une incohérence entre le projet Physiocap et ses données vous oblige à ")
            aText = aText + self.trUtf8( "créer une nouvelle instance de projet Physiocap")
            physiocap_error( self, aText)
            return physiocap_message_box( self, aText, "information") 
        except physiocap_exception_project_point_incoherence as e:
            physiocap_log_for_error( self)
            aText = self.trUtf8( "La couche de point {0} n'est pas retrouvé. ").\
                format( e)
            aText = aText + self.trUtf8( "Une incohérence entre le projet Physiocap et ses données vous oblige à ")
            aText = aText + self.trUtf8( "créer une nouvelle instance de projet Physiocap")
            physiocap_error( self, aText)
            return physiocap_message_box( self, aText, "information")  
        except physiocap_exception_windows_saga_ascii as e:
            physiocap_log_for_error( self)
            aText = self.trUtf8( "Le projet, le champ ou une valeur de champ {0} ont ").\
                format( e)
            aText = aText + self.trUtf8( "des caractères (non ascii) incompatibles avec l'interpolation SAGA.")
            aText = aText + self.trUtf8( "\nErreur bloquante sous Windows qui nécessite de créer une nouvelle instance du projet ")
            aText = aText + self.trUtf8( " et du contour avec seulement des caractères ascii (non accentuées).")
            physiocap_error( self, aText, "CRITICAL")        

            
##        except x as e:
##            physiocap_log_for_error( self)
##            aText = self.trUtf8( "Physiocap")
##            aText = aText + self.trUtf8( "Intra")
##            physiocap_error( self, aText)
##            return physiocap_message_box( self, aText, "information")

        except:
            raise
        finally:
            pass
        # Fin de capture des erreurs Physiocap        
        physiocap_log( self.trUtf8( "=~= {0} a terminé les interpolations intra parcelaire.").\
            format( PHYSIOCAP_UNI), "INTRA")

                   
    def slot_moyenne_inter_parcelles(self):
        """ Slot qui fait appel au traitement Inter Parcelles et traite exceptions """
       
        nom_complet_point = self.comboBoxPoints.currentText().split( SEPARATEUR_NOEUD)
        if ( len( nom_complet_point) != 2):
            aText = self.trUtf8( "Le shape de points n'est pas choisi. ")
            aText = aText + self.trUtf8( "Créer une nouvelle instance de projet - bouton OK - ")
            aText = aText + self.trUtf8( "avant de faire votre calcul de Moyenne Inter Parcellaire")
            physiocap_error( self, aText, "CRITICAL")
            return physiocap_message_box( self, aText, "information" )
        
        # Eviter les appels multiples
        self.ButtonInter.setEnabled( False)
        # Memorisation des saisies
        self.memoriser_saisies_inter_intra_parcelles()
            
        try:
            #physiocap_moyenne_InterParcelles(self)
            inter = PhysiocapInter( self)
            retour = inter.physiocap_moyenne_InterParcelles( self)        
        except physiocap_exception_rep as e:
            physiocap_log_for_error( self)
            aText = self.trUtf8( "Erreur bloquante lors de la création du répertoire : {0}").\
                format( e)
            physiocap_error( self, aText, "CRITICAL")
            return physiocap_message_box( self, aText, "information" )
        except physiocap_exception_vignette_exists as e:
            aText1 = self.trUtf8( "Les moyennes InterParcellaires dans {0} existent déjà. ").\
                format( e)
            physiocap_log(aText1, "information")
            physiocap_log_for_error( self)
            aText = aText1 + self.trUtf8( "Vous ne pouvez pas redemander ce calcul : vous devez détruire le groupe ") 
            aText = aText + self.trUtf8( "ou mieux créer un nouveau projet Physiocap")
            physiocap_error( self, aText, "CRITICAL")
            return physiocap_message_box( self, aText, "information" )
        except physiocap_exception_points_invalid as e:
            physiocap_log_for_error( self)
            physiocap_log_for_error( self)
            aText = self.trUtf8( "Le fichier de points du projet {0} ne contient pas les attributs attendus").\
                format( e)
            aText = aText + self.trUtf8( "Lancez le traitement initial - bouton OK - avant de faire votre ")
            aText = aText + self.trUtf8( "calcul de Moyenne Inter Parcellaire" )
            physiocap_error( self, aText, "CRITICAL")
            return physiocap_message_box( self, aText, "information" )
        except:
            raise
        finally:
            pass
        # Fin de capture des erreurs Physiocap        
        
        self.groupBoxIntra.setEnabled( True)
        self.ButtonIntra.setEnabled( True)
        physiocap_log( self.trUtf8( "== {0} a terminé les moyennes inter parcelaire.").\
            format( PHYSIOCAP_UNI))

    def slot_bascule_details_vignoble(self):
        """ Changement de demande pour les details vignoble : 
        on grise le groupe Vignoble
        """ 
        #physiocap_log( u"Changement de demande pour les details vignoble")
        if self.checkBoxInfoVignoble.isChecked():
            self.Vignoble.setEnabled( True)
        else:
            self.Vignoble.setEnabled( False)         

    def slot_calcul_densite( self):
        # Densité pied /ha

        interrang  = float( self.spinBoxInterrangs.value())
        intercep   = float( self.spinBoxInterceps.value())
        densite = ""
        if (interrang !=0) and ( intercep != 0):
            densite = int (10000 / ((interrang/100) * (intercep/100)))
        self.lineEditDensite.setText( str( densite))
        
    def slot_demander_contribution( self):
        """ Pointer vers page de paiement en ligne """ 
        help_url = QUrl("https://sites.google.com/a/jhemmi.eu/objectifs/tarifs")
        QDesktopServices.openUrl(help_url)
    
    def slot_demander_aide(self):
        """ Help html qui pointe vers gitHub""" 
        help_url = QUrl("file:///%s/help/index.html" % self.plugin_dir)
        QDesktopServices.openUrl(help_url)


    def reject( self ):
        """Close when bouton is Cancel"""
        # Todo : V3 prefixe Slot et nommage SLOT_Bouton_Cancel      
        #self.textEdit.clear()
        # On sauve le choix du repertoire des thematiques
        self.settings.setValue("Physiocap/leDirThematiques", self.fieldComboThematiques.currentText())
        self.settings.setValue("Physiocap/leChoixDeThematiques", self.fieldComboThematiques.currentIndex())
        QDialog.reject( self)
                
    def accept( self ):
        """Verify when bouton is OK"""
        # Todo : V3 prefixe Slot et nommage SLOT_Bouton_OK
        # Vérifier les valeurs saisies
        # QT confiance et initialisation par Qsettings sert d'assert sur la
        # cohérence des variables saisies

        repertoire_data = self.lineEditDirectoryPhysiocap.text()
        if ((repertoire_data == "") or ( not os.path.exists( repertoire_data))):
            aText = self.trUtf8( "Pas de répertoire de données brutes spécifié")
            physiocap_error( self, aText)
            return physiocap_message_box( self, aText)
        repertoire_cible = self.lineEditDirectoryFiltre.text()
        if ((repertoire_cible == "") or ( not os.path.exists( repertoire_cible))):
            aText = self.trUtf8( "Pas de répertoire de données cibles spécifié")
            physiocap_error( self, aText)
            return physiocap_message_box( self, aText)
        if self.lineEditProjet.text() == "":
            aText = self.trUtf8( "Pas de nom de projet spécifié")
            physiocap_error( self, aText)
            return physiocap_message_box( self, aText)                 
        # Remettre vide le textEditSynthese
        self.textEditSynthese.clear()

        # Sauvergarde des saisies dans les settings
        self.settings= QSettings( PHYSIOCAP_NOM, PHYSIOCAP_NOM)
        self.settings.setValue("Physiocap/projet", self.lineEditProjet.text() )
        self.settings.setValue("Physiocap/repertoire", self.lineEditDirectoryPhysiocap.text() )
        self.settings.setValue("Physiocap/cible_repertoire", self.lineEditDirectoryFiltre.text() )
        #self.settings.setValue("Physiocap/contours", self.lineEditContours.text() )


        # Cas recursif
        recursif = "NO"
        if self.checkBoxRecursif.isChecked():
            recursif = "YES"
            physiocap_log( self.trUtf8( "La recherche des MID fouille l'arbre de données"))
        self.settings.setValue("Physiocap/recursif", recursif )

        # Cas consolidation
        consolidation = "NO"
        if self.checkBoxConsolidation.isChecked():
            consolidation = "YES"
        self.settings.setValue("Physiocap/consolidation", consolidation )
            
        laProjection, EXT_CRS_SHP, EXT_CRS_PRJ, EXT_CRS_RASTER, EPSG_NUMBER = physiocap_quelle_projection_demandee( self) 
        self.settings.setValue("Physiocap/laProjection", laProjection)
        physiocap_log(self.trUtf8( "Projection des shapefiles demandée en {0}").\
                format( str( laProjection)))
           
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
        biomasse = "NO"
        if self.checkBoxBiomasse.isChecked():
            biomasse = "YES"
        self.settings.setValue("Affichage/biomasse", biomasse )
        vitesse = "NO"
        if self.checkBoxVitesse.isChecked():
            vitesse = "YES"
        self.settings.setValue("Affichage/vitesse", vitesse )

        self.settings.setValue("Physiocap/leFormat", self.fieldComboFormats.currentText())
        #self.settings.setValue("Physiocap/leChoixShapeDiametre", self.fieldComboShapeDiametre.currentIndex())
        self.settings.setValue("Physiocap/leChoixShapeSarment", self.fieldComboShapeSarment.currentIndex())
        self.settings.setValue("Physiocap/leChoixShapeBiomasse", self.fieldComboShapeBiomasse.currentIndex())
        self.settings.setValue("Physiocap/leChoixShapeVitesse", self.fieldComboShapeVitesse.currentIndex())
        
        # THEMATIQUES
        self.settings.setValue("Physiocap/leDirThematiques", self.fieldComboThematiques.currentText())
        self.settings.setValue("Physiocap/leChoixDeThematiques", self.fieldComboThematiques.currentIndex())
        # Filtrage
        self.settings.setValue("Physiocap/themeDiametre", self.lineEditThematiqueDiametre.text())
        self.settings.setValue("Physiocap/themeSarment", self.lineEditThematiqueSarment.text())
        self.settings.setValue("Physiocap/themeBiomasse",self.lineEditThematiqueBiomasse.text())
        self.settings.setValue("Physiocap/themeVitesse", self.lineEditThematiqueVitesse.text())
        # Inter
        self.settings.setValue("Physiocap/themeInterDiametre", self.lineEditThematiqueInterDiametre.text())
        self.settings.setValue("Physiocap/themeInterSarment", self.lineEditThematiqueInterSarment.text())
        self.settings.setValue("Physiocap/themeInterBiomasse", self.lineEditThematiqueInterBiomasse.text())
        self.settings.setValue("Physiocap/themeInterLibelle", self.lineEditThematiqueInterLibelle.text())
        # inter moyenne et points
        self.settings.setValue("Physiocap/themeInterMoyenne", self.lineEditThematiqueInterMoyenne.text())
        self.settings.setValue("Physiocap/themeInterPoints", self.lineEditThematiqueInterPoints.text())
        # intra
        self.settings.setValue("Physiocap/themeIntraIso", self.lineEditThematiqueIntraIso.text())
        self.settings.setValue("Physiocap/themeIntraImage", self.lineEditThematiqueIntraImage.text())
            
        # ########################################
        # Gestion de capture des erreurs Physiocap
        # ########################################
        try:
            filtreur = PhysiocapFiltrer( self)
            # Création des répertoires et des résultats de synthèse
            retour = filtreur.physiocap_creer_donnees_resultats( self, laProjection, EXT_CRS_SHP, EXT_CRS_PRJ,
                details, TRACE_HISTO, recursif)
        except physiocap_exception_rep as e:
            physiocap_log_for_error( self)
            aText = self.trUtf8( "Erreur bloquante lors de la création du répertoire : {0}").\
                format( e)
            physiocap_error( self, aText, "CRITICAL")
            return physiocap_message_box( self, aText, "information" )
        
        except physiocap_exception_err_csv as e:
            physiocap_log_for_error( self)
            aText = self.trUtf8( "Trop d'erreurs {0} dans les données brutes").\
                format( e)
            physiocap_error( self, aText, "CRITICAL")
            return physiocap_message_box( self, aText, "information" )
        
        except physiocap_exception_fic as e:
            physiocap_log_for_error( self)
            aText = self.trUtf8( "Erreur bloquante lors de la création du fichier : {0}").\
                format( e)
            physiocap_error( self, aText, "CRITICAL")
            return physiocap_message_box( self, aText, "information" )

        except physiocap_exception_csv as e:
            physiocap_log_for_error( self)
            aText = self.trUtf8( "Erreur bloquante lors de la création du fichier csv : {0}").\
                format( e)
            physiocap_error( self, aText, "CRITICAL")
            return physiocap_message_box( self, aText, "information" )

        except physiocap_exception_mid as e:
            physiocap_log_for_error( self)
            aText = self.trUtf8( "Erreur bloquante lors de la copie du fichier MID : {0}").\
                format( e)
            physiocap_error( self, aText, "CRITICAL")
            return physiocap_message_box( self, aText, "information" )

        except physiocap_exception_no_mid:
            physiocap_log_for_error( self)
            aText = self.trUtf8( "Erreur bloquante : aucun fichier MID à traiter")
            physiocap_error( self, aText, "CRITICAL")
            return physiocap_message_box( self, aText, "information" )
        
        except physiocap_exception_stop_user:
            return physiocap_log( \
                self.trUtf8( "Arrêt de {0} à la demande de l'utilisateur").format( PHYSIOCAP_UNI),
                "WARNING")
         # On remonte les autres exceptions
        except:
            raise
        finally:
            pass
        # Fin de capture des erreurs Physiocap
        if ( retour == 0 ):
            physiocap_log( self.trUtf8( "** {0} est prêt pour calcul Inter parcellaire - Onglet Parcelles").\
                format( PHYSIOCAP_UNI))
        return retour

