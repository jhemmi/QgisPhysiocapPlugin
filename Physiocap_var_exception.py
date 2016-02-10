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
# ###########################
# Preparation Python 3 pour QGIS 3
# ###########################
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
# Suppression des u''
from __future__ import unicode_literals

##from builtins import open
##from builtins import str

import os 
import platform

# ###########################
# VARIABLES GLOBALES
# ###########################

# Ces variables sont nommées en Francais par compatibilité avec la version physiocap_V8
# dont les fonctions de calcul sont conservé à l'identique
# Répertoire de base et projet
PHYSIOCAP_TRACE = "YES"
POSTGRES_NOM = "postgres"
# En prod CENTROIDES vaut NO
CENTROIDES = "NO"  # CENTROIDES YES est pour voir les centroides dans la synthese

REPERTOIRE_DONNEES_BRUTES = "Choisissez votre chemin"
PHYSIOCAP_NOM = "Physiocap"
PHYSIOCAP_UNI = "\u03D5"

# Test de robustesse de la gestion des unicodes
PHYSIOCAP_TEST1 = "ȧƈƈḗƞŧḗḓ ŧḗẋŧ ƒǿř ŧḗşŧīƞɠ"
PHYSIOCAP_TEST2 = "ℛℯα∂α♭ℓℯ ♭ʊ☂ η☺т Ѧ$☾ℐℐ"
PHYSIOCAP_TEST3 = "¡ooʇ ןnɟǝsn sı uʍop-ǝpısdn"
PHYSIOCAP_TEST4 = "Moët"

SEPARATEUR_ ="_"
NOM_PROJET = "PHY" + SEPARATEUR_ + PHYSIOCAP_TEST4 + SEPARATEUR_

# Listes de valeurs
#CEPAGES = [ "INCONNU", "CHARDONNAY", "MERLOT", "NEGRETTE", "PINOT NOIR", "PINOT MEUNIER"]
CEPAGES = [ "Inconnu", \
"Airen", "Chardonnay", "Trebbiano", "Grasevina", "Rkatsiteli", "Sauvignon", "Cayetana", \
"Catarratto", "Macabeo", "Chenin", "Riesling", "Colombard", "Aligote", "Muëller Thurgau", \
"Palomino Fino", "Muscat", "Semillon", "Feteasca", "Gruner Veltliner", "Trebbiano Romagnolo", \
"Pinot Blanc", "Garganega", "Niagara", "Pedro Gimenez", "Fernao Pires", "Sultaniye", "Chasselas", \
"Melon", \
"Cabernet Sauvignon", "Grenache", "Merlot", "Mazuelo", "Syrah", "Bobal", "Tempranillo", "Monastrell", \
"Sangiovese", "Négrette", "Pinot Noir", "Pinot Meunier", "Cabernet Franc", "Cinsaut", "Gamay", \
"Alicante", "Barbera", "Montepulciano", "Isabella", "Tribidrag", "Criolla Grande", "Cot", "Pamid", \
"Douce Noire", "Negroamaro", "Doukkali", "Listan Prieto", "Prokupac", "Castelao", "Mencia", \
"Blaufrankisch", "Concord", "Zinfandel" ]


TAILLES = [ "Inconnue", "Chablis", "Cordon de Royat", "Cordon libre", "Guyot simple", "Guyot double"]
FORMAT_VECTEUR = [ "ESRI Shapefile"] # POSTGRES_NOM] # "memory"]

# Répertoires des sources et de concaténation en fichiers texte
FICHIER_RESULTAT = "resultat.txt"
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
EXTENSION_RASTER = ".tif"
EXTENSION_RASTER_SAGA = ".sdat"

EXTENSION_QML = ".qml"

EXTENSION_POUR_ZERO = SEPARATEUR_ + "0"

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
#SHAPE_CONTOURS = '/home/jhemmi/Documents/GIS/SCRIPT/QGIS/PhysiocapAnalyseur/data Cap/Contour.shp'
SEPARATEUR_NOEUD = "~~"
NOM_MOYENNE = SEPARATEUR_ + "MOYENNE" + SEPARATEUR_
VIGNETTES_INTER = "INTER_PARCELLAIRE"
NOM_POINTS = SEPARATEUR_ + "POINTS"
NOM_INTER = SEPARATEUR_ + "INTER"

# Intra PARCELLAIRE
VIGNETTES_INTRA = "INTRA_PARCELLAIRE"
NOM_INTRA = SEPARATEUR_ + "INTRA"
REPERTOIRE_RASTERS = "IntraParcelle"
ATTRIBUTS_INTRA = [ "DIAM", "NBSARM", "BIOM"] 
ATTRIBUTS_INTRA_DETAILS = [ "BIOMGM2"] 
CHEMIN_TEMPLATES = [ "modeleQgis", "project_templates"]
UNE_SEULE_FOIS = "NO"

# Exceptions Physiocap 
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

# INTRA
class physiocap_exception_interpolation( physiocap_exception):
    pass
class physiocap_exception_vignette_exists( physiocap_exception):
    pass
class physiocap_exception_points_invalid( physiocap_exception):
    pass
class physiocap_exception_no_processing( ):
    pass
class physiocap_exception_no_saga( ):
    pass
class physiocap_exception_project_contour_incoherence( physiocap_exception):
    pass
class physiocap_exception_project_point_incoherence( physiocap_exception):
    pass
class physiocap_exception_windows_saga_ascii( physiocap_exception):
    pass
class physiocap_exception_windows_value_ascii( physiocap_exception):
    pass
class physiocap_exception_pg( physiocap_exception):
    pass

