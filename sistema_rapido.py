# SISTEMA RÁPIDO E LEVE - SEM TRAVAMENTOS
from flask import Flask, jsonify, request
import sqlite3
from datetime import datetime
import threading

app = Flask(__name__)

# ============== BANCO SIMPLES ==============
def init_db():
    conn = sqlite3.connect('ponto.db')
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS pontos (id INTEGER PRIMARY KEY, nome TEXT, unidade TEXT, tipo TEXT, data TEXT, hora TEXT, lat REAL, lng REAL)')
    conn.commit()
    conn.close()

# ============== HTML MÍNIMO ==============
HTML = '''
<!DOCTYPE html>
<html>
<head>
    <title>Ponto</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body { font-family: Arial; padding: 20px; max-width: 500px; margin: 0 auto; }
        input, button { width: 100%; padding: 15px; margin: 10px 0; font-size: 16px; box-sizing: border-box; }
        button { border: none; color: white; cursor: pointer; }
        .entrada { background: green; }
        .saida { background: red; }
        .status { background: #f0f0f0; padding: 15px; border-radius: 5px; margin: 10px 0; text-align: center; }
    </style>
</head>
<body>
    <h1>📍 Ponto Eletrônico</h1>
    
    <input type="text" id="nome" placeholder="Nome completo" autocomplete="off">
    <input type="text" id="unidade" placeholder="Unidade de trabalho" autocomplete="off">
    
    <div class="status" id="location">
        📍 Localização: <span id="loc-text">Aguardando...</span>
    </div>
    
    <button class="entrada" onclick="registrar('entrada')">🟢 ENTRADA</button>
    <button class="saida" onclick="registrar('saida')">🔴 SAÍDA</button>
    
    <div id="result" style="margin: 20px 0; padding: 15px;"></div>
    
    <div style="text-align: center; margin-top: 30px;">
        <a href="/admin" style="color: #0066cc;">📊 Ver Registros</a>
    </div>
    
    <script>
    let lat = null;
    let lng = null;
    
    // Localização SIMPLES
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(function(pos) {
            lat = pos.coords.latitude;
            lng = pos.coords.longitude;
            document.getElementById('loc-text').innerHTML = 'OK (' + lat.toFixed(2) + ', ' + lng.toFixed(2) + ')';
        }, function() {
            document.getElementById('loc-text').innerHTML = 'Permita acesso';
        });
    }
    
    // Registrar
    function registrar(tipo) {
        var nome = document.getElementById('nome').value;
        var unidade = document.getElementById('unidade').value;
        
        if (!nome || !unidade) {
            alert('Preencha nome e unidade');
            return;
        }
        
        document.getElementById('result').innerHTML = '<div style="background: #ffffcc; padding: 10px;">Registrando...</div>';
        
        // AJAX SIMPLES
        var xhr = new XMLHttpRequest();
        xhr.open('POST', '/api/registrar', true);
        xhr.setRequestHeader('Content-Type', 'application/json');
        
        xhr.onload = function() {
            if (xhr.status === 200) {
                var data = JSON.parse(xhr.responseText);
                if (data.ok) {
                    document.getElementById('result').innerHTML = 
                        '<div style="background: #ccffcc; padding: 15px;">' +
                        '✅ Registrado! ' + data.hora + '<br>' +
                        'Tipo: ' + data.tipo.toUpperCase() +
                        '</div>';
                    document.getElementById('nome').value = '';
                    document.getElementById('unidade').value = '';
                } else {
                    document.getElementById('result').innerHTML = 
                        '<div style="background: #ffcccc; padding: 15px;">❌ ' + data.erro + '</div>';
                }
            } else {
                document.getElementById('result').innerHTML = 
                    '<div style="background: #ffcccc; padding: 15px;">❌ Erro de conexão</div>';
            }
        };
        
        xhr.send(JSON.stringify({
            nome: nome,
            unidade: unidade,
            tipo: tipo,
            lat: lat,
            lng: lng
        }));
    }
    </script>
</body>
</html>
'''

# ============== ROTAS PRINCIPAIS ==============
@app.route('/')
def home():
    return HTML

