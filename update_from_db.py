#!/usr/bin/python3
from http.client import HTTPConnection,HTTPException,BadStatusLine
import json
import base64
from contextlib import closing
import sys,os,shutil,time

def die(message,code=23):
        print(message,file=sys.stderr)
        raise SystemExit(code)

server = "minetest.fensta.bplaced.net"
skinsdir = "u_skins/textures/"
metadir = "u_skins/meta/"
curskin = 580
curpage = 59
pages = None

def replace(location,base,encoding=None,path=None):
    if path is None:
        path = os.path.join(location,base)
    mode = "wt" if encoding else "wb"
    # an unpredictable temp name only needed for a+rwxt directories
    tmp = os.path.join(location,'.'+base+'-tmp')
    def deco(handle):
        with open(tmp,mode,encoding=encoding) as out:
            handle(out)
        os.rename(tmp,path)
    return deco

def maybeReplace(location,base,encoding=None):
    def deco(handle):
        path = os.path.join(location,base)
        if os.path.exists(path): return
        return replace(location,base,encoding=encoding,path=path)(handle)
    return deco

class Pipeline(list):
    "Gawd why am I being so elaborate?"
    def __init__(self, threshold=10):
        "threshold is how many requests in parallel to pipeline"
        self.threshold = threshold
        self.sent = True
    def __enter__(self,*a):
        self.reopen()
    def __exit__(self):
        self.drain()
    def reopen(self):
        self.c = HTTPConnection(server)
        self.send()
    def append(self,url,recv,diemessage):
        super().append((url,recv,diemessage))
        if len(self) > self.threshold:			
            self.send()
            self.drain()
    def trydrain(self):		
        for url,recv,diemessage in self:
            try:
                recv(self.c)
            except BadStatusLine as e:
                return False			
            except HTTPException as e:
                die(diemessage+' (url='+url+')')
            self.clear()
            return True
    def drain(self):
        print('draining pipeline...')
        assert self.sent, "Can't drain without sending the requests!"
        self.sent = False
        while trydrain() is not True:
            self.c.close()
            print('derped requesting',url)
            print('drain failed, trying again')
            time.sleep(1)
            self.reopen()
    def trysend(self):
        for url,_,diemessage in pipeline:
            try:
                self.c.request("GET", url)
            except BadStatusLine:
                return False
            except HTTPException as e:
                die(diemessage)
        return True
    def send(self):
        if self.sent: return
        print('filling pipeline...')
        while self.tryresend() is not True:
            self.c.close()
            print('derped resending')
            time.sleep(1)
            self.reopen()
        self.sent = True
        
with Pipeline() as pipeline:
    # two connections is okay, right? one for json, one for preview images
    c = HTTPConnection(server)
    def addpage(page):
        global curskin, pages
        print("Page: " + str(page))
        r = 0
        try:
            c.request("GET", "/api/get.json.php?getlist&page=" + str(page) + "&outformat=base64")
            r = c.getresponse()
        except Exception:
            if r != 0:
                if r.status != 200:
                    die("Error", r.status)
            return
        
        data = r.read().decode()
        l = json.loads(data)
        if not l["success"]:
            die("Success != True")
        r = 0
        pages = int(l["pages"])
        foundOne = False
        for s in l["skins"]:
            # make sure to increment this, even if the preview exists!
            curskin = curskin + 1
            previewbase = "character_" + str(curskin) + "_preview.png"
            preview = os.path.join(skinsdir, previewbase)
            if os.path.exists(preview):
                print('skin',curskin,'already retrieved')
                continue
            print('updating skin',curskin,'id',s["id"])
            foundOne = True
            @maybeReplace(skinsdir, "character_" + str(curskin) + ".png")
            def go(f):
                f.write(base64.b64decode(bytes(s["img"], 'utf-8')))
                f.close()
                
            @maybeReplace(metadir, "character_" + str(curskin) + ".txt",
                          encoding='utf-8')
            def go(f):
                f.write(str(s["name"]) + '\n')
                f.write(str(s["author"]) + '\n')
                f.write(str(s["license"]))
            url = "/skins/1/" + str(s["id"]) + ".png"
            def tryget(c):			
                with closing(c.getresponse()) as r:
                    if r.status != 200:
                        print("Error", r.status)
                        return
                    @replace(skinsdir,previewbase,path=preview)
                    def go(f):
                        shutil.copyfileobj(r,f)
                
            pipeline.append(url,tryget,
                            "Couldn't get {} because of a {}".format(
                                s["id"],
                                e))
        if not foundOne:
            print("No skins updated on this page. Seems we're done?")
            #raise SystemExit
    addpage(1)
    while pages > curpage:
        curpage = curpage + 1
        addpage(curpage)
    print("Skins have been updated!")
    
