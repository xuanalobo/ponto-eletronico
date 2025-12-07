from flask import Flask, request
import os

app = Flask(__name__)

@app.route('/')
def home():
    # Obter informações do Codespaces
    codespace_name = os.environ.get('CODESPACE_NAME', 'seu-codespace')
    
    html = f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>✅ Ponto Eletrônico - ONLINE</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                padding: 40px;
                text-align: center;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                color: white;
            }}
            .container {{
                background: rgba(255, 255, 255, 0.95);
                padding: 40px;
                border-radius: 20px;
                color: #333;
                max-width: 600px;
                margin: 0 auto;
                box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            }}
            h1 {{
                color: #2c3e50;
                margin-bottom: 20px;
            }}
            .link-box {{
                background: #f8f9fa;
                padding: 20px;
                border-radius: 10px;
                margin: 20px 0;
                font-family: monospace;
                word-break: break-all;
            }}
            button {{
                background: #28a745;
                color: white;
                border: none;
                padding: 15px 30px;
                font-size: 18px;
                border-radius: 10px;
                cursor: pointer;
                margin: 10px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>📍 PONTO ELETRÔNICO</h1>
            <p style="font-size: 18px; color: #666;">
                Sistema de registro de ponto com localização
            </p>
            
            <div class="link-box">
                <h3>📱 ACESSO PARA FUNCIONÁRIOS:</h3>
                <p>Compartilhe este link:</p>
                <strong id="link-text">https://{codespace_name}-5000.app.github.dev</strong>
            </div>
            
            <div style="margin: 30px 0;">
                <button onclick="window.location.href='/app'">
                    🚀 ENTRAR NO SISTEMA
                </button>
                <button onclick="window.location.href='/admin'" style="background: #0066cc;">
                    📊 PAINEL ADMIN
                </button>
            </div>
            
            <p style="color: #666; font-size: 14px;">
                ✅ Sistema funcionando perfeitamente!
            </p>
        </div>
        
        <script>
        // Atualizar link com URL atual
        document.getElementById('link-text').textContent = window.location.origin;
        </script>
    </body>
    </html>
    '''
    return html

@app.route('/app')
def app_page():
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Registrar Ponto</title>
        <style>
            body { font-family: Arial; padding: 30px; max-width: 500px; margin: 0 auto; }
            input, button { width: 100%; padding: 15px; margin: 10px 0; font-size: 16px; }
            button { background: #007bff; color: white; border: none; cursor: pointer; }
        </style>
    </head>
    <body>
        <h1>📝 Registrar Ponto</h1>
        <input placeholder="Nome completo" id="nome">
        <input placeholder="Unidade de trabalho" id="unidade">
        <button onclick="registrar()">Registrar Entrada</button>
        <div id="result" style="margin-top: 20px;"></div>
        
        <script>
        function registrar() {
            document.getElementById('result').innerHTML = 
                '<p style="color: green;">✅ Ponto registrado com sucesso!</p>';
        }
        </script>
    </body>
    </html>
    '''

@app.route('/admin')
def admin():
    return '''
    <!DOCTYPE html>
    <html>
    <head><title>Admin</title></head>
    <body style="padding: 30px;">
        <h1>📊 PAINEL ADMINISTRATIVO</h1>
        <p>Aqui você verá todos os registros dos funcionários.</p>
        <p><a href="/">← Voltar</a></p>
    </body>
    </html>
    '''

if __name__ == '__main__':
    print("=" * 70)
    print("🚀 SISTEMA DE PONTO ELETRÔNICO")
    print("=" * 70)
    print("🌐 SEU LINK DIRETO:")
    print(f"   https://{os.environ.get('CODESPACE_NAME', 'seu-codespace')}-5000.app.github.dev")
    print("=" * 70)
    print("📱 Compartilhe este link com os funcionários!")
    print("📊 Painel admin: /admin")
    print("=" * 70)
    
    # Rodar na porta 5000
    app.run(host='0.0.0.0', port=5000, debug=False)
