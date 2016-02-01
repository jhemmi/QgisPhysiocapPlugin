# -*- coding: utf-8 -*-
""" 
/***************************************************************************
 physiocap_creer_arbre
                                 A QGIS plugin
 Physiocap plugin helps analyse raw data from Physiocap in Qgis and 
 creates a synthesis of Physiocap measures' campaign
 Physiocap plugin permet l'analyse les données brutes de Physiocap dans Qgis et
 crée une synthese d'une campagne de mesures Physiocap
 
 Le module physiocap_creer_arbre gère le nommage et création 
 de l'arbre des résultats d'analyse (dans la même
 structure de données que celle créé par PHYSICAP_V8 du CIVC) 

 Les variables et fonctions sont nommées en Francais
 
                             -------------------
        begin                : 2015-12-05
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
        physiocap_look_for_MID, physiocap_list_MID, physiocap_quel_uriname, \
        physiocap_get_uri_by_layer, physiocap_tester_uri

from Physiocap_CIVC import physiocap_csv_vers_shapefile, physiocap_assert_csv, \
        physiocap_fichier_histo, physiocap_tracer_histo, physiocap_filtrer   

from Physiocap_inter import physiocap_fill_combo_poly_or_point

from Physiocap_var_exception import *

from PyQt4 import QtGui, uic
from PyQt4.QtCore import QSettings
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import *
from qgis.gui import *

import glob
import shutil
import time  
   
# Creation des repertoires source puis resultats puis histo puis shape
# Todo : creer une classe heritant de iface pour permettre la traduction