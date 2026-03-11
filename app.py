from flask import Flask, request, jsonify
from flask_cors import CORS
import urllib.request
import json
import os

app = Flask(__name__)
CORS(app)

API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

@app.route("/")
def index():
return "LCGE Scanner API — OK", 200

@app.route("/api/extract", methods=["POST"])
def extract():
try:
body = request.get_json()
image_b64 = body.get("image", "")
if not image_b64:
return jsonify({"error": "Image manquante"}), 400

prompt = """Extrais les données de cette fiche client énergie. Réponds UNIQUEMENT avec ce JSON valide, rien d'autre :
{"nom":"","type":"particulier","tel":"","email":"","ddn":"","ville":"","fournisseur":"","energie":"","date_signature":"","ancien_fournisseur":"","statut":"actif"}
Règles :
- type: particulier ou pro
- energie: Electricité, Gaz, ou Dual
- ddn: date de naissance JJ/MM/AAAA
- date_signature: date passage/signature JJ/MM/AAAA
- Si info absente: laisse vide"""

payload = json.dumps({
"model": "claude-sonnet-4-20250514",
"max_tokens": 600,
"system": "Tu es un extracteur OCR de fiches clients énergie. Réponds UNIQUEMENT avec du JSON valide, sans texte avant ni après.",
"messages": [{
"role": "user",
"content": [
{"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": image_b64}},
{"type": "text", "text": prompt}
]
}]
}).encode("utf-8")

req = urllib.request.Request(
"https://api.anthropic.com/v1/messages",
data=payload,
headers={
"Content-Type": "application/json",
"x-api-key": API_KEY,
"anthropic-version": "2023-06-01"
}
)

with urllib.request.urlopen(req, timeout=30) as resp:
result = json.loads(resp.read().decode("utf-8"))
text = "".join(b["text"] for b in result.get("content", []) if b.get("type") == "text").strip()
text = text.replace("```json", "").replace("```", "").strip()
s, e = text.find("{"), text.rfind("}")
if s == -1 or e == -1:
return jsonify({"error": "Réponse inattendue"}), 500
data = json.loads(text[s:e+1])
return jsonify(data)

except Exception as ex:
return jsonify({"error": str(ex)}), 500

if __name__ == "__main__":
port = int(os.environ.get("PORT", 5000))
app.run(host="0.0.0.0", port=port)
