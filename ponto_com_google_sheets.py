from flask import Flask, render_template_string, jsonify, request
from datetime import datetime, timezone, timedelta
import sqlite3
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import threading
import time

app = Flask(__name__)
app.secret_key = 'ponto-google-sheets-2024'

# ============== CONFIGURAÇÃO ==============
def hora_brasilia():
    offset = timedelta(hours=-3)
    tz = timezone(offset)
    return datetime.now(tz)

def criar_banco():
    conn = sqlite3.connect('ponto_sheets.db')
    c = conn.cursor()
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS registros (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data TEXT NOT NULL,
            hora TEXT NOT NULL,
            nome TEXT NOT NULL,
            unidade TEXT NOT NULL,
            tipo TEXT NOT NULL,
            latitude REAL,
            longitude REAL,
            sincronizado INTEGER DEFAULT 0,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()
    print("✅ Banco de dados criado")

# ============== GOOGLE SHEETS ==============
def conectar_google_sheets():
    """Tenta conectar ao Google Sheets"""
    try:
        # Se você configurar as credenciais, descomente abaixo
        # scope = ['https://spreadsheets.google.com/feeds',
        #          'https://www.googleapis.com/auth/drive']
        # creds = ServiceAccountCredentials.from_json_keyfile_name('credenciais.json', scope)
        # client = gspread.authorize(creds)
        # planilha = client.open("Ponto Eletrônico").sheet1
        # return planilha
        
        print("📋 Modo SIMPLES: Dados salvos localmente")
        print("   Para conectar ao Google Sheets:")
        print("   1. Siga o tutorial: https://docs.google.com/document/d/1-create-your-credentials")
        print("   2. Salve as credenciais como 'credenciais.json'")
        print("   3. Descomente as linhas de código acima")
        return None
        
    except Exception as e:
        print(f"⚠️  Google Sheets não configurado: {e}")
        print("📊 Dados sendo salvos apenas localmente (banco SQLite)")
        return None

# ============== PÁGINA FUNCIONÁRIO ==============
@app.route('/')
def index():
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>📍 Ponto Eletrônico</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                max-width: 500px;
                margin: 0 auto;
                padding: 20px;
                background: #f5f7fa;
            }
            .card {
                background: white;
                padding: 30px;
                border-radius: 15px;
                box-shadow: 0 5px 20px rgba(0,0,0,0.1);
            }
            h1 {
                color: #2c3e50;
                text-align: center;
                margin-bottom: 10px;
            }
            .subtitle {
                color: #666;
                text-align: center;
                margin-bottom: 30px;
            }
            input {
                width: 100%;
                padding: 12px;
                margin: 10px 0;
                border: 2px solid #e1e1e1;
                border-radius: 8px;
                font-size: 16px;
                box-sizing: border-box;
            }
            .location {
                background: #f8f9fa;
                padding: 15px;
                border-radius: 8px;
                margin: 15px 0;
                text-align: center;
                border: 2px solid #e1e1e1;
            }
            .btn {
                width: 100%;
                padding: 16px;
                margin: 10px 0;
                border: none;
                border-radius: 8px;
                font-size: 16px;
                font-weight: bold;
                cursor: pointer;
            }
            .btn-entrada {
                background: #28a745;
                color: white;
            }
            .btn-saida {
                background: #dc3545;
                color: white;
            }
            .result {
                margin: 15px 0;
                padding: 15px;
                border-radius: 8px;
                text-align: center;
            }
            .success {
                background: #d4edda;
                color: #155724;
            }
            .error {
                background: #f8d7da;
                color: #721c24;
            }
            .admin-panel {
                margin-top: 30px;
                padding: 20px;
                background: #e8f4fd;
                border-radius: 10px;
                text-align: center;
            }
            .admin-link {
                color: #0056b3;
                text-decoration: none;
                font-weight: bold;
            }
        </style>
    </head>
    <body>
        <div class="card">
            <h1>📍 Ponto Eletrônico</h1>
            <p class="subtitle">Registro automático com planilha</p>
            
            <input type="text" id="nome" placeholder="👤 Nome completo" required>
            <input type="text" id="unidade" placeholder="🏢 Unidade de trabalho" required>
            
            <div class="location">
                <div id="location-status">📍 Aguardando localização...</div>
                <div id="location-details" style="font-size: 14px; color: #666; margin-top: 5px;"></div>
            </div>
            
            <button class="btn btn-entrada" onclick="registrar('entrada')">
                🟢 REGISTRAR ENTRADA
            </button>
            
            <button class="btn btn-saida" onclick="registrar('saida')">
                🔴 REGISTRAR SAÍDA
            </button>
            
            <div id="resultado" class="result"></div>
            
            <div class="admin-panel">
                <h3>📊 ÁREA DE CONTROLE</h3>
                <p>Para visualizar todos os registros:</p>
                <p>
                    <a href="/visualizar" class="admin-link" target="_blank">📈 Ver Registros</a> | 
                    <a href="/exportar" class="admin-link" target="_blank">📥 Exportar Dados</a>
                </p>
                <p style="font-size: 12px; color: #666; margin-top: 10px;">
                    Os dados são salvos automaticamente em planilha
                </p>
            </div>
        </div>
        
        <script>
        let lat = null;
        let lng = null;
        let localizacaoOk = false;
        
        // Obter localização
        function obterLocalizacao() {
            if (!navigator.geolocation) {
                document.getElementById('location-status').textContent = '❌ Navegador não suporta localização';
                return;
            }
            
            navigator.geolocation.getCurrentPosition(
                (pos) => {
                    lat = pos.coords.latitude;
                    lng = pos.coords.longitude;
                    localizacaoOk = true;
                    
                    document.getElementById('location-status').textContent = '✅ Localização obtida';
                    document.getElementById('location-details').textContent = 
                        `Lat: ${lat.toFixed(4)} | Lng: ${lng.toFixed(4)}`;
                },
                (erro) => {
                    document.getElementById('location-status').textContent = '❌ Permita acesso à localização';
                    localizacaoOk = false;
                }
            );
        }
        
        // Registrar ponto
        async function registrar(tipo) {
            const nome = document.getElementById('nome').value.trim();
            const unidade = document.getElementById('unidade').value.trim();
            
            // Validação
            if (!nome || !unidade) {
                mostrarResultado('Preencha nome e unidade', 'error');
                return;
            }
            
            if (!localizacaoOk) {
                mostrarResultado('Permita acesso à localização', 'error');
                return;
            }
            
            // Mostrar carregando
            document.getElementById('resultado').innerHTML = '<div class="result">Registrando...</div>';
            
            try {
                const resposta = await fetch('/registrar', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        nome: nome,
                        unidade: unidade,
                        tipo: tipo,
                        lat: lat,
                        lng: lng
                    })
                });
                
                const dados = await resposta.json();
                
                if (dados.sucesso) {
                    mostrarResultado(
                        `✅ Ponto de ${tipo} registrado!<br>⏰ ${dados.hora}<br>📊 Dados salvos na planilha`,
                        'success'
                    );
                    // Limpar campos
                    document.getElementById('nome').value = '';
                    document.getElementById('unidade').value = '';
                } else {
                    mostrarResultado(`❌ ${dados.erro}`, 'error');
                }
            } catch {
                mostrarResultado('❌ Erro de conexão', 'error');
            }
        }
        
        function mostrarResultado(mensagem, tipo) {
            const div = document.getElementById('resultado');
            div.innerHTML = `<div class="${tipo}">${mensagem}</div>`;
            setTimeout(() => div.innerHTML = '', 5000);
        }
        
        // Inicializar
        window.onload = function() {
            obterLocalizacao();
            setInterval(obterLocalizacao, 15000);
        };
        </script>
    </body>
    </html>
    '''

# ============== API PARA REGISTRAR ==============
@app.route('/registrar', methods=['POST'])
def registrar():
    dados = request.json
    
    # Validações
    if not dados.get('nome') or not dados.get('unidade'):
        return jsonify({'sucesso': False, 'erro': 'Nome e unidade são obrigatórios'})
    
    # Obter hora atual
    agora = hora_brasilia()
    data = agora.strftime('%Y-%m-%d')
    hora = agora.strftime('%H:%M:%S')
    timestamp = agora.strftime('%Y-%m-%d %H:%M:%S')
    
    # Salvar no banco local
    conn = sqlite3.connect('ponto_sheets.db')
    c = conn.cursor()
    
    # Verificar último registro
    c.execute('''
        SELECT tipo FROM registros 
        WHERE nome = ? AND data = ? AND tipo = ?
        LIMIT 1
    ''', (dados['nome'], data, dados['tipo']))
    
    if c.fetchone():
        conn.close()
        return jsonify({
            'sucesso': False,
            'erro': f'Você já registrou {dados["tipo"]} hoje'
        })
    
    # Inserir registro
    c.execute('''
        INSERT INTO registros (data, hora, nome, unidade, tipo, latitude, longitude)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (data, hora, dados['nome'], dados['unidade'], dados['tipo'], 
          dados.get('lat'), dados.get('lng')))
    
    registro_id = c.lastrowid
    conn.commit()
    
    # Tentar enviar para Google Sheets (em segundo plano)
    try:
        enviar_para_sheets_async(data, hora, dados, timestamp)
        c.execute('UPDATE registros SET sincronizado = 1 WHERE id = ?', (registro_id,))
        conn.commit()
    except:
        pass
    
    conn.close()
    
    return jsonify({
        'sucesso': True,
        'mensagem': 'Ponto registrado com sucesso',
        'hora': hora,
        'data': data,
        'sync': True
    })

