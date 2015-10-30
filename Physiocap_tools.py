# -*- coding: utf-8 -*-
"""
/***************************************************************************
 Physiocap_tools
                                 A QGIS plugin
 Physiocap plugin helps analysing raw data from Physiocap in Qgis
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
from PyQt4 import QtGui, uic  # for Form_class
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import *
from qgis.gui import *

# Imports system & os
import os.path
import sys, string
import platform
if platform.system() == 'Windows':
    import win32api

try :
    import csv
except ImportError:
    aText = "Erreur bloquante : module csv n'est pas accessible." 
    print( aText)
    QgsMessageLog.logMessage( aText, "Physiocap erreurs", QgsMessageLog.WARNING)
    
try :
    from osgeo import osr
except ImportError:
    aText = "Erreur bloquante : module GDAL osr n'est pas accessible." 
    print( aText)
    QgsMessageLog.logMessage( aText, "Physiocap erreurs", QgsMessageLog.WARNING)
    
try :
    ##    from matplotlib.figure import Figure
    ##    from matplotlib import axes
    import matplotlib.pyplot as plt
except ImportError:
    aText ="Erreur bloquante : module matplotlib.pyplot n'est pas accessible\n" 
    aText = aText + "Sous Fedora : installez python-matplotlib-qt4" 
    print( aText)
    QgsMessageLog.logMessage( aText, "Physiocap erreurs", QgsMessageLog.WARNING)
    
try :
    import numpy as np
except ImportError:
    aText ="Erreur bloquante : module numpy n'est pas accessible" 
    print( aText)
    QgsMessageLog.logMessage( aText, "Physiocap erreurs", QgsMessageLog.WARNING)

# VARIABLES GLOBALES
PHYSIOCAP_TRACE = "Yes"
NB_VIRGULES = 58

# MESSAGES & LOG
def physiocap_message_box( self, text, level ="warning", title="Physiocap",):
    """Send a message box by default Warning"""
    if level == "about":
        QMessageBox.about( self, title, text)
    elif level == "information":
        QMessageBox.information( self, title, text)
    elif level == "error":
        QMessageBox.error( self, title, text)
    else:
        QMessageBox.warning( self, title, text)

def physiocap_log( aText, level ="INFO"):
    """Send a text to the Physiocap log"""
    if PHYSIOCAP_TRACE == "Yes":
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

    # Todo 1.5 ? Rajouter la trace d'errerur au fichier ?

    return -1      

def physiocap_write_in_synthese( self, aText):
    """Write a text in the results list"""
    uText = unicode( aText, 'utf-8')
    self.textEditSynthese.insertPlainText( uText)   

def get_vector_layers( self ):
    """Create a list of vector """
    layerMap = QgsMapLayerRegistry.instance().mapLayers()
    layerList = []
    for name, layer in layerMap.iteritems():
        if layer.type() == QgsMapLayer.VectorLayer:
            layerList.append( layer.name() )
            
    return layerList
            
        
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
 
def is_int_number(s):
    try:
        int(s)
        return True
    except ValueError:
        return False
    
def physiocap_rename_existing( chemin):
    """ Retourne le nom qu'il est possible de creer
        si chemin existe deja, on creer un "chemin + (1)"
        si "chemin_projet + (1)" existe déjà, on crée un "chemin_projet + (2)" etc         
    """
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
            if is_int_number( un_num):
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
               
    return nouveau_chemin

def physiocap_rename_existing_file ( chemin):
    """ Retourne le nom de fichier qu'il est possible de creer
        si chemin existe deja, on creer un "chemin + (1)"
        si "chemin_projet + (1)" existe déjà, on crée un "chemin_projet + (2)" etc         
    """
    if ( os.path.exists( chemin)):
        nouveau_chemin = physiocap_rename_existing( chemin)
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
        nouveau_chemin = physiocap_rename_existing( chemin)
        return physiocap_rename_create_dir( nouveau_chemin) 
    else:
        try:
            os.mkdir( chemin)
        except:
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

# Partie Calcul non modifié
# Definition des fonctions de traitement
# Ces variables sont nommées en Francais par compatibilité avec la version physiocap_V8

def physiocap_csv_to_shapefile( csv_name, shape_name, prj_name, laProjection, 
    nom_fichier_synthese = "NO", details = "NO"):
    """ Creation de shape file à partir des données des CSV
    Si nom_fichier_synthese n'est pas "NO", on produit les moyennes dans le fichier 
    qui se nomme nom_fichier_synthese
    Selon la valeur de détails , on crée les 5 premiers ("NO") ou tous les attibuts ("YES")
    """
    #Préparation de la liste d'arguments
    x,y,nbsarmshp,diamshp,biomshp,dateshp,vitesseshp= [],[],[],[],[],[],[]
    nbsarmm2,nbsarcep,biommm2,biomgm2,biomgcep=[],[],[],[],[]
    #Lecture des data dans le csv et stockage dans une liste
    with open(csv_name, "rt") as csvfile:
        try:
            r = csv.reader(csvfile, delimiter=";")
        except NameError:
            uText = u"Erreur bloquante : module csv n'est pas accessible."
            physiocap_erreur( uText)
            QgsMessageLog.logMessage( uText, "Physiocap erreurs", QgsMessageLog.WARNING)
            return -1
        for i,row in enumerate(r):
            if i > 0: #skip header
                if ( laProjection == "L93"):
                    x.append(float(row[2]))
                    y.append(float(row[3]))
                if ( laProjection == "GPS"):
                    x.append(float(row[0]))
                    y.append(float(row[1]))
                nbsarmshp.append(float(row[4]))
                diamshp.append(float(row[5]))
                biomshp.append(float(row[6]))
                dateshp.append(str(row[7]))
                vitesseshp.append(float(row[8]))
                if details == "YES":
                    # Niveau de detail demandé
                    # assert sur len row
                    if len(row) != 14:
                        return physiocap_error( u"Le nombre de colonnes :" +
                                str( len(row)) + 
                                u" du cvs ne permet pas le calcul détaillé")
                    nbsarmm2.append(float(row[9]))
                    nbsarcep.append(float(row[10]))
                    biommm2.append(float(row[11]))
                    biomgm2.append(float(row[12]))
                    biomgcep.append(float(row[13]))
                
    # Todo: V1.5 format pour Crs
    #un_crs = QgsCoordinateReferenceSystem.createFromUserInput(u"EPSG:2154")
    # Prepare les attributs
    les_champs = QgsFields()
    # V1.0 Ajout du GID
    les_champs.append( QgsField("GID", QVariant.Int, "integer", 10))
    les_champs.append( QgsField("DATE", QVariant.String, "string", 25))
    les_champs.append( QgsField("VITESSE", QVariant.Double, "double", 10,2))
    les_champs.append(QgsField("NBSARM",  QVariant.Double, "double", 10,2))
    les_champs.append(QgsField("DIAM",  QVariant.Double, "double", 10,2))
    les_champs.append(QgsField("BIOM", QVariant.Double,"double", 10,2)) 
    if details == "YES":
        # Niveau de detail demandé
        les_champs.append(QgsField("NBSARMM2", QVariant.Double,"double", 10,2))
        les_champs.append(QgsField("NBSARCEP", QVariant.Double,"double", 10,2))
        les_champs.append(QgsField("BIOMM2", QVariant.Double,"double", 10,2))
        les_champs.append(QgsField("BIOMGM2", QVariant.Double,"double", 10,2))
        les_champs.append(QgsField("BIOMGCEP", QVariant.Double,"double", 10,2))
    # Creation du Shape
    writer = QgsVectorFileWriter( shape_name, "utf-8", les_champs, 
        QGis.WKBPoint, None , "ESRI Shapefile")

    #Ecriture du shp
    for j,k in enumerate(x):
        feat = QgsFeature()
        feat.setGeometry( QgsGeometry.fromPoint(QgsPoint(k,y[j]))) #écrit la géométrie
        if details == "YES":
            # Ecrit tous les attributs
           feat.setAttributes( [ j, dateshp[j], vitesseshp[j], nbsarmshp[j], 
                                diamshp[j], biomshp[j],
                                nbsarmm2[j], nbsarcep[j], biommm2[j], 
                                biomgm2[j], biomgcep[j]]) 
        else:
            # Ecrit les 5 premiers attributs
            feat.setAttributes( [ j, dateshp[j], vitesseshp[j], nbsarmshp[j], 
                                diamshp[j], biomshp[j]])
        # Ecrit le feature
        writer.addFeature( feat)

    # Create the PRJ file
    prj = open(prj_name, "w")
    epsg = 'inconnu'
    if ( laProjection == "L93"):
        # Todo: V1.x ? Faire un fichier de metadata 
        epsg = 'PROJCS["RGF93_Lambert_93",GEOGCS["GCS_RGF93",DATUM["D_RGF_1993", \
        SPHEROID["GRS_1980",6378137,298.257222101]],PRIMEM["Greenwich",0], \
        UNIT["Degree",0.017453292519943295]],PROJECTION["Lambert_Conformal_Conic"], \
        PARAMETER["standard_parallel_1",49],PARAMETER["standard_parallel_2",44], \
        PARAMETER["latitude_of_origin",46.5],PARAMETER["central_meridian",3], \
        PARAMETER["false_easting",700000],PARAMETER["false_northing",6600000], \
        UNIT["Meter",1]]'
    if ( laProjection == "GPS"):
        #  prj pour GPS 4326
        epsg = 'GEOGCS["GCS_WGS_1984",DATUM["D_WGS_1984", \
        SPHEROID["WGS_1984",6378137,298.257223563]],PRIMEM["Greenwich",0], \
        UNIT["Degree",0.017453292519943295]]'
        
    prj.write(epsg)
    prj.close()    
    
    # Création de la synthese
    if nom_fichier_synthese != "NO":
        # ASSERT Le fichier de synthese existe
        if not os.path.isfile( nom_fichier_synthese):
            uMsg =u"Le fichier de synthese " + nom_fichier_synthese + "n'existe pas"
            physiocap_log( uMsg)
            return physiocap_error( uMsg)
        
        # Ecriture des resulats
        fichier_synthese = open(nom_fichier_synthese, "a")
        try:
            fichier_synthese.write("\n\nSTATISTIQUES\n")
            fichier_synthese.write("Vitesse moyenne d'avancement  \n	mean : %0.1f km/h\n" %np.mean(vitesseshp))
            fichier_synthese.write("Section moyenne \n	mean : %0.2f mm	std : %0.1f\n" %(np.mean(diamshp), np.std(diamshp)))
            fichier_synthese.write("Nombre de sarments au m \n	mean : %0.2f	std : %0.1f\n" %(np.mean(nbsarmshp), np.std(nbsarmshp)))
            fichier_synthese.write("Biomasse en mm²/m linéaire \n	mean : %0.1f	std : %0.1f\n" %(np.mean(biomshp), np.std(biomshp)))
            if details == "YES":
                fichier_synthese.write("Nombre de sarments au m² \n	mean : %0.1f	std : %0.1f\n" %(np.mean(nbsarmm2), np.std(nbsarmm2)))
                fichier_synthese.write("Nombre de sarments par cep \n	mean : %0.1f	std : %0.1f\n" %(np.mean(nbsarcep), np.std(nbsarcep)))
                fichier_synthese.write("Biommasse en mm²/m² \n	mean : %0.1f	std : %0.1f\n" %(np.mean(biommm2), np.std(biommm2)))
                fichier_synthese.write("Biomasse en gramme/m² \n	mean : %0.1f	std : %0.1f\n" %(np.mean(biomgm2), np.std(biomgm2)))
                fichier_synthese.write("Biomasse en gramme/cep \n	mean : %0.1f	std : %0.1f\n" %(np.mean(biomgcep), np.std(biomgcep))) 
        except:
            msg = "%s\n" %("Erreur bloquante durant les calculs de moyennes")
            physiocap_error( msg )
            return -1
                    
        fichier_synthese.close()
    return 0


# Fonction pour vérifier le fichier csv    
def physiocap_chercher_MID( repertoire, recursif, exclusion="fic_sources"):
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

def physiocap_lister_MID( repertoire, MIDs, synthese="xx"):
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
    
    
# Fonction pour vérifier le fichier csv    
def physiocap_assert_csv(src, err):
    """Fonction d'assert. 
    Vérifie si le csv est au bon format: 
    58 virgules
    une date en première colonne
    des float ensuite
    """
    numero_ligne = 0     
    nombre_erreurs = 0     
    while True :
        ligne = src.readline() # lit les lignes 1 à 1
        if not ligne: break 
        # Vérifier si ligne OK
        numero_ligne = numero_ligne + 1
        #physiocap_log( u"Assert CVS ligne lue %d" % (numero_ligne))

        result = ligne.split(",") # split en fonction des virgules        
        # Vérifier si le champ date a bien deux - et 2 deux points
        tirets = result[ 0].count("-") 
        deux_points = result[ 0].count(":") 
        #physiocap_log( u"Champ date contient %d tirets et %d deux points" % (tirets, deux_points))
        if ((tirets != 2) or (deux_points != 2)):
            aMsg = "La ligne numéro %d ne commence pas par une date" % (numero_ligne)
            uMsg = unicode(aMsg, 'utf-8')
            nombre_erreurs = nombre_erreurs + 1
            if nombre_erreurs < 10:
                physiocap_error( uMsg )
            err.write( aMsg + '\n' ) # on écrit la ligne dans le fichier ERREUR.csv
            
            continue # on a tracé erreur et on saute la ligne         

        # Vérifier si tous les champs sont des float        
        i = 0
        for x in result[1:58]:
            i = i+1
            try:
                y = float( x)
                # physiocap_log( u"%d Champ  %s est de type %s" % (i, x, type( y)))
            except:
                aMsg = "La ligne numéro %d a des colonnes mal formatées (x.zzz attendu)" % (numero_ligne)
                uMsg = unicode(aMsg, 'utf-8')
                nombre_erreurs = nombre_erreurs + 1
                if nombre_erreurs < 10:
                    physiocap_error( uMsg )
                    err.write( aMsg + "\n") # on écrit la ligne dans le fichier ERREUR.csv
                break # on a tracé une erreur et on saute la ligne            

        comptage = ligne.count(",") # compte le nombre de virgules
        if comptage > NB_VIRGULES:
            # Assert Trouver les lignes de données invalides ( sans 58 virgules ... etc)
            aMsg = "La ligne numéro %d n'a pas %s virgules" % (numero_ligne, NB_VIRGULES)
            uMsg = unicode(aMsg, 'utf-8')
            nombre_erreurs = nombre_erreurs + 1
            if nombre_erreurs < 10:
                physiocap_error( uMsg )
            err.write( aMsg + '\n') # on écrit la ligne dans le fichier ERREUR.csv
            continue # on a tracé erreur et on saute la ligne


    # Au bilan
    if (numero_ligne != 0):
        physiocap_log( u"Assert CVS a lu %d lignes et trouvé %d erreurs" % (numero_ligne, nombre_erreurs ))
        pourcentage_erreurs = float( nombre_erreurs * 100 / numero_ligne)
        return pourcentage_erreurs
    else:
        return 0

##            try:
##                raise physiocap_exception_err_csv( pourcentage_erreurs)
##            except:
##                raise
            
# Fonction pour créer les fichiers histogrammes    
def physiocap_fichier_histo(src, histo_diametre, histo_nbsarment, err):
    """Fonction de traitement. Creation des fichiers pour réaliser les histogrammes
    Lit et traite ligne par ligne le fichier source (src).
    Les résultats est écrit au fur et à mesure dans histo_diametre ou histo_nbsarment
    """
   
    numero_ligne = 0     
    while True :
        ligne = src.readline() # lit les lignes 1 à 1
        if not ligne: break 
        # Vérifier si ligne OK
        numero_ligne = numero_ligne + 1
        comptage = ligne.count(",") # compte le nombre de virgules
        if comptage != NB_VIRGULES:
            # Assert ligne sans 58 virgules 
            continue # on saute la ligne
        
        result = ligne.split(",") # split en fonction des virgules
        # Intergrer ici les autres cas d'erreurs
                
        try : # accompli cette fonction si pas d'erreur sinon except
            XY = [float(x) for x in result[1:9]]   # on extrait les XY et on les transforme en float  > Données GPS 
            diams = [float(x) for x in result[9:NB_VIRGULES+1]] # on extrait les diams et on les transforme en float 
            diamsF = [i for i in diams if i > 2 and i < 28 ] # on filtre les diams > diamsF correspond aux diams filtrés entre 2 et 28       
            if comptage==NB_VIRGULES and len(diamsF)>0 : # si le nombre de diamètre après filtrage != 0 alors mesures
                if XY[7] != 0:
                    nbsarm = len(diamsF)/(XY[7]*1000/3600) #8eme donnée du GPS est la vitesse. Dernier terme : distance entre les sarments
                else:
                    nbsarm = 0
                histo_nbsarment.write("%f%s" %(nbsarm,";"))                
                for n in range(len(diamsF)) :
                    histo_diametre.write("%f%s" %(diamsF[n],";"))
        except : # accompli cette fonction si erreur
            msg = "%s%s\n" %("Erreur histo",ligne)
            physiocap_error( msg )
            err.write( str(msg) ) # on écrit la ligne dans le fichier ERREUR.csv
            pass # on mange l'exception



def physiocap_histo(src, name, min=0, max =28, labelx = "Lab X", labely = "Lab Y", titre = "Titre", bins = 100):
    #"""Fonction de traitement.
    #Lit et traite ligne par ligne le fichier source (src).
    #Le résultat est écrit au fur et à mesure dans le
    #fichier destination (dst). 
    #"""
    ligne2 = src.readline()
    histo = ligne2.split(";") # split en fonction des virgules
    # Assert len(histo)
    XY = [float(x) for x in histo[0:-1]]   # on extrait les XY et on les transforme en float  
    valeur = len(XY)
    #physiocap_log( u"Histo min %d et nombre de valeurs : %d " % (min, valeur))
    classes = np.linspace(min, max, max+1)
    plt.hist(XY,bins=classes,normed=1, facecolor='green', alpha=0.75) 
    plt.xlabel(labelx)
    plt.ylabel(labely)
    plt.title(titre)
    plt.xlim((min, max))
    plt.grid(True)
    plt.savefig(name)
    plt.show( block = 'false')
    plt.close()
    

