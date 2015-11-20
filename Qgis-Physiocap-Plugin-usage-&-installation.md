Qgis Physiocap Extension installation & utilisation (version 1.2.2)

Voici la documentation de l'extension Physiocap pour Qgis qui permet de traiter les données brutes du capteur Physiocap et de visualiser les résultats filtrés sous Qgis. La version 1.2.2 permet d'activer le calcul des moyennes inter parcellaire à partir de votre contour de parcelles.
Pour mieux connaitre Qgis, vous pouvez consulter [une petite introduction sur les SIG](http://docs.qgis.org/testing/en/docs/gentle_gis_introduction/index.html) ou [le Manuel Utilisateur de Qgis.](http://docs.qgis.org/2.8/fr/docs/user_manual/)

### Installation de l'extension (plugin) 

Ouvrir le fichier zip envoyé par jhemmi.eu ou télécharger depuis gitHub.

Extraire le répertoire contenu dans "Qgis Physiocap Plugin zip" dans $HOME/.qgis2/python/plugins
* Si vous n'avez jamais installé aucune extension sous Qgis, il faut créer le répertoire "plugins".
* $HOME est le chemin à vos données utilisateur : 
   
sous Windows >= 7, il s'agit du chemin C:\Utilisateur\votre_propre_nom_utilisateur par exemple pour l’utilisateur "toto" le chemin devient C:\Utilisateur\toto\.qgis2\python\plugins  
sous Windows < 7, l'exemple devient C:\Documents and Settings\toto\.qgis2\python\plugins  
sous Linux, l'exemple devient /home/toto/.qgis2/python/plugins  

Renommer le nouveau répertoire "QgisPhysiocapPlugin-1.X.X" en "PhysiocapAnalyseur".

Relancer Qgis. Dans la barre d'outils, l'icone !["Phy"](https://github.com/jhemmi/QgisPhysiocapPlugin/blob/master/icon.png) permet de lancer Physiocap Analyseur. Dans le menu Extension, le menu Physiocap permet aussi d’accéder à Physiocap Analyseur.

Si vous n'avez jamais installé aucune extension sous Qgis, ouvrir le menu Extension, puis "Installer/Gérer les extensions" (onglet "Toutes") retrouver l'extension Physiocap et la cocher pour la rendre active.

Note : l'extension tourne sous Qgis 2.x. Aucune installation de librairie Python n'est requise. Celles présentent dans Qgis 2.x sont suffisantes (ogr, csv, numpy, mapplotlib, shutil, qgis et pyQT4). 

L'extension n'est pas encore déposé sous le dépôt standard Qgis.

### Utilisation

## Vos repères et outils
A tout moment vous pouvez accéder aux boutons : 
* "Aide" pour retrouver les liens vers la documentation de l'extension Physiocap.
* "Fermer" pour quitter l'extension 
* "Ok" pour lancer une itération de calculs dans un nouveau projet Physiocap.

Dans la log Qgis, deux onglets (Physiocap Information - visible au tiers haut dans la copie d'écran de l'onglet Paramètres et Physiocap Erreurs) permettent de suivre le déroulement du traitement et d'éventuelles erreurs).
*la Log Qgis peut être visualisée en appuyant sur l'icone ! à bas à droite ou par le menu Vues => Panneaux => Journal des messages. 

Pour activer Physiocap Analyseur,ouvrir Qgis & activer l'icone Physiocap (en haut à gauche sur la copie d'écran de l'onglet Paramètres). Vous pouvez aussi utiliser le menu Extension et le sous menu Physiocap. Dans le dialogue Physiocap, vous pouvez accéder aux onglets Paramètres, Synthèse, Histogrammes, Inter, A propos.

## Onglet Paramètres
![Onglet Paramètres](https://github.com/jhemmi/QgisPhysiocapPlugin/blob/master/help/Version%201.2%20Parametres.png)

Dans l'onglet Paramètres (visible à droite dans la copie d'écran ci dessus), vous pouvez préciser vos paramètres  pour les calculs : 
- Le Répertoire des données brutes (MIDs bruts issus du capteur).
- En option, vous pouvez choisir de chercher les MIDs dans les sous répertoires.
- Le nom de votre projet Physiocap qui sert de répertoire de base pour le stockage des résultats, de préfixe pour les fichiers générées et pour nommer le groupe dans le panneau de couches Qgis. ***Un nom concis et un préfixe "PHY_" est conseillé***.
- Choisir votre projection en L93 ou en GPS. Tous les shapefiles générés sont nommés en finissant par "_PROJECTION.shp" (par exemple _L93.shp).
- Les cartes de points et polygones sont générées au format shapefile uniquement.
- Les filtres permettant de nettoyer les données brutes.
- Calculs détaillés : précisez si les informations du vignoble doivent être prises en compte pour un calcul détaillé (ce choix est optionnel).

La sauvegarde des derniers paramètres saisies est effectuée à chaque exécution du calcul.

**_Pour activer les calculs, cliquez sur le bouton OK_**

_La barre d'avancement indique 100 % à la fin des traitements._

## Organisation des fichiers
Cette description n'est pas à connaitre, car vous retrouvez l'ensemble de ces données directement dans les onglets. Durant l'exécution, l'extension crée le répertoire "Nom projet Physiocap" (en cas d'existence du répertoire, il est créé un répertoire Nom projet Physiocap (puis Nom projet Physiocap(1), le plus haut chiffre est la dernière itération de calcul).
Dans cette racine, l'extension crée les répertoires et les fichiers suivants (même organisation et nommage que l'outil PHYSIOCAP_V8 du CIVC):
![Arbre de données](https://github.com/jhemmi/QgisPhysiocapPlugin/blob/master/help/Organisation%20des%20fichiers%20de%20chaque%20projet%20Physiocap.png)

A la racine, vous trouvez le fichier de synthèse du traitement : nom-projet-physiocap_resulat.txt (en bleu dans la copie d'écran ci dessus).
- "fichier_sources" contient la copie des données sources brutes (fichiers MID) et une version en csv "nom-projet-physiocap_RAW.cvs" qui contient les mesures brutes (copie de tous les MIDs).
- "fichier_textes" contient deux cvs "nom-projet-physiocap_OUT.cvs" données filtrées et moyennées et "nom-projet-physiocap_OUT0.cvs" données sans filtre (les vitesses nulles sont conservées). Les autres cvs sont utiles pour le calcul des histogrammes ("nbsarm*" et "diam*" tous les nombres de sarments et les diamètres bruts et filtrés). "Erreur.cvs" contient la trace des erreurs que vous pouvez aussi retrouver dans la log Physiocap Erreur.
- "histogrammes" contient les fichiers image des histogrammes des sarments, des diamètres bruts et des diamètres filtrés.
- "shapefile" contient les deux fichiers shapefiles résultants du filtrage des données brutes (avec ou sans 0).

**Dans panneaux de couches de Qgis, les shapefiles créés sont dans un groupe qui porte le nom du projet Physiocap**. L'organisation est semblable à celle des fichiers.

Trois thématiques sont ouvertes dans Qgis et sont mises en forme avec les styles qui se trouvent dans $HOME/.qgis2/python/plugins/physiocap_analyseur/modeleQgis
* "Vitesse.qml" pour le shapefile non filtré nom-projet-physiocap_0_L93.shp qui se nomme VITESSE (copie d'écran de l'onglet Synthèse)
* "Sarment 4 Jenks.qml" pour le shapefile filtré nom-projet-physiocap_L93.shp qui se nomme SARMENT 
* "Diametre 6 Jenks.qml" pour le shapefile filtré nom-projet-physiocap_L93.shp qui se nomme DIAMETRE (copie d'écran de l'onglet Histogramme)

## Onglet Synthèse
Dans l'onglet Synthèse, vous pouvez consulter le "résultat" du dernier traitement effectué.
![Onglet Synthèse](https://github.com/jhemmi/QgisPhysiocapPlugin/blob/master/help/Version%201.2%20Synthese.png)
La synthèse commence par une liste des MIDs pris en compte. Cette liste peut vous permettre d'identifier des doublons car pour chaque MID, il est présenté date et heure de début et fin de capture, moyenne de vitesse et sarment. Lorsque ces informations sont identiques, il s'agit de MID en doublons.

## Onglet Histogrammes
Dans l'onglet Histogrammes, vous devez demander la création des histogrammes avant de lancer le traitement. Les derniers histogrammes sont affichés.
![Onglet Histogrammes](https://github.com/jhemmi/QgisPhysiocapPlugin/blob/master/help/Version%201.2%20Histogrammes.png)

## Onglet Inter
Dans l'onglet Inter, vous devez rafraîchir la liste avant de demander le calcul des moyennes inter parcellaire à partir d'un contour des parcelles qui vous intéressent. 
***Le shapefile de Contour doit être ouvert dans Qgis - Menu Couche => Ajouter un vecteur et donnez le nom de votre shapefile de contour***. Choisissez un contour avec la même projection que celle demandée lors des traitements initiaux.
Vous pouvez efficacement, vous appuyer sur le couche Vitesse pour dessiner vos contours. Une photo aérienne (accessible par l'extension "OpenLayers Plugin") est le meilleur support pour être précis au rang.

![Onglet Inter avant](https://github.com/jhemmi/QgisPhysiocapPlugin/blob/master/help/Version%201.2%20Choix%20Contour.png)

Le bouton "Rafraîchir la liste des vecteurs" permet de lister les polygones de contours disponibles dans votre projet Qgis mais aussi le jeu de mesures à comparer (shapefiles de points) qui serviront de  base au calcul des moyennes. Le jeu de données de point est identifié par le nom du projet Physiocap.

Après le choix du contour et du jeu de mesures, vous lancez le traitement par le bouton "Moyenne Inter Parcellaire". 
![Onglet Inter après](https://github.com/jhemmi/QgisPhysiocapPlugin/blob/master/help/Version%201.2%20Inter%20Parcellaire.png)
Dans panneaux de couches de Qgis :  
* dans le groupe du projet Physiocap, il est ajouté un shapefile des points de mesures incluses chaque parcelle. 
* en haut du panneaux de couche, un shapefile PROJET_PHYSIOCAP_MOYENNE_INTER_nom_contour permet de visualiser les moyennes spécifiques de chaque parcelle.

Le "projet Qgis" n'est pas sauvé, mais vous pouvez le faire vous même (à vous de gérer la conservation des répertoires de calcul et des shapefile utilisés).

###  Vos retours et votre contribution
L'extension Physiocap pour Qgis est open source. Il est important de faire vos retours de tests [par courriel](mailto://jean@jhemmi.eu) au développeur ou directement de proposer des améliorations [sur le Wiki](https://github.com/jhemmi/QgisPhysiocapPlugin/issues). N'oubliez pas de [contribuer](https://plus.payname.fr/jhemmi?type=9xwqt) si l'extension vous est utile. Vous pourrez ainsi apparaître dans l'onglet "A propos".