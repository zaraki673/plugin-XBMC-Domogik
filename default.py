# -*- coding: utf-8 -*-
import os, re, socket, urllib
from traceback import print_exc
import xbmc, xbmcgui, xbmcaddon
#import json
import simplejson as json

__addon__     = xbmcaddon.Addon( "script.domogik.controler" )
__settings__  = xbmcaddon.Addon( "script.domogik.controler" )
__addonid__   = __addon__.getAddonInfo('id')
__addonname__ = __addon__.getAddonInfo('name')
__cwd__       = __addon__.getAddonInfo('path')
__author__    = __addon__.getAddonInfo('author')
__version__   = __addon__.getAddonInfo('version')
__language__  = __addon__.getLocalizedString
__useragent__ = "Mozilla/5.0 (Windows; U; Windows NT 5.1; fr; rv:1.9.0.1) Gecko/2008070208 Firefox/7.0"

__domogik_url__ = __settings__.getSetting("base_url").strip("/") 

DATA_PATH = os.path.join( xbmc.translatePath( "special://profile/addon_data/" ), __addonid__ )
RESOURCES_PATH = xbmc.translatePath( os.path.join( __cwd__, 'resources' ) )
sys.path.append( os.path.join( RESOURCES_PATH, "lib" ) )


def get_html_source(url , save=False):
    class AppURLopener(urllib.FancyURLopener):
        version = __useragent__
    urllib._urlopener = AppURLopener()
    succeed = 0
    while succeed < 5:
        try:
            urllib.urlcleanup()
            sock = urllib.urlopen(url)
            htmlsource = sock.read()
            if save: file( os.path.join( CACHE_PATH , save ) , "w" ).write( htmlsource )
            sock.close()
            succeed = 5
            return htmlsource
        except:
            succeed = succeed + 1
            print_exc()
            print( "### ERROR opening page %s ---%s---" % ( url , succeed) )
    return ""

if ( __name__ == "__main__" ):

    #récupération de la liste des pièces     
    def get_room_list():
        data = get_html_source( __domogik_url__ + "/base/room/list" )
        result = json.loads(data)
        print "get room list"
        print "status : %s" % result.get("status","")
        print "code : %s" % result.get("code","")
        print "description : %s" % result.get("description","")
        return result["room"]
    
    #Récupération des éléments d'une pièce
    def get_device_by_room( id_room ):
        data = get_html_source( __domogik_url__ + "/base/feature_association/list/by-room/%s" % id_room )
        result = json.loads(data)     
        print "get device by room"
        print "status : %s" % result.get("status","")
        print "code : %s" % result.get("code","")
        print "description : %s" % result.get("description","")
        return result["feature_association"]
    
    #récupération de la liste de l'ensemble des équipements connus
    def get_all_device_info():
        data = get_html_source( __domogik_url__ + "/base/device/list" )
        result = json.loads(data)             
        print "get all device info"
        print "status : %s" % result.get("status","")
        print "code : %s" % result.get("code","")
        print "description : %s" % result.get("description","")
        return result["device"]
        
    #prend une liste de device_id en paramètres, retourne une liste de dico contenant toute les infos nécessaires    
    def get_device_list_info( d_list ):
        current_list = []
        for d_id in d_list:
            if d_id in [ device["id"] for device in all_device_list ] :
                index = [ device["id"] for device in all_device_list ].index(d_id)
                current_list.append( all_device_list[index] )
        return current_list
        
    #Récupère l'action et le device    
    def do_action( action , cur_device):
        print "do action"
        print action
        print cur_device["address"]
        print cur_device["device_type"]["device_technology_id"]
        data = get_html_source( __domogik_url__ + "/command/" + cur_device["device_type"]["device_technology_id"] + "/" + cur_device["address"] + "/" + action )
        result = json.loads(data)        
        print "status : %s" % result.get("status","")
        print "code : %s" % result.get("code","")
        print "description : %s" % result.get("description","")
        
    #Récupère le device en paramêtre et présente les choix possibles en fonction du device
    def get_action( device ):
        if device["device_type"]["name"] == "Dimmer":
            dim_list = [str(i) for i in range(26)]
            dim_list[0] = "off"
            dim_list.append("on")
            dim_list.reverse()
            select = xbmcgui.Dialog().select( "intensité souhaitée" , dim_list )
            if select == -1: action = ""
            elif dim_list[select] in [ "on" , "off" ]: action = dim_list[select]
            else: action = "dim/%s" % (int(dim_list[select])*10)
        elif device["device_type"]["name"] == "Switch":
            select = xbmcgui.Dialog().select( "que voulez-vous faire?" , ["éteindre" , "allumer"] )
            print select
            if select == -1: action = ""
            elif select == 0: action = "off"  
            else: action = "on" 
        else: action = ""
        return  action                                                                                           
        
    #Propose une liste de choix en utilisant la propriété 'name' d'une liste de dico passée en paramêtre
    def choice_list( texte="" , dico_list={} ):
        select = xbmcgui.Dialog().select( texte , [ item["name"] for item in dico_list ] )
        return select                
        
    room_list = get_room_list()
    all_device_list = get_all_device_info()
    room_choice = None
    while not room_choice == -1 : #tant qu'on annule pas on revient sur le menu précédent
        room_choice = choice_list( "Choisir la pièce" , room_list )
        if not room_choice == -1 : #si annul ou retour arrière, on ne charge pas de données
            device_list = get_device_by_room(room_list[room_choice]["id"])
            print [ device["device_feature"]["device_id"] for device in device_list ]
            cur_device_list = get_device_list_info( [ device["device_feature"]["device_id"] for device in device_list ] )
            print [ device["name"] for device in cur_device_list ]
            device_choice = None
            while not device_choice == -1 : #tant qu'on annule pas on revient sur le menu précédent
                device_choice = choice_list( "Choisir l'équipement" , cur_device_list )
                if not device_choice == -1 : #si annul ou retour arrière, on ne fait pas d'action
                    print cur_device_list[device_choice]
                    action = None
                    while not action == "":
                        action = get_action(cur_device_list[device_choice])
                        print action
                        if not action == "" :
                            finalresult = do_action( action , cur_device_list[device_choice])
    
       
