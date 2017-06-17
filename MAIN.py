import os.path
import cherrypyimport sqlite3import jsonimport base64import timeimport urllibfrom hashlib import sha256from ImageEditor.imageMenu import run_optionfrom ImageEditor.text_menu_server import menu_server# ==================================================================# Setup stuff# The absolute path to this file's base directory:baseDir = os.path.dirname(os.path.abspath(__file__))# Dict with the this app's configuration (based on exampleApp)config = {    "/":     { "tools.staticdir.root": baseDir },    "/js":   { "tools.staticdir.on": True,               "tools.staticdir.dir": "./static/js" },    "/css":  { "tools.staticdir.on": True,               "tools.staticdir.dir": "./static/css" },    "/static": { "tools.staticdir.on": True,                 "tools.staticdir.dir": "./static/",                 "tools.staticdir.index": "./index.html" },    '/favicon.ico':{                'tools.staticfile.on': True,                'tools.staticfile.filename': './static/favicon.ico'                },}# Changes port to the one given to the groupcherrypy.config.update({"server.socket_port": 10002,})# Databasedb = "db/database.db"database = sqlite3.connect(db, check_same_thread=False)# Folder path to store imagesfolderPath = "ImageEditor/store"if not (os.path.exists(folderPath)):  # creates dir if it doesn't exist    os.makedirs(folderPath)# Effects and memes dictionaryeffects = ["", "thumbnails", "rotate", "moreContrast", "lessContrast", "moreSaturation", "lessSaturation", "moreLuminosity", "lessLuminosity", "change_2bpp", "blur", "negative", "blackWhite", "sepia", "isEdge", "", "", "", "", "", "", "oldPhoto", "pencilDraw", "colorDraw", "circlesBlack", "circlesWhite"]# ==================================================================class API():    @cherrypy.expose    def index(self):        return "API for 100Brains project. To use PUT, send POST request with a JSON {img , type, (effect), memeTopLine, imgExtension} where effects can be thumbnails, rotate, moreContrast, lessContrast, moreSaturation, lessSaturation, moreLuminosity, lessLuminosity, change_2bpp, blur, negative, blackWhite, sepia, isEdge, oldPhoto, pencilDraw, colorDraw, circlesBlack or circlesWhite"    # =================================================================================================================    # OK : GET    @cherrypy.expose    def get(self, id):        cherrypy.response.headers['Content-Type'] = 'image/jpeg'        # Go through the database and get file path        resultsGet = database.execute("SELECT path FROM gallery WHERE id = ?", (id, ))        for row in resultsGet:            path = row[0]        # returns image        return (open(path, 'rb').read())    # ===================================    # OK : GET any image saved in the folder, even without being registrated in the database (for intern - getThumbnails - purposes)    @cherrypy.expose    def getTemp(self, id):        cherrypy.response.headers['Content-Type'] = 'image/jpeg'        path = folderPath + "/" + str(id)        # returns image        return (open(path, 'rb').read())    # ===================================    # OK : GetImgInfo    @cherrypy.expose    def getImgInfo(self, id):        resultList = database.execute("SELECT * FROM gallery WHERE id = ?", (id, ))        message = []        for row in resultList:            id = str(row[0])            votes_up = int(row[1])            votes_down = int(row[2])            category = str(row[3])            date = int(row[4])            author = str(row[5])            #path = str(row[6])            views = int(row[7])            longdate = str(row[8])            username = str(row[9])        return json.dumps({            "author" : author,            #"path" : path,            "id" : id,            "date" : date,            "username" : username,            "views" : views,            "votes_down" : votes_down,            "category" : category,            "votes_up" : votes_up,            "longdate" : longdate        })    # =================================================================================================================    # OK : LIST    @cherrypy.expose    def list(self):        resultList = database.execute("SELECT * FROM gallery")        message = []        for row in resultList:            id         = str(row[0])            votes_up   = int(row[1])            votes_down = int(row[2])            category   = str(row[3])            date       = int(row[4])            author     = str(row[5])            #path       = str(row[6])            views      = int(row[7])            longdate   = str(row[8])            username   = str(row[9])            message.append(json.dumps({                "id"         : id,                "votes_up"   : votes_up,                "votes_down" : votes_down,                "category"   : category,                "date"       : date,                "author"     : author,                #"path"       : path,                "views"      : views,                "longdate"   : longdate,                "username"   : username            }))        # return "LIST"        return "[" + ",".join(message) + "]"    # ===================================    # OK : LIST-ALL    @cherrypy.tools.json_in()    @cherrypy.expose    def listAll(self):        # get actively listening addresses        req = urllib.request.Request(url="http://xcoa.av.it.pt/labi1617-p2-list")        addresses = urllib.request.urlopen(req).read().decode("utf-8")[1:-1].split(', ')        message = []        # for each listening address (which already includes our own), make a request        for addr in addresses:            addrNum = int(addr) % 10000            req = urllib.request.Request(url="http://xcoa.av.it.pt/labi1617-p2-g"+str(addrNum)+"/api/list")            try:                answer = urllib.request.urlopen(req).read().decode("utf-8")                message.append("{\"%s\":%s}" % (str(addrNum), answer))            except urllib.error.HTTPError:                pass            except urllib.error.URLError:                pass        return "[" + ",".join(message) + "]"    # =================================================================================================================    # OK: PUT-ADVANCED    @cherrypy.expose    @cherrypy.tools.json_out()    def putAdvanced(self, userID, id, type, allIDs):        # Get request info        #user = cherrypy.request.headers.get("X - Remote - User")        # Get photo info        date = time.time()        temp = time.ctime(date)        longdate = temp[4:10] + "," + temp[10:19] + "," + temp[19:]        path = folderPath + "/" + str(id)        # Update database        database.execute(            "INSERT INTO gallery(id, votes_up, votes_down, category, date, author, path, views, longdate, username) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",            (id, 0, 0, type, date, userID, path, 0, longdate, ""))        database.commit()        # remove temporary files (previews)        # allIDs = str(allIDs)[1:-1].split()[0].split(',')        # for img in allIDs:        #     imgPath = folderPath + "/" + img[1:]        #     if imgPath != path:        #         os.remove(imgPath)        return "[]"    # ===================================    # TODO : put    @cherrypy.expose    @cherrypy.tools.json_in()    def put(self, userID):        # Get request info        #user = cherrypy.request.headers.get("X - Remote - User")        info = cherrypy.request.json        img = info["img"]        type = info["type"]        imgExtension = info["imgExtension"]        filePath = ""        if (type == "PHOTO"):            imageInfo = img.split(',')            id = sha256(imageInfo[1].encode('utf-8')).hexdigest()            filePath = folderPath + "/" + id + "." + str(imageInfo[0]).split(';')[0].split('/')[1]            file = open(filePath, 'wb')            file.write(base64.b64decode(imageInfo[1]))            file.close()        if (type == "EFFECT"):            effect = info["effect"]            id = sha256(img.encode('utf-8')).hexdigest()            tempFilePath = folderPath + "/" + id + "." + imgExtension            file = open(filePath, 'wb')            file.write(base64.b64decode(img))            file.close()            # Apply selected effect            effectNum = effects.index(effect)            receivedImage = run_option(tempFilePath, effectNum)            # Save image            id = sha256(receivedImage.tobytes()).hexdigest()            filePath = folderPath + "/" + id + "." + imgExtension            receivedImage.save(filePath)        if (type == "MEME"):            topLine = info["memeTopLine"]            bottomLine = info["memeBottomLine"]            id = sha256(img.encode('utf-8')).hexdigest()            tempFilePath = folderPath + "/" + id + "." + imgExtension            file = open(filePath, 'wb')            file.write(base64.b64decode(img))            file.close()            # Apply selected meme            style = "meme"            # Applies and saves top line file (_tl)            receivedImage_tl = menu_server(filePath, topLine, "top", style)            newID_tl = sha256(receivedImage_tl.tobytes()).hexdigest() + "." + imgExtension            receivedFilePath_tl = folderPath + "/" + newID_tl            receivedImage_tl.save(receivedFilePath_tl)            # Applies and saves bottom line            receivedImage = menu_server(receivedFilePath_tl, bottomLine, "bottom", style)            id = sha256(receivedImage.tobytes()).hexdigest()            filePath = folderPath + "/" + id + "." + imgExtension            receivedImage.save(filePath)        # Add image to database - get photo info        date = time.time()        temp = time.ctime(date)        longdate = temp[4:10] + "," + temp[10:19] + "," + temp[19:]        # Update database        database.execute(            "INSERT INTO gallery(id, votes_up, votes_down, category, date, author, path, views, longdate, username) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",            (id, 0, 0, type, date, userID, filePath, 0, longdate, ""))        database.commit()    # =================================================================================================================    # OK : UpdateViews    @cherrypy.expose    @cherrypy.tools.json_out()    def updateViews(self, userID, imgID):        # Get info from request        #info = cherrypy.request.json        #user = cherrypy.request.headers.get("X - Remote - User")        #imgID = info["imgID"]        #views = info["views"]        # Update photo database        rawInfoGallery = database.execute("SELECT views FROM gallery WHERE id = ?", (imgID,))        for row in rawInfoGallery:            views = int(row[0])        views = views + 1        database.execute("UPDATE gallery SET views =? WHERE id = ?", (views, imgID,))        database.commit()        # Update user database        rawInfoUsers = database.execute("SELECT views FROM users WHERE userID = ?", (userID,))        for row in rawInfoUsers:            viewsUser = str(row[0])        if imgID not in viewsUser:            viewsUser += ", " + str(imgID)        database.execute("UPDATE users SET views =? WHERE userID =?", (viewsUser, userID,))        database.commit()        return "[]"    # =================================================================================================================    # TODO : Votes    @cherrypy.expose    @cherrypy.tools.json_out()    def updateVotes(self, userID, imgID, vote):        # Get info from request        #user = cherrypy.request.headers.get("X - Remote - User")        # Info from tables        rawInfoGallery = database.execute("SELECT votes_up, votes_down FROM gallery WHERE id = ?", (imgID,))        for row in rawInfoGallery:            upvotesPhoto = row[0]            downvotesPhoto = row[1]        rawInfoUsers = database.execute("SELECT upvotes, downvotes FROM users WHERE userID = ?", (userID,))        for row in rawInfoUsers:            upvotesUser = row[0]            downvotesUser = row[1]        if vote == 2 and id not in upvotesUser:            upvotesPhoto += 1            if (upvotesUser == ""):                upvotesUser = str(imgID)            else:                upvotesUser += ", " + str(imgID)        elif vote == 1 and imgID in upvotesUser:            upvotesPhoto -= 1            if (upvotesUser.index(str(imgID)) == 0):                upvotesUser.replace(str(imgID), "")            else:                upvotesUser.replace(", " + str(imgID), "")        elif vote == 0 and imgID not in downvotesUser:            downvotesPhoto -= 1            if (downvotesUser.index(str(imgID)) == 0):                downvotesUser.replace(str(imgID), "")            else:                downvotesUser.replace(", " + str(imgID), "")        elif vote == -1 and imgID in downvotesUser:            downvotesPhoto -= 1            if (downvotesUser.index(str(imgID)) == 0):                downvotesUser.replace(str(imgID), "")            else:                downvotesUser.replace(", " + str(imgID), "")        database.execute("UPDATE users SET upvotes = ? WHERE userID =?", (upvotesUser, userID, ))        database.execute("UPDATE users SET downvotes = ? WHERE userID =?", (downvotesUser, userID,))        database.execute("UPDATE gallery SET votes_up = ? WHERE id =?", (upvotesPhoto, imgID))        database.execute("UPDATE gallery SET votes_down = ? WHERE id =?", (downvotesPhoto, imgID))        database.commit()        return "[]"    # =================================================================================================================    # OK : Get meme preview    @cherrypy.expose    @cherrypy.tools.json_out()    def getMemePreview(self, tempImgID, topLine, bottomLine, imgExtension):        # Gets photo path        filePath = folderPath + "/" + tempImgID + "." + imgExtension        style = "meme"        # Applies and saves top line file (_tl)        receivedImage_tl = menu_server(filePath, topLine, "top", style)        newID_tl = sha256(receivedImage_tl.tobytes()).hexdigest() + "." + imgExtension        receivedFilePath_tl = folderPath + "/" + newID_tl        receivedImage_tl.save(receivedFilePath_tl)        # Applies and saves bottom line        receivedImage = menu_server(receivedFilePath_tl, bottomLine, "bottom", style)        newID = sha256(receivedImage.tobytes()).hexdigest() + "." + imgExtension        receivedFilePath = folderPath + "/" + newID        receivedImage.save(receivedFilePath)        # Create message        message = json.dumps({            "newImgID": newID        })        return message    # ===================================    # OK : Get effect preview    @cherrypy.tools.json_out()    @cherrypy.expose    def getEffectPreview(self, tempImgID, effect, imgExtension):        # Get photo path        filePath = folderPath + "/" + tempImgID + "." + imgExtension        # Apply effect        effectNum = effects.index(effect)        receivedImage = run_option(filePath, effectNum)        # Saves File        newID = sha256(receivedImage.tobytes()).hexdigest() + "." + imgExtension        receivedFilePath = folderPath + "/" + newID        receivedImage.save(receivedFilePath)        # Create message        message = json.dumps({            "newImgID": newID        })        return message    # ===================================    # OK : Get thumbnails    @cherrypy.expose    @cherrypy.tools.json_out()    def getEffectThumbnails(self, tempID, imgExtension):        # Get photo path        filePath = folderPath + "/" + tempID + "." + imgExtension        # Get thumbnails        receivedImage, thumbnails = run_option(filePath, 1)        message = []        # Create message (list of JSONs ["effect" , "id"})        for i in thumbnails:            for key, value in i.items():                newID = sha256(value.tobytes()).hexdigest()                receivedFilePath = folderPath + "/" + newID + "." + imgExtension                value.save(receivedFilePath)                message.append(json.dumps({                    "id": newID + "." + imgExtension,                    "effect": str(key),                    "image": str(base64.b64encode(open(receivedFilePath, 'rb').read()))[2:-1]                }))        return message    # ===================================    # OK : Get negative effect    @cherrypy.expose    @cherrypy.tools.json_out()    @cherrypy.tools.json_in()    def getNegative(self):        # Get info from request        info = cherrypy.request.json        img = info["img"]        imgExtension = info["imgExtension"]        # Save temp photo        id = sha256(img.encode('utf-8')).hexdigest()        filePath = folderPath + "/" + id + "." + imgExtension        file = open(filePath, 'wb')        file.write(base64.b64decode(img))        file.close()        # Applies effect (negative)        receivedImage = run_option(filePath, 11)        receivedFilePath = folderPath + "/" + id + "-neg." + imgExtension        receivedImage.save(receivedFilePath)        # Return info        message = json.dumps({            "tempImgID" : id + "." + imgExtension        })        return message    # =================================================================================================================    # OK : UserID    @cherrypy.expose    def userID(self, userID):        #user = cherrypy.request.headers.get("X - Remote - User")        resultList = database.execute("SELECT * FROM users WHERE userID = ?", (userID,))        message = []        username = userID        avatar = 0        views = json.dumps({"PHOTO": [], "EFFECT": [], "MEME": []})        upvotes = json.dumps({"PHOTO": [], "EFFECT": [], "MEME": []})        downvotes = json.dumps({"PHOTO": [], "EFFECT": [], "MEME": []})        # Doesn't exist        if (resultList.fetchone() == None):            database.execute("INSERT INTO users(userID, username, avatar, views, upvotes, downvotes) VALUES(?, ?, ?, ?, ?, ?)", (userID, username, avatar, views, upvotes, downvotes))            database.commit()        else:            for row in resultList:                username  = str(row[1])                avatar    = int(row[2])                views     = str(row[3])                upvotes   = str(row[4])                downvotes = str(row[5])        message.append(json.dumps({            "userID"   : userID,            "username" : username,            "avatar"   : avatar,            "views"    : views,            "upvotes"  : upvotes,            "downvotes": downvotes        }))        return message    # @cherrypy.expose    # def userID(self, userID):    #     #user = cherrypy.request.headers.get("X - Remote - User")    #    #     resultList = database.execute("SELECT * FROM users WHERE userID = ?", (userID,))    #     message = []    #     for row in resultList:    #         username  = str(row[1])    #         avatar    = int(row[2])    #         views     = str(row[3])    #         upvotes   = str(row[4])    #         downvotes = str(row[5])    #     else:    #         username  = userID    #         avatar    = 0    #         views     = json.dumps({"PHOTO":[],"EFFECT":[],"MEME":[]})    #         upvotes   = json.dumps({"PHOTO":[],"EFFECT":[],"MEME":[]})    #         downvotes = json.dumps({"PHOTO":[],"EFFECT":[],"MEME":[]})    #    #         database.execute("INSERT INTO users(userID, username, avatar, views, upvotes, downvotes) VALUES(?, ?, ?, ?, ?, ?)",    #         (userID, username, avatar, views, upvotes, downvotes))    #         database.commit()    #    #     message.append(json.dumps({    #         "userID"   : userID,    #         "username" : username,    #         "avatar"   : avatar,    #         "views"    : views,    #         "upvotes"  : upvotes,    #         "downvotes": downvotes    #     }))    #    #     return message    @cherrypy.expose    @cherrypy.tools.json_out()    def updateUserInfo(self, userID, avatar, username):        #user = cherrypy.request.headers.get("X - Remote - User")        database.execute("UPDATE users SET avatar = ?, username = ? WHERE userID =?", (avatar, username, userID))        database.commit()        return "[]"# ==================================================================class Root:    @cherrypy.expose    def index(self):        cherrypy.response.headers["Content-Type"] = "text/html"        path = "index.html"        return (open(path, "r").read())    api = API()# ==================================================================""" Runs """if __name__ == "__main__":    cherrypy.config.update( {'server.socket_host': '0.0.0.0' } )    cherrypy.quickstart(Root(), "/", config)