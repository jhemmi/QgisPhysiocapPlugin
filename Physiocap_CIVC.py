# -*- coding: utf-8 -*-
"""
/***************************************************************************
 Physiocap_CIVC
                                 A QGIS plugin
 Physiocap plugin helps analyse raw data from Physiocap in Qgis and 
 creates a synthesis of Physiocap measures' campaign
 Physiocap plugin permet l'analyse les données brutes de Physiocap dans Qgis et
 crée une synthese d'une campagne de mesures Physiocap
 
 Le module CIVC contient le filtre de données, de creation des csv 
 et shapfile, de creation des histogrammes
 
 Partie Calcul non modifié par rapport à physiocap_V8
 Les variables et fonctions sont nommées en Francais par compatibilité avec 
 la version physiocap_V8
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
        physiocap_log, physiocap_error, physiocap_write_in_synthese
        
##        physiocap_quel_uriname, physiocap_tester_uri, \
##        physiocap_detruit_table_uri, physiocap_existe_table_uri, \
##        physiocap_get_uri_by_layer 
from Physiocap_var_exception import *

from PyQt4.QtCore import QSettings, Qt, QVariant
from qgis.core import QGis, QgsCoordinateReferenceSystem, QgsFields, QgsField, \
        QgsFeature, QgsGeometry, QgsPoint, QgsVectorFileWriter, QgsMessageLog

import sys, string
if platform.system() == 'Windows':
    import win32api

try :
    import csv
except ImportError:
    aText = "Erreur bloquante : module csv n'est pas accessible." 
    QgsMessageLog.logMessage( aText, u"\u03D5 Erreurs", QgsMessageLog.WARNING)

try :
    from osgeo import osr
except ImportError:
    aText = "Erreur bloquante : module GDAL osr n'est pas accessible." 
    QgsMessageLog.logMessage( aText, u"\u03D5 Erreurs", QgsMessageLog.WARNING)
    
try :
    ##    from matplotlib.figure import Figure
    ##    from matplotlib import axes
    import matplotlib.pyplot as plt
except ImportError:
    aText ="Erreur bloquante : module matplotlib.pyplot n'est pas accessible\n" 
    aText = aText + "Sous Fedora : installez python-matplotlib-qt4" 
    QgsMessageLog.logMessage( aText, u"\u03D5 Erreurs", QgsMessageLog.WARNING)
    
try :
    import numpy as np
except ImportError:
    aText ="Erreur bloquante : module numpy n'est pas accessible" 
    QgsMessageLog.logMessage( aText, u"\u03D5 Erreurs", QgsMessageLog.WARNING)

def physiocap_csv_vers_shapefile( self, progress_barre, csv_name, shape_name, prj_name, laProjection, 
    nom_fichier_synthese = "NO", details = "NO"):
    """ Creation de shape file à partir des données des CSV
    Si nom_fichier_synthese n'est pas "NO", on produit les moyennes dans le fichier 
    qui se nomme nom_fichier_synthese
    Selon la valeur de détails , on crée les 5 premiers ("NO") ou tous les attibuts ("YES")
    """
    crs = None
    #Préparation de la liste d'arguments
    x,y,nbsarmshp,diamshp,biomshp,dateshp,vitesseshp= [],[],[],[],[],[],[]
    nbsarmm2,nbsarcep,biommm2,biomgm2,biomgcep=[],[],[],[],[]
    
    un_fic = open( csv_name, "r")
    lignes = un_fic.readlines()
    nombre_ligne = len( lignes)
    un_fic.close()
    progress_step = int( nombre_ligne / 19)
    barre = 1
    
    #Lecture des data dans le csv et stockage dans une liste
    with open(csv_name, "rt") as csvfile:
        try:
            r = csv.reader(csvfile, delimiter=";")
        except NameError:
            uText = u"Erreur bloquante : module csv n'est pas accessible."
            physiocap_error( self, uText)
            return -1

        for jj, row in enumerate( r):
            #skip header
            if jj > 0: 
                # ON fait avancer la barre de progression de 19 points
                if ( jj > progress_step * barre):
                    barre = barre + 1
                    progress_barre = progress_barre + 1
                    self.progressBar.setValue( progress_barre)
                    
                crs = None
                if ( laProjection == "L93"):
                    x.append(float(row[2]))
                    y.append(float(row[3]))
                    crs = QgsCoordinateReferenceSystem(EPSG_NUMBER_L93, 
                        QgsCoordinateReferenceSystem.PostgisCrsId)
                if ( laProjection == "GPS"):
                    x.append(float(row[0]))
                    y.append(float(row[1]))
                    crs = QgsCoordinateReferenceSystem(EPSG_NUMBER_GPS, 
                        QgsCoordinateReferenceSystem.PostgisCrsId)
                nbsarmshp.append(float(row[4]))
                diamshp.append(float(row[5]))
                biomshp.append(float(row[6]))
                dateshp.append(str(row[7]))
                vitesseshp.append(float(row[8]))
                if details == "YES":
                    # Niveau de detail demandé
                    # assert sur len row
                    if len(row) != 14:
                        return physiocap_error( self, u"Le nombre de colonnes :" +
                                str( len(row)) + 
                                u" du cvs ne permet pas le calcul détaillé")
                    nbsarmm2.append(float(row[9]))
                    nbsarcep.append(float(row[10]))
                    biommm2.append(float(row[11]))
                    biomgm2.append(float(row[12]))
                    biomgcep.append(float(row[13]))
                
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
            QGis.WKBPoint, crs , "ESRI Shapefile")
            
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

    # Flush vector
    del writer
    
    # Cas PG
##    if (self.fieldComboFormats.currentText() == POSTGRES_NOM ):
##        # Todo ; fonction physiocap_creer_PG_par_copie_vecteur( uri_nom, shape_modele)
##        # Vérifier si une connexion Physiocap existe
##        uri_nom = physiocap_quel_uriname( self)
##        uri_modele = physiocap_get_uri_by_layer( self, uri_nom )
##        if uri_modele != None:
##            uri_connect, uri_deb, uri_srid, uri_fin = physiocap_tester_uri( self, uri_modele)
##            if uri_deb != None:
##                nom_court_shp = os.path.basename( shape_name)
##                #laTable = "'public.\"" + nom_court_shp[ :-4] + "\"'"
##                laTable = "'\"" + nom_court_shp[ :-4] + "\"'"
##                reponse = physiocap_existe_table_uri( self, uri_deb, laTable)
##                if reponse != None:
##                    if reponse == True:
##                        laTable = "\"" + nom_court_shp[ :-4] + "\""
##                        #physiocap_log( u"Table existe déjà : " + str( laTable))
##                        # Cette table existe déjà = > drop 
##                        reponse_drop = physiocap_detruit_table_uri( self, uri_deb, laTable)
##                        if reponse_drop == None:
##                            aText = u"Problème lors de la destruction de la table : " + str( laTable)
##                            physiocap_log( aText)
##                            physiocap_error( self, aText)  
##                            # Todo : V3 gérer par exception physiocap_exception_pg
##                            return physiocap_message_box( self, 
##                                self.tr( aText),
##                                "warning")                   
##                    # Creer la table
##                    laTable = nom_court_shp[ :-4] 
##                    vector = QgsVectorLayer( shape_name, "INUTILE", 'ogr')
##                    uri = uri_deb + uri_srid + \
##                        " key=gid type=POINTS table=" + laTable + uri_fin
## #       uri = "dbname='testpostgis' host=localhost port=5432" + \
## #             " user='postgres' password='postgres'" + \
## #              " key=gid type=POINTS table=" + nom_court_shp[ :-4] + " (geom) sql="
##                    error = QgsVectorLayerImport.importLayer( vector, uri, POSTGRES_NOM, crs, False, False)
##                    if error[0] != 0:
##                        physiocap_error( self, u"Problème Postgres : " + str(error[0]) + " => " + str(error[1]))
##                        #iface.messageBar().pushMessage(u'Phyqiocap Error', error[1], QgsMessageBar.CRITICAL, 5)    
## #                    else:
## #                        # Sans erreur on détruit le shape file
## #                        if os.path.isfile( shape_name):
## #                            os.remove( shape_name)
##                else:
##                    aText = u"Vérification problématique pour la table : " + \
##                        str( laTable) + \
##                        u". On continue avec des shapefiles"
##                    physiocap_log( aText)
##                    piocap_error( aText)
##                    # Remettre le choix vers ESRI shape file
##                    self.fieldComboFormats.setCurrentIndex( 0)   
##            else:
##                aText = u"Pas de connection possible à Postgres : " + \
##                    str( uri_nom) + \
##                    u". On continue avec des shapefiles"
##                physiocap_log( aText)
##                physiocap_error( self, aText)
##                # Remettre le choix vers ESRI shape file
##                self.fieldComboFormats.setCurrentIndex( 0)   
##                
##        else:
##            aText = u"Pas de connecteur vers Postgres : " + \
##                        str( uri_nom) + \
##                        u". On continue avec des shapefiles"
##            physiocap_log( aText)
##            physiocap_error( self, aText)
##            # Remettre le choix vers ESRI shape file
##            self.fieldComboFormats.setCurrentIndex( 0)   
##    else:
    # Create the PRJ file
    prj = open(prj_name, "w")
    epsg = 'inconnu'
    if ( laProjection == PROJECTION_L93):
        # Todo: V3 ? Faire aussi un fichier de metadata 
        epsg = EPSG_TEXT_L93
    if ( laProjection == PROJECTION_GPS):
        #  prj pour GPS 4326
        epsg = EPSG_TEXT_GPS
        
    prj.write(epsg)
    prj.close()    
        
    # Création de la synthese
    if nom_fichier_synthese != "NO":
        # ASSERT Le fichier de synthese existe
        if not os.path.isfile( nom_fichier_synthese):
            uMsg =u"Le fichier de synthese " + nom_fichier_synthese + "n'existe pas"
            physiocap_log( uMsg)
            return physiocap_error( self, uMsg)
        
        # Ecriture des resulats
        fichier_synthese = open(nom_fichier_synthese, "a")
        try:
            fichier_synthese.write("\n\nSTATISTIQUES\n")
            fichier_synthese.write("Vitesse moyenne d'avancement  \n	mean : %0.1f km/h\n" %np.mean(vitesseshp))
            fichier_synthese.write("Section moyenne \n	mean : %0.2f mm\t std : %0.1f\n" %(np.mean(diamshp), np.std(diamshp)))
            fichier_synthese.write("Nombre de sarments au m \n	mean : %0.2f  \t std : %0.1f\n" %(np.mean(nbsarmshp), np.std(nbsarmshp)))
            fichier_synthese.write("Biomasse en mm²/m linéaire \n	mean : %0.1f\t std : %0.1f\n" %(np.mean(biomshp), np.std(biomshp)))
            if details == "YES":
                fichier_synthese.write("Nombre de sarments au m² \n	 mean : %0.1f  \t std : %0.1f\n" %(np.mean(nbsarmm2), np.std(nbsarmm2)))
                fichier_synthese.write("Nombre de sarments par cep \n	mean : %0.1f \t\t std : %0.1f\n" %(np.mean(nbsarcep), np.std(nbsarcep)))
                fichier_synthese.write("Biomasse en mm²/m² \n	mean : %0.1f\t std : %0.1f\n" %(np.mean(biommm2), np.std(biommm2)))
                fichier_synthese.write("Biomasse en gramme/m² \n	mean : %0.1f\t std : %0.1f\n" %(np.mean(biomgm2), np.std(biomgm2)))
                fichier_synthese.write("Biomasse en gramme/cep \n	mean : %0.1f\t std : %0.1f\n" %(np.mean(biomgcep), np.std(biomgcep))) 
        except:
            msg = "Erreur bloquante durant les calculs de moyennes\n"
            physiocap_error( self, msg )
            return -1
                    
        fichier_synthese.close()
    return 0
    
# Fonction pour vérifier le fichier csv    
def physiocap_assert_csv(self, src, err):
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
                physiocap_error( self, uMsg )
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
                    physiocap_error( self, uMsg )
                    err.write( aMsg + "\n") # on écrit la ligne dans le fichier ERREUR.csv
                break # on a tracé une erreur et on saute la ligne            

        comptage = ligne.count(",") # compte le nombre de virgules
        if comptage > NB_VIRGULES:
            # Assert Trouver les lignes de données invalides ( sans 58 virgules ... etc)
            aMsg = "La ligne numéro %d n'a pas %s virgules" % (numero_ligne, NB_VIRGULES)
            uMsg = unicode(aMsg, 'utf-8')
            nombre_erreurs = nombre_erreurs + 1
            if nombre_erreurs < 10:
                physiocap_error( self, uMsg )
            err.write( aMsg + '\n') # on écrit la ligne dans le fichier ERREUR.csv
            continue # on a tracé erreur et on saute la ligne


    # Au bilan
    if (numero_ligne != 0):
        #physiocap_log( u"Assert CVS a lu %d lignes et trouvé %d erreurs" % (numero_ligne, nombre_erreurs ))
        pourcentage_erreurs = float( nombre_erreurs * 100 / numero_ligne)
        return pourcentage_erreurs
    else:
        return 0

##            try:
##                raise physiocap_exception_err_csv( pourcentage_erreurs)
##            except:
##                raise
            
# Fonction pour créer les fichiers histogrammes    
def physiocap_fichier_histo( self, src, histo_diametre, histo_nbsarment, err):
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
            physiocap_error( self, msg )
            err.write( str( msg) ) # on écrit la ligne dans le fichier ERREUR.csv
            pass # on mange l'exception



def physiocap_tracer_histo(src, name, min=0, max =28, labelx = "Lab X", labely = "Lab Y", titre = "Titre", bins = 100):
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
def physiocap_filtrer(self, src, csv_sans_0, csv_avec_0, diametre_filtre, 
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
            return physiocap_error( self, self.trUtf8("Problème majeur dans le choix du détail du parcellaire"))
        csv_sans_0.write("%s\n" % ("X ; Y ; XL93 ; YL93 ; NBSARM ; DIAM ; BIOM ; Date ; Vitesse ; \
            NBSARMM2 ; NBSARCEP ; BIOMMM2 ; BIOMGM2 ; BIOMGCEP ")) # ecriture de l'entête
        csv_avec_0.write("%s\n" % ("X ; Y ; XL93 ; YL93 ; NBSARM ; DIAM ; BIOM ; Date ; Vitesse ; \
            NBSARMM2 ; NBSARCEP ; BIOMMM2 ; BIOMGM2 ; BIOMGCEP ")) # ecriture de l'entête

    nombre_ligne = 0
    # Pour progress bar entre 15 et 40
    lignes = src.readlines()
    max_lignes = len(lignes)
    progress_step = int( max_lignes / 25)
    #physiocap_log("Bar step: " + str( progress_step))
    progress_bar = 15
    barre = 1
    for ligne in lignes :
        nombre_ligne = nombre_ligne + 1
        if not ligne: break 
        
        # Progress BAR de 15 à 40 %
        if ( nombre_ligne > barre * progress_step):
            progress_bar = progress_bar + 1
            barre = barre + 1
            self.progressBar.setValue( progress_bar)  
                
        comptage = ligne.count(",") # compte le nombre de virgules
        result = ligne.split(",") # split en fonction des virgules

        try : # accompli cette fonction si pas d'erreur sinon except
            XY = [float(x) for x in result[1:9]]   # on extrait les XY et on les transforme en float  
            # On transforme les WGS84 en L93
            WGS84 = osr.SpatialReference()
            WGS84.ImportFromEPSG( EPSG_NUMBER_GPS)
            LAMB93 = osr.SpatialReference()
            LAMB93.ImportFromEPSG( EPSG_NUMBER_L93)
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
            physiocap_error( self, uMsg )
            err.write( aMsg) # on écrit la ligne dans le fichier ERREUR.csv
            return -1
    #physiocap_log( u"Fin filtrage OK des "+ str(nombre_ligne - 1) + " lignes.")
    return 0