#     room_list = get_room_list()
#     for room in room_list: print room["name"]
#    print [ room["name"] for room in room_list ]
        

#     #récup du nom d'un equipement
#     def get_name(iid):
#         response = ""
#         for item in inventory:
#             #print iid
#             #print item["id"]
#             if int(item["id"]) == int(iid): 
#                 response = item["name"]
#                 print "match"
#                 break
#         return response   
#     
#     #listing de l'ensemble des équipement identifiés
#     def get_all_device():
#         data = get_html_source( __domogik_url__ + "/base/device/list" )
#         result = re.findall(r'\{"description" : "(.*?)","reference" : "(.*?)","device_usage_id" : "(.*?)","device_type" : \{"description" : "(.*?)","id" : "(.*?)","name" : "(.*?)","device_technology_id" : "(.*?)"\},"address" : "(.*?)","device_type_id" : "(.*?)","device_usage" : \{"description" : "(.*?)","default_options" : "\{(.*?)\}","id" : "(.*?)","name" : "(.*?)"\},"id" : (\d+),"name" : "(.*?)"\}', data)
#         listing = []
#         for item in result:
#             equip= {"type" : item[2] ,
#                     "type2" : item[3] ,
#                     "cmd_id" : item[7]  ,
#                     "name" : item[14] ,
#                     "id" : item[13]
#                 }
#             listing.append( equip )
#         return listing
# 
#     #récupération de la liste des area .
#     data = get_html_source( __domogik_url__ + "/base/room/list" )
#     result = re.findall(r'\{"area_id" : (?P<area_id>\d+),"description" : "(?P<room_desc>.*?)","area" : \{"description" : "(?P<area_desc>.*?)","id" : \d+,"name" : "(?P<area_name>.*?)"\},"id" : (?P<room_id>\d+),"name" : "(?P<room_name>.*?)"\}', data)
#     room_list = []
#     for item in result:
#         room = {"area_id" : item[0],"room_desc" : item[1],"area_desc" : item[2],"area_name" : item[3],"room_id" : item[4],"room_name" : item[5]}
#         room_list.append(room)
#     print [ room["room_name"] for room in room_list ] 
#     #listing de sélection de pièce.
#     select = xbmcgui.Dialog().select( "Choisir la pièce" , [ room["room_name"] for room in room_list ] )
#     print room_list[select] 
#     
#     inventory = get_all_device()
#     for i in inventory: print i
#     
#     #récupération des équipements de la pièce.
#     data = get_html_source( __domogik_url__ + "/base/feature_association/list/by-room/%s" % room_list[select]["room_id"] )
#     result = re.findall(r'\{"place_id" : (?P<place_id>\d+),"place_type" : "(?P<place_type>.*?)","device_feature_id" : (?P<device_feature_id>\d+),"id" : \d+,"device_feature" : \{"device_feature_model_id" : "(?P<device_feature_model_id>.*?)","id" : \d+,"device_id" : (?P<device_id>\d+)\}\}', data)          
#     device_list = []
#     for item in result:
#         device = { "device_feature_id" : item[2] , "device_feature_model_id" : item[3] , "device_id" : int(item[4]) }
#         #print device["device_id"]
#         #print device_list 
#         if device["device_id"] not in [ dev["device_id"] for dev in device_list ] :
#             device["name"] = get_name(device["device_id"])
#             device_list.append( device )
#     #print [ device["device_id"] for device in device_list ]
#     print device_list
#     
#     #listing de sélection equipement dans pièce.
#     select = xbmcgui.Dialog().select( "Choisir l'équipement" , [ item["name"] for item in device_list ] )
#     print device_list[select]     
        
    

        
                