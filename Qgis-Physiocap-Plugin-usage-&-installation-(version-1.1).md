Qgis Physiocap Extension Utilisation & installation (version 1.1)

Voici la documentation de l'Extension Physiocap pour Qgis qui permet de traiter les données brutes de Physiocap et de visualiser les résultats filtrés sous Qgis.

### Installation de l'extension 

Depuis un zip file envoyé par jhemmi.eu ou depuis le gitHub zip file (*1):

Extraire Qgis Physiocap Plugin zip dans $HOME/.qgis2/python/plugins. 
(*1) Renommer le nouveau répertoire en PhysiocapAnalyseur.

L'extension tourne sous Qgis 2.*. Aucune installation de librairie Python n'est requise en plus de celles présentes dans Qgis 2.* (ogr, csv, numpy, mapplotlib, shutil, qgis et pyQT4). 

Note : L'extension n'est pas encore déposé sous le dépôt Qgis

### Utilisation
![Copie d'écran](https://github.com/jhemmi/QgisPhysiocapPlugin/blob/master/Ecran%20Physiocap%20Plugin.png)
[Copie d'écran de fichier de synthèse d'un traitement du plugin Physiocap](https://github.com/jhemmi/QgisPhysiocapPlugin/blob/master/Ecran%20Physiocap%20Plugin.png)

Ouvrir Qgis & activer Physiocap menu depuis le menu Extension ou directement sur l'icone Physiocap (en haut à droite sur la copie d'écran). Dans le dialogue Physiocap plusieurs onglets :
* Votre projet : permet de donner un 
Dans cette fenêtre, d'autres options sont à venir. 
* Vos paramètres (visible à droite dans la copie d'écran) : permet de préciser vos paramètres d'entrée pour les calculs
- Répertoire des données brutes
- Nom à votre projet Physiocap qui sert de répertoire de base pour le stockage des résultats et de préfixe pour les fichiers générées
- Filtres permettant de nettoyer les données brutes
- Calculs détaillés :  précisez si les informations du vignoble doivent être prises en compte pour un calcul détaillé (ce choix est optionnel)

Dans cette version les cartes de points sont générés au format shapefile et en L93. La sauvegarde de l'ensemble de ces paramètres est effectuée avant chaque exécution du calcul.

Pour activer les calculs, cliquez sur le bouton OK

La barre d'avancement indique à 100 % la fin des traitements.
 
Durant l'exécution, l'extension crée les répertoires:
* Nom projet Physiocap (en cas d'existence du répertoire, il est créé un répertoire Nom projet Physiocap(1), le plus haut chiffre est le plus récent.
Le fichier de synthèse du traitement : nom-projet-physiocap_resulat.txt
- "fichier_sources" contient les données sources brutes et une copie en csv
- "fichier_textes" contient les nom-projet-physiocap_OUT*.cvs filtré et les listes "nbsarm*" et "diam*" (respectivement) tous les nombre de sarments et les diametres bruts et filtrés prêts pour créer des histogramme.
- "shapefile" contient les deux fichiers shape résultats du filtrage des données brutes.

Dans l'onglet Synthèse, vous pouvez consulter le "resultat" du dernier traitement effectué.

Dans l'onglet Histogramme, vous devez demander la création et les derniers histogrammes sont affichés

Dans la log Qgis, deux onglets (Physiocap Information - visible au tiers haut dans la copie d'écran) et Physiocap Erreurs) permettent de suivre le déroulement du traitement et d'éventuelles erreurs).
_la Log Qgis peut être visualisée en appuyant sur l'icone ! à bas à droite ou par le menu Vues => Panneaux => Journal des messages. _
Les trois thématiques des fichiers shape sont ouvertes dans Qgis et sont mise en forme avec les styles qui se trouvent dans $HOME/.qgis2/python/plugins/physiocap_analyseur/modeleQgis
* "Vitesse.qml" pour le shape filtré nom-projet-physiocap_0_*.shp qui se nomme VITESSE (première copie d'écran)
* "Sarment 4 Jenks.qml" pour le shape nom-projet-physiocap_*.shp qui se nomme SARMENT (deuxième copie d'écran)
* "Diametre 6 quantilles.qml" pour le shape nom-projet-physiocap_*.shp qui se nomme DIAMETRE (troisième copie d'écran)

Le projet Qgis n'est pas sauvé, mais vous pouvez le faire vous même. Vous pouvez quitter l'extension par le bouton "Fermer".
