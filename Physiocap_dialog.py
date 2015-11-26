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
 et recupération des variables, sauvegarde des parametres,
 le nommage et création de l'arbre des résultats d'analyse (dans la même
 structure de données que celle créé par PHYSICAP_V8 du CIVC) 

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
        physiocap_log, physiocap_error, physiocap_write_in_synthese, \
        physiocap_rename_existing_file, physiocap_rename_create_dir, physiocap_open_file, \
        physiocap_quelle_projection_demandee, physiocap_look_for_MID, physiocap_list_MID

from Physiocap_CIVC import physiocap_csv_vers_shapefile, physiocap_assert_csv, \
        physiocap_fichier_histo, physiocap_tracer_histo, physiocap_filtrer   

from Physiocap_inter import physiocap_fill_combo_poly_or_point, physiocap_moyenne_InterParcelles

from Physiocap_exception import *

from PyQt4 import QtGui, uic
from PyQt4.QtCore import QSettings
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import *
from qgis.gui import *

import glob
import shutil
import time  

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'Physiocap_dialog_base.ui'))

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

        # Slot for boutons 
        #self.refreshButton.pressed.connect(self.create_contour_list )
        ##self.buttonBox.button( QDialogButtonBox.Ok ).pressed.connect(self.accept)
        ##self.buttonBox.button( QDialogButtonBox.Cancel ).pressed.connect(self.reject)
        self.comboBoxPolygone.currentIndexChanged[int].connect( self.update_field_list )
        self.buttonBox.button( QDialogButtonBox.Help ).pressed.connect(self.demander_aide)
        self.buttonContribuer.pressed.connect(self.demander_contribution)
        
        self.spinBoxInterrangs.valueChanged.connect( self.calcul_densite)
        self.spinBoxInterceps.valueChanged.connect( self.calcul_densite)
        
        self.ButtonInter.pressed.connect(self.moyenne_inter_parcelles)
        self.ButtonInterRefresh.pressed.connect(self.liste_inter_parcelles)
        self.groupBoxInter.setEnabled( False)

        # Slot pour données brutes
        self.toolButtonDirectoryPhysiocap.pressed.connect( self.lecture_repertoire_donnees_brutes )  
        # Slot pour le groupe vignoble
        self.checkBoxInfoVignoble.stateChanged.connect( self.bascule_details_vignoble)
        # Slot pour les contours
        # self.toolButtonContours.pressed.connect( self.lecture_shape_contours )   
              
        physiocap_log( u"Votre machine tourne sous " + platform.system())
        
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
        densite = ""
        if (interrang !=0) and ( intercep != 0):
            densite = int (10000 / ((interrang/100) * (intercep/100)))
        self.lineEditDensite.setText( str( densite))
        
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
    def update_field_list( self ):
        """ Create a list of fields for the current vector in fieldCombo Box"""
        nom_complet_poly = self.comboBoxPolygone.currentText().split( SEPARATEUR_NOEUD)
        inputLayer = nom_complet_poly[0] #str(self.comboBoxPolygone.itemText(self.comboBoxPolygone.currentIndex()))
        self.fieldComboContours.clear()
        layer = self.get_layer_by_name( inputLayer )
        self.fieldComboContours.addItem( "NOM_PHY")
        if layer is not None:
            #physiocap_log(u"Look for fields of layer >" + layer.name())
            for index, field in enumerate(layer.dataProvider().fields()):
                self.fieldComboContours.addItem( str( field.name()) )
##        else:
##            self.fieldComboContours( "Aucun autre champ retrouvé")
 
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

