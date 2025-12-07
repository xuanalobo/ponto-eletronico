from flask import Flask, render_template_string
import datetime

app = Flask(__name__)

PAGINA = '''
<!DOCTYPE html>
<html>
<head>
    <title>Ponto Eletrônico</title>
    <style>
        body { font-family: Arial; padding: 40px; text-align: center; }
        .container { max-width: 500px; margin: 0 auto; }
        input, button { width: 100%; padding: 15px; margin: 10px 0; font-size: 16px; }
        button { background: #007bff; color: white; border: none; cursor: pointer; }
    </style>
</head>
<body>
    <div class="container">
        <h1>📍 PONTO ELETRÔNICO</h1>
        <p>Sistema de registro de ponto</p>
        
        <input type="text" placeholder="Seu nome completo" id="nome">
        <input type="text" placeholder="Unidade de trabalho" id="unidade">
        
        <div style="background: #f0f0f0; padding: 15px; margin: 20px 0; border-radius: 10px;">
            <div id="localizacao">📍 Localização: Aguardando permissão...</div>
        </div>
        
        <button onclick="registrar('entrada')" style="background: #28a745;">
            🟢 REGISTRAR ENTRADA
        </button>
        
        <button onclick="registrar('saida')" style="background: #dc3545;">
            🔴 REGISTRAR SAÍDA
        </button>
        
        <div id="resultado" style="margin-top: 20px; padding: 15px;"></div>
        
        <div style="margin-top: 40px; padding-top: 20px; border-top: 1px solid #ddd;">
            <a href="/admin" style="color: #666;">�� Acessar Painel Admin</a>
        </div>
    </div>
    
    <script>
    let lat, lng;
    
    // Obter localização
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(
            function(pos) {
                lat = pos.coords.latitude;
                lng = pos.coords.longitude;
                document.getElementById('localizacao').innerHTML = 
                    '📍 Localização obtida!<br>Lat: ' + lat.toFixed(4) + ', Lng: ' + lng.toFixed(4);
            },
            function() {
                document.getElementById('localizacao').innerHTML = 
                    '⚠️ Permita o acesso à localização';
            }
        );
    }
    
    function registrar(tipo) {
        const nome = document.getElementById('nome').value;
        const unidade = document.getElementById('unidade').value;
        
        if (!nome || !unidade) {
            alert('Preencha nome e unidade');
            return;
        }
        
        document.getElementById('resultado').innerHTML = 
            '<div style="background: #fff3cd; padding: 10px;">Registrando...</div>';
        
        // Simular registro
        setTimeout(function() {
            const hora = new Date().toLocaleTimeString('pt-BR');
            document.getElementById('resultado').innerHTML = 
                '<div style="background: #d4edda; padding: 15px;">' +
                '✅ Ponto ' + tipo + ' registrado!<br>' +
                '⏰ ' + hora + '<br>' +
                '👤 ' + nome + ' | 🏢 ' + unidade +
                '</div>';
            
            // Limpar campos
            document.getElementById('nome').value = '';
            document.getElementById('unidade').value = '';
        }, 1000);
    }
    </script>
</body>
</html>
'''

@app.route('/')
def home():
    return render_template_string(PAGINA)

@app.route('/admin')
def admin():
    return '''
    <!DOCTYPE html>
    <html>
    <head><title>Admin</title></head>
    <body style="padding: 30px;">
        <h1>📊 PAINEL ADMINISTRATIVO</h1>
        <p>Aqui você verá todos os registros em tempo real.</p>
        <p>Funcionalidades em desenvolvimento...</p>
        <a href="/">← Voltar</a>
    </body>
    </html>
    '''

if __name__ == '__main__':
    print("=" * 60)
    print("🚀 SISTEMA DE PONTO ELETRÔNICO")
    print("=" * 60)
    print("✅ Servidor rodando na porta 5000")
    print("🌐 Acesse a URL na aba 'PORTS'")
    print("=" * 60)
    app.run(host='0.0.0.0', port=5000, debug=True)
