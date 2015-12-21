# -*- coding: utf-8 -*-
"""
/***************************************************************************
 Physiocap_tools
                                 A QGIS plugin
 Physiocap plugin helps analyse raw data from Physiocap in Qgis and 
 creates a synthesis of Physiocap measures' campaign
 Physiocap plugin permet l'analyse les données brutes de Physiocap dans Qgis et
 crée une synthese d'une campagne de mesures Physiocap
 
 Le module tools contient les utilitaires
 Les fonctions sont nommées en Anglais
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
from Physiocap_var_exception import *

from PyQt4 import QtGui, uic  # for Form_class
from PyQt4.QtCore import *
#from PyQt4.QtSql import *
import psycopg2
#from PyQt4.QtGui import *
from qgis.core import *
from qgis.gui import *

# Imports system & os
#import os.path
import sys, string
import time  

if platform.system() == 'Windows':
    import win32api

# MESSAGES & LOG
def physiocap_message_box( self, text, level ="warning", title="Physiocap"):
    """Send a message box by default Warning"""
    if level == "about":
        QMessageBox.about( self, title, text)
    elif level == "information":
        QMessageBox.information( self, title, text)
    elif level == "error":
        QMessageBox.error( self, title, text)
    else:
        QMessageBox.warning( self, title, text)

def physiocap_question_box( self, text="Etes-vous sûr(e) ?" , title = "Physiocap"):
    """Send a question box """
    reply = QMessageBox.question(self, title, text,
            QMessageBox.Yes|QMessageBox.Cancel)
    if reply == QMessageBox.Cancel:
        return False
    if reply == QMessageBox.Yes:
        return True
    return False

def physiocap_log( aText, level ="INFO"):
    """Send a text to the Physiocap log"""
    if PHYSIOCAP_TRACE == "YES":
        if level == "WARNING":
            QgsMessageLog.logMessage( aText, "Physiocap informations", QgsMessageLog.WARNING)
        else:
            QgsMessageLog.logMessage( aText, "Physiocap informations", QgsMessageLog.INFO)
           
def physiocap_error( aText, level ="WARNING"):
    """Send a text to the Physiocap error"""
    if level == "WARNING":
        QgsMessageLog.logMessage( aText, "Physiocap erreurs", QgsMessageLog.WARNING)
    else:
        QgsMessageLog.logMessage( aText, "Physiocap erreurs", QgsMessageLog.CRITICAL)

    # Todo 1.5 ? Rajouter la trace d'erreur au fichier ?

    return -1      

def physiocap_write_in_synthese( self, aText):
    """Write a text in the results list"""
    uText = unicode( aText, 'utf-8')
    self.textEditSynthese.insertPlainText( uText)   
    
def JH_is_int_number(s):
    try:
        int(s)
        return True
    except ValueError:
        return False
 
def physiocap_get_layer_by_ID( layerID):
    """ Retrouve un layer ID dans la map Tree Root"""
    layer_trouve = None
    root = QgsProject.instance().layerTreeRoot()
 
    ids = root.findLayerIds()
    layers = root.findLayers()
##    physiocap_log( "--- layerids: " + str( ids))
##    physiocap_log( "- layers : " + str( layers))    

    for id in ids:
        if id == layerID:
            #physiocap_log( u"Layer retrouvé : " + str( layerID))
            layer_trouve = root.findLayer( layerID)
            le_layer = layer_trouve.layer()
            break
    if ( layer_trouve != None):
        if ( le_layer.isValid()):
            return le_layer
        else:
            physiocap_log( "Layer invalide : " + str( le_layer.name()))
            return None
    else:
        physiocap_log( "Aucun layer retrouvé pour ID : " + str( layerID))
        return None

   
def physiocap_quelle_projection_demandee( self):
    """ Selon la valeur cochée dans le radio de projection
    positionne laProjection, EXTENSION_SHP, EXTENSION_PRJ et epsg
    """
    laProjection = PROJECTION_L93
    if self.radioButtonGPS.isChecked():
        laProjection = PROJECTION_GPS
    if self.radioButtonL93.isChecked():
        laProjection = PROJECTION_L93
    #physiocap_log(u"Projection des shapefiles demandée en " + laProjection)
 
    EXTENSION_SHP_COMPLET = SEPARATEUR_ + laProjection + EXTENSION_SHP
    EXTENSION_PRJ_COMPLET = SEPARATEUR_ + laProjection + EXTENSION_PRJ
   
    if ( laProjection == PROJECTION_L93 ):
        EPSG_NUMBER = EPSG_NUMBER_L93
    if ( laProjection == PROJECTION_GPS ):
        EPSG_NUMBER = EPSG_NUMBER_GPS
    
    # Cas du nom du raster 
    if self.radioButtonSAGA.isChecked():
        EXTENSION_RASTER_COMPLET = SEPARATEUR_ + laProjection + EXTENSION_RASTER_SAGA
    else:
        EXTENSION_RASTER_COMPLET = SEPARATEUR_ + laProjection + EXTENSION_RASTER

    return laProjection, EXTENSION_SHP_COMPLET, EXTENSION_PRJ_COMPLET, EXTENSION_RASTER_COMPLET, EPSG_NUMBER

def physiocap_quel_uriname( self):
    """ Retourne l'uriName attendu """
    a_time = time.strftime( "%d/%m/%y %H:%M\n",time.localtime())
    maRef = self.settings.value("Physiocap/nomJhemmi", "xx").split( SEPARATEUR_NOEUD) 
    if (len( maRef) == 2):
        monMo = a_time.split("/") 
        uriName = maRef[0]  + SEPARATEUR_ + monMo[1] + SEPARATEUR_ + maRef[1]
        return uriName
    else:
        return None
 
