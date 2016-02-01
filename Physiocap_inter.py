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
 à partir d'un shapefile de contour de parcelles et l'extration des points de
 chaque parcelle 

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


def physiocap_vector_poly_or_point( vector):
    """Vérifie le type de forme du vector : s'appuie sur la premiere valeur"""

    try:
        # geom = vector.getFeatures().next().geometry()
        # Todo : tester avec QGis.WKBPolygon
        # et vérifier multi forme ou singleType
        # et Postgres    
        for uneForme in vector.getFeatures():
##            physiocap_log( "- Vector feature format:" + str( uneForme.__format__))        
##            physiocap_log( "- Vector feature attirbutes :" + str( uneForme.attributes()))        
##            physiocap_log( "- Vector feature geo interface :" + str( uneForme.__geo_interface__))        
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
        physiocap_error( "Warning : Layer ni point, ni polygone : " + vector.id())
        pass
        # on evite les cas imprévus
        return "Inconnu"
            
 
def physiocap_fill_combo_poly_or_point( self, isRoot = None, node = None ):
    """ Recherche dans l'arbre Physiocap (recursif)
    les Polygones,
    les Points de nom DIAMETRE qui correspondent au données filtreés
    Remplit deux listes pour le comboxBox des vecteurs "inter Parcellaire"
    Rend aussi le nombre de poly et point retrouvé
    """
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
        #physiocap_log( "- in noeud : comment connaitre le type")        
        if isinstance(child, QgsLayerTreeGroup):
            #physiocap_log( "- group: " + child.name())
            noeud_en_cours = child.name()
            groupe_inter = noeud_en_cours + SEPARATEUR_ + VIGNETTES_INTER
            if ( noeud_en_cours != groupe_inter ):
                # On exclut les vignettes
                un_nombre_poly, un_nombre_point = physiocap_fill_combo_poly_or_point( self, noeud, child)
                nombre_point = nombre_point + un_nombre_point
                nombre_poly = nombre_poly + un_nombre_poly
        elif isinstance(child, QgsLayerTreeLayer):
            #physiocap_log( "- in tree layer: ")
            #physiocap_log( "- layer: " + child.layerName() + "  ID: " + child.layerId()) 
            # Tester si poly ou point
            if ( physiocap_vector_poly_or_point( child.layer()) == "Point"):
                if ( child.layerName() == "DIAMETRE mm"):
                    node_layer = noeud_en_cours + SEPARATEUR_NOEUD + child.layerId()
                    # Todo : WT DATA BUG unicode acsii dans certain cas...        
                    self.comboBoxPoints.addItem( str(node_layer))
                    nombre_point = nombre_point + 1
            elif ( physiocap_vector_poly_or_point( child.layer()) == "Polygone"):
                node_layer = child.layerName() + SEPARATEUR_NOEUD + child.layerId()        
                self.comboBoxPolygone.addItem( str(node_layer) )
                nombre_poly = nombre_poly + 1
            #else:
                #physiocap_log( "- layer rejeté : " + child.layerName() + "  ID: " + child.layerId()) 
    return nombre_poly, nombre_point

              
