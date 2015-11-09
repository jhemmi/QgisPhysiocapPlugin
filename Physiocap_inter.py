# -*- coding: utf-8 -*-
"""
/***************************************************************************
 PhysiocapInter
                                 A QGIS plugin
 Physiocap plugin helps analyse raw data from Physiocap in Qgis and 
 creates a synthesis of Physiocap measures' campaign
 Physiocap plugin permet l'analyse les données brutes de Physiocap dans Qgis et
 crée une synthese d'une campagne de mesures Physiocap
 
 Le module Inter gère la création des moyennes inter parcellaire
 à partir d'un shapefile de contour de parcelles

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
        physiocap_open_file, physiocap_quelle_projection_demandee

from Physiocap_exception import *

from PyQt4 import QtGui, uic
##from PyQt4.QtCore import QSettings
from PyQt4.QtCore import *
##from PyQt4.QtGui import *
from qgis.core import *
from qgis.gui import *


    # Vectors

def JH_get_layer_by_ID( layerID):
    """ Retrouve un layer ID dans la map Tree Root"""
    layer_trouve = None
    root = QgsProject.instance().layerTreeRoot()
 
    ids = root.findLayerIds()
    layers = root.findLayers()
    #physiocap_log( "--- layerids: " + str( ids))
    #physiocap_log( "- layers : " + str( layers))    
    for id in ids:
        if id == layerID:
            physiocap_log( u"Layer retrouvé : " + str( layerID))
            layer_trouve = root.findLayer( layerID)
            le_layer = layer_trouve.layer()
            break
    if ( layer_trouve != None):
        if ( le_layer.isValid()):
            return le_layer
        else:
            physiocap_log( "Layer invalide : " + str( le_layer.layerName()))
            return None
    else:
        physiocap_log( "Aucun layer retrouvé pour : " + str( layerID))
        return None


def JH_vector_poly_or_point( vector):
    """Vérifie le type de forme du vector : s'appuie sur la premiere valeur"""

    try:
        # geom = vector.getFeatures().next().geometry()
        # Todo : tester avec QGis.WKBPolygon
        # et vifier multi forme ou singleType    
        for uneForme in vector.getFeatures():
            #physiocap_log( "- dans boucle")        
            geom = uneForme.geometry()
            if geom.type() == QGis.Point:
                return "Point"
            elif geom.type() == QGis.Line:
                return "Ligne"
            elif geom.type() == QGis.Polygon:
                return "Polygone"
            else:
                return "Inconnu"
    except:
        raise
        # on evite les cas imprévus
        return "Inconnu"
            
def physiocap_fill_combo_poly_or_point( self, isRoot = None, node = None ):
    """ Recherche dans l'arbre Physiocap (recursif)
    les Polygones,
    les Points de nom DIAMETRE qui correspondent au données filtreés
    Remplit deux listes pour le comboxBox des vecteurs "inter Parcellaire"
    Rend aussi le nombre de poly et point retrouvé
    """
    # Todo : Memoriser les eventuels choix : les remettre en place en fin de traitement 
    nombre_poly = 0
    nombre_point = 0
    
    if ( isRoot == None):
        root = QgsProject.instance().layerTreeRoot()
        self.comboBoxPolygone.clear( )
        self.comboBoxPoints.clear( )
        noeud_en_cours = ""
        noeud = root
    else:
        # On force root comme le noeud
        noeud = node
        noeud_en_cours = node.name()
    # On descend de l'arbre par la racine
    for child in noeud.children():
        if isinstance(child, QgsLayerTreeGroup):
            #physiocap_log( "- group: " + child.name())
            noeud_en_cours = child.name()
            if ( noeud_en_cours != VIGNETTES ):
                # On exclut les vignettes
                un_nombre_poly, un_nombre_point = physiocap_fill_combo_poly_or_point( self, noeud, child)
                nombre_point = nombre_point + un_nombre_point
                nombre_poly = nombre_poly + un_nombre_poly
        elif isinstance(child, QgsLayerTreeLayer):
            #physiocap_log( "- layer: " + child.layerName() + "  ID: " + child.layerId()) 