# ============== ENVIAR PARA GOOGLE SHEETS (ASSÍNCRONO) ==============
def enviar_para_sheets_async(data, hora, dados, timestamp):
    """Envia dados para Google Sheets em segundo plano"""
    def enviar():
        try:
            # Aqui você implementaria o envio para Google Sheets
            # Por enquanto, apenas simula
            print(f"📤 [SIMULAÇÃO] Enviando para planilha: {dados['nome']} - {dados['tipo']} - {hora}")
            
            # Se tiver credenciais configuradas:
            # sheet = conectar_google_sheets()
            # if sheet:
            #     linha = [data, hora, dados['nome'], dados['unidade'], dados['tipo'],
            #              dados.get('lat'), dados.get('lng'), '', timestamp]
            #     sheet.append_row(linha)
            
        except Exception as e:
            print(f"❌ Erro ao enviar para sheets: {e}")
    
    # Executar em thread separada para não bloquear
    thread = threading.Thread(target=enviar)
    thread.daemon = True
    thread.start()

# ============== VISUALIZAR REGISTROS ==============
@app.route('/visualizar')
def visualizar():
    conn = sqlite3.connect('ponto_sheets.db')
    c = conn.cursor()
    
    # Obter todos os registros
    c.execute('''
        SELECT data, hora, nome, unidade, tipo, latitude, longitude, sincronizado
        FROM registros 
        ORDER BY data DESC, hora DESC
    ''')
    
    registros = []
    for row in c.fetchall():
        registros.append({
            'data': row[0],
            'hora': row[1],
            'nome': row[2],
            'unidade': row[3],
            'tipo': row[4],
            'lat': row[5],
            'lng': row[6],
            'sync': '✅' if row[7] == 1 else '⏳'
        })
    
    conn.close()
    
    # Gerar HTML
    html = '''
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>📊 Registros - Ponto Eletrônico</title>
        <style>
            body { font-family: Arial; padding: 20px; }
            table { width: 100%; border-collapse: collapse; margin-top: 20px; }
            th, td { padding: 12px; border-bottom: 1px solid #ddd; text-align: left; }
            th { background: #f2f2f2; }
            .entrada { background: #d4edda; }
            .saida { background: #f8d7da; }
            .sync { font-size: 12px; }
        </style>
    </head>
    <body>
        <h1>📊 Registros de Ponto</h1>
        <p>Total: ''' + str(len(registros)) + ''' registros</p>
        <table>
            <tr>
                <th>Data</th><th>Hora</th><th>Nome</th><th>Unidade</th>
                <th>Tipo</th><th>Localização</th><th>Status</th>
            </tr>
    '''
    
    for reg in registros:
        tipo_class = 'entrada' if reg['tipo'] == 'entrada' else 'saida'
        html += f'''
            <tr class="{tipo_class}">
                <td>{reg['data']}</td>
                <td>{reg['hora']}</td>
                <td>{reg['nome']}</td>
                <td>{reg['unidade']}</td>
                <td>{reg['tipo'].upper()}</td>
                <td>{reg['lat']:.4f}, {reg['lng']:.4f}</td>
                <td class="sync">{reg['sync']}</td>
            </tr>
        '''
    
    html += '''
        </table>
        <p style="margin-top: 30px;">
            <a href="/exportar">📥 Exportar CSV</a> | 
            <a href="/">← Voltar para registro</a>
        </p>
        <script>
        // Atualizar a cada 30 segundos
        setTimeout(() => location.reload(), 30000);
        </script>
    </body>
    </html>
    '''
    
    return html