def physiocap_existe_table_uri( self, uri_deb, laTable):
    """ Retourne true si la table existe dans uri """
        
    try:
        conn = psycopg2.connect( uri_deb)
    except:
        physiocap_log( u"Impossible de se connecter à la base de données " + str( uri_deb))
        physiocap_error( u"Impossible de se connecter à la base de données " + str( uri_deb))
        return False
    
    # Ouvre une curseur
    cur = conn.cursor()
    # Execute a command: this creates a new table
    commande = "select '" + laTable + "'::regclass;"
    physiocap_log( u"La commande " + str( commande))
    cur.execute( commande)
    rows = cur.fetchall()
    for row in rows:
        physiocap_log( u"Existe ? : " + str(row))
    return True

def physiocap_tester_uri( self, uriSource):
    """ Retourne uri_connect et uri_deb et uri_fin retrouvés dans uriSource """
    # Tester si la source est bien une base
    if (str( type( uriSource)) != "<class 'qgis._core.QgsDataSourceURI'>"):
        physiocap_log( u"Incohérence trop flag")
        return None, None, None
##    try:
##        physiocap_log( u"xxx Uri source dir : " + str( dir( uriSource)))
##        #physiocap_log( u"xxx Uri source key : " + str( uriSource.keyColumn()))
##        #physiocap_log( u"xxx Uri source wkbtype : " + str( uriSource.wkbType()))
##    except:
##        pass
        
    # Tester la connection à la base
    uri_deb = "dbname='" + uriSource.database() + "'" + \
              " host='" + uriSource.host() + "'" + \
              " port=" + uriSource.port() + \
              " user='" + uriSource.username() + "'" + \
              " password='" + uriSource.password() + "'" # Fin
    uneDatabase = uriSource.database()
    try:
        #conn = psycopg2.connect("dbname='testpostgis' user='postgres' host='localhost' password='postgres'")
        conn = psycopg2.connect( uri_deb)
    except:
        physiocap_log( u"Impossible de se connecter à la base de données " + str( uneDatabase))
        physiocap_error( u"Impossible de se connecter à la base de données " + str( uneDatabase))
        return None, None, None
    
    physiocap_log( u"PG == Ouverture de la base de données " + str( uneDatabase) + \
        " == " + str( conn.status))

    # Ouvre une curseur
    cur = conn.cursor()
    # Execute a command: this creates a new table
    cur.execute( "select version();")
    rows = cur.fetchall()
    physiocap_log( u"PG == Version de la base : " + str(rows[ 0]))