##            if ( child.layer().isValid()):
##                physiocap_log( "- layer: valide")
            # Tester si poly ou point
            if ( JH_vector_poly_or_point( child.layer()) == "Point"):
                if ( child.layerName() == "DIAMETRE"):
                    node_layer = noeud_en_cours + SEPARATEUR_NOEUD + child.layerId()        
                    self.comboBoxPoints.addItem( str(node_layer))
                    nombre_point = nombre_point + 1
            elif ( JH_vector_poly_or_point( child.layer()) == "Polygone"):
                node_layer = child.layerName() + SEPARATEUR_NOEUD + child.layerId()        
                self.comboBoxPolygone.addItem( str(node_layer) )
                nombre_poly = nombre_poly + 1
    return nombre_poly, nombre_point

def physiocap_moyenne_InterParcelles( self):
    """Verification et requete spatiale"""
    # QT Confiance
    repertoire_data = self.lineEditDirectoryPhysiocap.text()
    if ((repertoire_data == "") or ( not os.path.exists( repertoire_data))):
        physiocap_error( u"Pas de répertoire de donnée spécifié")
        return physiocap_message_box( self, 
            self.tr( u"Pas de répertoire de données brutes spécifié" ),
            "information")
            
    details = "NO"
    if self.checkBoxInfoVignoble.isChecked():
        details = "YES"
            
    physiocap_log( u"Début du calcul des moyennes à partir de vos contours" )
    
    # Récupérer des styles pour chaque shape
    dir_template = os.path.join( os.path.dirname(__file__), 'modeleQgis')       
    le_template_moyenne = os.path.join( dir_template, "Moyenne Intra.qml")
    le_template_point = os.path.join( dir_template, "Diametre 6 quantilles.qmll")
 
    # QT confiance
 
    # Pour polygone de contour   
    nom_complet_poly = self.comboBoxPolygone.currentText().split( SEPARATEUR_NOEUD)
    if ( len( nom_complet_poly) != 2):
        physiocap_error( u"Le polygone de contour n'est pas choisi." +
          "Avez-vous ouvert votre shapefile de contour ?")
        return physiocap_message_box( self,
            self.tr( u"Le polygone de contour n'est pas choisi." +
                "Avez-vous ouvert votre shapefile de contour ?" ),
            "information")            
    nom_poly = nom_complet_poly[ 0] 
    id_poly = nom_complet_poly[ 1] 
    vecteur_poly = JH_get_layer_by_ID( id_poly)
    
    # Pour les points
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
    nom_noeud_arbre = nom_complet_point[ 0] 
    id_point = nom_complet_point[ 1] 
    vecteur_point = JH_get_layer_by_ID( id_point)
    
    # Vérification 
    if ( vecteur_point == None):
        physiocap_error( u"Le jeu de données choisi n'est pas valide. " +
          "Lancez le traitement initial - bouton OK - avant de faire votre" +
          "calcul de Moyenne Inter Parcellaire")
        return physiocap_message_box( self,
            self.tr( u"Le jeu de données choisi n'est pas valide. " +
                "Lancez le traitement initial - bouton OK - avant de faire votre" +
                "calcul de Moyenne Inter Parcellaire" ),
            "information")    

    if ( vecteur_poly == None) or ( not vecteur_poly.isValid()):
        physiocap_error( u"Le contour choisi n'est pas valide. " +
          "Lancez le traitement initial - bouton OK - avant de faire votre" +
          "calcul de Moyenne Inter Parcellaire")
        return physiocap_message_box( self,
            self.tr( u"Le contour choisi n'est pas valide. " +
                "Lancez le traitement initial - bouton OK - avant de faire votre" +
                "calcul de Moyenne Inter Parcellaire" ),
            "information")
            
    # Verifier SRCs sont les même
    crs_poly = vecteur_poly.crs().authid()
    crs_point = vecteur_point.crs().authid()
    if ( crs_poly != crs_point):
        mes = "Les projections (Crs) des coutours et mesures brutes sont différentes !"
        physiocap_error( mes)
        return physiocap_message_box( self, self.tr( mes),"information")
    else:
        # Assert repertoire shapfile : c'est le repertoire qui contient le vecteur point
        chemin_shapes = os.path.dirname( unicode( vecteur_point.dataProvider().dataSourceUri() ) ) ;
        if ( not os.path.exists( chemin_shapes)):
            raise physiocap_exception_rep( chemin_shapes)
       
        # On passe sur les differents contours
        id = 0
        contour_avec_point = 0
        for un_contour in vecteur_poly.getFeatures(): #iterate poly features
            id = id + 1
            try:
                un_nom = str( un_contour["NAME"]) #get attribute of poly layer
            except:
                un_nom = "PHY_ID" + str(id)
                pass
            
            physiocap_log ( u"================ ")
            physiocap_log ( u"== Nom Contour : " + un_nom)
            
            un_autre_nom = "PHY_ID" + str(id)
            geom_poly = un_contour.geometry() #get geometry of poly layer
            #physiocap_log ( "Dans polygone geom multipart : " + str(geom_poly.wkbType()))