@app.route('/api/registrar', methods=['POST'])
def api_registrar():
    try:
        dados = request.json
        
        # Validação básica
        if not dados or not dados.get('nome') or not dados.get('unidade'):
            return jsonify({'ok': False, 'erro': 'Dados incompletos'})
        
        # Data/hora
        agora = datetime.now()
        data = agora.strftime('%Y-%m-%d')
        hora = agora.strftime('%H:%M:%S')
        
        # Salvar no banco (SIMPLES)
        conn = sqlite3.connect('ponto.db')
        c = conn.cursor()
        
        # Verificar se já registrou este tipo hoje
        c.execute("SELECT 1 FROM pontos WHERE nome=? AND data=? AND tipo=?",
                 (dados['nome'], data, dados['tipo']))
        
        if c.fetchone():
            conn.close()
            return jsonify({'ok': False, 'erro': 'Já registrou ' + dados['tipo'] + ' hoje'})
        
        # Inserir
        c.execute("INSERT INTO pontos (nome, unidade, tipo, data, hora, lat, lng) VALUES (?, ?, ?, ?, ?, ?, ?)",
                 (dados['nome'], dados['unidade'], dados['tipo'], data, hora, dados.get('lat'), dados.get('lng')))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'ok': True,
            'hora': hora,
            'tipo': dados['tipo'],
            'mensagem': 'Registrado com sucesso'
        })
        
    except Exception as e:
        return jsonify({'ok': False, 'erro': 'Erro interno'})

# ============== PÁGINA ADMIN ==============
@app.route('/admin')
def admin():
    conn = sqlite3.connect('ponto.db')
    c = conn.cursor()
    
    c.execute("SELECT * FROM pontos ORDER BY data DESC, hora DESC LIMIT 100")
    
    rows = c.fetchall()
    conn.close()
    
    html = '''
    <!DOCTYPE html>
    <html>
    <head><title>Registros</title>
    <style>
        body { font-family: Arial; padding: 20px; }
        table { width: 100%; border-collapse: collapse; }
        th, td { padding: 10px; border: 1px solid #ddd; }
        th { background: #f2f2f2; }
    </style>
    </head>
    <body>
        <h1>📊 Registros</h1>
        <p>Total: ''' + str(len(rows)) + ''' registros</p>
        <table>
            <tr><th>Data</th><th>Hora</th><th>Nome</th><th>Unidade</th><th>Tipo</th><th>Local</th></tr>
    '''
    
    for row in rows:
        tipo_color = 'green' if row[3] == 'entrada' else 'red'
        html += f'''
            <tr>
                <td>{row[4]}</td><td>{row[5]}</td><td>{row[1]}</td>
                <td>{row[2]}</td><td style="color:{tipo_color}"><b>{row[3].upper()}</b></td>
                <td>{row[6] if row[6] else ''}, {row[7] if row[7] else ''}</td>
            </tr>
        '''
    
    html += '''
        </table>
        <p style="margin-top: 20px;">
            <a href="/">← Voltar</a> | 
            <button onclick="exportar()">📥 Exportar CSV</button>
        </p>
        <script>
        function exportar() {
            window.location.href = '/exportar';
        }
        </script>
    </body>
    </html>
    '''
    
    return html

# ============== EXPORTAR ==============
@app.route('/exportar')
def exportar():
    conn = sqlite3.connect('ponto.db')
    c = conn.cursor()
    c.execute("SELECT * FROM pontos ORDER BY data DESC, hora DESC")
    
    csv = "ID,Nome,Unidade,Tipo,Data,Hora,Latitude,Longitude\\n"
    for row in c.fetchall():
        csv += f"{row[0]},{row[1]},{row[2]},{row[3]},{row[4]},{row[5]},{row[6] or ''},{row[7] or ''}\\n"
    
    conn.close()
    
    return app.response_class(
        csv,
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=ponto.csv'}
    )

# ============== INICIAR ==============
if __name__ == '__main__':
    init_db()
    
    print("=" * 60)
    print("🚀 SISTEMA RÁPIDO - PRONTO!")
    print("=" * 60)
    print("🌐 Abra a aba 'PORTS' e clique no 🌐 da porta 5000")
    print("📱 Página principal: /")
    print("📊 Registros: /admin")
    print("📥 Exportar: /exportar")
    print("=" * 60)
    
    # Configuração para evitar travamentos
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=False,  # DEBUG DESLIGADO (causa travamento)
        threaded=True,
        use_reloader=False
    )
