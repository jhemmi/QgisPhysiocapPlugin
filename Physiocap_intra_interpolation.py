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
from Physiocap_tools import physiocap_message_box,\
        physiocap_log, physiocap_error, physiocap_write_in_synthese, \
        physiocap_rename_existing_file, physiocap_rename_create_dir, \
        physiocap_open_file, physiocap_quelle_projection_demandee, \
        physiocap_get_layer_by_ID

from Physiocap_var_exception import *

from PyQt4 import QtGui
from PyQt4.QtCore import Qt, QVariant 
from qgis.core import QgsProject, QgsVectorLayer , QgsMapLayerRegistry,\
    QgsMapLayer, QgsLayerTreeGroup, QgsLayerTreeLayer,  QgsRasterLayer, \
    QgsCoordinateReferenceSystem, QgsMessageLog
    
def physiocap_affiche_raster_iso( nom_raster_final, nom_court_raster, le_template_raster, affiche_raster,
                    nom_iso_final, nom_court_isoligne, le_template_isolignes, affiche_iso,
                    vignette_group_intra):
    """ Affichage du raster et Iso"""
    
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

class PhysiocapIntra( QtGui.QDialog):
    """QGIS Pour voir les messages traduits."""

    def __init__(self, parent=None):
        """Class constructor."""
        super( PhysiocapIntra, self).__init__()
        
    def physiocap_creer_raster_iso( self, dialogue,
                nom_noeud_arbre, chemin_raster, 
                nom_court_vignette, nom_vignette, nom_court_point, nom_point,
                le_champ_choisi, un_nom):
        """ Creation du raster et Iso
        Cas Saga ou Gdal : appel des Processing (Traitement) correspondants
        """
        # Pour appel de processing on attend d'etre dans Qgis et Intra
        try :
            import processing
            versionGDAL = processing.tools.raster.gdal.__version__
            versionSAGA = processing.algs.saga.SagaUtils.getSagaInstalledVersion()
        except ImportError:
            physiocap_log( self.trUtf8( "{0} nécessite l'extension {1}").\
                format( PHYSIOCAP_UNI, self.tr("Traitement")))
            raise physiocap_exception_no_processing
        except AttributeError:
            # Todo : Vérifier syntaxe en Win 32 bits et attraper cette erreur
            physiocap_log( self.trUtf8( "{0} nécessite SAGA version 2.1.0 à 2.1.2").\
                format( PHYSIOCAP_UNI))
            raise physiocap_exception_no_saga
        
        # Test SAGA version, sinon annonce de l'utilisation de GDAL
        if dialogue.radioButtonSAGA.isChecked():
            #physiocap_log ( self.trUtf8( "= Version SAGA = %s" % ( str( versionSAGA))))
            unite, dixieme, millieme = versionSAGA.split( ".")
            versionNum = float(unite) + float(dixieme)/10 + float(millieme)/100
            if ( versionNum >= 2.10) and ( versionNum <= 2.12):
                physiocap_log ( self.trUtf8( "= Version SAGA OK : %s" % ( str( versionSAGA))), "INTRA")
            else:
                physiocap_log ( self.trUtf8( "= Version SAGA %s est inférieure à 2.1.0 " % ( str( versionSAGA))))
                physiocap_log ( self.trUtf8( "= ou supérieure à 2.1.2"))
                physiocap_log ( self.trUtf8( "= On force l'utilisation de Gdal : "))
                dialogue.radioButtonSAGA.setEnabled( False)
                dialogue.radioButtonGDAL.setChecked(  Qt.Checked)
                dialogue.radioButtonSAGA.setChecked(  Qt.Unchecked)
                dialogue.spinBoxPower.setEnabled( False)
                physiocap_message_box( dialogue,
                    self.trUtf8( "= Saga a une version incompatible : on force l'utilisation de Gdal" ),
                    "information")

        # Récupération des parametres d'Intra
        powerIntra = float ( dialogue.spinBoxPower.value())
        #rayonIntra = float ( dialogue.spinBoxRayon.value())
        rayonDoubleIntra = float ( dialogue.spinBoxDoubleRayon.value())
        physiocap_log( self.trUtf8( "== Double rayon saisi =>> {0} ==== ").\
            format(  str(rayonDoubleIntra)), "INTRA")
