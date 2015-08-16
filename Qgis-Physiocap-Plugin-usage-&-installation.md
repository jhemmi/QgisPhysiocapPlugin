Qgis Physiocap Extension Utilisation & installation (version 0.1 pour tests uniquement)

Voici la documentation de l'Extension Physiocap pour Qgis qui permet de traiter les données brutes de Physiocap et de visualiser les résultats filtrés sous Qgis.

La dernière source document est sous github.com/jhemmi/QgisPhysiocapPlugin

### Installation de l'extension 

Depuis un zip file envoyé par jhemmi.eu ou depuis le gitHub zip file (*1):

Extraire Qgis Physiocap Plugin zip dans $HOME/.qgis2/python/plugins. 
(*1) Renommer le nouveau répertoire en PhysiocapAnalyseur.

L'extension tourne sous Qgis 2.*. Aucune librairie Python n'est requise en plus de celles présentes dans Qgis 2.* (ogr, csv, numpy, shutil, qgis et pyQT4). 

Note : L'extension n'est pas encore déposé sous le dépôt Qgis

### Utilisation
![Copie d'écran](https://github.com/jhemmi/QgisPhysiocapPlugin/blob/master/Ecran%20Physiocap%20Plugin.png)
[Copie d'écran de fichier de synthèse d'un traitement du plugin Physiocap](https://github.com/jhemmi/QgisPhysiocapPlugin/blob/master/Ecran%20Physiocap%20Plugin.png)

Ouvrir Qgis & activer Physiocap menu depuis le menu Extension ou directement sur l'icone Physiocap (en haut à droite sur la copie d'écran). Dans le dialogue Physiocap plusieurs onglets :
* Votre projet : permet de donner un nom à votre projet Physiocap qui sert de répertoire de base pour le stockage des résultats et de préfixe pour les fichiers générées
Dans cette fenêtre, d'autres options sont à venir. Dans cette version les cartes de points sont générés au format shapefile et en L93.
* Vos paramètres (visible à droite dans la copie d'écran) : permet de donner les paramètres d'entrée pour les calculs
- Répertoire des données brutes
- Filtres permettant de nettoyer les données brutes
- Calculs détaillés :  précisez si les informations du vignoble doivent être prises en compte pour un calcul détaillé (ce choix est optionnel)
La sauvegarde de l'ensemble de ces paramètres n'est pas encore active.

Pour activer les calculs, activer le bouton OK

Durant l'exécution, l'extension crée les répertoires:
* Nom projet Physiocap (en cas d'existence du répertoire, il est créé un répertoire Nom projet Physiocap(1), le plus haut chiffre est le plus récent.
Le fichier de synthèse du traitement : nom-projet-physiocap_resulat.txt
- fichier_sources contient les données sources brutes et une copie en csv
- fichier_textes contient les nom-projet-physiocap_OUT*.cvs filtré et les listes "nbsarm*" et "diam*" (respectivement) tous les nombre de sarments et les diametres bruts et filtrés prêts pour créer des histogramme.
- shapefile contient les deux fichiers shape résultats du filtrage des données brutes.

Dans la log Qgis, deux onglets (Physiocap Information - visible en bas dans la copie d'écran) et Physiocap Erreurs) permettent de suivre le déroulement du traitement et d'éventuelles erreurs).

Les deux fichiers shape sont ouvert dans Qgis. Il est conseillé de mettre en forme ces shapes avec les styles qui se trouvent dans $HOME/.qgis2/python/plugins/physiocap_analyseur/modeleQgis
* "Diametre 6 quantilles.qml" pour le shape nom-projet-physiocap_*.shp
* "Vitesse.qml" pour le shape filtré nom-projet-physiocap_0_*.shp

Le projet Qgis n'est pas sauvé, mais vous pouvez le faire vous même. Vous pouvez quitter l'extension par le bouton "Fermer".

Note : Le répertoire et le calcul des histogrammes n'est pas implémenté dans cette version.