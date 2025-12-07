from flask import Flask, render_template_string, jsonify, request
from datetime import datetime, timezone, timedelta
import sqlite3
import csv
from io import StringIO

app = Flask(__name__)
app.secret_key = 'ponto-local-navegador-2024'

# ============== TIMEZONE BRASÍLIA ==============
def hora_brasilia():
    """Retorna hora atual no fuso de Brasília"""
    # Brasília é UTC-3 (ou UTC-2 durante horário de verão)
    offset = timedelta(hours=-3)
    tz = timezone(offset)
    return datetime.now(tz)

# ============== BANCO DE DADOS ==============
def criar_banco():
    conn = sqlite3.connect('ponto_local.db')
    c = conn.cursor()
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS pontos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            unidade TEXT NOT NULL,
            tipo TEXT NOT NULL,
            data TEXT NOT NULL,
            hora TEXT NOT NULL,
            data_hora TEXT NOT NULL,
            latitude REAL,
            longitude REAL,
            cidade TEXT,
            estado TEXT,
            endereco_completo TEXT,
            fonte_localizacao TEXT  -- 'navegador' ou 'api'
        )
    ''')
    
    conn.commit()
    conn.close()
    print("✅ Banco de dados criado")

# ============== VALIDAÇÃO SIMPLES BRASIL ==============
def esta_no_brasil(lat, lng):
    """Validação básica - dentro dos limites do Brasil"""
    # Coordenadas aproximadas do Brasil
    return (-33.75 <= lat <= 5.27 and -73.99 <= lng <= -34.80)

# ============== PÁGINA HTML ==============
PAGINA_HTML = '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Ponto Eletrônico - Localização do Navegador</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: 'Segoe UI', Arial, sans-serif; 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
        }
        .container {
            width: 100%;
            max-width: 500px;
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }
        .header {
            background: linear-gradient(135deg, #2c3e50 0%, #3498db 100%);
            color: white;
            padding: 25px;
            text-align: center;
        }
        .header h1 { font-size: 22px; margin-bottom: 8px; }
        .header p { opacity: 0.9; font-size: 14px; }
        .content { padding: 25px; }
        .form-group { margin-bottom: 18px; }
        label { display: block; margin-bottom: 6px; color: #333; font-weight: 600; font-size: 14px; }
        input { 
            width: 100%; 
            padding: 12px; 
            border: 2px solid #e1e1e1; 
            border-radius: 8px; 
            font-size: 16px;
            transition: border-color 0.3s;
        }
        input:focus { outline: none; border-color: #3498db; }
        .location-box {
            background: #f8f9fa;
            border-radius: 10px;
            padding: 18px;
            margin: 18px 0;
            text-align: center;
            border: 2px solid #e1e1e1;
        }
        .btn {
            width: 100%;
            padding: 16px;
            background: linear-gradient(135deg, #3498db 0%, #2980b9 100%);
            color: white;
            border: none;
            border-radius: 10px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s;
            margin: 10px 0;
        }
        .btn:hover { transform: translateY(-2px); box-shadow: 0 8px 20px rgba(52, 152, 219, 0.3); }
        .btn-success { background: linear-gradient(135deg, #2ecc71 0%, #27ae60 100%); }
        .btn-danger { background: linear-gradient(135deg, #e74c3c 0%, #c0392b 100%); }
        .btn-logout { background: #95a5a6; margin-top: 20px; }
        .registros-table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 15px;
            background: white;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 3px 10px rgba(0,0,0,0.05);
        }
        .registros-table th {
            background: #2c3e50;
            color: white;
            padding: 10px;
            text-align: left;
            font-size: 12px;
        }
        .registros-table td {
            padding: 10px;
            border-bottom: 1px solid #eee;
            font-size: 13px;
        }
        .badge {
            padding: 4px 10px;
            border-radius: 15px;
            font-size: 11px;
            font-weight: 500;
        }
        .badge-entrada { background: #d4edda; color: #155724; }
        .badge-saida { background: #f8d7da; color: #721c24; }
        .alert {
            padding: 12px;
            border-radius: 8px;
            margin: 12px 0;
            text-align: center;
            font-size: 14px;
        }
        .alert-success { background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
        .alert-danger { background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
        .alert-info { background: #d1ecf1; color: #0c5460; border: 1px solid #bee5eb; }
        .horario-brasilia {
            background: #fff3cd;
            border: 1px solid #ffeaa7;
            padding: 10px;
            border-radius: 8px;
            text-align: center;
            margin: 10px 0;
            font-weight: 600;
            color: #856404;
            font-size: 14px;
        }
        .local-detalhes {
            font-size: 12px;
            color: #666;
            margin-top: 5px;
            line-height: 1.4;
        }
        .small { font-size: 12px; color: #666; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📍 Ponto Eletrônico</h1>
            <p>Horário de Brasília • Localização do seu navegador</p>
        </div>
        
        <div class="content">
            <div id="login">
                <div class="form-group">
                    <label for="nome">👤 Nome Completo</label>
                    <input type="text" id="nome" placeholder="Digite seu nome completo" required>
                </div>
                
                <div class="form-group">
                    <label for="unidade">🏢 Unidade de Trabalho</label>
                    <input type="text" id="unidade" placeholder="Ex: Matriz, Filial, Home Office" required>
                </div>
                
                <div class="location-box">
                    <div id="location-status">📍 Aguardando permissão de localização...</div>
                    <div id="location-details" class="local-detalhes">
                        <div>O sistema usará a localização exata do seu navegador</div>
                        <div class="small">Permita o acesso à localização quando solicitado</div>
                    </div>
                </div>
                
                <div id="horario-atual" class="horario-brasilia">
                    🕐 Horário de Brasília: <span id="hora-brasilia">--:--:--</span>
                </div>
                
                <button class="btn" onclick="iniciarSistema()">🚀 Iniciar Sistema de Ponto</button>
                
                <div id="login-error" class="alert alert-danger" style="display: none;"></div>
            </div>
            
            <div id="ponto" style="display: none;">
                <div class="form-group">
                    <h3 id="usuario-nome" style="margin-bottom: 5px;"></h3>
                    <p id="usuario-unidade" class="small"></p>
                </div>
                
                <div class="location-box">
                    <div id="location-info">📍 Localização Atual</div>
                    <div id="cidade-info" class="local-detalhes"></div>
                    <div id="coordenadas" class="small" style="margin-top: 5px;"></div>
                </div>
                
                <div id="horario-ponto" class="horario-brasilia">
                    🕐 Horário atual: <span id="hora-atual">--:--:--</span>
                </div>
                
                <button class="btn btn-success" onclick="registrarPonto('entrada')">
                    🟢 REGISTRAR ENTRADA
                </button>
                
                <button class="btn btn-danger" onclick="registrarPonto('saida')">
                    🔴 REGISTRAR SAÍDA
                </button>
                
                <div id="resultado"></div>
                
                <h4 style="margin: 20px 0 10px 0; color: #2c3e50; font-size: 16px;">📋 Seus Registros de Hoje</h4>
                <div id="registros-container"></div>
                
                <button class="btn btn-logout" onclick="sairDoSistema()">Sair do Sistema</button>
            </div>
        </div>
    </div>
    
    <script>
    // Variáveis globais
    let usuario = null;
    let localizacaoValida = false;
    let latitude = null;
    let longitude = null;
    let enderecoCompleto = "Localização não disponível";
    let cidadeDetectada = "";
    let estadoDetectado = "";
    
    // Atualizar horário de Brasília
    function atualizarHorarioBrasilia() {
        const agora = new Date();
        const horaBrasilia = agora.toLocaleTimeString('pt-BR', {
            timeZone: 'America/Sao_Paulo',
            hour12: false,
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit'
        });
        
        document.getElementById('hora-brasilia').textContent = horaBrasilia;
        if (document.getElementById('hora-atual')) {
            document.getElementById('hora-atual').textContent = horaBrasilia;
        }
    }
    
    // Obter localização COMPLETA do navegador
    function obterLocalizacaoCompleta() {
        if (!navigator.geolocation) {
            atualizarStatusLocalizacao('❌ Seu navegador não suporta geolocalização');
            return;
        }
        
        atualizarStatusLocalizacao('📍 Solicitando localização...');
        
        // Primeiro: obter coordenadas
        navigator.geolocation.getCurrentPosition(
            async (posicao) => {
                latitude = posicao.coords.latitude;
                longitude = posicao.coords.longitude;
                
                // Mostrar coordenadas imediatamente
                document.getElementById('coordenadas').innerHTML = 
                    `Lat: ${latitude.toFixed(6)} | Long: ${longitude.toFixed(6)}`;
                
                // AGORA: usar API de geocoding reversa do navegador (se disponível)
                if (typeof google !== 'undefined' && google.maps && google.maps.Geocoder) {
                    // Se Google Maps API estiver disponível
                    usarGoogleGeocoding(latitude, longitude);
                } else {
                    // Tentar usar API nativa do navegador
                    usarGeocodingNativo(latitude, longitude);
                }
                
                // Validar se está no Brasil (coordernadas)
                const resposta = await fetch('/validar-coordenadas', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ lat: latitude, lng: longitude })
                });
                
                const dados = await resposta.json();
                localizacaoValida = dados.valida;
                
                if (localizacaoValida) {
                    atualizarStatusLocalizacao('✅ Localização válida no Brasil');
                } else {
                    atualizarStatusLocalizacao('❌ Fora do território brasileiro');
                }
            },
            (erro) => {
                let mensagem = 'Erro ao obter localização';
                switch(erro.code) {
                    case 1: mensagem = 'Permissão negada. Permita a localização nas configurações do navegador.'; break;
                    case 2: mensagem = 'Localização indisponível. Verifique seu GPS.'; break;
                    case 3: mensagem = 'Tempo esgotado. Tente novamente.'; break;
                }
                atualizarStatusLocalizacao(`❌ ${mensagem}`);
                localizacaoValida = false;
            },
            {
                enableHighAccuracy: true,
                timeout: 10000,
                maximumAge: 0
            }
        );
    }
    
    // Usar geocoding nativo (navegador moderno)
    async function usarGeocodingNativo(lat, lng) {
        try {
            // API de Geocoding do próprio navegador (experimental)
            if ('geolocation' in navigator && 'ReverseGeocoder' in window) {
                const geocoder = new ReverseGeocoder();
                const resultado = await geocoder.reverse(lat, lng);
                if (resultado) {
                    processarResultadoGeocoding(resultado);
                }
            }
            
            // Alternativa: usar API gratuita (OpenStreetMap)
            await usarOpenStreetMap(lat, lng);
            
        } catch (erro) {
            console.log('Geocoding nativo falhou:', erro);
            // Se falhar, usar apenas coordenadas
            cidadeDetectada = "Localização por coordenadas";
            estadoDetectado = "BR";
            enderecoCompleto = `Lat: ${lat.toFixed(4)}, Long: ${lng.toFixed(4)}`;
            atualizarDisplayLocalizacao();
        }
    }
    
    // Usar OpenStreetMap (gratuito, sem chave)
    async function usarOpenStreetMap(lat, lng) {
        try {
            const resposta = await fetch(
                `https://nominatim.openstreetmap.org/reverse?format=json&lat=${lat}&lon=${lng}&zoom=18&addressdetails=1`
            );
            
            if (resposta.ok) {
                const dados = await resposta.json();
                
                if (dados.address) {
                    const addr = dados.address;
                    
                    // Tentar obter cidade de diferentes campos
                    cidadeDetectada = addr.city || addr.town || addr.village || addr.municipality || 
                                     addr.county || "Localidade não identificada";
                    
                    estadoDetectado = addr.state || addr.region || "BR";
                    
                    // Montar endereço completo
                    const partes = [];
                    if (addr.road) partes.push(addr.road);
                    if (addr.suburb) partes.push(addr.suburb);
                    if (cidadeDetectada !== "Localidade não identificada") partes.push(cidadeDetectada);
                    if (estadoDetectado !== "BR") partes.push(estadoDetectado);
                    if (addr.country) partes.push(addr.country);
                    
                    enderecoCompleto = partes.join(', ');
                    
                    atualizarDisplayLocalizacao();
                }
            }
        } catch (erro) {
            console.log('OpenStreetMap falhou:', erro);
            cidadeDetectada = "Localização por coordenadas";
            estadoDetectado = "BR";
            enderecoCompleto = `Lat: ${lat.toFixed(4)}, Long: ${lng.toFixed(4)}`;
            atualizarDisplayLocalizacao();
        }
    }
    
    function processarResultadoGeocoding(resultado) {
        // Processar resultado de geocoding
        if (resultado.address_components) {
            let cidade = '';
            let estado = '';
            
            for (const component of resultado.address_components) {
                if (component.types.includes('locality')) {
                    cidade = component.long_name;
                }
                if (component.types.includes('administrative_area_level_1')) {
                    estado = component.short_name;
                }
            }
            
            cidadeDetectada = cidade || "Cidade não identificada";
            estadoDetectado = estado || "BR";
            enderecoCompleto = resultado.formatted_address || `Lat: ${latitude.toFixed(4)}, Long: ${longitude.toFixed(4)}`;
        }
        
        atualizarDisplayLocalizacao();
    }
    
    function atualizarDisplayLocalizacao() {
        let display = '';
        
        if (cidadeDetectada && cidadeDetectada !== "Cidade não identificada") {
            display = `<strong>${cidadeDetectada}</strong>`;
            if (estadoDetectado && estadoDetectado !== "BR") {
                display += ` - ${estadoDetectado}`;
            }
        } else {
            display = `📍 Localização por coordenadas`;
        }
        
        document.getElementById('cidade-info').innerHTML = display;
        
        if (enderecoCompleto && !enderecoCompleto.startsWith('Lat:')) {
            document.getElementById('location-details').innerHTML = 
                `<div style="color: #27ae60;">✅ ${enderecoCompleto}</div>`;
        }
    }
    
    function atualizarStatusLocalizacao(status) {
        document.getElementById('location-status').innerHTML = status;
        const infoEl = document.getElementById('location-info');
        if (infoEl) infoEl.innerHTML = status;
    }
    
    // Iniciar sistema
    async function iniciarSistema() {
        const nome = document.getElementById('nome').value.trim();
        const unidade = document.getElementById('unidade').value.trim();
        
        if (!nome || !unidade) {
            mostrarErro('Por favor, preencha nome e unidade');
            return;
        }
        
        if (!localizacaoValida) {
            mostrarErro('Localização inválida ou não permitida. É necessário estar no Brasil e permitir localização.');
            return;
        }
        
        usuario = { nome, unidade };
        
        // Mostrar seção de ponto
        document.getElementById('login').style.display = 'none';
        document.getElementById('ponto').style.display = 'block';
        
        // Atualizar informações do usuário
        document.getElementById('usuario-nome').textContent = `👤 ${nome}`;
        document.getElementById('usuario-unidade').textContent = `🏢 ${unidade}`;
        
        // Carregar registros
        await carregarRegistros();
    }
    
    // Registrar ponto
    async function registrarPonto(tipo) {
        if (!usuario || !localizacaoValida) {
            mostrarResultado('❌ Dados incompletos ou localização inválida', 'danger');
            return;
        }
        
        mostrarResultado('⏳ Registrando ponto...', 'info');
        
        try {
            const resposta = await fetch('/registrar-ponto', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    nome: usuario.nome,
                    unidade: usuario.unidade,
                    tipo: tipo,
                    lat: latitude,
                    lng: longitude,
                    cidade: cidadeDetectada,
                    estado: estadoDetectado,
                    endereco: enderecoCompleto
                })
            });
            
            const dados = await resposta.json();
            
            if (dados.sucesso) {
                mostrarResultado(
                    `✅ Ponto de ${tipo} registrado com sucesso!<br>` +
                    `⏰ ${dados.hora} | 📍 ${dados.local_display}`,
                    'success'
                );
                await carregarRegistros();
            } else {
                mostrarResultado(`❌ ${dados.erro}`, 'danger');
            }
        } catch (erro) {
            mostrarResultado('❌ Erro ao conectar com o servidor', 'danger');
        }
    }
    
    // Carregar registros
    async function carregarRegistros() {
        if (!usuario) return;
        
        try {
            const resposta = await fetch(`/meus-registros?nome=${encodeURIComponent(usuario.nome)}`);
            const dados = await resposta.json();
            
            if (dados.registros && dados.registros.length > 0) {
                let html = '<table class="registros-table">';
                html += '<thead><tr><th>Hora</th><th>Tipo</th><th>Local</th></tr></thead><tbody>';
                
                dados.registros.forEach(reg => {
                    html += `
                        <tr>
                            <td>${reg.hora}</td>
                            <td>
                                <span class="badge ${reg.tipo === 'entrada' ? 'badge-entrada' : 'badge-saida'}">
                                    ${reg.tipo.toUpperCase()}
                                </span>
                            </td>
                            <td>${reg.local}</td>
                        </tr>
                    `;
                });
                
                html += '</tbody></table>';
                document.getElementById('registros-container').innerHTML = html;
            } else {
                document.getElementById('registros-container').innerHTML = 
                    '<div class="alert alert-info">Nenhum registro encontrado para hoje</div>';
            }
        } catch {
            document.getElementById('registros-container').innerHTML = 
                '<div class="alert alert-danger">Erro ao carregar registros</div>';
        }
    }
    
    // Sair do sistema
    function sairDoSistema() {
        usuario = null;
        document.getElementById('ponto').style.display = 'none';
        document.getElementById('login').style.display = 'block';
        document.getElementById('nome').value = '';
        document.getElementById('unidade').value = '';
        document.getElementById('registros-container').innerHTML = '';
    }
    
    // Funções auxiliares
    function mostrarErro(mensagem) {
        const erroEl = document.getElementById('login-error');
        erroEl.textContent = mensagem;
        erroEl.style.display = 'block';
        setTimeout(() => erroEl.style.display = 'none', 5000);
    }
    
    function mostrarResultado(mensagem, tipo) {
        const resultadoEl = document.getElementById('resultado');
        resultadoEl.innerHTML = `
            <div class="alert alert-${tipo}">
                ${mensagem}
            </div>
        `;
        setTimeout(() => resultadoEl.innerHTML = '', 5000);
    }
    
    // Inicializar
    window.onload = function() {
        // Atualizar horário a cada segundo
        atualizarHorarioBrasilia();
        setInterval(atualizarHorarioBrasilia, 1000);
        
        // Obter localização completa
        obterLocalizacaoCompleta();
        
        // Atualizar localização periodicamente
        setInterval(obterLocalizacaoCompleta, 30000);
    };
    </script>
</body>
</html>
'''

