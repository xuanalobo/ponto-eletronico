from flask import Flask
app = Flask(__name__)

@app.route('/')
def home():
    return "<h1 style='color:green;'>✅ FUNCIONANDO!</h1><p>Flask está rodando.</p>"

if __name__ == '__main__':
    print("🌐 TENTE ACESSAR: http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
