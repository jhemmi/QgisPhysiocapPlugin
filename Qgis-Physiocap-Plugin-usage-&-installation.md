Qgis Physiocap Extension Utilisation & installation (version 1.2)

Voici la documentation de l'Extension Physiocap pour Qgis qui permet de traiter les données brutes de Physiocap et de visualiser les résultats filtrés sous Qgis. La version 1.2 permet d'activer le calcul des moyennes inter parcellaire à partir de votre contour de parcelles.

### Installation de l'extension 

Depuis un zip file envoyé par jhemmi.eu ou depuis le gitHub zip file (*1):

Extraire le contenu de "Qgis Physiocap Plugin zip" dans $HOME/.qgis2/python/plugins (*2) 
(*1) Renommer le nouveau répertoire en PhysiocapAnalyseur.
(*2) Si vous n'avez jamais installé aucun plugin, il faut créer le répertoire "plugins"
 
L'extension tourne sous Qgis 2.*. Aucune installation de librairie Python n'est requise en plus de celles déjà présentes dans Qgis 2.* (ogr, csv, numpy, mapplotlib, shutil, qgis et pyQT4). 

Note : L'extension n'est pas encore déposé sous le dépôt Qgis

### Utilisation
![Onglet Paramètre](https://github.com/jhemmi/QgisPhysiocapPlugin/blob/master/help/Version%201.1%20Parametres.png)

Ouvrir Qgis & activer Physiocap menu depuis le menu Extension ou directement sur l'icone Physiocap (en haut à gauche sur la copie d'écran). Dans le dialogue Physiocap plusieurs onglets :
* Dans **l'onglet Paramètres** (visible à droite dans la copie d'écran) : permet de préciser vos paramètres  pour les calculs
- Répertoire des données brutes
- Nom à votre projet Physiocap qui sert de répertoire de base pour le stockage des résultats et de préfixe pour les fichiers générées
- Filtres permettant de nettoyer les données brutes
- Calculs détaillés :  précisez si les informations du vignoble doivent être prises en compte pour un calcul détaillé (ce choix est optionnel)

Dans cette version, les cartes de points sont générés au format shapefile et en L93 (ou GPS). La sauvegarde de l'ensemble de ces paramètres est effectuée avant chaque exécution du calcul.

**_Pour activer les calculs, cliquez sur le bouton OK_**

_La barre d'avancement indique 100 % à la fin des traitements._
 
Durant l'exécution, l'extension crée les répertoires:
* Nom projet Physiocap (en cas d'existence du répertoire, il est créé un répertoire Nom projet Physiocap(1), le plus haut chiffre est le plus récent.
Le fichier de synthèse du traitement : nom-projet-physiocap_resulat.txt
- "fichier_sources" contient les données sources brutes et une copie en csv
- "fichier_textes" contient les nom-projet-physiocap_OUT*.cvs filtré et les listes "nbsarm*" et "diam*" (respectivement) tous les nombre de sarments et les diametres bruts et filtrés prêts pour créer des histogramme.
- "shapefile" contient les deux fichiers shape résultats du filtrage des données brutes.

**Dans panneaux de couches de Qgis, les shapefiles créés par le plugin sont regroupés dans un groupe qui porte le nom du projet Physiocap.**

Dans **l'onglet Synthèse**, vous pouvez consulter le "résultat" du dernier traitement effectué.
![Onglet Synthèse](https://github.com/jhemmi/QgisPhysiocapPlugin/blob/master/help/Version%201.1%20Synthese.png)


Dans **l'onglet Histogramme**, vous devez demander la création et les derniers histogrammes sont affichés
![Onglet Histogrammes](https://github.com/jhemmi/QgisPhysiocapPlugin/blob/master/help/Version%201.1%20Histogrammes.png)


Dans la log Qgis, deux onglets (Physiocap Information - visible au tiers haut dans la copie d'écran) et Physiocap Erreurs) permettent de suivre le déroulement du traitement et d'éventuelles erreurs).
*la Log Qgis peut être visualisée en appuyant sur l'icone ! à bas à droite ou par le menu Vues => Panneaux => Journal des messages. 
*Les trois thématiques des fichiers shape sont ouvertes dans Qgis et sont mises en forme avec les styles qui se trouvent dans $HOME/.qgis2/python/plugins/physiocap_analyseur/modeleQgis
* "Vitesse.qml" pour le shape non filtré nom-projet-physiocap_0_L93.shp qui se nomme VITESSE (deuxième copie d'écran)
* "Sarment 4 Jenks.qml" pour le shape filtré nom-projet-physiocap_L93.shp qui se nomme SARMENT 
* "Diametre 6 quantilles.qml" pour le shape filtré nom-projet-physiocap_L93.shp qui se nomme DIAMETRE (troisième copie d'écran)

Dans **l'onglet Inter**, vous devez demander le calcul des moyenne inter parcellaire à partir d'un contour de parcelles qui vous intéressent. Dans le shapefile de Contour, veillez à garder la même projection que celle demandés lors des traitements initiaux.
Le bouton "Rafraîchir la liste des vecteurs" permet de lister les polygones de contours disponibles dans votre projet Qgis mais aussi le jeu de mesures à comparer (shapefiles de points) qui serviront de  base au calcul des moyennes.
Après le choix du contour et du jeu de mesures, vous lancez le traitement par le bouton "Moyenne Inter Parcellaire". 

Le projet Qgis n'est pas sauvé, mais vous pouvez le faire vous même (il vous gérer la conservation des répertoires de calcul et des shapefile utilisés).

Vous pouvez quitter l'extension par le bouton "Fermer".