##    # shape file contours :
##    def lecture_shape_contours( self):
##        """Catch file *.shp for contours """
##        # Récuperer dans setting le nom du dernier ou sinon SHAPE_CONTOURS
##        self.settings= QSettings(PHYSIOCAP_NOM, PHYSIOCAP_NOM)
##        exampleShapeName =  self.settings.value("Physiocap/contours", SHAPE_CONTOURS)
##        
##        shapeName = QFileDialog.getOpenFileName( self, u"ShapeFile de vos contours de parcelles",
##                                                 exampleShapeName,
##                                                 ("Shapefile (*.shp)"));
##                                                
##        if len( shapeName) == 0:
##          return
##        self.lineEditContours.setText( shapeName )
 
    def liste_inter_parcelles( self):
        """ Rafraichit les listes avant le calcul inter parcelles"""
        # Todo : refresh auto avec addedChildrenSignal ?
        nombre_poly = 0
        nombre_point = 0
        nombre_poly, nombre_point = physiocap_fill_combo_poly_or_point( self)

        if (( nombre_poly > 0) and ( nombre_point > 0)):
            # Liberer le bouton "moyenne"
            self.groupBoxInter.setEnabled( True)
            self.update_field_list()
        else:
            self.groupBoxInter.setEnabled( False)
            
    def moyenne_inter_parcelles(self):
        """ Slot qui fait appel au traitement Inter Parcelels et traite exceptions """
       
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
            physiocap_log( ERREUR_EXCEPTION + ". Consultez le journal Physiocap Erreur",
                "WARNING")
            physiocap_error( ERREUR_EXCEPTION)
            physiocap_error(u"Les moyennes InterParcellaires du projet Physiocap " + str( e) + " existent déjà.",
                "CRITICAL")
            return physiocap_message_box( self, self.tr( ERREUR_EXCEPTION + "\n" + \
                u"Les moyennes InterParcellaires du projet Physiocap " + str( e) + " existent déjà."),
                "information" )
        except physiocap_exception_points_invalid as e:
            physiocap_log( ERREUR_EXCEPTION + ". Consultez le journal Physiocap Erreur",
                "WARNING")
            physiocap_error( ERREUR_EXCEPTION)
            physiocap_error(u"Le fichier de points du projet" + str( e) + "ne contient pas les attributs attendus",
                "CRITICAL")
            return physiocap_message_box( self, self.tr( ERREUR_EXCEPTION + "\n" + \
                u"Le fichier de points du projet" + str( e) + "ne contient pas les attributs attendus"),
                "information" )
        except:
            raise
        finally:
            pass
        # Fin de capture des erreurs Physiocap        
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
            
        # ########################################
        # Gestion de capture des erreurs Physiocap
        # ########################################
        try:
            # Création des répertoires et des résultats de synthèse
            retour = self.physiocap_creer_donnees_resultats( details, TRACE_HISTO, recursif, laProjection)
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
            return physiocap_log( "Arret de Physiocap à la demande de l'utilisateur",
                "WARNING")
         # On remonte les autres exceptions
        except:
            raise
        finally:
            pass
            # Todo : Se mettre sur l'onglet synthese ou (histo)

        
        # Fin de capture des erreurs Physiocap
        
        physiocap_log(u"Physiocap a terminé son analyse.")
        
    
    # Creation des repertoires source puis resultats puis histo puis shape
    def physiocap_creer_donnees_resultats( self, details = "NO", histogrammes = "NO", recursif = "NO", 
        laProjection = "L93", EXT_SHP = EXTENSION_SHP_L93, EXT_PRJ = EXTENSION_PRJ_L93):
        """ Récupération des paramètres saisies et 
        creation de l'arbre "source" "texte" et du fichier "resultats"
        Ce sont les résultats de l'analyse filtration des données brutes"""
        
        # Récupérer les paramètres saisies
        REPERTOIRE_DONNEES_BRUTES = self.lineEditDirectoryPhysiocap.text()
        NOM_PROJET = self.lineEditProjet.text()
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
                physiocap_log( "Erreur dans fonction creer_donnees_resultats ==" + chemin_projet)
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
            uMsg =u"Plus de 15 fichier MIDs sont à analyser. Temps de traitement > à 1 minute. Voulez-vous continuer ?"
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
            uMsg =u"Le fichier " + nom_court_csv_concat + u" a une taille nulle !"
            physiocap_message_box( self, uMsg)
            return physiocap_error( uMsg)
        
        # Création la première partie du fichier de synthèse
        nom_fichier_synthese, fichier_synthese = physiocap_open_file( FICHIER_RESULTAT, chemin_projet , "w")
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
                fichier_synthese.write( "\n" + str(info[5]) + "--" + str(info[6]))
            fichier_synthese.write("\n")
