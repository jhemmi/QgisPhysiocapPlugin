Qgis Physiocap Extension installation & utilisation (version 1.2)

Voici la documentation de l'extension Physiocap pour Qgis qui permet de traiter les données brutes du capteur Physiocap et de visualiser les résultats filtrés sous Qgis. La version 1.2 permet d'activer le calcul des moyennes inter parcellaire à partir de votre contour de parcelles.

### Installation de l'extension (plugin) 

Ouvrir le fichier zip envoyé par jhemmi.eu ou télécharger depuis gitHub.

Extraire le contenu de "Qgis Physiocap Plugin zip" dans $HOME/.qgis2/python/plugins . Si vous n'avez jamais installé aucune extension sous Qgis, il faut créer le répertoire "plugins".

Renommer le nouveau répertoire en PhysiocapAnalyseur.

Relancer Qgis. Dans la barre d'outils, l'icone !["Phy"](https://github.com/jhemmi/QgisPhysiocapPlugin/blob/master/icon.png) permet de lancer Physiocap Analyseur. Dans le menu Extension, le menu Physiocap permet aussi d’accéder à Physiocap Analyseur.

Si vous n'avez jamais installé aucune extension sous Qgis, il faut dans le menu Extension, puis "Installer/Gérer les extensions" (onglet "Toutes") retrouver l'extension Physiocap et la cocher pour la rendre active.

Notes : 
 
L'extension tourne sous Qgis 2.x. Aucune installation de librairie Python n'est requise. Celles présentent dans Qgis 2.x sont suffisantes (ogr, csv, numpy, mapplotlib, shutil, qgis et pyQT4). 

L'extension n'est pas encore déposé sous le dépôt standard Qgis.

### Utilisation

## Vos outils
A tout moment vous pouvez accéder aux boutons : 
* "Aide" pour retrouver les liens vers la documentation de l'extension Physiocap.
* "Fermer" pour quitter l'extension 
* "Ok" pour lancer une itération de calcul dans un nouveau projet Physiocap.

Dans la log Qgis, deux onglets (Physiocap Information - visible au tiers haut dans la copie d'écran) et Physiocap Erreurs) permettent de suivre le déroulement du traitement et d'éventuelles erreurs).
*la Log Qgis peut être visualisée en appuyant sur l'icone ! à bas à droite ou par le menu Vues => Panneaux => Journal des messages. 

Ouvrir Qgis & activer Physiocap menu depuis l'icone Physiocap (en haut à gauche sur la copie d'écran) ou par le menu Extension sous menu Physiocap. Dans le dialogue Physiocap, vous pouvez accéder aux onglets Paramètres, Synthèse, Histogrammes, Inter, A propos.

## Onglet Paramètres
![Onglet Paramètres](https://github.com/jhemmi/QgisPhysiocapPlugin/blob/master/help/Version%201.2%20Parametres.png)

Dans l'onglet Paramètres (visible à droite dans la copie d'écran), vous pouvez préciser vos paramètres  pour les calculs
- Répertoire des données brutes (MIDs bruts issus du capteur)
- En option, vous pouvez choisir de chercher les MIDs dans les sous répertoires
- Nom à votre projet Physiocap qui sert de répertoire de base pour le stockage des résultats et de préfixe pour les fichiers générées. Un préfixe "PHY_" est proposé.
- Filtres permettant de nettoyer les données brutes
- Calculs détaillés : précisez si les informations du vignoble doivent être prises en compte pour un calcul détaillé (ce choix est optionnel)

Les cartes de points sont générées au format shapefile et selon votre choix dans la référentiel L93 ou GPS. 

La sauvegarde de l'ensemble des paramètres saisies est effectuée avant chaque exécution du calcul.

**_Pour activer les calculs, cliquez sur le bouton OK_**

_La barre d'avancement indique 100 % à la fin des traitements._