##    cur.execute( "select 'public.\"DIAMETRE\"'::regclass;")
##    rows = cur.fetchall()
##    physiocap_log( u"Version de la base : " + str(rows[ 0]))

    # conn.commit()
    # Close communication with the database
    cur.close()
    conn.close()    
    physiocap_log( u"PG == Fermeture de la base de données " + str( uneDatabase) + \
        " == " + str( conn.status))
    # Tout est OK
    uri_connect = uriSource.connectionInfo()   ## de bd à ssl
##    physiocap_log( u"xxx Uri connection : " + str( uri_connect) )

    uri_deb = uri_connect + \
              " srid=" + uriSource.srid()
    uri_fin = " (geom) sql="
##    physiocap_log( u"xxx Uri debut : " + uri_deb )
##    physiocap_log( u"xxx Uri fin : " + uri_fin )
    return uri_connect, uri_deb, uri_fin
    
def physiocap_get_uri_by_layer( self, uriName = "INIT" ):
    """ Retourne une uri correspondans au premier layer qui est dans
        une base postgres
        Rend uriname pour le ca "init"
    """
    if (uriName == "INIT"):
        # Vérification que l'on a un URI Physiocap
        uriName = physiocap_quel_uriname( self)
        return uriName
    else:
        # uriName est recherché
        layerMap = QgsMapLayerRegistry.instance().mapLayers()
        layerOK = None
        for name, layer in layerMap.iteritems():
            pro = layer.dataProvider() 
            if (( layer.type() == QgsMapLayer.VectorLayer) and ( pro.name() == JHPOST)):
                #physiocap_log( u"URI BY LAYER Couche trouvée est : " + str( name))
                layerOK = layer
               # The layer is found
                break
        
        if ( layerOK != None):
            if layerOK.isValid():
                physiocap_log( u"URI BY LAYER Db trouvée : "  + QgsDataSourceURI(pro.dataSourceUri()).database())
                if (QgsDataSourceURI(pro.dataSourceUri()).database() == uriName):
                    return QgsDataSourceURI(pro.dataSourceUri()) #.uri())
                else:
                    return None
            else:
                return None
    return None
        
def JH_rename_existing( chemin):
    """ Retourne le nom qu'il est possible de creer
        si chemin existe deja, on creer un "chemin + (1)"
        si "chemin_projet + (1)" existe déjà, on crée un "chemin_projet + (2)" etc         
    """
    # Exception suffixe
    extension = ""
    pos_extension = -1
    if ( os.path.isfile(chemin)):
        pos_extension = chemin.rfind( ".")
        extension = chemin[ pos_extension:]
        if ( pos_extension != -1):
            chemin = chemin[: pos_extension]
            #physiocap_log(u"Nouveau chemin" + chemin)
            
    # Si chemin a déjà une parenthèse dans la 3 derniers caracteres
    longueur = len(chemin)
    if chemin[-1:] == ")":
        # cas du chemin qui a été déjà renommer
        pos = -2
        while chemin[ pos:][0] != "(":
            pos = pos - 1
            if pos == (-1 * longueur): 
                pos = -1
                break
        if pos != (-1):
            # ici la "(" est à pos et la ")" est à -1:
            un_num_parenthese = chemin[ pos+1:]
            un_num = un_num_parenthese[ :-1]
            nouveau_numero = 1
            if JH_is_int_number( un_num):
                nouveau_numero = int(un_num) + 1
                nouveau_chemin = chemin[:pos] + "(" +str(nouveau_numero) +")"
            else:
                # cas d'un nom etrange
                nouveau_chemin = chemin + "(1)"        
        else:
            # cas d'un nom etrange
            nouveau_chemin = chemin + "(1)" 
    else:
        # cas du premier fichier renommer
        nouveau_chemin = chemin + "(1)"

    # Remettre extension
    if (extension != ""):
        nouveau_chemin = nouveau_chemin + extension
               
    return nouveau_chemin


def physiocap_rename_existing_file ( chemin):
    """ Retourne le nom de fichier qu'il est possible de creer
        si chemin existe deja, on creer un "chemin + (1)"
        si "chemin_projet + (1)" existe déjà, on crée un "chemin_projet + (2)" etc         
    """
    if ( os.path.exists( chemin)):
        nouveau_chemin = JH_rename_existing( chemin)
        return physiocap_rename_existing_file( nouveau_chemin) 
    else:
        #physiocap_log( "chemin pour creation du fichier ==" + chemin)
        return chemin