# Fonction de filtrage et traitement des données
def physiocap_filtrer(src, csv_sans_0, csv_avec_0, diametre_filtre, 
    nom_fichier_synthese, err, 
    mindiam, maxdiam, max_sarments_metre, details,
    eer, eec, d, hv):
    """Fonction de traitement.
    Filtre ligne par ligne les données de source (src) pour les valeurs 
    comprises entre mindiam et maxdiam et verifie si on n'a pas atteint le max_sarments_metre.
    Le résultat est écrit au fur et à mesure dans les fichiers 
    csv_sans_0 et csv_avec_0 mais aussi diametre_filtre 
    La synthese est allongé
    "details" pilote l'ecriture de 5 parametres ou de la totalité des 10 parametres 
    """
    
    #S'il n'existe pas de données parcellaire, le script travaille avec les données brutes
    if details == "NO" :
        csv_sans_0.write("%s\n" % ("X ; Y ; XL93 ; YL93 ; NBSARM ; DIAM ; BIOM ; Date ; Vitesse")) # ecriture de l'entête
        csv_avec_0.write("%s\n" % ("X ; Y ; XL93 ; YL93 ; NBSARM ; DIAM ; BIOM ; Date ; Vitesse")) # ecriture de l'entête
    #S'il existe des données parcellaire, le script travaille avec les données brutes et les données calculées
    else:
        # Assert details == "YES"
        if details != "YES" : 
            return physiocap_error(u"Problème majeur dans le choix du détail du parcellaire")
        csv_sans_0.write("%s\n" % ("X ; Y ; XL93 ; YL93 ; NBSARM ; DIAM ; BIOM ; Date ; Vitesse ; \
            NBSARMM2 ; NBSARCEP ; BIOMMM2 ; BIOMGM2 ; BIOMGCEP ")) # ecriture de l'entête
        csv_avec_0.write("%s\n" % ("X ; Y ; XL93 ; YL93 ; NBSARM ; DIAM ; BIOM ; Date ; Vitesse ; \
            NBSARMM2 ; NBSARCEP ; BIOMMM2 ; BIOMGM2 ; BIOMGCEP ")) # ecriture de l'entête

    nombre_ligne = 0
    while True :
        ligne = src.readline()
        nombre_ligne = nombre_ligne + 1
        if not ligne: break 
        comptage = ligne.count(",") # compte le nombre de virgules
        result = ligne.split(",") # split en fonction des virgules
        #physiocap_log("Comptage de virgules : " + str(comptage))

        try : # accompli cette fonction si pas d'erreur sinon except
            XY = [float(x) for x in result[1:9]]   # on extrait les XY et on les transforme en float  
            # On transforme les WGS84 en L93
            WGS84 = osr.SpatialReference()
            WGS84.ImportFromEPSG(4326)
            LAMB93 = osr.SpatialReference()
            LAMB93.ImportFromEPSG(2154)
            transformation1 = osr.CoordinateTransformation(WGS84,LAMB93) 
            L93 = transformation1.TransformPoint(XY[0],XY[1])
            diams = [float(x) for x in result[9:NB_VIRGULES+1]] # on extrait les diams et on les transforme en float 
            diamsF = [i for i in diams if i > mindiam and i < maxdiam ] # on filtre les diams avec les paramètres entrés ci-dessus
            if details == "NO" :
                if len(diamsF)==0: # si le nombre de diamètre après filtrage = 0 alors pas de mesures
                    nbsarm = 0
                    diam =0
                    biom = 0
                    csv_avec_0.write("%.7f%s%.7f%s%.7f%s%.7f%s%i%s%i%s%i%s%s%s%0.2f\n" %(XY[0],";",XY[1],";",L93[0],";",L93[1],";",nbsarm,";",diam ,";",biom,";",result[0],";",XY[7]))  # on écrit la ligne dans le fichier OUT0.csv  
                elif comptage==NB_VIRGULES and len(diamsF)>0 : # si le nombre de diamètre après filtrage != 0 alors mesures
                    if XY[7] != 0:
                        nbsarm = len(diamsF)/(XY[7]*1000/3600)
                    else:
                        nbsarm = 0
                    if nbsarm > 1 and nbsarm < max_sarments_metre :                   
                        diam =sum(diamsF)/len(diamsF)
                        biom=3.1416*(diam/2)*(diam/2)*nbsarm
                        csv_avec_0.write("%.7f%s%.7f%s%.7f%s%.7f%s%0.2f%s%.2f%s%.2f%s%s%s%0.2f\n" %(XY[0],";",XY[1],";",L93[0],";",L93[1],";",nbsarm,";",diam,";",biom,";",result[0],";",XY[7])) # on écrit la ligne dans le fichier OUT0.csv 
                        csv_sans_0.write("%.7f%s%.7f%s%.7f%s%.7f%s%0.2f%s%.2f%s%.2f%s%s%s%0.2f\n" %(XY[0],";",XY[1],";",L93[0],";",L93[1],";",nbsarm,";",diam,";",biom,";",result[0],";",XY[7])) # on écrit la ligne dans le fichier OUT.csv
                        for n in range(len(diamsF)) :
                            diametre_filtre.write("%f%s" %(diamsF[n],";"))
            elif details == "YES" :
                if len(diamsF)==0: # si le nombre de diamètre après filtrage = 0 alors pas de mesures
                    nbsarm = 0
                    diam =0
                    biom = 0
                    nbsarmm2 = 0
                    nbsarcep = 0
                    biommm2 = 0
                    biomgm2 = 0
                    biomgcep = 0
                    csv_avec_0.write("%.7f%s%.7f%s%.7f%s%.7f%s%i%s%i%s%i%s%s%s%0.2f%s%i%s%i%s%i%s%i%s%i\n" %(XY[0],";",XY[1],";",L93[0],";",L93[1],";",nbsarm,";",diam ,";",biom,";",result[0],";",XY[7],";",nbsarmm2,";",nbsarcep,";",biommm2,";",biomgm2,";",biomgcep))  # on écrit la ligne dans le fichier OUT0.csv  
                elif comptage==NB_VIRGULES and len(diamsF)>0 : # si le nombre de diamètre après filtrage != 0 alors mesures
                    if XY[7] != 0:
                        nbsarm = len(diamsF)/(XY[7]*1000/3600)
                    else:
                        nbsarm = 0
                    if nbsarm > 1 and nbsarm < max_sarments_metre :                   
                        diam =sum(diamsF)/len(diamsF)
                        biom=3.1416*(diam/2)*(diam/2)*nbsarm
                        nbsarmm2 = nbsarm/eer*100
                        nbsarcep = nbsarm*eec/100
                        biommm2 = biom/eer*100
                        biomgm2 = biom*d*hv/eer
                        biomgcep = biom*d*hv*eec/100/100
                        csv_avec_0.write("%.7f%s%.7f%s%.7f%s%.7f%s%.2f%s%.2f%s%.2f%s%s%s%.2f%s%.2f%s%.2f%s%.2f%s%.2f%s%.2f\n" %(XY[0],";",XY[1],";",L93[0],";",L93[1],";",nbsarm,";",diam ,";",biom,";",result[0],";",XY[7],";",nbsarmm2,";",nbsarcep,";",biommm2,";",biomgm2,";",biomgcep)) # on écrit la ligne dans le fichier OUT0.csv 
                        csv_sans_0.write("%.7f%s%.7f%s%.7f%s%.7f%s%.2f%s%.2f%s%.2f%s%s%s%.2f%s%.2f%s%.2f%s%.2f%s%.2f%s%.2f\n" %(XY[0],";",XY[1],";",L93[0],";",L93[1],";",nbsarm,";",diam ,";",biom,";",result[0],";",XY[7],";",nbsarmm2,";",nbsarcep,";",biommm2,";",biomgm2,";",biomgcep)) # on écrit la ligne dans le fichier OUT.csv
                        for n in range(len(diamsF)) :
                            diametre_filtre.write("%f%s" %(diamsF[n],";"))
        except : # accompli cette fonction si erreur
            aMsg = "Erreur bloquante durant filtrage : pour la ligne numéro %d" %( nombre_ligne)
            uMsg = unicode(aMsg, 'utf-8')
            physiocap_error( uMsg )
            err.write( aMsg) # on écrit la ligne dans le fichier ERREUR.csv
            return -1
    physiocap_log( u"Fin filtrage OK des "+ str(nombre_ligne - 1) + " lignes.")
    return 0
 

# Example pour faire une jointure patiale sous Py Qgis
##lyrs = iface.legendInterface().layers()
##lyrPoly = lyrs[1] #polygon layer
##lyrPnts = lyrs[0] #point layer
##
##featsPoly = lyrPoly.getFeatures() #get all features of poly layer
###featsPoly = lyrPoly.selectedFeatures() #for testing, use selected features only
##
##for featPoly in featsPoly: #iterate poly features
##    zipPoly = featPoly["POSTCODE"] #get attribute of poly layer
##    geomPoly = featPoly.geometry() #get geometry of poly layer
##    #performance boost: get point features by poly bounding box first
##    featsPnt = lyrPnts.getFeatures(QgsFeatureRequest().setFilterRect(geomPoly.boundingBox()))
##    for featPnt in featsPnt:
##        #iterate preselected point features and perform exact check with current polygon
##        if featPnt.geometry().within(geomPoly):
##            print '"' + zipPoly + '"' + ';' + featPnt["Zipcode"]