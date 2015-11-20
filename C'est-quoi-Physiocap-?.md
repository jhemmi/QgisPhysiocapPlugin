### L'essentiel
Physiocap est un capteur géolocalise des mesures de diamètre des sarments d'une vigne.
**L'extension (plugin) Physiocap pour Qgis n'intéresse que le métier "Agronomie de la vigne"**. 

Le concept a été défini par le CIVC et industrialisé par Ereca qui s'appuie sur son boitier Tiny.
Physiocap est breveté en 2013 par le CIVC.

### Quelques détails sur le capteur
Le capteur est embarqué sur un portique qui porte deux cellules (émettrice et réceptrice) qui traitent un rayon laser et réalise une mesure du diamètre des sarments. Il s'agit de mesures directes de la fréquence et du diamètre des sarments : indicateurs fidèles de l'expression végétative et de la vigueur de la vigne.
Chaque seconde, un GPS capture la position de chaque lot de mesures.
Les différents fichiers bruts (MID de 15 minutes de capture) sont récupérés sur une clé USB.

Le capteur peut fonctionner avec d'autre outils, par exemple lors du pré-taillage automnal.

Le capteur a été industrialisé par Ereca.

### Quelques détails sur l'extension (plugin)
L'extension Physiocap est dédié au métier "Agronomie de la vigne".

Elle permet de faire l'analyse des données brutes sans quitter Qgis. Les paramètres précisent les seuils du filtre de données. Les résultats de chaque itération de calcul sont présentés sous forme de shapefiles thématisés. Une synthèse et des histogrammes permettent de valider la traitement des données brutes.

A partir de votre contour de parcelles de vigne, des moyennes inter parcellaire sont calculées et présentées sous Qgis. Ces extractions de moyennes et de points à la parcelle permettent de réaliser une interprétation agronomique des résultats. 
Nous conseillons l'appui d'un agronome ou d'un technicien vigne averti.

### A venir
L'extension proposera une analyse intra parcellaire 