##            if geom_poly.wkbType() == QGis.WKBPolygon:
##                physiocap_log ( "c'est un polygone simple: " + un_nom)
##            if geom_poly.wkbType() == QGis.WKBMultiPolygon:
##                physiocap_log ( "c'est un polygone multiple: " + un_nom)
                
            # Préfiltre dans un rectangle
            les_geom = []
            les_dates = []
            les_GID = []
            les_vitesses = []
            les_sarments = []
            les_diametres = []
            nb_dia = 0
            nb_sar = 0
            les_biom = []
            les_biomgm2 = []
            i = 0
            date_debut = ""
            heure_fin = ""
            for un_point in vecteur_point.getFeatures(QgsFeatureRequest().
                            setFilterRect(geom_poly.boundingBox())):
                # un_point est un feature ! 
##                geom_point = None
##                geom_point = un_point.geometry().within(geom_poly)
                #feat.setGeometry( QgsGeometry.fromPolygon(geom_poly.asPolygon())) #écrit la géométrie tel que lu dans shape contour
                #physiocap_log ( "Dans un point : " + str(i))
                #if geom_point != None:
                if un_point.geometry().within(geom_poly):
                    if i == 0:
                        contour_avec_point = contour_avec_point + 1
                    i = i + 1
                    #physiocap_log ( "Dans un point : " + str(i))
                    try:
                        if i == 2:
                            # Attraper date début
                            date_debut = un_point["DATE"]
                        les_geom.append( un_point.geometry().asPoint())
                        les_dates.append( un_point["DATE"])
                        les_GID.append( un_point["GID"])
                        les_vitesses.append( un_point["VITESSE"])
                        les_sarments.append( un_point["NBSARM"])
                        les_diametres.append( un_point["DIAM"])
                        les_biom.append( un_point["BIOM"])
                        if ( details == "YES"):
                            les_biomgm2.append( un_point["BIOMGM2"])
                    except:
                        raise
                        #raise physiocap_exception_points_invalid( un_nom) 
                            
            # en sortie de boucle on attrape la derniere heure
            if i > 10:
                heure_fin = un_point["DATE"][-8:]
            nb_dia = len( les_diametres)
            nb_sar = len( les_sarments)
            if ( (nb_dia > 0) and ( nb_dia == nb_sar )):
                moyenne_vitesse = sum(les_vitesses) /  len( les_vitesses)
                moyenne_sar = sum(les_sarments) / nb_sar
                moyenne_dia = sum(les_diametres) / nb_dia
                moyenne_biom = sum(les_biom) / len( les_biom)
                moyenne_biomgm2 = sum(les_biomgm2) / len( les_biom)
                physiocap_log ( u"== Nombre Diam : " + str(nb_dia) ) 
                physiocap_log ( u"== Date début : " + str(date_debut) + " et heure Fin : " + heure_fin) 
                physiocap_log ( u"== Moyenne des sarments : " + str(moyenne_sar))
                physiocap_log ( u"== Moyenne des diamètres : " + str(moyenne_dia))
                physiocap_log ( u"================ ")
                #physiocap_log( u"Fin du calcul des moyennes à partir de vos contours" )
                
                # Création du Shape moyenne et prj
                laProjection, EXT_SHP, EXT_PRJ, EPSG_NUMBER = physiocap_quelle_projection_demandee(self)
                crs = QgsCoordinateReferenceSystem( EPSG_NUMBER, QgsCoordinateReferenceSystem.PostgisCrsId)
                # vignette - nom_noeud_arbre + SEPARATEUR_
                nom_court_vignette = un_nom + NOM_MOYENNE + EXT_SHP     
                nom_court_prj = un_nom + NOM_MOYENNE + EXT_PRJ     
                #physiocap_log( u"== Vignette court : " + nom_court_vignette )       
                nom_vignette = physiocap_rename_existing_file( os.path.join( chemin_shapes, nom_court_vignette))        
                nom_prj = physiocap_rename_existing_file( os.path.join( chemin_shapes, nom_court_prj))        

                # ###################
                # CRÉATION Vignette
                # ###################
                if ( contour_avec_point == 1):
                    # Gestion de l'arbre
                    root = QgsProject.instance().layerTreeRoot( )
                    un_groupe = root.findGroup( nom_noeud_arbre)
                    if un_groupe != None:
                        vignette_existante = un_groupe.findGroup( VIGNETTES)
                        if ( vignette_existante == None ):
                            vignette_group = un_groupe.addGroup( VIGNETTES)
                        else:
                            # Si vignette preexiste, on ne recommence pas
                            raise physiocap_exception_vignette_exists( nom_noeud_arbre) 
 
                physiocap_moyenne_vers_vignette( crs, nom_vignette, nom_prj, 
                    geom_poly, un_nom, un_autre_nom, date_debut, heure_fin,
                    moyenne_vitesse, moyenne_sar, moyenne_dia, moyenne_biom, 
                    moyenne_biomgm2, details)
                
                # ###################
                # CRÉATION point
                # ###################
                # point 
                nom_court_point = un_nom + NOM_POINTS + EXT_SHP     
                nom_court_point_prj = un_nom + NOM_POINTS + EXT_PRJ     
                #physiocap_log( u"== Vignette court : " + nom_court_vignette )       
                nom_point = physiocap_rename_existing_file( os.path.join( chemin_shapes, nom_court_point))        
                nom_point_prj = physiocap_rename_existing_file( os.path.join( chemin_shapes, nom_court_point_prj))        
                
                physiocap_moyenne_vers_point( crs, nom_point, nom_point_prj, 
                    les_geom, les_GID, les_dates, 
                    les_vitesses, les_sarments, les_diametres, les_biom, 
                    les_biomgm2, details)
                
                # Affichage dans arbre "vignettes"
                vignette_vector = QgsVectorLayer( nom_vignette, nom_court_vignette, 'ogr')
                points_vector = QgsVectorLayer( nom_point, nom_court_point, 'ogr')
                if vignette_group != None:
                    QgsMapLayerRegistry.instance().addMapLayer( vignette_vector, False)
                    QgsMapLayerRegistry.instance().addMapLayer( points_vector, False)
                    # Ajouter le vecteur dans un groupe
                    vector_node = vignette_group.addLayer( vignette_vector)
                    vector_point_node = vignette_group.addLayer( points_vector)
                else:
                    QgsMapLayerRegistry.instance().addMapLayer( vignette_vector)
                    QgsMapLayerRegistry.instance().addMapLayer( points_vector)
                # Mise en action du template
                if ( os.path.exists( le_template_moyenne)):
                    vignette_vector.loadNamedStyle( le_template_moyenne)                                
                if ( os.path.exists( le_template_point)):
                    points_vector.loadNamedStyle( le_template_point)                                
            else:
                physiocap_log( u"Aucune point dans votre contour : " + str(un_nom) + 
                    ". Pas de comparaison inter parcellaire" )       
        
        if ( contour_avec_point == 0):
            return physiocap_message_box( self, 
                    self.tr( u"Aucune point dans vos contours : pas de comparaison inter parcellaire"),
                    "information")
                    
    return physiocap_message_box( self,
            self.tr( u"Fin du calcul moyenne à partir de vos contours" ),
            "information")

