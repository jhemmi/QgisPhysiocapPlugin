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
def physiocap_creer_donnees_resultats( self, laProjection, EXT_CRS_SHP, EXT_CRS_PRJ,
    details = "NO", histogrammes = "NO", recursif = "NO"):
    """ Récupération des paramètres saisies et 
    creation de l'arbre "source" "texte" et du fichier "resultats"
    Ce sont les résultats de l'analyse filtration des données brutes"""
    
    # Récupérer les paramètres saisies
    REPERTOIRE_DONNEES_BRUTES = self.lineEditDirectoryPhysiocap.text()
    NOM_PROJET = self.lineEditProjet.text()
    mindiam = float( self.spinBoxMinDiametre.value())
    maxdiam = float( self.spinBoxMaxDiametre.value())
    max_sarments_metre = float( self.spinBoxMaxSarmentsParMetre.value())
    physiocap_log(u"Paramètres choisis min diametre : " + str(mindiam) + " max diametre : " + str(maxdiam))

    if details == "YES":
        interrangs = float( self.spinBoxInterrangs.value())
        interceps = float( self.spinBoxInterceps.value())
        hauteur = float( self.spinBoxHauteur.value())
        densite = float( self.doubleSpinBoxDensite.value())
        leCepage = self.fieldComboCepage.currentText()
        laTaille = self.fieldComboTaille.currentText()
        
    # Vérification de l'existance ou création du répertoire projet
    chemin_projet = os.path.join(REPERTOIRE_DONNEES_BRUTES, NOM_PROJET)
    #physiocap_log(u"Repertoire projet : " + str(chemin_projet))
    if not (os.path.exists( chemin_projet)):
        try:
            os.mkdir( chemin_projet)
        except:
            raise physiocap_exception_rep( NOM_PROJET)
    else:
        # Le répertoire existant est renommé en (+1)
        try: 
            chemin_projet = physiocap_rename_create_dir( chemin_projet)
        except:
            physiocap_log( "Erreur dans fonction creer_donnees_resultats ==" + chemin_projet)
            raise physiocap_exception_rep( chemin_projet)
    
    
    # Stocker dans la fenetre de synthese le nom du projet
    chemin_base_projet = os.path.basename( chemin_projet)
    self.lineEditDernierProjet.setText( chemin_base_projet)
    self.settings= QSettings( PHYSIOCAP_NOM, PHYSIOCAP_NOM)
    self.settings.value("Physiocap/dernier_repertoire", chemin_base_projet) 
    
    # Progress BAR 2 %
    self.progressBar.setValue( 2)
    
        
    # Verification de l'existance ou création du répertoire des sources MID et fichier csv
    chemin_sources = os.path.join(chemin_projet, REPERTOIRE_SOURCES)
    if not (os.path.exists( chemin_sources)):
        try:
            os.mkdir( chemin_sources)
        except:
            raise physiocap_exception_rep( REPERTOIRE_SOURCES)
                
    # Fichier de concaténations CSV des résultats bruts        
    nom_court_csv_concat = NOM_PROJET + SUFFIXE_BRUT_CSV
    try:
        nom_csv_concat, csv_concat = physiocap_open_file( nom_court_csv_concat, chemin_sources, "w")
    except physiocap_exception_fic as e:
        raise physiocap_exception_csv( nom_court_csv_concat)
        
    # Création du fichier concaténé
    nom_fichiers_recherches = os.path.join(REPERTOIRE_DONNEES_BRUTES, EXTENSION_MID)
    
    # Assert le nombre de MID > 0
    # le Tri pour retomber dans l'ordre de Physiocap_V8
    if ( recursif == "YES"):
        # On appelle la fonction de recherche récursive
        listeTriee = physiocap_look_for_MID( REPERTOIRE_DONNEES_BRUTES, "YES", REPERTOIRE_SOURCES)
    else:
        # Non recursif
        listeTriee = sorted(glob.glob( nom_fichiers_recherches))

    if len( listeTriee) == 0:
        raise physiocap_exception_no_mid()
    
    # Verification si plus de 10 MIDs
    if len( listeTriee) >= 15:
        # Beaucoup de MIDs Poser une question si cancel, on stoppe
        uMsg =u"Plus de 15 fichier MIDs sont à analyser. Temps de traitement > à 1 minute. Voulez-vous continuer ?"
        if ( physiocap_question_box( self, uMsg)):
            pass
        else:
            # Arret demandé
            raise physiocap_exception_stop_user()
        
    for mid in listeTriee:
        try:
            shutil.copyfileobj(open(mid, "r"), csv_concat)
            # et copie des MID
            nom_cible = os.path.join( chemin_sources, os.path.basename(mid))
            if os.path.exists( nom_cible):
                nouveau_long = physiocap_rename_existing_file( nom_cible)
                shutil.copyfile( mid, nouveau_long)
            else:
                shutil.copy( mid, chemin_sources)
        except:
            raise physiocap_exception_mid( mid)
    csv_concat.close()

    # Assert le fichier de données n'est pas vide
    if os.path.getsize( nom_csv_concat ) == 0 :
        uMsg =u"Le fichier " + nom_court_csv_concat + u" a une taille nulle !"
        physiocap_message_box( self, uMsg)
        return physiocap_error( uMsg)
    
    # Création la première partie du fichier de synthèse
    fichier_resultat_analyse = chemin_base_projet + SEPARATEUR_ + FICHIER_RESULTAT
    nom_fichier_synthese, fichier_synthese = physiocap_open_file( fichier_resultat_analyse, chemin_projet , "w")
    fichier_synthese.write( "SYNTHESE PHYSIOCAP\n\n")
    fichier_synthese.write( "Générée le : ")
    a_time = time.strftime( "%d/%m/%y %H:%M\n",time.localtime())
    fichier_synthese.write( a_time)
    fichier_synthese.write( "Répertoire de base ")
    fichier_synthese.write( chemin_base_projet + "\n")
    fichier_synthese.write( "Nom des MID \t\t Date et heures\n=>Nb. Valeurs brutes\tVitesse km/h")
    if (CENTROIDES == "YES"):
        fichier_synthese.write("\nCentroïdes")
    fichier_synthese.write("\n")
    info_mid = physiocap_list_MID( REPERTOIRE_DONNEES_BRUTES, listeTriee)
    for all_info in info_mid:
        info = all_info.split(";")
        fichier_synthese.write( str(info[0]) + "\t" + str(info[1]) + "->" + str(info[2])+ "\n")
        fichier_synthese.write( "=>\t" +str(info[3]) + "\t" + str(info[4]))
        if (CENTROIDES == "YES"):
            # Centroides
            fichier_synthese.write( "\n" + str(info[5]) + "--" + str(info[6]))
        fichier_synthese.write("\n")
