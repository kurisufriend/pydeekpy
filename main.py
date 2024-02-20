import requests, websockets, asyncio, json, re, threading, time, random, os, datetime
import traceback
import html
import ratelimiter
import subprocess

class bird_inst():
    def __init__(self, endpoint, httpendpoint, config):
        self.endpoint = endpoint
        self.httpendpoint = httpendpoint
        self.config = config
        self.ws = None
        self.headers = {
            "User-Agent": "renabot",
            "Origin": "https://deek.chat", 
            "DNT": "1",
        }
        self.send_queue = []
        self.apitok = ""
        self.sesside = ""

        self.limiter = ratelimiter.ratelimit(.5)
        self.lastmessages = []

    def auth(self, name, passwd):
        h = {
            "User-Agent": "renabot",
            "Origin": "https://deek.chat", 
            "DNT": "1",
        }
        res = requests.post(self.httpendpoint+"/login/submit", headers=h, data={"name": name, "password": passwd, "submit": "log+in"}, allow_redirects=False)
        print(res.headers)
        token = re.search("(?:api_token)=[^;]+", res.headers.get("Set-Cookie")).group(0)
        sessid = re.search("(?:session_id)=[^;]+", res.headers.get("Set-Cookie")).group(0)
        self.apitok = token
        self.sesside = sessid
        h["Cookie"] = token+"; "+sessid
        self.headers = h
    async def run(self):
        print("running main loop")
        async with websockets.connect(self.endpoint, extra_headers=self.headers) as self.ws:
            print(self.ws)
            asyncio.get_event_loop().create_task(self._send_post())
            asyncio.get_event_loop().create_task(self.ship_queued_messages())
            while True:
                data = json.loads(await self.ws.recv())
                print(">>>", data)
                #getattr(self, "handle_"+data["type"], None)(data)
                try: await getattr(self, "handle_"+data["type"], None)(data)
                except Exception as e: print("hey buddy your shits fucked thought you might want to know", e)
    async def handle_message(self, ctx):
        room = int(ctx["roomId"])
        print("btw i just got this", ctx["data"]["text"])
        ctx["data"]["text"] = html.unescape(ctx["data"]["text"])
        #if ctx["data"]["name"] == self.config["deek_user"]: return
        mesg = ctx["data"]["text"].replace("\n", " ")
        
        if mesg.startswith("^test"):
            self.send_post("harohime~", room)
        elif mesg.startswith("^image"):
            cookies = {
                'session_id': self.sesside.split("=")[1],
                'api_token': self.apitok.split("=")[1],
            }

            headers = {
            #    'Content-Type': 'multipart/form-data; boundary=---------------------------108795733040959562943643236942',
            }



            files = {
                "text": (None, "aids"),
                "files[]": ("temp.png", open("temp.png", "rb").read(), "image/png")
            }

            response = requests.post('https://deek.chat/message/send/'+str(room), cookies=cookies, headers=headers, files=files)

        self.lastmessages.append(mesg)
        if len(self.lastmessages) > 15:
            self.lastmessages.pop(0)
    

    async def handle_messageStart(self, ctx): pass
    async def handle_messageChange(self, ctx): pass
    async def handle_messageEnd(self, ctx): self.handle_message(ctx)
    async def handle_avatar(self, ctx): pass
    async def handle_loadUsers(self, ctx): pass
    async def handle_files(self, ctx):
        ctx["data"]["text"] = html.unescape(ctx["data"]["text"])
        for f in ctx["data"]["files"]:
            pass
    async def handle_exit(self, ctx): pass
    async def handle_enter(self, ctx): pass
    async def handle_userLoaded(self, ctx): pass
    def send_post(self, msg, room):
        if self.ws is None: return
        print(msg)
        self.send_queue.append((msg, room))
    async def _send_post(self):
        while True:
            for msg in self.send_queue:
                await self.ws.send(json.dumps({"type": "message", "data": msg[0], "roomId": msg[1]}))
                self.send_queue.remove(msg)
                print("shipped", msg)
            await asyncio.sleep(.1)
    async def ship_queued_messages(self):
        while True:
            self.limiter.lazyrun()
            await asyncio.sleep(.1)
cfg = json.loads(open("config.json", "r").read())
bi = bird_inst("wss://deek.chat/ws", "https://deek.chat", cfg)
print("yes hello birdchat here")
bi.auth(cfg["deek_user"], cfg["deek_passwd"])
while True:
    try: asyncio.run(bi.run())
    except KeyboardInterrupt:
        break
    except Exception as e:
        print("yo ur shits broken", e)
        print(traceback.format_exc())
        continue