def physiocap_moyenne_vers_vignette( crs, nom_vignette, nom_prj,
        geom_poly, un_nom, un_autre_nom, date_debut, heure_fin, 
        moyenne_vitesse, moyenne_sar, moyenne_dia, moyenne_biom,
        moyenne_biomgm2, details = "NO", NAME_NAME = "PHY_ID"):
    """ Creation d'une vignette nommé un_nom avec les moyennes
    qui se trouvent moyenne_sar, moyenne_dia 
        moyennes des nombres de sarments / Metre
        moyennes du diametre
    Il s'agit d'un seul polygone
    """
    # physiocap_log( u"Début de shape vignette :"+ str( un_nom ))
    # Prepare les attributs
    les_champs = QgsFields()
    les_champs.append( QgsField( "GID", QVariant.Int, "integer", 10))
    les_champs.append( QgsField( NAME_NAME, QVariant.String, "string", 25))
    les_champs.append( QgsField( "NOM_PHY", QVariant.String, "string", 25))
    les_champs.append( QgsField( "DEBUT", QVariant.String, "string", 25))
    les_champs.append( QgsField( "FIN", QVariant.String, "string", 12))
    les_champs.append( QgsField("VITESSE", QVariant.Double, "double", 10,2))
    les_champs.append(QgsField( "NBSARM",  QVariant.Double, "double", 10,2))
    les_champs.append(QgsField( "DIAM",  QVariant.Double, "double", 10,2))
    les_champs.append(QgsField("BIOM", QVariant.Double,"double", 10,2)) 
    if details == "YES":
        # Niveau de detail demandé
        les_champs.append(QgsField("BIOMGM2", QVariant.Double,"double", 10,2))

    # Creation du Shape
    writer = QgsVectorFileWriter( nom_vignette, "utf-8", les_champs, 
        QGis.WKBPolygon, crs , "ESRI Shapefile")

    feat = QgsFeature()
    feat.setGeometry( QgsGeometry.fromPolygon(geom_poly.asPolygon())) #écrit la géométrie tel que lu dans shape contour
    if details == "YES":
        # Ecrit tous les attributs
        feat.setAttributes( [ 1, un_nom, un_autre_nom, date_debut, heure_fin, 
            moyenne_vitesse, moyenne_sar, moyenne_dia, moyenne_biom, moyenne_biomgm2])
    else:
        # Ecrit les premiers attributs
        feat.setAttributes( [ 1, un_nom, un_autre_nom, date_debut, heure_fin, 
            moyenne_vitesse, moyenne_sar, moyenne_dia, moyenne_biom])
   # Ecrit le feature
    writer.addFeature( feat)

    # Create the PRJ file
    prj = open(nom_prj, "w")
    epsg = 'inconnu'
    if ( crs == EPSG_NUMBER_L93):
        # Todo: V1.x ? Faire aussi un fichier de metadata 
        epsg = EPSG_TEXT_L93
    if (crs == EPSG_NUMBER_GPS):
        epsg = EPSG_TEXT_GPS
    prj.write(epsg)
    prj.close()    
    
    physiocap_log( u"Fin vignette :"+ str( un_nom ))
    return 0