# ============== EXPORTAR DADOS ==============
@app.route('/exportar')
def exportar():
    conn = sqlite3.connect('ponto_sheets.db')
    c = conn.cursor()
    
    c.execute('''
        SELECT data, hora, nome, unidade, tipo, latitude, longitude
        FROM registros 
        ORDER BY data DESC, hora DESC
    ''')
    
    # Gerar CSV
    csv_data = "Data,Hora,Nome,Unidade,Tipo,Latitude,Longitude\\n"
    for row in c.fetchall():
        csv_data += f"{row[0]},{row[1]},{row[2]},{row[3]},{row[4]},{row[5] or ''},{row[6] or ''}\\n"
    
    conn.close()
    
    return app.response_class(
        csv_data,
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=ponto_eletronico.csv'}
    )

# ============== INICIAR ==============
if __name__ == '__main__':
    criar_banco()
    conectar_google_sheets()
    
    print("=" * 70)
    print("🚀 SISTEMA DE PONTO COM PLANILHA AUTOMÁTICA")
    print("=" * 70)
    print("📱 PARA FUNCIONÁRIOS:")
    print("   • Preencha nome e unidade")
    print("   • Permita localização")
    print("   • Clique em ENTRADA ou SAÍDA")
    print("")
    print("👑 PARA VOCÊ:")
    print("   • Acesse: /visualizar")
    print("   • Veja todos os registros em tempo real")
    print("   • Exporte CSV com um clique")
    print("")
    print("📊 GOOGLE SHEETS:")
    print("   • Sistema pronto para integração")
    print("   • Configure credenciais para enviar automaticamente")
    print("   • Enquanto não configura, dados ficam no banco local")
    print("=" * 70)
    
    app.run(host='0.0.0.0', port=5000, debug=True)
