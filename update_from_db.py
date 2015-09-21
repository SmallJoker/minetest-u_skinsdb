#!/usr/bin/python3
from http.client import HTTPConnection,HTTPException
import json
import base64
from contextlib import closing
import sys,os,shutil

def die(message,code=23):
        print(message,file=sys.stderr)
        raise SystemExit(code)

server = "minetest.fensta.bplaced.net"
skinsdir = "u_skins/textures/"
metadir = "u_skins/meta/"
curskin = 0
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
        print('updating skin',curskin)
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
        try:
            c.request("GET", url)
            with closing(c.getresponse()) as r:
                if r.status != 200:
                    print("Error", r.status)
                    continue
                @replace(skinsdir,previewbase,path=preview)
                def go(f):
                    shutil.copyfileobj(r,f)
        except HTTPException as e:
            die("Couldn't get {} because of a {} (url={})".format(
                s["id"],
                e,
                url))
    if not foundOne:
        print("No skins updated on this page. Seems we're done?")
        raise SystemExit
addpage(1)
curpage = 1
while pages > curpage:
    curpage = curpage + 1
    addpage(curpage)
print("Skins have been updated!")