def physiocap_moyenne_vers_vignette( crs, EPSG_NUMBER, nom_vignette, nom_prj,
        geom_poly, un_nom, un_autre_ID, date_debut, heure_fin, 
        moyenne_vitesse, moyenne_sar, moyenne_dia, moyenne_biom,
        moyenne_biomgm2, details = "NO"):
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
    #les_champs.append( QgsField( NAME_NAME, QVariant.String, "string", 25))
    les_champs.append( QgsField( "NOM_PHY", QVariant.String, "string", 25))
    les_champs.append( QgsField( "ID_PHY", QVariant.String, "string", 15))
    les_champs.append( QgsField( "DEBUT", QVariant.String, "string", 25))
    les_champs.append( QgsField( "FIN", QVariant.String, "string", 12))
    les_champs.append( QgsField("VITESSE", QVariant.Double, "double", 10,2))
    les_champs.append( QgsField( "NBSARM",  QVariant.Double, "double", 10,2))
    les_champs.append( QgsField( "DIAM",  QVariant.Double, "double", 10,2))
    les_champs.append( QgsField( "BIOM", QVariant.Double,"double", 10,2))
    if details == "YES":
        # Niveau de detail demandé
        les_champs.append( QgsField( "BIOMGM2", QVariant.Double,"double", 10,2))

    # Creation du Shape
    writer = QgsVectorFileWriter( nom_vignette, "utf-8", les_champs, 
        QGis.WKBPolygon, crs , "ESRI Shapefile")

    # Cas PG à tester
    #physiocap_log(u" Type de geom_poly :" + str( type(geom_poly)))
    #physiocap_log(u" Type de geom_poly.asPolygon :" + str( type(geom_poly.asPolygon)))

    feat = QgsFeature()
    feat.setGeometry( QgsGeometry.fromPolygon(geom_poly.asPolygon())) #écrit la géométrie tel que lu dans shape contour
    if details == "YES":
        # Ecrit tous les attributs
        feat.setAttributes( [ 1, un_nom, un_autre_ID, date_debut, heure_fin, 
            moyenne_vitesse, moyenne_sar, moyenne_dia, moyenne_biom, moyenne_biomgm2])
    else:
        # Ecrit les premiers attributs
        feat.setAttributes( [ 1, un_nom, un_autre_ID, date_debut, heure_fin, 
            moyenne_vitesse, moyenne_sar, moyenne_dia, moyenne_biom])
   # Ecrit le feature
    writer.addFeature( feat)

    # Create the PRJ file
    prj = open(nom_prj, "w")
    epsg = 'inconnu'
    if ( EPSG_NUMBER == EPSG_NUMBER_L93):
        epsg = EPSG_TEXT_L93
    if (EPSG_NUMBER == EPSG_NUMBER_GPS):
        epsg = EPSG_TEXT_GPS
    prj.write(epsg)
    prj.close()    
    
    #physiocap_log( u"Fin vignette :"+ str( un_nom ))
    return 0

def physiocap_moyenne_vers_point( crs, EPSG_NUMBER, nom_point, nom_prj,
                    les_geom_point_feat, les_GID, les_dates, 
                    les_vitesses, les_sarments, les_diametres, les_biom, 
                    les_biomgm2, details = "NO"):
    """ Creation d'un shape de points se trouvant dans le contour
    """
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
        feat.setGeometry( QgsGeometry.fromPoint( les_geom_point_feat[ i])) #écrit la géométrie tel que lu dans shape contour
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
    if ( EPSG_NUMBER == EPSG_NUMBER_L93):
        epsg = EPSG_TEXT_L93
    if (EPSG_NUMBER == EPSG_NUMBER_GPS):
        epsg = EPSG_TEXT_GPS
    prj.write(epsg)
    prj.close()    
    
    #physiocap_log( u"Fin point :")
    return 0

