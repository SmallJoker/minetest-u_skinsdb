#!/usr/bin/python3
from http.client import HTTPConnection
import json
import base64
import sys

def die(message,code=23):
		print(message,file=sys.stderr)
		raise SystemExit(code)

server = "minetest.fensta.bplaced.net"
skinsdir = "u_skins/textures/"
metadir = "u_skins/meta/"
curskin = 0
pages = None

def replace(path,encoding=None):
	mode = "wt" if encoding else "wb"
	# an unpredictable temp name only needed for a+rwxt directories
	tmp = '.'+path+'-tmp'
	def deco(handle):
		with open(tmp,mode,encoding=encoding) as out:
			yield out
		os.rename(tmp,path)
	return deco

def maybeReplace(path,encoding=None):
	def deco(handle):
		if os.path.exists(path): return
		return replace(path,encoding)(handle)	

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
		preview = skinsdir + "character_" + str(curskin) + "_preview.png"
		if os.path.exists(preview): continue
		foundOne = True
		tmp = dest+'-tmp'
		@maybeReplace(skinsdir + "character_" + str(curskin) + ".png")
		def go(f):
			f.write(base64.b64decode(bytes(s["img"], 'utf-8')))
			f.close()
			
		@maybeReplace(metadir + "character_" + str(curskin) + ".txt",
					  encoding='utf-8')
		def go(f):
			f.write(str(s["name"]) + '\n')
			f.write(str(s["author"]) + '\n')
			f.write(str(s["license"]))
		try:
			c.request("GET", "/skins/1/" + str(s["id"]) + ".png")
			r = c.getresponse()
		except HTTPException as e:
			print(type(e),dir(e))
			raise(e)
		if r.status != 200:
			print("Error", r.status)
			continue
		@replace(preview)
		def go(f):
			shutil.copyfileobj(r,f)
	if not foundOne:
		print("No skins updated on this page. Seems we're done?")
		raise SystemExit
addpage(1)
curpage = 1
while pages > curpage:
	curpage = curpage + 1
	addpage(curpage)
print("Skins have been updated!")
