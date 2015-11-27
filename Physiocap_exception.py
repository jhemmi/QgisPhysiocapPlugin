# -*- coding: utf-8 -*-
"""
/***************************************************************************
 PhysiocapException
                                 A QGIS plugin

 Le module Exception contient les définition d'exception
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
import os 
import platform

# ###########################
# VARIABLES GLOBALES
# ###########################

# Ces variables sont nommées en Francais par compatibilité avec la version physiocap_V8
# dont les fonctions de calcul sont conservé à l'identique
# Répertoire de base et projet
PHYSIOCAP_TRACE = "Yes"
CENTROIDES = "NO"
SHAPE_MOYENNE_PAR_CONTOUR = "NO"
# Todo : Parametre Intra
INTRA = "YES"

REPERTOIRE_DONNEES_BRUTES = "/home/jhemmi/Documents/GIS/SCRIPT/QGIS/PhysiocapAnalyseur/data"
PHYSIOCAP_NOM = "Physiocap"
SEPARATEUR_ ="_"
NOM_PROJET = "PHY" + SEPARATEUR_

# Listes de valeurs
CEPAGES = [ "INCONNU", "CHARDONNAY", "MERLOT", "NEGRETTE", "PINOT NOIR", "PINOT MEUNIER"]
TAILLES = [ "Inconnue", "Chablis", "Guyot simple", "Guyot double", "Cordon de Royat", "Cordon libre" ]
FORMAT_VECTEUR = [ "ESRI Shapefile"] #, "postgres", "memory"]

# Répertoires des sources et de concaténation en fichiers texte
FICHIER_RESULTAT = NOM_PROJET  + SEPARATEUR_ + "resultat.txt"
REPERTOIRE_SOURCES = "fichiers_sources"
SUFFIXE_BRUT_CSV = SEPARATEUR_ + "RAW.csv"
EXTENSION_MID = "*.MID"
NB_VIRGULES = 58

REPERTOIRE_TEXTES = "fichiers_texte"
# Pour histo
REPERTOIRE_HELP = os.path.join( os.path.dirname(__file__),"help")
FICHIER_HISTO_NON_CALCULE = os.path.join( REPERTOIRE_HELP, 
    "Histo_non_calcule.png")

REPERTOIRE_HISTOS = "histogrammes"
if platform.system() == 'Windows':
    # Matplotlib et png problematique sous Windows
    SUFFIXE_HISTO = ".tiff"
else:
    SUFFIXE_HISTO = ".png"
FICHIER_HISTO_SARMENT = "histogramme_SARMENT_RAW" + SUFFIXE_HISTO
FICHIER_HISTO_DIAMETRE = "histogramme_DIAMETRE_RAW"  + SUFFIXE_HISTO
FICHIER_HISTO_DIAMETRE_FILTRE = "histogramme_DIAM_FILTERED" +  SUFFIXE_HISTO

REPERTOIRE_SHAPEFILE = "shapefile"
PROJECTION_L93 = "L93"
PROJECTION_GPS = "GPS"
EXTENSION_SHP = ".shp"
EXTENSION_PRJ = ".prj"
EXTENSION_RASTER = ".grd"


EXTENSION_SHP_L93 = SEPARATEUR_  + PROJECTION_L93 + EXTENSION_SHP
EXTENSION_SHP_GPS = SEPARATEUR_  + PROJECTION_GPS + EXTENSION_SHP
EXTENSION_POUR_ZERO = SEPARATEUR_ + "0"
EXTENSION_PRJ_L93 = SEPARATEUR_ + PROJECTION_L93 + EXTENSION_PRJ
EXTENSION_PRJ_GPS = SEPARATEUR_ + PROJECTION_GPS + EXTENSION_PRJ
EXTENSION_RASTER_L93 = SEPARATEUR_ + PROJECTION_L93 + EXTENSION_RASTER
EXTENSION_RASTER_GPS = SEPARATEUR_ + PROJECTION_GPS + EXTENSION_RASTER
EPSG_NUMBER_L93 = 2154
EPSG_NUMBER_GPS = 4326
        
EPSG_TEXT_L93 = 'PROJCS["RGF93_Lambert_93",GEOGCS["GCS_RGF93",DATUM["D_RGF_1993", \
SPHEROID["GRS_1980",6378137,298.257222101]],PRIMEM["Greenwich",0], \
UNIT["Degree",0.017453292519943295]],PROJECTION["Lambert_Conformal_Conic"], \
PARAMETER["standard_parallel_1",49],PARAMETER["standard_parallel_2",44], \
PARAMETER["latitude_of_origin",46.5],PARAMETER["central_meridian",3], \
PARAMETER["false_easting",700000],PARAMETER["false_northing",6600000], \
UNIT["Meter",1]]'
EPSG_TEXT_GPS = 'GEOGCS["GCS_WGS_1984",DATUM["D_WGS_1984", \
SPHEROID["WGS_1984",6378137,298.257223563]],PRIMEM["Greenwich",0], \
UNIT["Degree",0.017453292519943295]]'

# Inter PARCELLAIRE
SHAPE_CONTOURS = '/home/jhemmi/Documents/GIS/SCRIPT/QGIS/PhysiocapAnalyseur/data Cap/Contour.shp'
SEPARATEUR_NOEUD = "~~"
NOM_MOYENNE = "MOYENNE"
VIGNETTES_INTER = "INTER_PARCELLAIRE"
NOM_POINTS = SEPARATEUR_ + "POINTS"
NOM_INTER = SEPARATEUR_ + "INTER"

# Exceptions Physiocap 
ERREUR_EXCEPTION = u"Physiocap n'a pas correctement terminé son analyse"
TAUX_LIGNES_ERREUR= 30

# ###########################
# Exceptions Physiocap
# ###########################
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
class physiocap_exception_stop_user( ):
    pass  
class physiocap_exception_params( physiocap_exception):
    pass
class physiocap_exception_vignette_exists( physiocap_exception):
    pass
class physiocap_exception_points_invalid( physiocap_exception):
    pass
    