def physiocap_moyenne_vers_contour( crs, EPSG_NUMBER, nom_contour_moyenne, nom_contour_moyenne_prj,
    les_geoms_poly, les_parcelles, les_parcelles_ID, les_dates_parcelle, les_heures_parcelle,
    les_moyennes_vitesse, les_moyennes_sarment, les_moyennes_diametre, les_moyennes_biom,
    les_moyennes_biomgm2, details = "NO"):
    """ Creation d'un contour avec les moyennes
       Il s'agit de plusieurs polygones
    """
    
    # Prepare les attributs
    les_champs = QgsFields()
    les_champs.append( QgsField( "GID", QVariant.Int, "integer", 10))
    les_champs.append( QgsField( "NOM_PHY", QVariant.String, "string", 25))
    les_champs.append( QgsField( "ID_PHY", QVariant.String, "string", 15))
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
    writer = QgsVectorFileWriter( nom_contour_moyenne, "utf-8", les_champs, 
        QGis.WKBPolygon, crs , "ESRI Shapefile")
    
    physiocap_log( u"Nombre contours contenant des données moyennes : %s" + str( len(les_parcelles)))

    for i in range( 0, len( les_parcelles)) :
        
        feat = QgsFeature()
        feat.setGeometry( QgsGeometry.fromPolygon( les_geoms_poly[ i])) #écrit la géométrie tel que lu dans shape contour
        if details == "YES":
            # Ecrit tous les attributs
            feat.setAttributes( [ i, les_parcelles[ i], les_parcelles_ID[ i],
                les_dates_parcelle[ i],  les_heures_parcelle[ i],
                les_moyennes_vitesse[ i], les_moyennes_sarment[ i], les_moyennes_diametre[ i], 
                les_moyennes_biom[ i], les_moyennes_biomgm2[ i]])
        else:
            # Ecrit les premiers attributs
            feat.setAttributes( [ i, les_parcelles[ i], les_parcelles_ID[ i],
                les_dates_parcelle[ i],  les_heures_parcelle[ i],
                les_moyennes_vitesse[ i], les_moyennes_sarment[ i], les_moyennes_diametre[ i], 
                les_moyennes_biom[ i]])
        # Ecrit le feature
        writer.addFeature( feat)

    # Create the PRJ file
    prj = open(nom_contour_moyenne_prj, "w")
    epsg = 'inconnu'
    if ( EPSG_NUMBER == EPSG_NUMBER_L93):
        # Todo: V1.5 ? Faire aussi un fichier de metadata 
        epsg = EPSG_TEXT_L93
    if (EPSG_NUMBER == EPSG_NUMBER_GPS):
        epsg = EPSG_TEXT_GPS
    prj.write(epsg)
    prj.close()    
    
    #physiocap_log( u"Fin contour moyenne :")
    return 0     
                    