def physiocap_rename_create_dir( chemin):
    """ Retourne le repertoire qu'il est possible de creer
        si chemin existe deja, on creer un "chemin + (1)"
        si "chemin_projet + (1)" existe déjà, on crée un "chemin_projet + (2)" etc         
    """
    #physiocap_log( "Dans create rename DIR DEBUT ==" + chemin)
    if ( os.path.exists( chemin)):
        nouveau_chemin = JH_rename_existing( chemin)
        return physiocap_rename_create_dir( nouveau_chemin) 
    else:
        try:
            os.mkdir( chemin)
        except:
            physiocap_log( "Erreur dans fonction recursive ==" + chemin)
            raise physiocap_exception_rep( chemin)
            
        #physiocap_log( "avant retour OK et apres creation DIR ==>>" + chemin + "<<==")
        return chemin


def physiocap_open_file( nom_court, chemin, type_ouverture="w"):
    """ Créer ou detruit et re-crée un fichier"""
    # Fichier des diamètres     
    nom_fichier = os.path.join(chemin, nom_court)
    if ((type_ouverture == "w") and os.path.isfile( nom_fichier)):
        os.remove( nom_fichier)
    try :
        fichier_pret = open(nom_fichier, type_ouverture)
    except :
        raise physiocap_exception_fic( nom_court)
    return nom_fichier, fichier_pret


# Fonction pour vérifier le fichier csv    
def physiocap_look_for_MID( repertoire, recursif, exclusion="fic_sources"):
    """Fonction de recherche des ".MID". 
    Si recursif vaut "Oui", on scrute les sous repertoires à la recheche de MID 
    mais on exclut le repertoire de Exclusion dont on ignore les MID 
    """
    root_base = ""
    MIDs = []
    for root, dirs, files in os.walk( repertoire, topdown=True):
        if root_base == "":
            root_base = root
##        physiocap_log("ALL Root :" + str(root))
##        physiocap_log("ALL DIR :" + str(dirs))
##        physiocap_log("ALL FILE :" + str(files))
        if exclusion in root:
            continue
        for name_file in files:
            if ".MID" in name_file[-4:]:
                MIDs.append( os.path.join( root, name_file))
    return sorted( MIDs)

def physiocap_list_MID( repertoire, MIDs, synthese="xx"):
    """Fonction qui liste les MID.
    En entrée la liste des MIDs avec leurs nom complet
    nom court, taille en ligne, centroide GPS, vitesse moyenne
    sont ajoutés à la synthse
    """
    resultats = []
    un_MIDs_court = ""
  
    for un_mid in MIDs: 
        texte_MID = ""
        if (os.path.isfile( un_mid)):
            fichier_pret = open(un_mid, "r")
            lignes = fichier_pret.readlines()
            if un_mid.find( repertoire) == 0:
                #print( "VERY GOOD MID :" + trouve[ len( root_base) + 1:])
                un_MIDs_court = un_mid[ len( repertoire) + 1:]
            gps_x = []
            gps_y = []
            vitesse = []
            for ligne in lignes:
                try:
                    champ = ligne.split( ",")
                    if len(champ) >= 2:
                        gps_x.append( float(champ[ 1]))
                        gps_y.append( float(champ[ 2]))
                    if len(champ) >= 8:
                        vitesse.append( float(champ[ 8]))
                except ValueError:
                    pass
            texte_MID = un_MIDs_court + ";" + lignes[0][0:19] + \
                ";" + lignes[-1][10:19]
            if ((len( gps_x) > 0) and (len( gps_y) > 0) ):
                texte_MID = texte_MID + ";" + str( len(gps_x))                  
                if (len( vitesse) > 0 ):
                    texte_MID = texte_MID + ";" + \
                        str(sum(vitesse)/len(vitesse))
                else:
                    texte_MID = texte_MID + ";"
                texte_MID = texte_MID + ";" + \
                    str(sum(gps_x)/len(gps_x))+ ";" +   \
                    str(sum(gps_y)/len(gps_y))

            resultats.append( texte_MID)
    
    # Mettre dans Synthese
    return resultats
    