##        nom_mid = ""
##        for fichier_mid in listeTriee:
##            nom_mid = nom_mid + os.path.basename( fichier_mid) + " & "
##        fichier_synthese.write("Liste des fichiers MID : " + nom_mid[:-3] + "\n")
##        physiocap_log( "Liste des MID : " + nom_mid[:-3])
   
    # Progress BAR 5 %
    self.progressBar.setValue( 5)
    physiocap_log ( u"Fin de la création csv et début de synthèse")
   
    # Verification de l'existance ou création du répertoire textes
    chemin_textes = os.path.join(chemin_projet, REPERTOIRE_TEXTES)
    if not (os.path.exists( chemin_textes)):
        try :
            os.mkdir( chemin_textes)
        except :
            raise physiocap_exception_rep( REPERTOIRE_TEXTES)
                   
    # Ouverture du fichier des diamètres     
    nom_court_fichier_diametre = "diam" + SUFFIXE_BRUT_CSV
    nom_data_histo_diametre, data_histo_diametre = physiocap_open_file( nom_court_fichier_diametre, 
        chemin_textes)
    
    # Appel fonction de creation de fichier
    nom_court_fichier_sarment = "nbsarm" + SUFFIXE_BRUT_CSV
    nom_data_histo_sarment, data_histo_sarment = physiocap_open_file( nom_court_fichier_sarment, 
        chemin_textes)

    # Todo: V1.5 ? Supprimer le fichier erreur
    nom_fichier_erreur, erreur = physiocap_open_file( "erreurs.csv" , chemin_textes)

    # ouverture du fichier source
    csv_concat = open(nom_csv_concat, "r")
    # Appeler la fonction de vérification du format du fichier csv
    # Si plus de 20 % d'erreur exception est monté
    try:
        pourcentage_erreurs = physiocap_assert_csv( csv_concat, erreur)
        if ( pourcentage_erreurs > TAUX_LIGNES_ERREUR):
            fichier_synthese.write("\nTrop d'erreurs dans les données brutes")
            # Todo : question selon le taux de lignes en erreur autorisées
            #raise physiocap_exception_err_csv( pourcentage_erreurs)
    except:
        raise

    # Progress BAR 10 %
    self.progressBar.setValue( 10)        
    fichier_synthese.write("\n\nPARAMETRES SAISIS ")
    
    if os.path.getsize( nom_csv_concat ) == 0 :
        uMsg =u"Le fichier " + nom_court_csv_concat + u" a une taille nulle !"
        physiocap_message_box( self, uMsg)
        return physiocap_error( uMsg)

    # ouverture du fichier source
    csv_concat = open(nom_csv_concat, "r")

    # Appeler la fonction de traitement
    if histogrammes == "YES":
        #################
        physiocap_fichier_histo( csv_concat, data_histo_diametre,    
                    data_histo_sarment, erreur)
        #################
        # Fermerture des fichiers
        data_histo_diametre.close()
        data_histo_sarment.close()
    csv_concat.close()
    erreur.close()
    
    # Progress BAR 12 %
    self.progressBar.setValue( 12)
    
    # Verification de l'existance 
    chemin_histos = os.path.join(chemin_projet, REPERTOIRE_HISTOS)
    if not (os.path.exists( chemin_histos)):
        try:
            os.mkdir( chemin_histos)
        except:
            raise physiocap_exception_rep( REPERTOIRE_HISTOS)

    if histogrammes == "YES":
        # creation d'un histo
        nom_data_histo_sarment, data_histo_sarment = physiocap_open_file( nom_court_fichier_sarment, chemin_textes, 'r')
        nom_histo_sarment, histo_sarment = physiocap_open_file( FICHIER_HISTO_SARMENT, chemin_histos)
        name = nom_histo_sarment
        physiocap_tracer_histo( data_histo_sarment, name, 0, 50, "SARMENT au m", "FREQUENCE en %", "HISTOGRAMME NBSARM AVANT TRAITEMENT")
        histo_sarment.close()
        
        nom_data_histo_diametre, data_histo_diametre = physiocap_open_file( nom_court_fichier_diametre, chemin_textes, 'r')
        nom_histo_diametre, histo_diametre = physiocap_open_file( FICHIER_HISTO_DIAMETRE, chemin_histos)
        name = nom_histo_diametre
        physiocap_tracer_histo( data_histo_diametre, name, 0, 30, "DIAMETRE en mm", "FREQUENCE en %", "HISTOGRAMME DIAMETRE AVANT TRAITEMENT")
        histo_diametre.close()        
        
        physiocap_log ( u"Fin de la création des histogrammes bruts")
    else:
        physiocap_log ( u"Pas de création des histogrammes")

    # Progress BAR 15 %
    self.progressBar.setValue( 15) 
              
    # Création des csv
    nom_court_csv_sans_0 = NOM_PROJET + SEPARATEUR_ + "OUT.csv"
    nom_csv_sans_0, csv_sans_0 = physiocap_open_file( 
        nom_court_csv_sans_0, chemin_textes)

    nom_court_csv_avec_0 = NOM_PROJET + SEPARATEUR_ + "OUT0.csv"
    nom_csv_avec_0, csv_avec_0 = physiocap_open_file( 
        nom_court_csv_avec_0, chemin_textes)
   
    nom_court_fichier_diametre_filtre = "diam_FILTERED.csv"
    nom_fichier_diametre_filtre, diametre_filtre = physiocap_open_file( 
        nom_court_fichier_diametre_filtre, chemin_textes )

    # Ouverture du fichier source et re ouverture du ficheir erreur
    csv_concat = open(nom_csv_concat, "r")       
    erreur = open(nom_fichier_erreur,"a")

    # Filtrage des données Physiocap
    #################
    if details == "NO":
        interrangs = 1
        interceps = 1 
        densite = 1
        hauteur = 1        
    retour_filtre = physiocap_filtrer( self, csv_concat, csv_sans_0, csv_avec_0, \
                diametre_filtre, nom_fichier_synthese, erreur, \
                mindiam, maxdiam, max_sarments_metre, details,
                interrangs, interceps, densite, hauteur)
    #################
    # Fermeture du fichier destination
    csv_sans_0.close()
    csv_avec_0.close()
    diametre_filtre.close()
    erreur.close()
    # Fermerture du fichier source
    csv_concat.close()  

    # Todo : V1.5 ? Gerer cette erreur par exception
    if retour_filtre != 0:
        return physiocap_error(u"Erreur bloquante : problème lors du filtrage des données de : " + 
                nom_court_csv_concat)  

    # Progress BAR 60 %
    self.progressBar.setValue( 41)

    if histogrammes == "YES":
        # Histo apres filtatration
        nom_fichier_diametre_filtre, diametre_filtre = physiocap_open_file( 
            nom_court_fichier_diametre_filtre, chemin_textes , "r")
        nom_histo_diametre_filtre, histo_diametre = physiocap_open_file( FICHIER_HISTO_DIAMETRE_FILTRE, chemin_histos)

        physiocap_tracer_histo( diametre_filtre, nom_histo_diametre_filtre, 0, 30, "DIAMETRE en mm", "FREQUENCE en %", "HISTOGRAMME DIAMETRE APRES TRAITEMENT")
        diametre_filtre.close()        
                                          
    # On écrit dans le fichiers résultats les paramètres du modéle
    fichier_synthese = open(nom_fichier_synthese, "a")
    if details == "NO":
        fichier_synthese.write("\nAucune information parcellaire saisie\n")
    else:
        fichier_synthese.write("\n")
        msg = "Cépage : " + str( leCepage) + "\n"
        fichier_synthese.write( msg)
        fichier_synthese.write("Type de taille : %s\n" %laTaille)        
        fichier_synthese.write("Hauteur de végétation : %s cm\n" %hauteur)
        fichier_synthese.write("Densité des bois de taille : %s \n" %densite)
        fichier_synthese.write("Ecartement entre rangs : %s cm\n" %interrangs)
        fichier_synthese.write("Ecartement entre ceps : %s cm\n" %interceps)        

    fichier_synthese.write("\n")
    fichier_synthese.write("Nombre de sarments max au mètre linéaire: %s \n" %max_sarments_metre)
    fichier_synthese.write("Diamètre minimal : %s mm\n" %mindiam)
    fichier_synthese.write("Diamètre maximal : %s mm\n" %maxdiam)
    fichier_synthese.close()

    # Progress BAR 42%
    self.progressBar.setValue( 42)
    
    # Verification de l'existance ou création du répertoire des sources MID et fichier csv
    chemin_shapes = os.path.join(chemin_projet, REPERTOIRE_SHAPEFILE)
    if not (os.path.exists( chemin_shapes)):
        try :
            os.mkdir( chemin_shapes)
        except :
            raise physiocap_exception_rep( REPERTOIRE_SHAPEFILE)

    # Création des shapes sans 0
    nom_court_shape_sans_0 = NOM_PROJET + NOM_POINTS + EXT_CRS_SHP
    nom_shape_sans_0 = os.path.join(chemin_shapes, nom_court_shape_sans_0)
    nom_court_prj_sans_0 = NOM_PROJET + NOM_POINTS + EXT_CRS_PRJ
    nom_prj_sans_0 = os.path.join(chemin_shapes, nom_court_prj_sans_0)

        
    # Si le shape existe dejà il faut le détruire
    if os.path.isfile( nom_shape_sans_0):
        physiocap_log ( u"Le shape file existant déjà, il est détruit.")
        os.remove( nom_shape_sans_0)            

    # cas sans 0, on demande la synthese en passant le nom du fichier
    retour = physiocap_csv_vers_shapefile( self, 45, nom_csv_sans_0, nom_shape_sans_0, nom_prj_sans_0, 
            laProjection,
            nom_fichier_synthese, details)
    if retour != 0:
        return physiocap_error(u"Erreur bloquante : problème lors de la création du shapefile : " + 
            nom_court_shape_sans_0)                

    # Progress BAR 65 %
    self.progressBar.setValue( 65)
            
    # Création des shapes avec 0
    nom_court_shape_avec_0 = NOM_PROJET + NOM_POINTS + EXTENSION_POUR_ZERO + EXT_CRS_SHP
    nom_shape_avec_0 = os.path.join(chemin_shapes, nom_court_shape_avec_0)
    nom_court_prj_avec_0 = NOM_PROJET + NOM_POINTS + EXTENSION_POUR_ZERO + EXT_CRS_PRJ
    nom_prj_avec_0 = os.path.join(chemin_shapes, nom_court_prj_avec_0)
    # Si le shape existe dejà il faut le détruire
    if os.path.isfile( nom_shape_avec_0):
        physiocap_log ( u"Le shape file existant déjà, il est détruit.")
        os.remove( nom_shape_avec_0) 
        
    # cas avec 0, pas de demande de synthese
    retour = physiocap_csv_vers_shapefile( self, 65, nom_csv_avec_0, nom_shape_avec_0, nom_prj_avec_0, laProjection,
        "NO", details)
    if retour != 0:
        return physiocap_error(u"Erreur bloquante : problème lors de la création du shapefile : " + 
                nom_court_shape_avec_0) 
                          
    # Progress BAR 95%
    self.progressBar.setValue( 95)
    
    # Creer un groupe pour cette analyse
    # Attention il faut qgis > 2.4 metadata demande V2.4 mini
    root = QgsProject.instance().layerTreeRoot( )
    # Nommmer le groupe chemin_base_projet
    sous_groupe = root.addGroup( chemin_base_projet)
    
    # Récupérer des styles pour chaque shape
    #dir_template = os.path.join( os.path.dirname(__file__), 'modeleQgis')       
    dir_template = self.fieldComboThematiques.currentText()
    # Affichage des différents shapes dans Qgis
    SHAPE_A_AFFICHER = []
    qml_is = ""
    if self.checkBoxDiametre.isChecked():
        qml_is = str( self.lineEditThematiqueDiametre.text()) + EXTENSION_QML
        SHAPE_A_AFFICHER.append( (nom_shape_sans_0, 'DIAMETRE', qml_is))
    if self.checkBoxSarment.isChecked():
        qml_is = str( self.lineEditThematiqueSarment.text()) + EXTENSION_QML
        SHAPE_A_AFFICHER.append( (nom_shape_sans_0, 'SARMENT', qml_is))
    if self.checkBoxVitesse.isChecked():
        qml_is = str( self.lineEditThematiqueVitesse.text()) + EXTENSION_QML
        SHAPE_A_AFFICHER.append( (nom_shape_avec_0, 'VITESSE', qml_is))
    
    for shapename, titre, unTemplate in SHAPE_A_AFFICHER:
        vector = QgsVectorLayer( shapename, titre, 'ogr')
        if (self.fieldComboFormats.currentText() == "ESRI Shapefile" ):
            vector = QgsVectorLayer( shapename, titre, 'ogr')
        elif (self.fieldComboFormats.currentText() == POSTGRES_NOM ):
            uri_nom = physiocap_quel_uriname( self)
            #physiocap_log( u"URI nom : " + str( uri_nom))
            uri_modele = physiocap_get_uri_by_layer( self, uri_nom )
            if uri_modele != None:
                uri_connect, uri_deb, uri_srid, uri_fin = physiocap_tester_uri( self, uri_modele, "YES")            
                nom_court_shp = os.path.basename( shapename)
                #TABLES = "public." + nom_court_shp
                uri = uri_deb +  uri_srid + \
                   " key='gid' type='POINTS' table=" + nom_court_shp[ :-4] + " (geom) sql="            