##        nom_mid = ""
##        for fichier_mid in listeTriee:
##            nom_mid = nom_mid + os.path.basename( fichier_mid) + " & "
##        fichier_synthese.write("Liste des fichiers MID : " + nom_mid[:-3] + "\n")
##        physiocap_log( "Liste des MID : " + nom_mid[:-3])
       
        # Progress BAR 5 %
        self.progressBar.setValue( 5)
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
                # Todo : question selon le taux de lignes en erreur autorisées
                #raise physiocap_exception_err_csv( pourcentage_erreurs)
        except:
            raise

        # Progress BAR 10 %
        self.progressBar.setValue( 10)        
        fichier_synthese.write("\n\nPARAMETRES SAISIS ")
        
        if os.path.getsize( nom_csv_concat ) == 0 :
            uMsg =u"Le fichier " + nom_court_csv_concat + u" a une taille nulle !"
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
            
            physiocap_log ( u"Fin de la création des histogrammes bruts")
        else:
            physiocap_log ( u"Pas de création des histogrammes")

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
            return physiocap_error(u"Erreur bloquante : problème lors du filtrage des données de : " + 
                    nom_court_csv_concat)  

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
        nom_court_shape_sans_0 = NOM_PROJET + NOM_POINTS + EXT_SHP
        nom_shape_sans_0 = os.path.join(chemin_shapes, nom_court_shape_sans_0)
        nom_court_prj_sans_0 = NOM_PROJET + NOM_POINTS + EXT_PRJ
        nom_prj_sans_0 = os.path.join(chemin_shapes, nom_court_prj_sans_0)
        # Si le shape existe dejà il faut le détruire
        if os.path.isfile( nom_shape_sans_0):
            physiocap_log ( u"Le shape file existant déjà, il est détruit.")
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
        nom_court_shape_avec_0 = NOM_PROJET + NOM_POINTS + EXTENSION_POUR_ZERO + EXT_SHP
        nom_shape_avec_0 = os.path.join(chemin_shapes, nom_court_shape_avec_0)
        nom_court_prj_avec_0 = NOM_PROJET + NOM_POINTS + EXTENSION_POUR_ZERO + EXT_PRJ
        nom_prj_avec_0 = os.path.join(chemin_shapes, nom_court_prj_avec_0)
        # Si le shape existe dejà il faut le détruire
        if os.path.isfile( nom_shape_avec_0):
            physiocap_log ( u"Le shape file existant déjà, il est détruit.")
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
        # Todo : V2.4 ? OK
        root = QgsProject.instance().layerTreeRoot( )
        # Nommmer le groupe chemin_base_projet
        sous_groupe = root.addGroup( chemin_base_projet)
        
        # Récupérer des styles pour chaque shape
        dirTemplate = os.path.join( os.path.dirname(__file__), 'modeleQgis')       
        # Affichage des deux shapes dans Qgis
        for shapename, titre,unTemplate   in [(nom_shape_sans_0, 'DIAMETRE', 'Diametre 6 Jenks.qml') , 
                        (nom_shape_sans_0, 'SARMENT', 'Sarments 4 Jenks.qml') , 
                        (nom_shape_avec_0, 'VITESSE', 'Vitesse.qml')]:
            vector = QgsVectorLayer( shapename, titre, 'ogr')
            QgsMapLayerRegistry.instance().addMapLayer( vector, False)
            # Ajouter le vecteur dans un groupe
            vector_node = sous_groupe.addLayer( vector)
            leTemplate = os.path.join( dirTemplate, unTemplate)
            #physiocap_log ( u"Physiocap le template : " + os.path.basename( leTemplate) )
            vector.loadNamedStyle( leTemplate)
        
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
                physiocap_log ( u"Physiocap histo sarment chargé")
            if ( self.label_histo_diametre_avant.setPixmap( QPixmap( nom_histo_diametre))):
                physiocap_log ( u"Physiocap histo diametre chargé")                
            if ( self.label_histo_diametre_apres.setPixmap( QPixmap( nom_histo_diametre_filtre))):
                physiocap_log ( u"Physiocap histo diametre chargé")    
        else:
            self.label_histo_sarment.setPixmap( QPixmap( FICHIER_HISTO_NON_CALCULE))
            self.label_histo_diametre_avant.setPixmap( QPixmap( FICHIER_HISTO_NON_CALCULE))
            self.label_histo_diametre_apres.setPixmap( QPixmap( FICHIER_HISTO_NON_CALCULE))
            physiocap_log ( u"Physiocap pas d'histogramme calculé")    
                           
        # Progress BAR 100 %
        self.progressBar.setValue( 100)
        # Fin 
        
        physiocap_log ( u"Fin de la synthèse Physiocap : sans erreur")
        physiocap_fill_combo_poly_or_point( self)
        physiocap_log ( u"Mise à jour des poly et points")
        return 0 

