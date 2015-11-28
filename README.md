# QgisPhysiocapPlugin
_Physiocap plugin helps analysing raw data from Physiocap in Qgis. 
This version is in French only._

L'extension Physiocap pour Qgis permet d'analyser les résultats bruts de Physiocap. Il s'agit de mesures directes de la vigueur et de l'expression végétative de la vigne.
Trois métriques sont calculés à partir des données brutes :
	nombre de bois au mètre
	le diamètre moyen et
	l'indice de biomasse (kg de bois par m2)
	
L'extension permet de choisir plusieurs paramètres pour filtrer les données qui ont un intérêt. Elle réalise une série de calcul aboutissant à :
	une synthèse des métriques moyens des données retenues,
	deux shapefiles qui permettent de visualiser les données mesurées et les données retenues (après filtration),
	trois histogrammes qui décrivent la population des données mesurées (sarment et diamètre).

L'extension "version 1.2.3 Inter" réalise une extraction des données filtrés à partir de votre contour de parcelles. Vous obtenez les moyennes Inter parcellaires pour faire un premier diagnostic de chaque entité agronomique.

*"Physiocap" est déposé par le CIVC.*

L'extension QgisPysiocapPlugin intègre le code de calcul du CIVC (PHYSIOCAP_V8). QgisPysiocapPlugin est donc sous licence Common Creative CC-BY-NC-SA V4.

La documentation se trouve dans le Wiki
https://github.com/jhemmi/QgisPhysiocapPlugin/wiki/Qgis-Physiocap-Plugin-usage-&-installation

**Attention, ce dépot contient la version 1.2.3 (version stable https://github.com/jhemmi/QgisPhysiocapPlugin/releases) et la version 1.3.0 en cours de construction - Novembre 2015**

**Warning, this repo is version 1.2.3 (stable https://github.com/jhemmi/QgisPhysiocapPlugin/releases) and version 1.3.0 under construction - Novembre 2015**