def physiocap_moyenne_vers_point( crs, nom_point, nom_prj,
                    les_geom, les_GID, les_dates, 
                    les_vitesses, les_sarments, les_diametres, les_biom, 
                    les_biomgm2, details = "NO"):
    """ Creation d'un shape de points se trouvant dans le contour
    """
    physiocap_log( u"Début de shape point :")
    # Prepare les attributs
    les_champs = QgsFields()
    les_champs.append( QgsField( "GID", QVariant.Int, "integer", 10))
    les_champs.append( QgsField( "DATE", QVariant.String, "string", 25))
    les_champs.append( QgsField("VITESSE", QVariant.Double, "double", 10,2))
    les_champs.append(QgsField( "NBSARM",  QVariant.Double, "double", 10,2))
    les_champs.append(QgsField( "DIAM",  QVariant.Double, "double", 10,2))
    les_champs.append(QgsField("BIOM", QVariant.Double,"double", 10,2)) 
    if details == "YES":
        # Niveau de detail demandé
        les_champs.append(QgsField("BIOMGM2", QVariant.Double,"double", 10,2))

    # Creation du Shape
    writer = QgsVectorFileWriter( nom_point, "utf-8", les_champs, 
        QGis.WKBPoint, crs , "ESRI Shapefile")

    i = -1
    for gid in les_GID:   
        i = i+1
        feat = QgsFeature()
        feat.setGeometry( QgsGeometry.fromPoint( les_geom[ i])) #écrit la géométrie tel que lu dans shape contour
        if details == "YES":
            # Ecrit tous les attributs
            feat.setAttributes( [ les_GID[ i], les_dates[ i], les_vitesses[ i], 
            les_sarments[ i], les_diametres[ i], les_biom[ i], les_biomgm2[ i] ])
        else:
            # Ecrit les premiers attributs
            feat.setAttributes( [ les_GID[ i], les_dates[ i], les_vitesses[ i], 
             les_sarments[ i], les_diametres[ i], les_biom[ i] ])
       # Ecrit le feature
        writer.addFeature( feat)

    # Create the PRJ file
    prj = open(nom_prj, "w")
    epsg = 'inconnu'
    if ( crs == EPSG_NUMBER_L93):
        # Todo: V1.x ? Faire aussi un fichier de metadata 
        epsg = EPSG_TEXT_L93
    if (crs == EPSG_NUMBER_GPS):
        epsg = EPSG_TEXT_GPS
    prj.write(epsg)
    prj.close()    
    
    physiocap_log( u"Fin point :")
    return 0