def physiocap_moyenne_InterParcelles( self):
    """Verification et requete spatiale"""
    physiocap_log( u"== Début du calcul des moyennes à partir de vos contours" )

    # QT Confiance
    repertoire_data = self.lineEditDirectoryPhysiocap.text()
    # Attention peut être non renseigné repertoire_projet = self.lineEditDernierProjet.text()
    if ((repertoire_data == "") or ( not os.path.exists( repertoire_data))):
        aText = self.trUtf8( "Pas de répertoire de données brutes spécifié" )
        physiocap_error( aText)
        return physiocap_message_box( self, aText, "information")
            
    details = "NO"
    if self.checkBoxInfoVignoble.isChecked():
        details = "YES"
    
    # Récupérer des styles pour chaque shape dans Affichage
    #dir_template = os.path.join( os.path.dirname(__file__), 'modeleQgis')       
    dir_template = self.fieldComboThematiques.currentText()
    qml_is = str( self.lineEditThematiqueInterMoyenne.text().strip('"')) + EXTENSION_QML
    le_template_moyenne = os.path.join( dir_template, qml_is)
    qml_is = str( self.lineEditThematiqueInterPoints.text().strip('"')) + EXTENSION_QML
    le_template_point = os.path.join( dir_template, qml_is)
   
    # Pour polygone de contour   
    nom_complet_poly = self.comboBoxPolygone.currentText().split( SEPARATEUR_NOEUD)
    if ( len( nom_complet_poly) != 2):
        aText = self.trUtf8( "Le polygone de contour n'est pas choisi. " +
          "Avez-vous ouvert votre shapefile de contour ?")
        physiocap_error( aText)
        return physiocap_message_box( self, aText)           
    nom_poly = nom_complet_poly[ 0] 
    id_poly = nom_complet_poly[ 1] 
    vecteur_poly = physiocap_get_layer_by_ID( id_poly)

    leChampPoly = self.fieldComboContours.currentText()
    #physiocap_log( u"Champ Poly " + str( leChampPoly))
        
    # Pour les points
    nom_complet_point = self.comboBoxPoints.currentText().split( SEPARATEUR_NOEUD)
    if ( len( nom_complet_point) != 2):
        physiocap_error( u"Le shape de points n'est pas choisi. " +
          "Lancez le traitement initial - bouton OK - avant de faire votre"  +
          "calcul de Moyenne Inter Parcellaire")
        return physiocap_message_box( self,
            self.trUtf8( "Le shape de points n'est pas choisi. " +
                "Lancez le traitement initial - bouton OK - avant de faire votre " +
                "calcul de Moyenne Inter Parcellaire" ),
            "information")
    nom_noeud_arbre = nom_complet_point[ 0] 
    id_point = nom_complet_point[ 1] 
    vecteur_point = physiocap_get_layer_by_ID( id_point)

    # Verification de l'arbre
    root = QgsProject.instance().layerTreeRoot( )
    un_groupe = root.findGroup( nom_noeud_arbre)
    if ( not isinstance( un_groupe, QgsLayerTreeGroup)):
        physiocap_error( u"Le projet " + nom_noeud_arbre + " n'existe pas " +
            "Lancez le traitement initial - bouton OK - avant de faire votre" +
            "calcul de Moyenne Inter Parcellaire" )
        return physiocap_message_box( self,
            self.trUtf8( "Le projet " + nom_noeud_arbre + " n'existe pas " +
            "Lancez le traitement initial - bouton OK - avant de faire votre" +
            "calcul de Moyenne Inter Parcellaire" ),
            "information")            

    # Vérification 
    if ( vecteur_point == None):
        physiocap_error( u"Le jeu de points choisi n'est pas valide. " +
          "Lancez le traitement initial - bouton OK - avant de faire votre " +
          "calcul de Moyenne Inter Parcellaire")
        return physiocap_message_box( self,
            self.trUtf8( "Le jeu de points choisi n'est pas valide. " +
                "Lancez le traitement initial - bouton OK - avant de faire votre " +
                "calcul de Moyenne Inter Parcellaire" ),
            "information")    

    if ( vecteur_poly == None) or ( not vecteur_poly.isValid()):
        physiocap_error( u"Le contour choisi n'est pas valide. " +
          "Lancez le traitement initial - bouton OK - avant de faire votre " +
          "calcul de Moyenne Inter Parcellaire")
        return physiocap_message_box( self,
            self.trUtf8( "Le contour choisi n'est pas valide. " +
                "Lancez le traitement initial - bouton OK - avant de faire votre " +
                "calcul de Moyenne Inter Parcellaire" ),
            "information")
            
    # Verifier SRCs sont les même
    crs_poly = vecteur_poly.crs().authid()
    crs_point = vecteur_point.crs().authid()
    if ( crs_poly != crs_point):
        mes = "Les projections (Crs) des coutours et mesures brutes sont différentes !"
        physiocap_error( mes)
        return physiocap_message_box( self, self.trUtf8( mes),"information")
                
    laProjection, EXT_CRS_SHP, EXT_CRS_PRJ, EXT_CRS_RASTER, EPSG_NUMBER = \
        physiocap_quelle_projection_demandee(self)
    crs = QgsCoordinateReferenceSystem( EPSG_NUMBER, QgsCoordinateReferenceSystem.PostgisCrsId)

    # Verification du repertoire shape
    pro = vecteur_point.dataProvider() 
    if ( pro.name() == POSTGRES_NOM):
        # On construit le chemin depuis data/projet...
        chemin_projet = os.path.join( repertoire_data, nom_noeud_arbre)
        chemin_shapes = os.path.join( chemin_projet, REPERTOIRE_SHAPEFILE)
    else:
        # Assert repertoire shapfile : c'est le repertoire qui contient le vecteur point
        chemin_shapes = os.path.dirname( unicode( vecteur_point.dataProvider().dataSourceUri() ) ) ;
    if ( not os.path.exists( chemin_shapes)):
        raise physiocap_exception_rep( chemin_shapes)
    
    #physiocap_log ( u"======= là c'est OK >> ")
        
    # On passe sur les differents contours
    id = 0
    contour_avec_point = 0
    les_geoms_poly = []
    les_parcelles = []
    les_parcelles_ID = []
    les_dates_parcelle = []
    les_heures_parcelle = []
    les_moyennes_vitesse = []
    les_moyennes_sarment = []
    les_moyennes_diametre = []
    les_moyennes_biom = []
    les_moyennes_biomgm2 = []


    for un_contour in vecteur_poly.getFeatures(): #iterate poly features
        id = id + 1
        try:
            un_nom = str( un_contour[ leChampPoly]) #get attribute of poly layer
        except:
            un_nom = "PHY_ID_" + str(id)
            pass
        
        physiocap_log ( u"======= Inter >> ")
        physiocap_log ( self.trUtf8( "== Contour : %s" % ( str( un_nom))))
        
        un_autre_ID = "PHY_ID" + str(id)
        geom_poly = un_contour.geometry() #get geometry of poly layer
        
        # Todo : WT DATA BUG contour :  test validé geom_poly
        
        #physiocap_log ( "Dans polygone geom multipart : " + str(geom_poly.wkbType()))
        if geom_poly.wkbType() == QGis.WKBPolygon:
            physiocap_log ( "== Polygone simple: " + un_nom)
        elif geom_poly.wkbType() == QGis.WKBMultiPolygon:
            physiocap_log ( "== Polygone multiple: " + un_nom)
        else:
            aText = self.trUtf8( "== Cette forme n'est pas un polygone : %s" % ( str(un_nom)))
            physiocap_log ( aText)
            physiocap_error ( aText)
            physiocap_message_box( self, aText, "information")
            continue
        
        # on initialise pour ce contour
        les_geom_point_feat = []
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
        # Préfiltre dans un rectangle
        # Récupération des entites qui concerne ce coutours
        for un_point in vecteur_point.getFeatures(QgsFeatureRequest().
                        setFilterRect(geom_poly.boundingBox())):
            # un_point est un feature ! 
            if un_point.geometry().within(geom_poly):
                # Cas du premier point d'un contour 
                if i == 0:
                    contour_avec_point = contour_avec_point + 1
                i = i + 1
                #physiocap_log ( "== Dans un point : " + str(i))
                try:
                    if i == 2:
                        # Attraper date début
                        date_debut = un_point["DATE"]
                    les_geom_point_feat.append( un_point.geometry().asPoint())
                    les_dates.append( un_point["DATE"])
                    les_GID.append( un_point["GID"])
                    les_vitesses.append( un_point["VITESSE"])
                    les_sarments.append( un_point["NBSARM"])
                    les_diametres.append( un_point["DIAM"])
                    les_biom.append( un_point["BIOM"])
                    if ( details == "YES"):
                        try:
                            les_biomgm2.append( un_point["BIOMGM2"])
                        except KeyError:
                            # Se remettre en détails non
                            details = "NO"
                except KeyError:
                    raise physiocap_exception_points_invalid( un_nom) 
                        
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
            physiocap_log ( self.trUtf8( "== Date : %s" % (str(date_debut)))) 
            physiocap_log ( self.trUtf8( "== Moyenne des sarments : %s" % (str(moyenne_sar))))
            physiocap_log ( self.trUtf8( "== Moyenne des diamètres : %s" % (str(moyenne_dia))))
            physiocap_log ( u"======= Inter << ")
            #physiocap_log( u"Fin du calcul des moyennes à partir de vos contours" )

            # ###################
            # CRÉATION groupe INTER _ PROJET
            # ###################
            if ( contour_avec_point == 1):
                if un_groupe != None:
                    vignette_projet = nom_noeud_arbre + SEPARATEUR_ + VIGNETTES_INTER  
                    vignette_existante = un_groupe.findGroup( vignette_projet)
                    if ( vignette_existante == None ):
                        vignette_group_inter = un_groupe.addGroup( vignette_projet)
                    else:
                        # Si vignette preexiste, on ne recommence pas
                        raise physiocap_exception_vignette_exists( nom_noeud_arbre) 
                    
                chemin_vignettes = os.path.join( chemin_shapes, VIGNETTES_INTER)
                if not (os.path.exists( chemin_vignettes)):
                    try:
                        os.mkdir( chemin_vignettes)
                    except:
                        raise physiocap_exception_rep( VIGNETTES_INTER)

            
            # Création du Shape moyenne et prj
            # vignette - nom_noeud_arbre + SEPARATEUR_
            nom_court_vignette = nom_noeud_arbre + NOM_MOYENNE + un_nom +  EXT_CRS_SHP     
            nom_court_prj = nom_noeud_arbre + NOM_MOYENNE + un_nom  + EXT_CRS_PRJ     
            #physiocap_log( u"== Vignette court : " + nom_court_vignette )       
            nom_vignette = physiocap_rename_existing_file( os.path.join( chemin_vignettes, nom_court_vignette))        
            nom_prj = physiocap_rename_existing_file( os.path.join( chemin_vignettes, nom_court_prj))        
            physiocap_moyenne_vers_vignette( crs, EPSG_NUMBER, nom_vignette, nom_prj, 
                geom_poly, un_nom, un_autre_ID, date_debut, heure_fin,
                moyenne_vitesse, moyenne_sar, moyenne_dia, moyenne_biom, 
                moyenne_biomgm2, details)
                                        
            # Memorisation de la parcelle du contour et des moyennes
            les_geoms_poly.append( geom_poly.asPolygon())
            les_parcelles.append( un_nom)
            les_parcelles_ID.append( un_autre_ID)
            les_dates_parcelle.append( date_debut)
            les_heures_parcelle.append( heure_fin)
            les_moyennes_vitesse.append( moyenne_vitesse)
            les_moyennes_sarment.append( moyenne_sar)
            les_moyennes_diametre.append( moyenne_dia)
            les_moyennes_biom.append( moyenne_biom)
            les_moyennes_biomgm2.append( moyenne_biomgm2)
            
            
            # ###################
            # CRÉATION point
            # ###################
            # point 
            nom_court_point = nom_noeud_arbre + NOM_POINTS + SEPARATEUR_ + un_nom + EXT_CRS_SHP     
            nom_court_point_prj = nom_noeud_arbre + NOM_POINTS + SEPARATEUR_ + un_nom + EXT_CRS_PRJ     
            #physiocap_log( u"== Vignette court : " + nom_court_vignette )       
            nom_point = physiocap_rename_existing_file( os.path.join( chemin_vignettes, nom_court_point))        
            nom_point_prj = physiocap_rename_existing_file( os.path.join( chemin_vignettes, nom_court_point_prj))        
            
            physiocap_moyenne_vers_point( crs, EPSG_NUMBER, nom_point, nom_point_prj, 
                les_geom_point_feat, les_GID, les_dates, 
                les_vitesses, les_sarments, les_diametres, les_biom, 
                les_biomgm2, details)
            
            # Affichage dans arbre "vignettes" selon les chack dans onglet Affichage
            SHAPE_MOYENNE_PAR_CONTOUR = "NO"
            if self.checkBoxInterMoyennes.isChecked():
                SHAPE_MOYENNE_PAR_CONTOUR = "YES"
            SHAPE_POINTS_PAR_CONTOUR = "NO"
            if self.checkBoxInterPoints.isChecked():
                SHAPE_POINTS_PAR_CONTOUR = "YES"
                                                
            if SHAPE_MOYENNE_PAR_CONTOUR == "YES":
                vignette_vector = QgsVectorLayer( nom_vignette, nom_court_vignette, 'ogr')
            if SHAPE_POINTS_PAR_CONTOUR == "YES":
                points_vector = QgsVectorLayer( nom_point, nom_court_point, 'ogr')
            if vignette_group_inter != None:
                if SHAPE_MOYENNE_PAR_CONTOUR == "YES":
                    QgsMapLayerRegistry.instance().addMapLayer( vignette_vector, False)
                    vector_node = vignette_group_inter.addLayer( vignette_vector)
                if SHAPE_POINTS_PAR_CONTOUR == "YES":
                    QgsMapLayerRegistry.instance().addMapLayer( points_vector, False)
                # Ajouter le vecteur dans un groupe
                    vector_point_node = vignette_group_inter.addLayer( points_vector)
            else:
                # Pas de vignette ...
                if SHAPE_MOYENNE_PAR_CONTOUR == "YES":
                    QgsMapLayerRegistry.instance().addMapLayer( vignette_vector)
                if SHAPE_POINTS_PAR_CONTOUR == "YES":
                    QgsMapLayerRegistry.instance().addMapLayer( points_vector)
            # Mise en action du template
            if SHAPE_MOYENNE_PAR_CONTOUR == "YES":
                if ( os.path.exists( le_template_moyenne)):
                    vignette_vector.loadNamedStyle( le_template_moyenne)                                
            if SHAPE_POINTS_PAR_CONTOUR == "YES":
                if ( os.path.exists( le_template_point)):
                    points_vector.loadNamedStyle( le_template_point)
               
        else:
            physiocap_log( self.trUtf8( "== Aucune point dans %s. Pas de comparaison \
                inter parcellaire" % ( str(un_nom))))       
    
    if ( contour_avec_point == 0):
        return physiocap_message_box( self, 
                self.trUtf8( "== Aucun point dans vos contours : pas de comparaison inter parcellaire"),
                "information")
    else:
        
        # On a des parcelles dans le contour avec des moyennes
        nom_court_du_contour = os.path.basename( vecteur_poly.name() + EXTENSION_SHP)
        # Inserer "MOYENNES"
        nom_court_du_contour_moyenne = nom_noeud_arbre + NOM_MOYENNE + nom_court_du_contour
        nom_court_du_contour_moyenne_prj = nom_court_du_contour_moyenne [:-4] + EXT_CRS_PRJ[ -4:]     
        nom_contour_moyenne = physiocap_rename_existing_file( 
        os.path.join( chemin_vignettes, nom_court_du_contour_moyenne))        
        nom_contour_moyenne_prj = physiocap_rename_existing_file( 
            os.path.join( chemin_vignettes, nom_court_du_contour_moyenne_prj)) 
        
        physiocap_moyenne_vers_contour( crs, EPSG_NUMBER, nom_contour_moyenne, nom_contour_moyenne_prj, 
            les_geoms_poly, les_parcelles, les_parcelles_ID, les_dates_parcelle,  les_heures_parcelle,
            les_moyennes_vitesse, les_moyennes_sarment, les_moyennes_diametre, les_moyennes_biom, 
                les_moyennes_biomgm2, details) 
                
        # Affichage du resultat
        nom_court_affichage = nom_noeud_arbre + SEPARATEUR_
        SHAPE_A_AFFICHER = []
        if self.checkBoxInterDiametre.isChecked():
            nom_affichage = nom_court_affichage + 'DIAMETRE' + SEPARATEUR_ + nom_court_du_contour
            qml_is = str( self.lineEditThematiqueInterDiametre.text().strip('"')) + EXTENSION_QML
            SHAPE_A_AFFICHER.append( (nom_affichage, qml_is))
        if self.checkBoxInterBiomasse.isChecked():
            nom_affichage = nom_court_affichage + 'BIOMASSE' + SEPARATEUR_ + nom_court_du_contour
            qml_is = str( self.lineEditThematiqueInterBiomasse.text().strip('"')) + EXTENSION_QML
            SHAPE_A_AFFICHER.append( (nom_affichage, qml_is))
        if self.checkBoxInterLibelle.isChecked():
            nom_affichage = nom_court_affichage + 'LIBELLE' + SEPARATEUR_ + nom_court_du_contour
            qml_is = str( self.lineEditThematiqueInterLibelle.text().strip('"')) + EXTENSION_QML
            SHAPE_A_AFFICHER.append( (nom_affichage, qml_is))

        # Afficher ce contour_moyennes dans arbre "projet"
        k=0
        for titre, unTemplate in SHAPE_A_AFFICHER:
            vector = QgsVectorLayer( nom_contour_moyenne, titre, 'ogr')
           # On se positionne dans l'arbre
            if vignette_group_inter != None:
                QgsMapLayerRegistry.instance().addMapLayer( vector, False)
                vector_node = vignette_group_inter.addLayer( vector)
            else:
                QgsMapLayerRegistry.instance().addMapLayer( vector)
                
            le_template = os.path.join( dir_template, unTemplate)
            if ( os.path.exists( le_template)):
                #physiocap_log ( u"Physiocap le template : " + os.path.basename( leTemplate) )
                vector.loadNamedStyle( le_template)  

    return physiocap_message_box( self, 
                    self.trUtf8( "Fin du traitement inter-parcellaire"),
                    "information")
      