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
##    def physiocap_get_vector_layers( self ):
##        """Create a list of vector """
##        layerMap = QgsMapLayerRegistry.instance().mapLayers()
##        layerList = []
##        for name, layer in layerMap.iteritems():
##            if layer.type() == QgsMapLayer.VectorLayer:
##                layerList.append( layer.name() )
##                
##        return layerList
                
##    def physiocap_create_vector_point_list( self ):
##        """Create a list of vector and initialize the comboBoxPoints"""
##        layers = self.physiocap_get_vector_layers()
##        if len( layers) == 0:
##            self.comboBoxPoints.setCurrentIndex( 0)
##            physiocap_log( u"Pas de layer de type Points")
##        self.comboBoxPoints.clear( )
##        self.comboBoxPoints.addItems( layers )
##        self.comboBoxPoints.setCurrentIndex( 2)

def JH_get_layer_by_name( layerName, noeud = None ):
    # exemple : layers = QgsMapLayerRegistry.instance().mapLayers().values()
    layerMap = QgsMapLayerRegistry.instance().mapLayers()
    for name, layer in layerMap.iteritems():
        if layer.type() == QgsMapLayer.VectorLayer and layer.name() == layerName:
            # The layer is found
            # Vérifier si on est dans le bon noeud
            if noeud == None:
                break
            else:
                root = QgsProject.instance().layerTreeRoot()
                un_groupe = root.findGroup( noeud)
                if ( un_groupe != None ):
                    #physiocap_log( "- group: ")
                    layer_trouve = un_groupe.findLayer( layer.id())
                    if ( layer_trouve != None ):
                        #physiocap_log( "- layerid: " + str( layer.id()))
                        break
    if layer.isValid():
        return layer, layer.id()
    else:
        return None

def JH_vector_poly_or_point( vector):
    """Vérifie le type de forme du vector : s'appuie sur la premiere valeur"""
            