##              "dbname='testpostgis' host='localhost' port='5432'" + \
##              " user='postgres' password='postgres' SRID='2154'" + \
##              " key='gid' type='POINTS' table=" + nom_court_shp[ :-4] + " (geom) sql="
                #physiocap_log ( "Affichage POSTGRES : >>" + uri + "<<")
                vector = QgsVectorLayer( uri, titre, POSTGRES_NOM)
            else:
                aText = u"Pas de connecteur vers Postgres : " + \
                        str( uri_nom) + \
                        u". On continue avec des shapefiles"
                physiocap_log( aText)
                vector = QgsVectorLayer( shapename, titre, 'ogr')
                # Remettre le choix vers ESRI shape file
                self.fieldComboFormats.setCurrentIndex( 0)  
        else:
            physiocap_error ( u"Physiocap est étrange. C'est bizarre")            
            continue
            
        QgsMapLayerRegistry.instance().addMapLayer( vector, False)
        # Ajouter le vecteur dans un groupe
        vector_node = sous_groupe.addLayer( vector)
        le_template = os.path.join( dir_template, unTemplate)
        if ( os.path.exists( le_template)):
            #physiocap_log ( u"Physiocap le template : " + os.path.basename( leTemplate) )
            vector.loadNamedStyle( le_template)
    
    # Fichier de synthese dans la fenetre resultats   
    fichier_synthese = open(nom_fichier_synthese, "r")
    while True :
        ligne = fichier_synthese.readline() # lit les lignes 1 à 1
        physiocap_write_in_synthese( self, ligne)
        if not ligne: 
            fichier_synthese.close
            break     

    # Progress BAR 95 %
    self.progressBar.setValue( 95)
                
    # Mettre à jour les histogrammes dans fenetre resultat
    if histogrammes == "YES":
        if ( self.label_histo_sarment.setPixmap( QPixmap( nom_histo_sarment))):
            physiocap_log ( u"Physiocap histo sarment chargé")
        if ( self.label_histo_diametre_avant.setPixmap( QPixmap( nom_histo_diametre))):
            physiocap_log ( u"Physiocap histo diametre chargé")                
        if ( self.label_histo_diametre_apres.setPixmap( QPixmap( nom_histo_diametre_filtre))):
            physiocap_log ( u"Physiocap histo diametre chargé")    
    else:
        self.label_histo_sarment.setPixmap( QPixmap( FICHIER_HISTO_NON_CALCULE))
        self.label_histo_diametre_avant.setPixmap( QPixmap( FICHIER_HISTO_NON_CALCULE))
        self.label_histo_diametre_apres.setPixmap( QPixmap( FICHIER_HISTO_NON_CALCULE))
        physiocap_log ( u"Physiocap pas d'histogramme calculé")    
                       
    # Progress BAR 100 %
    self.progressBar.setValue( 100)
    # Fin 
    
    physiocap_log ( u"Fin de la synthèse Physiocap : sans erreur")
    physiocap_fill_combo_poly_or_point( self)
    physiocap_log ( u"Mise à jour des poly et points")
    return 0 