##        calculDoubleRayonIntra = float ( dialogue.lineEditDoubleRayon.text())
##        physiocap_log( self.trUtf8( "== Double rayon calculé =>> {0} ==== ").\
##            format(  str( calculDoubleRayonIntra)), "INTRA")

        pixelIntra = float ( dialogue.spinBoxPixel.value())

         # Pour isolignes
        isoMin = float ( dialogue.spinBoxIsoMin.value())
        isoMax = float ( dialogue.spinBoxIsoMax.value())
        #isoNombreIso = float ( dialogue.spinBoxNombreIso.value())
        isoInterlignes = float ( dialogue.lineEditDistanceIso.text())
     
        # Parametres fixes
        angle = 0    # Pas utiliser
        val_nulle = 0 # Valeur nulle reste nulle
        float_32 = 5
      
        # Trace des entités en entrée
        physiocap_log( self.trUtf8( "== Nom =>> {0} ==== ").\
            format(  un_nom), "INTRA")
        physiocap_log( self.trUtf8( "Vignette (moyenne Inter) {0} et chemin à la vignette \n{1}").\
            format( nom_court_vignette, nom_vignette), "INTRA")
        physiocap_log( self.trUtf8( "Point {0} et chemin aux points \n{1}").\
            format( nom_court_point, nom_point), "INTRA")
        physiocap_log( self.trUtf8( "== Champ = {0} <<=== ").\
            format(  le_champ_choisi), "INTRA")
        # Lire points_vector et vignette_vector
        try:
            # Attrapper l'existance du fichier pour monter erreur (cas BIOMGM2)
            vignette_vector = QgsVectorLayer( nom_vignette, nom_court_vignette, 'ogr')
        except:
            physiocap_log( self.trUtf8( "{0} ne retrouve pas vos contours {1}").\
                format( PHYSIOCAP_UNI, nom_court_vignette))
            raise physiocap_exception_project_contour_incoherence( nom_court_vignette)     
        try:
            points_vector = QgsVectorLayer( nom_point, nom_court_point, 'ogr')
        except:
            physiocap_log( self.trUtf8( "{0} ne retrouve pas la couche de point {1}").\
                format( PHYSIOCAP_UNI, nom_court_point))
            raise physiocap_exception_project_point_incoherence( nom_court_point)       
     
        laProjection, EXT_CRS_SHP, EXT_CRS_PRJ, EXT_CRS_RASTER, EPSG_NUMBER = \
            physiocap_quelle_projection_demandee(dialogue)

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
        
        physiocap_log( self.trUtf8( "isoligne {0} et chemin vers isoligne\n{1}").\
            format( nom_court_isoligne, nom_isoligne), "INTRA")
        
        
        # Sous Windows :attraper les exceptions processing SAGA ascii        
        try:
            # Gérer le cas de la valeur d'un champ à part
            if platform.system() == 'Windows':            
                physiocap_log( "Type de un_nom " + str( type( un_nom)), "INTRA")
                un_nom.decode("ascii")
        except UnicodeEncodeError as e:
            physiocap_log( self.trUtf8( "{0} ne peut pas dialoguer avec Saga et des caractères non ascii").\
                format( PHYSIOCAP_UNI))
            raise physiocap_exception_windows_value_ascii( un_nom)  
        
        try:
            if platform.system() == 'Windows':            
                unicode( nom_isoligne)
                physiocap_log( "Type de isoligne " + str( type( nom_isoligne)), "INTRA")
                nom_isoligne.decode("ascii")
        except UnicodeEncodeError as e:
            physiocap_log( self.trUtf8( "{0} ne peut pas dialoguer avec Saga et des caractères non ascii").\
                format( PHYSIOCAP_UNI))
            #physiocap_log( e)
            raise physiocap_exception_windows_saga_ascii( nom_isoligne)  

        # Initialisation avant Interpolation
        nom_raster_temp = ""
        premier_raster =""
        nom_raster_final = ""
        raster_dans_poly = ""
        iso_dans_poly = ""
        nom_iso_final = ""
        # Et pour la SAGA
        iso_dans_poly_brut = ""
        nom_iso_sans_ELEV = ""
        iso_dans_poly_plus = ""
        nom_iso_avec_ELEV = ""
        
        # Récuperer Extent du polygone en cours
        ex = vignette_vector.extent()
        xmin, xmax, ymin, ymax = ex.xMinimum(),ex.xMaximum(), ex.yMinimum(), ex.yMaximum()
        info_extent = str(xmin) + "," + str(xmax) + "," + str(ymin) + "," + str(ymax)
        #physiocap_log( u"=~= Extent layer >>> " + info_extent + " <<<")  
        
        if dialogue.radioButtonSAGA.isChecked():
            # Appel SAGA power à 2 fixe
            physiocap_log( self.trUtf8( "=~= Interpolation SAGA dans {0}").\
                format(  nom_court_raster))
            # Les parametres proviennent du modele d'interpolation Physiocap du CIVC
            # apres le champ, 1 veut dire Linearly discreasing with search radius
            # 2 est power
            # 1 est bande pour expo ou gauss (non utilisé)
            # 0 recherche locale dans le rayon
            # rayon de recherche (defaut saga est 100) : local maximum search distance given in map units
            # 0 all directions et non quadrans
            # 1 tous les points ce qui annule ? le 10 qui suit
            # 10 nombre de point max
            # extent calculé precedemment
            # cellsize ou taille du pixel (unité de la carte)
            premier_raster = processing.runalg("saga:inversedistanceweighted",
                nom_point, le_champ_choisi, 1, 2, 1, 0,rayonDoubleIntra, 0, 1,
                10, info_extent, pixelIntra,
                None) 
                                       
            if (( premier_raster != None) and ( str( list( premier_raster)).find( "USER_GRID") != -1)):
                if premier_raster[ 'USER_GRID'] != None:
                    nom_raster_temp = premier_raster[ 'USER_GRID']
                    physiocap_log( "=~= Premier raster : inversedistanceweighted \n{0}".\
                        format( nom_raster_temp), "INTRA")
                else:
                    physiocap_error( self, self.trUtf8( "=~= Problème bloquant durant {0} partie-{1}").\
                        format("inversedistanceweighted","B"))
                    raise physiocap_exception_interpolation( nom_point)
            else:
                physiocap_error( self, self.trUtf8( "=~= Problème bloquant durant {0} partie-{1}").\
                    format("inversedistanceweighted","A"))
                raise physiocap_exception_interpolation( nom_point)
                                            
            # On passe ETAPE CLIP si nom_raster_temp existe
            if ( nom_raster_temp != ""):
                raster_dans_poly = processing.runalg("saga:clipgridwithpolygon",
                nom_raster_temp,
                nom_vignette,
                nom_raster)
            
            if (( raster_dans_poly != None) and ( str( list( raster_dans_poly)).find( "OUTPUT") != -1)):
                if raster_dans_poly[ 'OUTPUT'] != None:
                    nom_raster_final = raster_dans_poly[ 'OUTPUT']
                    physiocap_log( self.trUtf8("=~= Raster clippé : clipgridwithpolygon\n{0}").\
                        format( nom_raster_final), "INTRA")
                else:
                    physiocap_error( self, self.trUtf8( "=~= Problème bloquant durant {0} partie-{1}").\
                        format("clipgridwithpolygon","B"))
                    raise physiocap_exception_interpolation( nom_point)
            else:
                physiocap_error( self, self.trUtf8( "=~= Problème bloquant durant {0} partie-{1}").\
                    format("clipgridwithpolygon","A"))
                raise physiocap_exception_interpolation( nom_point)

            # On passe ETAPE ISO si nom_raster_final existe
            if ( nom_raster_final != ""):
                # Isolignes
                iso_dans_poly_brut = processing.runalg("saga:contourlinesfromgrid",
                    nom_raster_final,
                    isoMin, isoMax, isoInterlignes,
                    None)
                # physiocap_log( self.trUtf8( "=~= Interpolation SAGA - Etape 2 - FIN"))
            
                if (( iso_dans_poly_brut != None) and ( str( list( iso_dans_poly_brut)).find( "CONTOUR") != -1)):
                    if iso_dans_poly_brut[ 'CONTOUR'] != None:
                        nom_iso_sans_ELEV = iso_dans_poly_brut[ 'CONTOUR']
                        physiocap_log( self.trUtf8("=~= Iso sans LEVEL : contourlinesfromgrid\n{0}").\
                            format( nom_iso_sans_ELEV), "INTRA")
                    else:
                        physiocap_error( self, self.trUtf8( "=~= Problème bloquant durant {0} partie-{1}").\
                            format("contourlinesfromgrid","B"))
                        raise physiocap_exception_interpolation( nom_point)
                else:
                    physiocap_error( self, self.trUtf8( "=~= Problème bloquant durant {0} partie-{1}").\
                        format("contourlinesfromgrid","A"))
                    raise physiocap_exception_interpolation( nom_point)

                # On passe ETAPE FIELD si nom_iso_sans_ELEV existe
                if ( nom_iso_sans_ELEV != ""):                              
                    iso_dans_poly_plus = processing.runalg("qgis:addfieldtoattributestable", \
                        nom_iso_sans_ELEV, \
                        "ELEV", 1, 15, 2 , None)
 
                if (( iso_dans_poly_plus != None) and ( str( list( iso_dans_poly_plus)).find( "OUTPUT_LAYER") != -1)):
                    if iso_dans_poly_plus[ 'OUTPUT_LAYER'] != None:
                        nom_iso_avec_ELEV = iso_dans_poly_plus[ 'OUTPUT_LAYER']
                        physiocap_log( self.trUtf8("=~= Iso avec LEVEL ajouté : addfieldtoattributestable\n{0}").\
                            format( nom_iso_avec_ELEV), "INTRA")
                    else:
                        physiocap_error( self, self.trUtf8( "=~= Problème bloquant durant {0} partie-{1}").\
                            format("addfieldtoattributestable","B"))
                        raise physiocap_exception_interpolation( nom_point)
                else:
                    physiocap_error( self, self.trUtf8( "=~= Problème bloquant durant {0} partie-{1}").\
                        format("addfieldtoattributestable","A"))
                    raise physiocap_exception_interpolation( nom_point)

                # On passe ETAPE CALCULATOR si nom_iso_final existe
                if ( nom_iso_avec_ELEV != ""):                              
                    # Retrouver le nom de l'attribut créé
                    intra_iso_modifie = QgsVectorLayer( nom_iso_avec_ELEV, 
                            "Ne pas voir serait mieux", 'ogr')
                    fields = intra_iso_modifie.pendingFields()
                    field_probable = fields[1]
                    field_name = field_probable.name()
                    field_formule = '"' + str( field_name) + '"'  
                    physiocap_log( "=~= Isolignes formule : " + str( field_formule), "INTRA")                                                 
                    QgsMessageLog.logMessage( "PHYSIOCAP : Avant calculator ", "Processing", QgsMessageLog.WARNING)
                    # Le remplacer par "ELEV", en fait on le copie dans "ELEV"
                    iso_dans_poly = processing.runalg("qgis:fieldcalculator", \
                        nom_iso_avec_ELEV, "ELEV", 0, 15, 2, False, field_formule , nom_isoligne)

                if (( iso_dans_poly != None) and ( str( list( iso_dans_poly)).find( "OUTPUT_LAYER") != -1)):
                    if iso_dans_poly[ 'OUTPUT_LAYER'] != None:
                        nom_iso_final = iso_dans_poly[ 'OUTPUT_LAYER']
                        physiocap_log( self.trUtf8("=~= Iso final : fieldcalculator\n{0}").\
                            format( nom_iso_final), "INTRA")
                    else:
                        physiocap_error( self, self.trUtf8( "=~= Problème bloquant durant {0} partie-{1}").\
                            format("fieldcalculator","B"))
                        raise physiocap_exception_interpolation( nom_point)
                else:
                    physiocap_error( self, self.trUtf8( "=~= Problème bloquant durant {0} partie-{1}").\
                        format("fieldcalculator","A"))
                    raise physiocap_exception_interpolation( nom_point)
            else:
                physiocap_error( self, self.trUtf8( "=~= Problème bloquant durant {0} partie-{1}").\
                    format("clipgridwithpolygon","0"))
                raise physiocap_exception_interpolation( nom_point)
            physiocap_log( self.trUtf8( "=~= Interpolation SAGA - Fin iso - {0}").\
                format( nom_iso_final), "INTRA")          
        else:
            # Appel GDAL