##    if ( vector.isValid()):
##        physiocap_log( "- vecteur: valide")        
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
    Rend deux listes pour le comboxBox des vecteurs "inter Parcellaire"
    """
    
    # Todo : Memoriser les eventuels choix : les remettre en place en fin de traitement 
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
##            physiocap_log( "- group: " + child.name())
            noeud_en_cours = child.name()
            if ( noeud_en_cours != VIGNETTES ):
                # On exclut les vignettes
                physiocap_fill_combo_poly_or_point( self, noeud, child)
        elif isinstance(child, QgsLayerTreeLayer):
##            physiocap_log( "- layer: " + child.layerName() + "  ID: " + child.layerId()) 
##            if ( child.layer().isValid()):
##                physiocap_log( "- layer: valide")
            node_layer = noeud_en_cours + SEPARATEUR_NOEUD + child.layerId()        
            # Tester si poly ou point
            if ( JH_vector_poly_or_point( child.layer()) == "Point"):
                if ( child.layerName() == "DIAMETRE"):
                    self.comboBoxPoints.addItem( str(node_layer))
            elif ( JH_vector_poly_or_point( child.layer()) == "Polygone"):
                self.comboBoxPolygone.addItem( str(child.layerName()) )

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
    dirTemplate = os.path.join( os.path.dirname(__file__), 'modeleQgis')       
    leTemplate = os.path.join( dirTemplate, "Moyenne Intra.qml")
 
    # QT confiance
    vecteur_poly, poly_ID = JH_get_layer_by_name( self.comboBoxPolygone.currentText())
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
    nom_ID = nom_complet_point[ 1] 
    vecteur_point, point_ID = JH_get_layer_by_name( "DIAMETRE", nom_noeud_arbre)
    if (( vecteur_point == None) or ( not vecteur_point.isValid()) or
        ( point_ID != nom_ID)):
        physiocap_error( u"Le jeu de données choisi n'est pas valide. " +
          "Lancez le traitement initial - bouton OK - avant de faire votre" +
          "calcul de Moyenne Inter Parcellaire")
        return physiocap_message_box( self,
            self.tr( u"Le shape de points choisi n'est pas valide. " +
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
        
        # On passe sur les differents contours
        id = 0
        for un_contour in vecteur_poly.getFeatures(): #iterate poly features
            id = id + 1
            try:
                un_nom = str( un_contour["Name"]) #get attribute of poly layer
            except:
                un_nom = "PHY_ID" + str(id)
                pass
            geom_poly = un_contour.geometry() #get geometry of poly layer
            #physiocap_log ( "Dans polygone geom multipart : " + str(geom_poly.wkbType()))
##            if geom_poly.wkbType() == QGis.WKBPolygon:
##                physiocap_log ( "c'est un polygone simple: " + un_nom)
##            if geom_poly.wkbType() == QGis.WKBMultiPolygon:
##                physiocap_log ( "c'est un polygone multiple: " + un_nom)
                
            # Préfiltre dans un rectangle
            vitesse = []
            sarment = []
            diametre = []
            biom = []
            biomgm2 = []
            i = 0
            date_debut = ""
            heure_fin = ""
            for un_point in vecteur_point.getFeatures(QgsFeatureRequest().
                            setFilterRect(geom_poly.boundingBox())):
                if un_point.geometry().within(geom_poly):
                    i = i + 1
                    try:
                        if i == 2:
                            # Attraper date début
                            date_debut = un_point["DATE"]
                        vitesse.append( un_point["VITESSE"])
                        sarment.append( un_point["NBSARM"])
                        diametre.append( un_point["DIAM"])
                        biom.append( un_point["BIOM"])
                        # todo : shape de points : geom_point.append( un_point.geometry())
                        if ( details == "YES"):
                            biomgm2.append( un_point["BIOMGM2"])
                    except:
                        raise physiocap_exception_points_invalid( un_nom) 
                            
            # en sortie de boucle on attrape la derniere heure
            if i > 10:
                heure_fin = un_point["DATE"][-8:]
            nb_dia = len( diametre)
            nb_sar = len( sarment)
            if ( (len( diametre) > 0) and ( nb_dia == nb_sar )):
                moyenne_vitesse = sum(vitesse) /  len( vitesse)
                moyenne_sar = sum(sarment) / nb_sar
                moyenne_dia = sum(diametre) / nb_dia
                moyenne_biom = sum(biom) / len( biom)
                moyenne_biomgm2 = sum(biomgm2) / len( biom)
                physiocap_log ( u"== Date début : " + str(date_debut) + " et heure Fin : " + heure_fin) 
                physiocap_log ( u"== Moyenne des sarments : " + str(moyenne_sar))
                physiocap_log ( u"== Moyenne des diamètres : " + str(moyenne_dia))
                #physiocap_log( u"Fin du calcul des moyennes à partir de vos contours" )
                
                # Création du Shape moyenne et prj
                laProjection, EXT_SHP, EXT_PRJ, EPSG_NUMBER = physiocap_quelle_projection_demandee(self)
                crs = QgsCoordinateReferenceSystem( EPSG_NUMBER, QgsCoordinateReferenceSystem.PostgisCrsId)
                # vignette - nom_noeud_arbre + SEPARATEUR_
                nom_court_vignette = un_nom + NOM_MOYENNE + EXT_SHP     
                nom_court_prj = un_nom + NOM_MOYENNE + EXT_PRJ     
                physiocap_log( u"== Vignette court : " + nom_court_vignette )       
                nom_vignette = physiocap_rename_existing_file( os.path.join( chemin_shapes, nom_court_vignette))        
                nom_prj = physiocap_rename_existing_file( os.path.join( chemin_shapes, nom_court_prj))        
                # ###################
                # CRÉATION Vignette
                # ###################
                physiocap_moyenne_vers_vignette( crs, nom_vignette, nom_prj, 
                    geom_poly, un_nom, date_debut, heure_fin,
                    moyenne_vitesse, moyenne_sar, moyenne_dia, moyenne_biom, 
                    moyenne_biomgm2, details)
                
                # Affichage dans arbre "vignettes"
                vignette_vector = QgsVectorLayer( nom_vignette, nom_court_vignette, 'ogr')
                if vignette_group != None:
                    QgsMapLayerRegistry.instance().addMapLayer( vignette_vector, False)
                    # Ajouter le vecteur dans un groupe
                    vector_node = vignette_group.addLayer( vignette_vector)
                else:
                    QgsMapLayerRegistry.instance().addMapLayer( vignette_vector)
                # Mise en action du template
                if ( os.path.exists( leTemplate)):
                    vignette_vector.loadNamedStyle( leTemplate)                                
            else:
                physiocap_log( u"Aucune point dans vos contours : pas de comparaison inter parcellaire" )       
                return physiocap_message_box( self, 
                    self.tr( u"Aucune point dans vos contours : pas de comparaison inter parcellaire"),
                    "information")
                    
    return physiocap_message_box( self,
            self.tr( u"Fin du calcul moyenne à partir de vos contours" ),
            "information")

def physiocap_moyenne_vers_vignette( crs, nom_vignette, nom_prj,
        geom_poly, un_nom, date_debut, heure_fin, 
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
        feat.setAttributes( [ 1, un_nom, date_debut, heure_fin, 
            moyenne_vitesse, moyenne_sar, moyenne_dia, moyenne_biom, moyenne_biomgm2])
    else:
        # Ecrit les premiers attributs
        feat.setAttributes( [ 1, un_nom, date_debut, heure_fin, 
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