Durant l'exécution, l'extension crée le répertoire "Nom projet Physiocap" (en cas d'existence du répertoire, il est créé un répertoire Nom projet Physiocap(1), le plus haut chiffre est le plus récent.
Dans cette racine, l'extension crée les répertoires et les fichiers suivants (même organisation et nommage que l'outil PHYSIOCAP_V8 du CIVC):
![Arbre de données](https://github.com/jhemmi/QgisPhysiocapPlugin/blob/master/help/Organisation%20des%20fichiers%20de%20chaque%20projet%20Physiocap.png)

A la racine, vous trouvez le fichier de synthèse du traitement : nom-projet-physiocap_resulat.txt.
- "fichier_sources" contient la copie des données sources brutes (fichiers MID) et une version en csv "nom-projet-physiocap_RAW.cvs" qui contient les mesures brutes (copie de tous les MIDs).
- "fichier_textes" contient deux cvs "nom-projet-physiocap_OUT.cvs" données filtrées et moyennées et "nom-projet-physiocap_OUT0.cvs" données sans filtre (les vitesses nulles sont conservées). Les autres cvs sont utile pour le calcul des histogrammes ("nbsarm*" et "diam*" tous les nombres de sarments et les diamètres bruts et filtrés).
Erreur.cvs contient la trace des erreurs que vous pouvez aussi retrouver 
- "shapefile" contient les deux fichiers shape résultats du filtrage des données brutes.

**Dans panneaux de couches de Qgis, les shapefiles créés par le plugin sont regroupés dans un groupe qui porte le nom du projet Physiocap.**

Dans **l'onglet Synthèse**, vous pouvez consulter le "résultat" du dernier traitement effectué.
![Onglet Synthèse](https://github.com/jhemmi/QgisPhysiocapPlugin/blob/master/help/Version%201.2%20Synthese.png)


Dans **l'onglet Histogramme**, vous devez demander la création et les derniers histogrammes sont affichés
![Onglet Histogrammes](https://github.com/jhemmi/QgisPhysiocapPlugin/blob/master/help/Version%201.2%20Histogrammes.png)


Les **trois thématiques** des fichiers shape sont ouvertes dans Qgis et sont mises en forme avec les styles qui se trouvent dans $HOME/.qgis2/python/plugins/physiocap_analyseur/modeleQgis
* "Vitesse.qml" pour le shape non filtré nom-projet-physiocap_0_L93.shp qui se nomme VITESSE (deuxième copie d'écran)
* "Sarment 4 Jenks.qml" pour le shape filtré nom-projet-physiocap_L93.shp qui se nomme SARMENT 
* "Diametre 6 Jenks.qml" pour le shape filtré nom-projet-physiocap_L93.shp qui se nomme DIAMETRE (troisième copie d'écran)

Dans **l'onglet Inter**, vous devez rafraîchir la liste avant de demander le calcul des moyenne inter parcellaire à partir d'un contour des parcelles qui vous intéressent. 
Le shapefile de Contour doit être ouvert dans Qgis - Menu Couche => Ajouter un vecteur et donnez le nom de votre shapefile de contour. Choisissez un contour avec la même projection que celle demandés lors des traitements initiaux.
![Onglet Inter](https://github.com/jhemmi/QgisPhysiocapPlugin/blob/master/help/Version%201.2%20Choix%20Contour.png)
Le bouton "Rafraîchir la liste des vecteurs" permet de lister les polygones de contours disponibles dans votre projet Qgis mais aussi le jeu de mesures à comparer (shapefiles de points) qui serviront de  base au calcul des moyennes.
Après le choix du contour et du jeu de mesures, vous lancez le traitement par le bouton "Moyenne Inter Parcellaire". 
![Onglet Inter](https://github.com/jhemmi/QgisPhysiocapPlugin/blob/master/help/Version%201.2%20Inter%20Parcellaire.png)
Dans panneaux de couches de Qgis :  
* dans le groupe du projet Physiocap, il est ajouté un shapefile des points de mesure inclut chaque parcelle. 
* en haut du panneaux de couche, un shapefile PROJET_PHYSIOCAP_MOYENNE_INTER_nom_contour permet de visualiser les moyennes spécifiques à chaque parcelle.

Le projet Qgis n'est pas sauvé, mais vous pouvez le faire vous même (il vous gérer la conservation des répertoires de calcul et des shapefile utilisés).