##            physiocap_log( self.trUtf8( "=xg= Interpolation GDAL {0}").\
##                format( nom_court_raster))
            # Paramètres apres le champ
            # Power vaut 2 
            # lissage à 0 car ce lissage peut se faire dans les propriétés du raster
            # Rayon identique (unité douteuse)
            # Max points à 1000 difference avec SAGA    
            # Min à 5 
            # Angle à 0 (c'est l'angle de l'elipse
            premier_raster = processing.runalg("gdalogr:gridinvdist",
                nom_point, le_champ_choisi, powerIntra, 0.0, rayonDoubleIntra, rayonDoubleIntra, 
                1000, 5, angle, val_nulle ,float_32, 
                None)
          
            if (( premier_raster != None) and ( str( list( premier_raster)).find( "OUTPUT") != -1)):
                if premier_raster[ 'OUTPUT'] != None:
                    nom_raster_temp = premier_raster[ 'OUTPUT']
                    physiocap_log( "=xg= Premier raster : gridinvdist \n{0}".\
                        format( nom_raster_temp), "INTRA")
                else:
                    physiocap_error( self, self.trUtf8( "=~= Problème bloquant durant {0} partie-{1}").\
                        format("gridinvdist","B"))
                    raise physiocap_exception_interpolation( nom_point)
            else:
                physiocap_error( self, self.trUtf8( "=~= Problème bloquant durant {0} partie-{1}").\
                    format("gridinvdist","A"))
                raise physiocap_exception_interpolation( nom_point)           
            QgsMessageLog.logMessage( "PHYSIOCAP : Avant clip", "Processing", QgsMessageLog.WARNING)
            
            option_clip_raster = ""
            if ( EPSG_NUMBER == EPSG_NUMBER_L93 ):
                #physiocap_log( u"=xg= Projection à translater vers : " + str( EPSG_NUMBER) )
                #option_clip_raster = '-s_2015-12-09T16:17:46	1	PHYSIOCAP : Avant calculator 
                #srs "EPSG:' + str(EPSG_NUMBER_GPS) + '" -t_srs "EPSG:' + str(EPSG_NUMBER_L93) + '"'
                option_clip_raster = "-t_srs \"EPSG:" + str(EPSG_NUMBER_L93) + "\""
                
            # On passe ETAPE CLIP si nom_raster_temp existe
            if ( nom_raster_temp != ""):
                physiocap_log( self.trUtf8( "=xg= Option du clip: {0}").\
                    format( option_clip_raster), "INTRA") 
                raster_dans_poly = processing.runalg("gdalogr:cliprasterbymasklayer",
                nom_raster_temp,
                nom_vignette,
                "-9999",False,False,
                option_clip_raster, 
                nom_raster)
            
            if (( raster_dans_poly != None) and ( str( list( raster_dans_poly)).find( "OUTPUT") != -1)):
                if raster_dans_poly[ 'OUTPUT'] != None:
                    nom_raster_final = raster_dans_poly[ 'OUTPUT']
                    physiocap_log( self.trUtf8("=xg= Raster clippé : cliprasterbymasklayer \n{0}").\
                        format( nom_raster_temp), "INTRA")
                else:
                    physiocap_error( self, self.trUtf8( "=~= Problème bloquant durant {0} partie-{1}").\
                        format("cliprasterbymasklayer","B"))
                    raise physiocap_exception_interpolation( nom_point)
            else:
                physiocap_error( self, self.trUtf8( "=~= Problème bloquant durant {0} partie-{1}").\
                    format("cliprasterbymasklayer","A"))
                raise physiocap_exception_interpolation( nom_point)
            
            QgsMessageLog.logMessage( "PHYSIOCAP : Avant Iso", "Processing", QgsMessageLog.WARNING)

            # On passe ETAPE ISO si nom_raster_final existe
            if ( nom_raster_final != ""):
                # Isolignes
                iso_dans_poly = processing.runalg("gdalogr:contour",
                    nom_raster,
                    isoInterlignes,
                    "ELEV",
                    "",
                    nom_isoligne)
                                
            if (( iso_dans_poly != None) and ( str( list( iso_dans_poly)).find( "OUTPUT_VECTOR") != -1)):
                if iso_dans_poly[ 'OUTPUT_VECTOR'] != None:
                    nom_iso_final = iso_dans_poly[ 'OUTPUT_VECTOR']
                    physiocap_log( self.trUtf8("=xg= isoligne FINAL : contour \n{0}").\
                        format( nom_iso_final), "INTRA")
                else:
                    physiocap_error( self, self.trUtf8( "=~= Problème bloquant durant {0} partie-{1}").\
                        format("contour","B"))
                    raise physiocap_exception_interpolation( nom_point)
            else:
                physiocap_error( self, self.trUtf8( "=~= Problème bloquant durant {0} partie-{1}").\
                    format("contour","A"))
                raise physiocap_exception_interpolation( nom_point)
        
        return nom_raster_final, nom_court_raster, nom_iso_final, nom_court_isoligne            

    def physiocap_interpolation_IntraParcelles( self, dialogue):
        """Interpolation des données de points intra parcellaires"""
        NOM_PROJET = dialogue.lineEditProjet.text()

        # QT Confiance 
        le_champ_choisi = dialogue.fieldComboIntra.currentText()
        # Récupérer des styles pour chaque shape
        #dir_template = os.path.join( os.path.dirname(__file__), 'modeleQgis')       
        dir_template = dialogue.fieldComboThematiques.currentText()
        qml_prefix = dialogue.lineEditThematiqueIntraImage.text().strip('"')
        nom_intra_attribut = qml_prefix + str( le_champ_choisi) + EXTENSION_QML
        le_template_raster = os.path.join( dir_template, nom_intra_attribut)
        qml_prefix = dialogue.lineEditThematiqueIntraIso.text().strip('"')
        nom_isolignes_attribut = qml_prefix + le_champ_choisi + EXTENSION_QML
        le_template_isolignes  = os.path.join( dir_template, nom_isolignes_attribut)
        
        # Répertoire
        repertoire_data = dialogue.lineEditDirectoryPhysiocap.text()
        if ((repertoire_data == "") or ( not os.path.exists( repertoire_data))):
            aText = self.trUtf8( "Pas de répertoire de donnée spécifié")
            physiocap_error( self, aText)
            return physiocap_message_box( dialogue, aText, "information")
               
        # Pour polygone de contour   
        nom_complet_poly = dialogue.comboBoxPolygone.currentText().split( SEPARATEUR_NOEUD)
        if ( len( nom_complet_poly) != 2):
            aText = self.trUtf8( "Le polygone de contour n'est pas choisi. ")
            aText = aText + self.trUtf8( "Avez-vous ouvert votre shapefile de contour ?")
            physiocap_error( self, aText)
            return physiocap_message_box( dialogue, aText, "information")            
        nom_poly = nom_complet_poly[ 0] 
        id_poly = nom_complet_poly[ 1] 
        vecteur_poly = physiocap_get_layer_by_ID( id_poly)

        # Pour attribut en cours d'interpolation
        leChampPoly = dialogue.fieldComboContours.currentText()
            
        # Pour les points
        nom_complet_point = dialogue.comboBoxPoints.currentText().split( SEPARATEUR_NOEUD)
        if ( len( nom_complet_point) != 2):
            aText = self.trUtf8( "Le shape de points n'est pas choisi. ")
            aText = aText + self.trUtf8( "Lancez le traitement initial - bouton OK puis Inter - ")
            aText = aText + self.trUtf8( "avant de faire votre calcul de Moyenne Intra Parcellaire")
            physiocap_error( self, aText) 
            return physiocap_message_box( dialogue, aText, "information")            
        nom_noeud_arbre = nom_complet_point[ 0] 
        id_point = nom_complet_point[ 1] 
        vecteur_point = physiocap_get_layer_by_ID( id_point)
       
        physiocap_log( self.trUtf8( "=~= {0} début de l'interpolation des points de {1}").\
            format( PHYSIOCAP_UNI, nom_noeud_arbre))
        # Progress BAR 2%
        dialogue.progressBarIntra.setValue( 2)
        
        # Vérification de l'arbre
        root = QgsProject.instance().layerTreeRoot( )
        un_groupe = root.findGroup( nom_noeud_arbre)
        if ( not isinstance( un_groupe, QgsLayerTreeGroup)):
            aText = self.trUtf8( "Le projet {0} n'existe pas. ").\
                format(  nom_noeud_arbre)
            aText = aText + self.trUtf8( "Créer une nouvelle instance de projet - bouton OK puis Inter - ")
            aText = aText + self.trUtf8( "avant de faire votre interpolation Intra Parcellaire")
            physiocap_error( self, aText, "CRITICAL")
            return physiocap_message_box( dialogue, aText, "information" )            
        
        # Vérification 
        if ( vecteur_point == None):
            aText = self.trUtf8( "Le jeu de points choisi n'est pas valide. ")
            aText = aText + self.trUtf8( "Créer une nouvelle instance de projet - bouton OK puis Inter - ")
            aText = aText + self.trUtf8( "avant de faire votre interpolation Intra Parcellaire")
            physiocap_error( self, aText, "CRITICAL")
            return physiocap_message_box( dialogue, aText, "information" )  

        if ( vecteur_poly == None) or ( not vecteur_poly.isValid()):
            aText = self.trUtf8( "Le contour choisi n'est pas valide. ")
            aText = aText + self.trUtf8( "Créer une nouvelle instance de projet - bouton OK puis Inter - ")
            aText = aText + self.trUtf8( "avant de faire votre interpolation Intra Parcellaire")
            physiocap_error( self, aText, "CRITICAL")
            return physiocap_message_box( dialogue, aText, "information" ) 
                   
        laProjection, EXT_CRS_SHP, EXT_CRS_PRJ, EXT_CRS_RASTER, EPSG_NUMBER = \
            physiocap_quelle_projection_demandee(dialogue)
        crs = QgsCoordinateReferenceSystem( EPSG_NUMBER, QgsCoordinateReferenceSystem.PostgisCrsId)

        # Assert repertoire shapefile 
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
        dialogue.progressBarIntra.setValue( 4)

        lesFormes = vecteur_poly.getFeatures()
        iforme = 0
        for f in lesFormes:
            iforme = iforme + 1
        stepBar = int( 60 / iforme)
        positionBar = 5
        
        # On passe sur le contour général
        contour_avec_point = 0
        contours_possibles = 0
       
        # #####################
        # Cas d'une image seule
        # #####################
        if ( dialogue.checkBoxIntraUnSeul.isChecked()):
            contours_possibles = contours_possibles + 1

            # Nom du Shape moyenne et de sa vignette dans l'arbre
            nom_vecteur_contour = vecteur_poly.name()
            nom_court_du_contour = os.path.basename( nom_vecteur_contour + EXTENSION_SHP)
            nom_court_vignette = nom_noeud_arbre + NOM_MOYENNE + nom_court_du_contour
            nom_vignette = os.path.join( chemin_vignettes, nom_court_vignette)        
                                                   
            # Nom point 
            nom_court_point = NOM_PROJET + NOM_POINTS + EXT_CRS_SHP     
            nom_point = os.path.join( chemin_shapes, nom_court_point)                    

            # Vérifier si le point et la vignette existent
            if not (os.path.exists( nom_vignette)):
                physiocap_log( self.trUtf8( "=~=  Pas d'interpolation, Vignette absente : {0}").\
                    format( nom_vignette))
            if not (os.path.exists( nom_point)):
                physiocap_log( self.trUtf8( "=~=  Pas d'interpolation, Points absents : {0}").\
                    format( nom_point))
            else:
                try:
                    # ###############
                    # Calcul raster et iso
                    # ###############
                    physiocap_log( self.trUtf8( "=~=  Le contour : {0}").\
                        format( nom_vecteur_contour), "INTRA")
                    nom_raster_final, nom_court_raster, nom_iso_final, nom_court_isoligne = \
                        self.physiocap_creer_raster_iso( dialogue,
                        nom_noeud_arbre, chemin_raster, 
                        nom_court_vignette, nom_vignette, nom_court_point, nom_point,
                        le_champ_choisi, nom_vecteur_contour[:-4]) 
                    contour_avec_point = contour_avec_point + 1
                except physiocap_exception_windows_value_ascii as e:
                    aText = self.trUtf8( "La valeur {0} a ").\
                        format( e)
                    aText = aText + self.trUtf8( "des caractères (non ascii) incompatibles avec l'interpolation SAGA.")
                    aText = aText + self.trUtf8( "Erreur bloquante sous Windows qui empêche de traiter cette interpolation.")
                    physiocap_error( self, aText, "CRITICAL")        
                except:
                    raise
                finally:
                    pass
                # Fin de capture des err
                            
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
                if ( dialogue.checkBoxIntraUnSeul.isChecked()):
                    physiocap_affiche_raster_iso( \
                        nom_raster_final, nom_court_raster, le_template_raster, "YES",
                        nom_iso_final, nom_court_isoligne, le_template_isolignes, "YES",
                        vignette_group_intra)


        # Progress BAR + un stepBar%
        positionBar = positionBar + stepBar     
        dialogue.progressBarIntra.setValue( positionBar)
        positionBarInit = positionBar
     
        # On tourne sur les contours qui ont été crée par Inter
        # On passe sur les differents contours de chaque parcelle
        id_contour = 0
        for un_contour in vecteur_poly.getFeatures(): #iterate poly features
            id_contour = id_contour + 1
            contours_possibles = contours_possibles + 1
            try:
                #un_nom = str( un_contour[ leChampPoly]) #get attribute of poly layer
                un_nom = un_contour[ leChampPoly] #get attribute of poly layer
            except:
                un_nom = "PHY_ID_" + str(id_contour)
                pass
            
            physiocap_log ( self.trUtf8( "=~= Début Interpolation de {0} >>>>").\
                format( un_nom))

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
                physiocap_log( self.trUtf8( "=~= Vignette absente : pas d'interpolation"))
                continue
            if not (os.path.exists( nom_point)):
                physiocap_log( self.trUtf8( "=~= Points absents : pas d'interpolation"))
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
     
            try:
                # ###############
                # Calcul raster et iso
                # ###############
