# -*- coding: utf-8 -*-
"""
/***************************************************************************
 PhysiocapIntra
                                 A QGIS plugin
 Physiocap plugin helps analyse raw data from Physiocap in Qgis and 
 creates a synthesis of Physiocap measures' campaign
 Physiocap plugin permet l'analyse les données brutes de Physiocap dans Qgis et
 crée une synthese d'une campagne de mesures Physiocap
 
 Le module Intra gère l(interpolation des données le chaque parcelle
 à partir d'un shapefile de contour de parcelles et d'un shape de points de
 chaque parcelle
 Il tourne après qu'inter ait tourné

 Les variables et fonctions sont nommées dans la même langue
  en Anglais pour les utilitaires
  en Francais pour les données Physiocap

                             -------------------
        begin                : 2015-11-04
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
        physiocap_rename_existing_file, physiocap_rename_create_dir, \
        physiocap_open_file, physiocap_quelle_projection_demandee, \
        physiocap_get_layer_by_ID

from Physiocap_var_exception import *

from PyQt4 import QtGui, uic
##from PyQt4.QtCore import QSettings
from PyQt4.QtCore import *
##from PyQt4.QtGui import *
from qgis.core import *
from qgis.gui import *


def physiocap_affiche_raster_iso( nom_raster_final, nom_court_raster, le_template_raster, affiche_raster,
                    nom_iso_final, nom_court_isoligne, le_template_isolignes, affiche_iso,
                    vignette_group_intra):
    """ Affichage du raster et Iso"""
        
    # Todo : V1.4 ? Faire exception 
    if ( nom_raster_final != ""):
        intra_raster = QgsRasterLayer( nom_raster_final, 
            nom_court_raster)
        if ( nom_iso_final != ""):
            intra_isoligne = QgsVectorLayer( nom_iso_final, 
                nom_court_isoligne, 'ogr')
    
        if vignette_group_intra != None:
            if (( affiche_iso == "YES") and ( nom_iso_final != "")):
                QgsMapLayerRegistry.instance().addMapLayer( intra_isoligne, False)
                iso_node = vignette_group_intra.addLayer( intra_isoligne)
            if ( affiche_raster == "YES"): 
                QgsMapLayerRegistry.instance().addMapLayer( intra_raster, False)
                raster_node = vignette_group_intra.addLayer( intra_raster)
        else:
            if (( affiche_iso == "YES") and ( nom_iso_final != "")):
                QgsMapLayerRegistry.instance().addMapLayer( intra_isoligne)
            if ( affiche_raster == "YES"): 
                QgsMapLayerRegistry.instance().addMapLayer( intra_raster)
    
        if (( affiche_raster == "YES") and 
            ( os.path.exists( le_template_raster))):
            intra_raster.loadNamedStyle( le_template_raster)
            if (( affiche_iso == "YES") and ( nom_iso_final != "") and 
                ( os.path.exists( le_template_isolignes))):
                intra_isoligne.loadNamedStyle( le_template_isolignes)

def physiocap_creer_raster_iso( self,
            nom_noeud_arbre, chemin_raster, 
            nom_court_vignette, nom_vignette, nom_court_point, nom_point,
            le_champ_choisi, un_nom):
    """ Creation du raster et Iso
    Cas Saga ou Gdal : appel des processing correspondants
    """
        
    # Pour appel de processing on attend d'etre dans Qgis et Intra
    try :
        import processing
        versionGDAL = processing.tools.raster.gdal.__version__
        # Todo : Vérifier syntaxe en Win 32 bits et attraper cette erreur
        versionSAGA = processing.algs.saga.SagaUtils.getSagaInstalledVersion()
    except ImportError:
        aText = self.trUtf8( "L'extension Traitement (Processing) n'est pas accessible. ")
        aText = aText + self.trUtf8( "Pour réaliser du calcul intra parellaire, vous devez installer ")
        aText = aText + self.trUtf8( "l'extension Traitement (menu Extension => Installer une extension)") 
        physiocap_error( aText)
        return physiocap_message_box( self,
        self.trUtf8( u"Physiocap nécessite l'extension Traitement (Processing)" ),
        "information")
    except AttributeError:
        aText = self.trUtf8( "SAGA n'est pas accessible. ")
        aText = aText + self.trUtf8( "Pour réaliser du calcul intra parellaire, vous devez installer SAGA.")
        physiocap_error( aText)
        return physiocap_message_box( self,
        self.trUtf8( u'Physiocap nécessite SAGA version 2.1.0 à 2.1.2' ),
        "information")
                
    # Test SAGA version, sinon annoncer l'utilisation de Gdal
    if self.radioButtonSAGA.isChecked():
        physiocap_log ( self.trUtf8( "= Version SAGA = %s" % ( str( versionSAGA))))
        unite, dixieme, millieme = versionSAGA.split( ".")
        versionNum = float(unite) + float(dixieme)/10 + float(millieme)/100
        if ( versionNum >= 2.10) and ( versionNum <= 2.12):
            physiocap_log ( self.trUtf8( "= Version SAGA OK : %s" % ( str( versionSAGA))))
        else:
            physiocap_log ( self.trUtf8( "= Version SAGA %s est inférieure à 2.1.0 " % ( str( versionSAGA))))
            physiocap_log ( self.trUtf8( "= ou supérieure à 2.1.2"))
            physiocap_log ( self.trUtf8( "= On force l'utilisation de Gdal : "))
            self.radioButtonSAGA.setEnabled( False)
            self.radioButtonGDAL.setChecked(  Qt.Checked)
            self.radioButtonSAGA.setChecked(  Qt.Unchecked)
            self.spinBoxPower.setEnabled( False)
            self.spinBoxPixel.setEnabled( False)
            physiocap_message_box( self,
                self.trUtf8( "= Saga a une version incompatible : on force l'utilisation de Gdal" ),
                "information")
##    else:
##           physiocap_log ( u"= Version GDAL = " + str( versionGDAL))

    # Récupération des parametres d'Intra
    powerIntra = float ( self.spinBoxPower.value())
    rayonIntra = float ( self.spinBoxRayon.value())
    pixelIntra = float ( self.spinBoxPixel.value())

     # Pour isolignes
    isoMin = float ( self.spinBoxIsoMin.value())
    isoMax = float ( self.spinBoxIsoMax.value())
    #isoNombreIso = float ( self.spinBoxNombreIso.value())
    isoInterlignes = float ( self.lineEditDistanceIso.text())
 
    # Parametres fixes
    angle = 0    # Pas utiliser
    val_nulle = 0 # Valeur nulle reste nulle
    float_32 = 5
  
    # Lire points_vector et  vignette_vector
    try:
        # Todo : Attrapper l'existance du fichier pour monter erreur (cas BIOMGM2)
        vignette_vector = QgsVectorLayer( nom_vignette, nom_court_vignette, 'ogr')
        points_vector = QgsVectorLayer( nom_point, nom_court_point, 'ogr')
    except:
        # Todo : ? En faire une exception et tester dans try
        aText = self.trUtf8( "Le polygone ou le fichier de point n'est pas retrouvé. ")
        aText = aText + self.trUtf8( "Une inconsistence entre le projet Physiocap et ses données vous oblige ")
        aText = aText + self.trUtf8( "à relancer la chaine de traitement.") 
        physiocap_error( aText)
        return physiocap_message_box( self, aText, "information")            
 
    laProjection, EXT_CRS_SHP, EXT_CRS_PRJ, EXT_CRS_RASTER, EPSG_NUMBER = \
        physiocap_quelle_projection_demandee(self)

    # ###################
    # CRÉATION raster
    # ###################
    # Nom du raster avec le_champ_choisi
    nom_court_raster = nom_noeud_arbre + SEPARATEUR_ + le_champ_choisi + SEPARATEUR_ + \
        un_nom + EXT_CRS_RASTER
    nom_raster =  physiocap_rename_existing_file( os.path.join( chemin_raster, nom_court_raster)) # utile physiocap_rename_existing_file()        
    nom_court_isoligne = nom_noeud_arbre + SEPARATEUR_  + le_champ_choisi + SEPARATEUR_ + "ISOLIGNE_" + \
        un_nom + EXT_CRS_SHP
    nom_isoligne =  physiocap_rename_existing_file( os.path.join( chemin_raster, nom_court_isoligne)) # utile physiocap_rename_existing_file()        
    
    # Attraper les exceptions processing
    nom_raster_temp = ""
    nom_raster_final = ""
    nom_iso_final = ""
    # Récuperer Extent du polygone en cours
    ex = vignette_vector.extent()
    xmin, xmax, ymin, ymax = ex.xMinimum(),ex.xMaximum(), ex.yMinimum(), ex.yMaximum()
    info_extent = str(xmin) + "," + str(xmax) + "," + str(ymin) + "," + str(ymax)
    #physiocap_log( u"=~= Extent layer >>> " + info_extent + " <<<")  
    
    if self.radioButtonSAGA.isChecked():
        # Appel SAGA power à 2 fixe
        physiocap_log( u"=~= Interpolation SAGA " + str( nom_court_raster))
        premier_raster = processing.runalg("saga:inversedistanceweighted",
            str( nom_point), le_champ_choisi, 1, 2, 1, 0,rayonIntra, 0, 1,
            10, info_extent, pixelIntra,
            None)                        
        if (  premier_raster != None):
            if ( str( list( premier_raster) == "USER_GRID")):
                if str( premier_raster[ 'USER_GRID']) != None:
                    #physiocap_log( u"=~= premier fichier SAGA : " + str( premier_raster[ 'USER_GRID']))
                    nom_raster_temp =  str( premier_raster[ 'USER_GRID'])
        else:
            raise physiocap_exception_interpolation( nom_point)
                                        
        if ( nom_raster_temp != ""):
            #physiocap_log( u"=~= Option du clip: " + option_clip_raster )
            raster_dans_poly = processing.runalg("saga:clipgridwithpolygon",
            nom_raster_temp,
            str( nom_vignette),
            nom_raster)
        
        if (  raster_dans_poly != None):
            if ( str( list( raster_dans_poly) == "Output")):
                if str( raster_dans_poly[ 'OUTPUT']) != None:
                    nom_raster_final = str( raster_dans_poly[ 'OUTPUT'])
        
        if ( nom_raster_final != ""):
            # Isolignes
            iso_dans_poly_brut = processing.runalg("saga:contourlinesfromgrid",
                nom_raster_final,
                isoMin, isoMax, isoInterlignes,
                str( nom_isoligne))
            if ( iso_dans_poly_brut != None):                              
                if ( str( list( iso_dans_poly_brut) == "CONTOUR")):
                    if str( iso_dans_poly_brut[ 'CONTOUR']) != None:
                        nom_iso_final = str( iso_dans_poly_brut[ 'CONTOUR'])

                if ( nom_iso_final != ""):                              
                    iso_dans_poly_plus = processing.runalg("qgis:addfieldtoattributestable", \
                        nom_iso_final, \
                        "ELEV", 1, 15, 2 ,None)
                
                if ( iso_dans_poly_plus != None):                              
                    if ( str( list( iso_dans_poly_plus) == "OUTPUT_LAYER")):
                        if str( iso_dans_poly_plus[ 'OUTPUT_LAYER']) != None:
                            nom_iso_final = str( iso_dans_poly_plus[ 'OUTPUT_LAYER'])
                            
            if ( nom_iso_final != ""):                              
                # Retrouver le nom de l'atribut créé et 
                intra_iso_modifie = QgsVectorLayer( nom_iso_final, 
                        nom_court_isoligne, 'ogr')
                fields = intra_iso_modifie.pendingFields()
                field_probable = fields[1]
                field_name = field_probable.name()
                field_formule = '"' + str( field_name) + '"'  
##                    physiocap_log( u"=~= Isolignes formule : " + str(field_formule))                                                 
##                    QgsMessageLog.logMessage( "PHYSIOCAP : Avant calculator ", "Processing", QgsMessageLog.WARNING)
                # Le remplacer par "Elev"
                iso_dans_poly = processing.runalg("qgis:fieldcalculator", \
                    nom_iso_final, "ELEV", 0, 15, 2, False, field_formule ,None)
            if ( iso_dans_poly != None):                              
                nom_iso_final = str( iso_dans_poly[ 'OUTPUT_LAYER'])                                
                if ( str( list( iso_dans_poly) == "OUTPUT_LAYER")):
                    if str( iso_dans_poly[ 'OUTPUT_LAYER']) != None:
                        nom_iso_final = str( iso_dans_poly[ 'OUTPUT_LAYER'])
                        physiocap_log( self.trUtf8( "=~= Isolignes SAGA : %s" % ( str( nom_court_isoligne))))                                 
                        physiocap_log( u"=~= =~=~=~=~= <<")
            else:
                raise physiocap_exception_interpolation( nom_point)
        else:
            raise physiocap_exception_interpolation( nom_point)                    
    else:
        # Appel GDAL
        physiocap_log( u"=xg= Interpolation GDAL " + str( nom_court_raster))
        #QgsMessageLog.logMessage( "PHYSIOCAP : Avant invdist", "Processing", QgsMessageLog.WARNING)

        premier_raster = processing.runalg("gdalogr:gridinvdist",
            str( nom_point), le_champ_choisi, powerIntra, 0.0, rayonIntra, rayonIntra, 
            1000, 5, angle, val_nulle ,float_32, 
            None)

        if (  premier_raster != None):
            if ( str( list( premier_raster) == "Output")):
                if str( premier_raster[ 'OUTPUT']) != None:
                    #physiocap_log( u"=xg= premier fichier GDAL : " + str( premier_raster[ 'OUTPUT']))
                    nom_raster_temp =  str( premier_raster[ 'OUTPUT'])
        else:
            raise physiocap_exception_interpolation( nom_point)

        QgsMessageLog.logMessage( "PHYSIOCAP : Avant clip", self.tr( "Traitement"), QgsMessageLog.WARNING)
        
        option_clip_raster = ""

        if ( EPSG_NUMBER == EPSG_NUMBER_L93 ):
            #physiocap_log( u"=xg= Projection à translater vers : " + str( EPSG_NUMBER) )
            #option_clip_raster = '-s_2015-12-09T16:17:46	1	PHYSIOCAP : Avant calculator 
            #srs "EPSG:' + str(EPSG_NUMBER_GPS) + '" -t_srs "EPSG:' + str(EPSG_NUMBER_L93) + '"'
            option_clip_raster = "-t_srs \"EPSG:" + str(EPSG_NUMBER_L93) + "\""
            
        if ( nom_raster_temp != ""):
            physiocap_log( u"=xg= Option du clip: " + option_clip_raster )
            raster_dans_poly = processing.runalg("gdalogr:cliprasterbymasklayer",
            str( nom_raster_temp),
            str( nom_vignette),
            "-9999",False,False,
            option_clip_raster, 
            str( nom_raster))
        
        if (  raster_dans_poly != None):
            physiocap_log( u"=xg= raster du clip: " + str( list(raster_dans_poly)) )
            if ( str( list( raster_dans_poly) == "Output")):
                if str( raster_dans_poly[ 'OUTPUT']) != None:
                    nom_raster_final = str( raster_dans_poly[ 'OUTPUT'])
        
        QgsMessageLog.logMessage( "PHYSIOCAP : Avant Iso", self.tr( "Traitement"), QgsMessageLog.WARNING)

        if ( nom_raster_final != ""):
            # Isolignes
            iso_dans_poly = processing.runalg("gdalogr:contour",
                str( nom_raster),
                isoInterlignes,
                "ELEV",
                "",
                str( nom_isoligne))
                            
            if (  iso_dans_poly != None):
                if ( str( list( iso_dans_poly) == "OUTPUT_VECTOR")):
                    if str( iso_dans_poly[ 'OUTPUT_VECTOR']) != None:
                        nom_iso_final = str( iso_dans_poly[ 'OUTPUT_VECTOR'])
                        #physiocap_log( u"=xg= Isolignes GDAL : " + nom_court_isoligne)                                
                        physiocap_log ( u"=~= =~=~=~=~= <<")
            else:
                physiocap_log( u"=xg= Problème avec iso_dans_poly : ")
                raise physiocap_exception_interpolation( nom_point)
        else:
            physiocap_log( u"=xg= Problème fin clip : ")
            raise physiocap_exception_interpolation( nom_point)
        
    return nom_raster_final, nom_court_raster, nom_iso_final, nom_court_isoligne            

def physiocap_interpolation_IntraParcelles( self):
    """Interpolation des données de points intra parcellaires"""
    physiocap_log( u"=~= Début de l'interpolation des points de chaque parcelle" )

    NOM_PROJET = self.lineEditProjet.text()

    # QT Confiance 
    le_champ_choisi = self.fieldComboIntra.currentText()
    # Récupérer des styles pour chaque shape
    #dir_template = os.path.join( os.path.dirname(__file__), 'modeleQgis')       
    dir_template = self.fieldComboThematiques.currentText()
    qml_prefix = str( self.lineEditThematiqueIntraImage.text().strip('"'))
    nom_intra_attribut = qml_prefix + str( le_champ_choisi) + EXTENSION_QML
    le_template_raster = os.path.join( dir_template, nom_intra_attribut)
    qml_prefix = str( self.lineEditThematiqueIntraIso.text().strip('"'))
    nom_isolignes_attribut = qml_prefix + str( le_champ_choisi) + EXTENSION_QML
    le_template_isolignes  = os.path.join( dir_template, nom_isolignes_attribut)


    # Todo : V 1.4 ? Faire une fonction commune à inter et Intra jusqu'à 162 param "calcul de Moyenne Intra Parcellaire"
    repertoire_data = self.lineEditDirectoryPhysiocap.text()
    if ((repertoire_data == "") or ( not os.path.exists( repertoire_data))):
        physiocap_error( u"Pas de répertoire de donnée spécifié")
        return physiocap_message_box( self, 
            self.trUtf8( "Pas de répertoire de données brutes spécifié" ),
            "information")
           
    # Pour polygone de contour   
    nom_complet_poly = self.comboBoxPolygone.currentText().split( SEPARATEUR_NOEUD)
    if ( len( nom_complet_poly) != 2):
        physiocap_error( u"Le polygone de contour n'est pas choisi. " +
          "Avez-vous ouvert votre shapefile de contour ?")
        return physiocap_message_box( self,
            self.trUtf8( "Le polygone de contour n'est pas choisi. " +
                "Avez-vous ouvert votre shapefile de contour ?" ),
            "information")            
    nom_poly = nom_complet_poly[ 0] 
    id_poly = nom_complet_poly[ 1] 
    vecteur_poly = physiocap_get_layer_by_ID( id_poly)

    # Pour attribut en cours d'interpolation
    leChampPoly = self.fieldComboContours.currentText()
        
    # Pour les points
    nom_complet_point = self.comboBoxPoints.currentText().split( SEPARATEUR_NOEUD)
    if ( len( nom_complet_point) != 2):
        physiocap_error( u"Le shape de points n'est pas choisi. " +
          "Lancez le traitement initial - bouton OK puis Inter - avant de faire votre " +
          "calcul de Moyenne Intra Parcellaire")
        return physiocap_message_box( self,
            self.trUtf8( "Le shape de points n'est pas choisi. " +
                "Lancez le traitement initial - bouton OK puis Inter - avant de faire votre " +
                "calcul de Moyenne Intra Parcellaire" ),
            "information")
    nom_noeud_arbre = nom_complet_point[ 0] 
    id_point = nom_complet_point[ 1] 
    vecteur_point = physiocap_get_layer_by_ID( id_point)

    # Progress BAR 2%
    self.progressBarIntra.setValue( 2)
    
    # Verification de l'arbre
    root = QgsProject.instance().layerTreeRoot( )
    un_groupe = root.findGroup( nom_noeud_arbre)
    if ( not isinstance( un_groupe, QgsLayerTreeGroup)):
        physiocap_error( u"Le projet " + nom_noeud_arbre + " n'existe pas " +
            "Lancez le traitement initial - bouton OK puis Inter- avant de faire votre " +
            "calcul de Moyenne Intra Parcellaire" )
        return physiocap_message_box( self,
            self.trUtf8( "Le projet " + nom_noeud_arbre + " n'existe pas " +
            "Lancez le traitement initial - bouton OK puis Inter - avant de faire votre " +
            "calcul de Moyenne Intra Parcellaire" ),
            "information")            

    # Vérification 
    if ( vecteur_point == None):
        physiocap_error( u"Le jeu de points choisi n'est pas valide. " +
          "Lancez le traitement initial - bouton OK puis Inter - avant de faire votre " +
          "calcul de Moyenne Intra Parcellaire")
        return physiocap_message_box( self,
            self.trUtf8( "Le jeu de points choisi n'est pas valide. " +
                "Lancez le traitement initial - bouton OK puis Inter - avant de faire votre " +
                "calcul de Moyenne Intra Parcellaire" ),
            "information")    

    if ( vecteur_poly == None) or ( not vecteur_poly.isValid()):
        physiocap_error( u"Le contour choisi n'est pas valide. " +
          "Lancez le traitement initial - bouton OK puis Inter - avant de faire votre " +
          "calcul de Moyenne Intra Parcellaire")
        return physiocap_message_box( self,
            self.trUtf8( "Le contour choisi n'est pas valide. " +
                "Lancez le traitement initial - bouton OK puis Inter - avant de faire votre " +
                "calcul de Moyenne Intra Parcellaire" ),
            "information")
               
    laProjection, EXT_CRS_SHP, EXT_CRS_PRJ, EXT_CRS_RASTER, EPSG_NUMBER = \
        physiocap_quelle_projection_demandee(self)
    crs = QgsCoordinateReferenceSystem( EPSG_NUMBER, QgsCoordinateReferenceSystem.PostgisCrsId)

    # Assert repertoire shapfile 
    chemin_shapes = os.path.dirname( unicode( vecteur_point.dataProvider().dataSourceUri() ) ) ;
    if ( not os.path.exists( chemin_shapes)):
        raise physiocap_exception_rep( chemin_shapes)

    # Assert repertoire vignette inter 
    chemin_vignettes = os.path.join( chemin_shapes, VIGNETTES_INTER)
    if not (os.path.exists( chemin_vignettes)):
        raise physiocap_exception_rep( VIGNETTES_INTER)


    # Création du REP RASTER
    chemin_projet = os.path.join( repertoire_data, nom_noeud_arbre)
    chemin_raster = os.path.join(chemin_projet, REPERTOIRE_RASTERS)
    if not (os.path.exists( chemin_raster)):
        try:
            os.mkdir( chemin_raster)
        except:
            raise physiocap_exception_rep( REPERTOIRE_RASTERS)

    # Progress BAR 4%
    self.progressBarIntra.setValue( 4)

    lesFormes = vecteur_poly.getFeatures()
    iforme = 0
    for f in lesFormes:
        iforme = iforme + 1
    stepBar = int( 60 / iforme)
    positionBar = 5
    
    # On passe sur le contour général
    contour_avec_point = 0
   
    # #####################
    # Cas d'une image seule
    # #####################
    if ( self.checkBoxIntraUnSeul.isChecked()):

        # Nom du Shape moyenne 
        nom_vecteur_contour = vecteur_poly.name()
        nom_court_du_contour = os.path.basename( nom_vecteur_contour + EXTENSION_SHP)
        nom_court_vignette = nom_noeud_arbre + NOM_MOYENNE + nom_court_du_contour
        nom_vignette = os.path.join( chemin_vignettes, nom_court_vignette)        
                                               
        # Nom point 
        nom_court_point = NOM_PROJET + NOM_POINTS + EXT_CRS_SHP     
        nom_point = os.path.join( chemin_shapes, nom_court_point)                    
        #physiocap_log( u"=~= Vignette court : " + str( nom_court_vignette) )       

        # Vérifier si le point et la vignette existent
        if not (os.path.exists( nom_vignette)):
            physiocap_log( u"=~= Vignette absente : pas d'interpolation")
        if not (os.path.exists( nom_point)):
            physiocap_log( u"=~= Points absents : pas d'interpolation")
        else:
            contour_avec_point = contour_avec_point + 1
            #physiocap_log( u"=~= Points - nom court : " + str( nom_court_point) )
            #physiocap_log( u"=~= Points - nom  : " + str( nom_point) )

            # ###############
            # Calcul raster et iso
            # ###############
            nom_raster_final, nom_court_raster, nom_iso_final, nom_court_isoligne = \
                physiocap_creer_raster_iso( self,
                nom_noeud_arbre, chemin_raster, 
                nom_court_vignette, nom_vignette, nom_court_point, nom_point,
                le_champ_choisi, nom_vecteur_contour) 
                        
        # CRÉATION groupe INTRA
        if (( contour_avec_point == 1) and (un_groupe != None)):
            vignette_projet = nom_noeud_arbre + SEPARATEUR_ + le_champ_choisi + \
                SEPARATEUR_ + VIGNETTES_INTRA 
            vignette_existante = un_groupe.findGroup( vignette_projet)
            if ( vignette_existante == None ):
                vignette_group_intra = un_groupe.addGroup( vignette_projet)
            else:
                # Si vignette preexiste, on ne recommence pas
                raise physiocap_exception_vignette_exists( vignette_projet) 

        if ( contour_avec_point >  0 ):                                            
            # Affichage dans panneau Qgis                           
            if ( self.checkBoxIntraUnSeul.isChecked()):
                physiocap_affiche_raster_iso( \
                    nom_raster_final, nom_court_raster, le_template_raster, "YES",
                    nom_iso_final, nom_court_isoligne, le_template_isolignes, "YES",
                    vignette_group_intra)


    # Progress BAR + un stepBar%
    positionBar = positionBar + stepBar     
    self.progressBarIntra.setValue( positionBar)
    positionBarInit = positionBar
 
    # On tourne sur les contours qui ont été crée par Inter
    # On passe sur les differents contours de chaque parcelle
    id_contour = 0
    for un_contour in vecteur_poly.getFeatures(): #iterate poly features
        id_contour = id_contour + 1
        try:
            un_nom = str( un_contour[ leChampPoly]) #get attribute of poly layer
        except:
            un_nom = "PHY_ID_" + str(id_contour)
            pass
        
        physiocap_log ( u"=~= =~=~=~=~= >>")
        physiocap_log ( u"=~= Nom Contour : >>" + str( un_nom) + "<<")

        # Nom du Shape moyenne 
        nom_court_vignette = nom_noeud_arbre + NOM_MOYENNE + un_nom +  EXT_CRS_SHP     
        # Attention j'ai enleve physiocap_rename_existing_file(
        nom_vignette = os.path.join( chemin_vignettes, nom_court_vignette)        
                                               
        # Nom point 
        nom_court_point = nom_noeud_arbre + NOM_POINTS + SEPARATEUR_ + un_nom + EXT_CRS_SHP     
        # JHJHJH Attention j'ai enleve physiocap_rename_existing_file(
        nom_point = os.path.join( chemin_vignettes, nom_court_point)                    
        #physiocap_log( u"=~= Vignette court : " + str( nom_court_vignette) )       

        # Verifier si le point et la vignette existent
        if not (os.path.exists( nom_vignette)):
            physiocap_log( u"=~= Vignette absente : pas d'interpolation")
            continue
        if not (os.path.exists( nom_point)):
            physiocap_log( u"=~= Points absent : pas d'interpolation")
            continue
        else:
            contour_avec_point = contour_avec_point + 1
            #physiocap_log( u"=~= Points - nom court : " + str( nom_court_point) )
            #physiocap_log( u"=~= Points - nom  : " + str( nom_point) )

        # ###################
        # CRÉATION groupe INTRA
        # ###################
        if ( contour_avec_point == 1):
            if un_groupe != None:
                vignette_projet = nom_noeud_arbre + SEPARATEUR_ + le_champ_choisi + SEPARATEUR_ + VIGNETTES_INTRA 
                vignette_existante = un_groupe.findGroup( vignette_projet)
                if ( vignette_existante == None ):
                    vignette_group_intra = un_groupe.addGroup( vignette_projet)
                else:
                    # Si vignette preexiste, on ne recommence pas
                    raise physiocap_exception_vignette_exists( vignette_projet) 
 

        # ###############
        # Calcul raster et iso
        # ###############
        nom_raster_final, nom_court_raster, nom_iso_final, nom_court_isoligne = physiocap_creer_raster_iso( self,
            nom_noeud_arbre, chemin_raster, 
            nom_court_vignette, nom_vignette, nom_court_point, nom_point,
            le_champ_choisi, un_nom)
    
        # Progress BAR + un stepBar%
        positionBar = positionBarInit + ( stepBar * id_contour)    
        self.progressBarIntra.setValue( positionBar)
        #physiocap_log( u"=~= Barre " + str( positionBar) )                      
           
        if ( id_contour >  0 ):                                            
            # Affichage dans panneau Qgis                           
            if (( self.checkBoxIntraIsos.isChecked()) or 
                ( self.checkBoxIntraImages.isChecked())):
                afficheIso = "NO"
                if ( self.checkBoxIntraIsos.isChecked()):
                    afficheIso = "YES"                
                afficheRaster = "NO"
                if ( self.checkBoxIntraImages.isChecked()):
                    afficheRaster = "YES"
                physiocap_affiche_raster_iso( \
                    nom_raster_final, nom_court_raster, le_template_raster, afficheRaster,
                    nom_iso_final, nom_court_isoligne, le_template_isolignes, afficheIso,
                    vignette_group_intra)

    if ( contour_avec_point >  0 ):                                            
        physiocap_log( u"=~= Fin des " + str(contour_avec_point) + u" interpolation(s) intra parcellaire" )                      
    else:
        physiocap_log( u"=~= Aucune point dans votre contour"
            ". Pas d'interpolation intra parcellaire" )       
        return physiocap_message_box( self, 
                self.trUtf8( "Aucune point dans votre contour. Pas d'interpolation intra parcellaire"),
                "information")
        
    self.progressBarIntra.setValue( 100)

    return physiocap_message_box( self, 
                    self.trUtf8( "Fin de l'interpolation intra-parcellaire"),
                    "information")
                    