import os
root_base = ""
MIDs = []
for root, dirs, files in os.walk( "/home/jhemmi/Documents/GIS/SCRIPT/QGIS/PhysiocapAnalyseur/data Checker", topdown=True):
    if root_base == "":
        root_base = root
    #print ("ALL Root :" + str(root))
    #print ("ALL DIR :" + str(dirs))
    #print ("ALL FILE :" + str(files))
    if "fichiers_sources" in root:
        #print("DIR EXCLUS: " + os.path.join(root, name_dir))
        continue
    #print("GOOD DIR : " + os.path.join(root, name_dir))
    for name_file in files:
        if "MID" in name_file[-3:]:
            trouve = os.path.join( root, name_file)
            #print("GOOD MID : " + trouve)
            if trouve.find( root_base) == 0:
                print len( root_base)
                print( "VERY GOOD MID :" + trouve[ len( root_base) + 1:])
                MIDs.append( trouve[ len( root_base) + 1:])
print ("ALORA : "+ str(MIDs))
for un_mid in sorted(MIDs): 
    nom_fichier = os.path.join(root_base, un_mid)
    if (os.path.isfile( nom_fichier)):
        fichier_pret = open(nom_fichier, "r")
        lignes = fichier_pret.readlines()
        #print( "LIGNE 0 :" + lignes[0])
        #print( "DATE DEBUT :" + lignes[0][0:19])
        #print( "HEURE FIN :" + lignes[-1][10:19])
        gps_x = []
        gps_y = []
        vitesse = []
        for ligne in lignes:
            try:
                champ = ligne.split( ",")
                if len(champ) >= 2:
                    gps_x.append( float(champ[ 1]))
                    gps_y.append( float(champ[ 2]))
                if len(champ) >= 8:
                    vitesse.append( float(champ[ 8]))
            except ValueError:
                pass
        print( un_mid + " entre " + lignes[0][0:19] +
            " et " + lignes[-1][10:19])
        if (len( gps_x) > 0 and len( gps_y) > 0 ):
            print( "Nombre de mesures brutes :" + " " + 
                str( len(gps_x)))
            print( "Centroides GPS :" + " " + 
                str(sum(gps_x)/len(gps_x))+ " " +   
                str(sum(gps_y)/len(gps_y))) 
        if (len( vitesse) > 0 ):
            print( "Vitesse moyenne :" + " " + 
                str(sum(vitesse)/len(vitesse)))
     
        
        