##            physiocap_log( u"=~= Points CHAQUE - nom court : " + str( nom_court_point) )
##            physiocap_log( u"=~= Points CHAQUE - nom  : " + str( nom_point) )
                nom_raster_final, nom_court_raster, nom_iso_final, nom_court_isoligne = \
                    self.physiocap_creer_raster_iso( dialogue, nom_noeud_arbre, chemin_raster, 
                    nom_court_vignette, nom_vignette, nom_court_point, nom_point,
                    le_champ_choisi, un_nom)
            except physiocap_exception_windows_value_ascii as e:
                aText = self.trUtf8( "La valeur {0} a ").\
                    format( e)
                aText = aText + self.trUtf8( "des caractères (non ascii) incompatibles avec l'interpolation SAGA.")
                aText = aText + self.trUtf8( "Erreur bloquante sous Windows qui empeche de traiter cette interpolation.")
                physiocap_error( self, aText, "CRITICAL")        
                continue    
            except:
                raise
            finally:
                pass
            # Fin de capture des err        
            
            
            # Progress BAR + un stepBar%
            positionBar = positionBarInit + ( stepBar * id_contour)    
            dialogue.progressBarIntra.setValue( positionBar)
            #physiocap_log( u"=~= Barre " + str( positionBar) )                      
               
            if ( id_contour >  0 ):                                            
                # Affichage dans panneau Qgis                           
                if (( dialogue.checkBoxIntraIsos.isChecked()) or 
                    ( dialogue.checkBoxIntraImages.isChecked())):
                    afficheIso = "NO"
                    if ( dialogue.checkBoxIntraIsos.isChecked()):
                        afficheIso = "YES"                
                    afficheRaster = "NO"
                    if ( dialogue.checkBoxIntraImages.isChecked()):
                        afficheRaster = "YES"
                    physiocap_affiche_raster_iso( \
                        nom_raster_final, nom_court_raster, le_template_raster, afficheRaster,
                        nom_iso_final, nom_court_isoligne, le_template_isolignes, afficheIso,
                        vignette_group_intra)
                physiocap_log ( self.trUtf8( "=~= Fin Interpolation de {0} <<<<").\
                    format( un_nom))

        if ( contour_avec_point >  0 ):                                            
            physiocap_log( self.trUtf8( "=~= Fin des {0}/{1} interpolation(s) intra parcellaire").\
                format( str(contour_avec_point), str( contours_possibles)))
        else:
            aText = self.trUtf8( "=~= Aucune point dans votre contour. ")
            aText = aText + self.trUtf8( "Pas d'interpolation intra parcellaire")       
            physiocap_log( aText)
            return physiocap_message_box( dialogue, aText, "information")
            
        dialogue.progressBarIntra.setValue( 100)

        return physiocap_message_box( dialogue, 
                        self.trUtf8( "Fin de l'interpolation intra-parcellaire"),
                        "information")
                        