##def physiocap_moyenne_vers_shapefile( crs, shape_name, prj_name,
##    X_LIST, Y_LIST, NAME_LIST, DATE_LIST, SARMENT_LIST, DIAMETRE_LIST, 
##    NAME_NAME = "NOM",  details = "NO"):
##    """ Creation de shape file des moyennes
##    qui se trouve dans :
##    NAME_LIST = attributs nommant le contour
##    DATE_LIST date capture
##    DIAMETRE_LIST = moyennes du diametre
##    SARMENT_LIST = moyennes des nombres de sarments / Metre
##    ...
##    Selon la valeur de détails , on crée les 5 premiers ("NO") ou tous les attibuts ("YES")
##    """
##    physiocap_log( u"Début des shapes moyennes :"+ str( len (NAME_LIST) ))
##    # Prepare les attributs
##    les_champs = QgsFields()
##    les_champs.append( QgsField("GID", QVariant.Int, "integer", 10))
##    les_champs.append( QgsField(NAME_NAME, QVariant.String, "string", 25))
##    les_champs.append( QgsField("DATE", QVariant.String, "string", 25))
##    #les_champs.append( QgsField("VITESSE", QVariant.Double, "double", 10,2))
##    les_champs.append(QgsField("NBSARM",  QVariant.Double, "double", 10,2))
##    les_champs.append(QgsField("DIAM",  QVariant.Double, "double", 10,2))
##    #les_champs.append(QgsField("BIOM", QVariant.Double,"double", 10,2)) 
##    if details == "YES":
##        # Niveau de detail demandé
##        pass  #les_champs.append(QgsField("BIOMGM2", QVariant.Double,"double", 10,2))
##
##    # Creation du Shape
##    writer = QgsVectorFileWriter( shape_name, "utf-8", les_champs, 
##        QGis.WKBPoint, None , "ESRI Shapefile")
##
##    #Lecture des noms 
##    # Todo assert len NAME_LIST = DIAMETRE_LIST = SARMENT_LIST
##    for i,unName in enumerate( NAME_LIST):
##        feat = QgsFeature()
##        feat.setGeometry( QgsGeometry.fromPoint(QgsPoint(X_LIST[i],Y_LIST[i]))) #écrit la géométrie
##        if details == "YES":
##            # Ecrit tous les attributs
##           feat.setAttributes( [ i, NAME_LIST[i], DATE_LIST[i], SARMENT_LIST[i], DIAMETRE_LIST[i]])
##        else:
##            # Ecrit les x premiers attributs
##            feat.setAttributes( [ i, NAME_LIST[i], DATE_LIST[i], SARMENT_LIST[i], DIAMETRE_LIST[i]])
##       # Ecrit le feature
##        writer.addFeature( feat)
##
##    # Create the PRJ file
##    prj = open(prj_name, "w")
##    epsg = 'inconnu'
##    if ( crs == EPSG_NUMBER_L93):
##        epsg = EPSG_TEXT_L93
##    if (crs == EPSG_NUMBER_GPS):
##        epsg = EPSG_TEXT_GPS
##    prj.write(epsg)
##    prj.close()
##    physiocap_log( u"Fin des shapes moyennes" )
##
##    return 0
 


#Example d'appel de processing
##import processing
##layers = QgsMapLayerRegistry.instance().mapLayers().values()
##outputLayers=[]
##
##for layer in layers:
##    i = layer.name().split("_")[-1]
##    processing.runalg('qgis:lineintersections', layer, layer, 'id', 'id', 'C:/Phoenix/intersection_%s.shp' % (i))
##    outputLayers.append(QgsVectorLayer('C:/Phoenix/intersection_%s.shp' % (i) , 'intersection_%s' % (i), "ogr"))
##
##QgsMapLayerRegistry.instance().addMapLayers( outputLayers )