# ============== ROTAS DO SERVIDOR ==============
@app.route('/')
def home():
    return render_template_string(PAGINA_HTML)

@app.route('/validar-coordenadas', methods=['POST'])
def validar_coordenadas():
    dados = request.json
    valida = esta_no_brasil(dados['lat'], dados['lng'])
    return jsonify({'valida': valida})

@app.route('/registrar-ponto', methods=['POST'])
def registrar_ponto():
    dados = request.json
    
    # Validar localização
    if not esta_no_brasil(dados['lat'], dados['lng']):
        return jsonify({
            'sucesso': False,
            'erro': 'Localização fora do território brasileiro. Não é possível registrar ponto.'
        })
    
    # Obter hora atual em Brasília
    agora_brasilia = hora_brasilia()
    data = agora_brasilia.strftime('%Y-%m-%d')
    hora = agora_brasilia.strftime('%H:%M:%S')
    data_hora = agora_brasilia.strftime('%Y-%m-%d %H:%M:%S')
    
    # Usar informações de localização fornecidas pelo navegador
    cidade = dados.get('cidade', 'Localização do navegador')
    estado = dados.get('estado', 'BR')
    endereco = dados.get('endereco', f'Lat: {dados["lat"]:.4f}, Long: {dados["lng"]:.4f}')
    
    # Determinar fonte da localização
    fonte = 'navegador' if dados.get('cidade') else 'coordenadas'
    
    # Montar display para o usuário
    local_display = cidade
    if estado and estado != 'BR':
        local_display += f' - {estado}'
    
    # Conectar ao banco
    conn = sqlite3.connect('ponto_local.db')
    c = conn.cursor()
    
    # Verificar sequência de ponto
    c.execute('''
        SELECT tipo FROM pontos 
        WHERE nome = ? AND data = ?
        ORDER BY data_hora DESC LIMIT 1
    ''', (dados['nome'], data))
    
    ultimo = c.fetchone()
    
    if ultimo and ultimo[0] == dados['tipo']:
        conn.close()
        return jsonify({
            'sucesso': False,
            'erro': f'Você já registrou {dados["tipo"]}. Próximo: {"SAÍDA" if dados["tipo"] == "entrada" else "ENTRADA"}'
        })
    
    # Inserir registro
    c.execute('''
        INSERT INTO pontos 
        (nome, unidade, tipo, data, hora, data_hora, latitude, longitude, 
         cidade, estado, endereco_completo, fonte_localizacao)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        dados['nome'], dados['unidade'], dados['tipo'], 
        data, hora, data_hora, dados['lat'], dados['lng'], 
        cidade, estado, endereco, fonte
    ))
    
    conn.commit()
    conn.close()
    
    return jsonify({
        'sucesso': True,
        'mensagem': 'Ponto registrado com sucesso!',
        'hora': hora,
        'data': data,
        'local_display': local_display,
        'cidade': cidade,
        'estado': estado
    })

@app.route('/meus-registros')
def meus_registros():
    nome = request.args.get('nome', '')
    data_hoje = hora_brasilia().strftime('%Y-%m-%d')
    
    conn = sqlite3.connect('ponto_local.db')
    c = conn.cursor()
    
    c.execute('''
        SELECT hora, tipo, cidade, estado, endereco_completo 
        FROM pontos 
        WHERE nome = ? AND data = ?
        ORDER BY data_hora DESC
    ''', (nome, data_hoje))
    
    registros = []
    for row in c.fetchall():
        local = row[2]  # cidade
        if row[3] and row[3] != 'BR':
            local += f' - {row[3]}'
        elif row[4]:  # endereco_completo
            local = row[4]
        
        registros.append({
            'hora': row[0],
            'tipo': row[1],
            'local': local
        })
    
    conn.close()
    return jsonify({'registros': registros})

# ============== ROTAS ADMIN (apenas para você) ==============
@app.route('/admin/exportar-csv')
def exportar_csv():
    conn = sqlite3.connect('ponto_local.db')
    c = conn.cursor()
    
    c.execute('''
        SELECT data, hora, nome, unidade, tipo, cidade, estado, 
               latitude, longitude, endereco_completo, fonte_localizacao
        FROM pontos 
        ORDER BY data_hora DESC
    ''')
    
    # Criar CSV
    output = StringIO()
    writer = csv.writer(output)
    
    # Cabeçalho
    writer.writerow(['Data', 'Hora (Brasília)', 'Nome', 'Unidade', 'Tipo', 
                     'Cidade', 'Estado', 'Latitude', 'Longitude', 
                     'Endereço Completo', 'Fonte Localização'])
    
    # Dados
    for row in c.fetchall():
        writer.writerow(row)
    
    conn.close()
    
    response = app.response_class(
        response=output.getvalue(),
        status=200,
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=ponto_localizacao_navegador.csv'}
    )
    return response

# ============== INICIAR APLICAÇÃO ==============
if __name__ == '__main__':
    criar_banco()
    
    print("=" * 70)
    print("🚀 SISTEMA DE PONTO - LOCALIZAÇÃO DO NAVEGADOR")
    print("=" * 70)
    print("✅ CARACTERÍSTICAS:")
    print("   📍 Usa a localização EXATA do navegador do usuário")
    print("   🗺️  Tenta obter endereço via geocoding (OpenStreetMap)")
    print("   ⏰ Horário sincronizado com Brasília")
    print("   🇧🇷 Valida se está dentro do território brasileiro")
    print("   💾 Armazena informações completas de localização")
    print("=" * 70)
    print("🌐 Sistema: http://localhost:5000")
    print("📊 Admin (exportar): http://localhost:5000/admin/exportar-csv")
    print("=" * 70)
    print("⚠️  IMPORTANTE: O usuário precisa PERMITIR localização no navegador")
    print("=" * 70)
    
    app.run(host='0.0.0.0', port=5000, debug=True)
