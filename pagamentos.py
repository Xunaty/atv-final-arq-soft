from flask import Flask, request, jsonify
import pika
import json
import time
import uuid

app = Flask(__name__)

pagamentos = {}


def conectar():
    while True:
        try:
            conexao = pika.BlockingConnection(pika.ConnectionParameters(host='rabbitmq'))
            return conexao
        except:
            print("rabbitmq ainda nao subiu, tentando de novo...")
            time.sleep(3)


def publicar_evento(evento):
    conexao = conectar()
    canal = conexao.channel()
    canal.exchange_declare(exchange='eventos', exchange_type='fanout', durable=True)
    canal.basic_publish(exchange='eventos', routing_key='', body=json.dumps(evento),
                        properties=pika.BasicProperties(delivery_mode=2))
    conexao.close()


@app.route('/pagamentos', methods=['POST'])
def pagar():
    dados = request.get_json()
    chave = dados['chave']

    if chave in pagamentos:
        print("pagamento repetido, nao vou cobrar de novo:", chave)
        return jsonify(pagamentos[chave]), 200

    pagamento = {
        'id': str(uuid.uuid4()),
        'chave': chave,
        'aluno': dados['aluno'],
        'email': dados['email'],
        'curso': dados['curso'],
        'valor': dados['valor'],
        'status': 'aprovado'
    }
    pagamentos[chave] = pagamento

    evento = {
        'id_evento': str(uuid.uuid4()),
        'tipo': 'PagamentoAprovado',
        'pagamento': pagamento
    }
    publicar_evento(evento)
    print("evento PagamentoAprovado publicado para o aluno", dados['aluno'])

    return jsonify(pagamento), 201


@app.route('/pagamentos', methods=['GET'])
def listar():
    lista = []
    for chave in pagamentos:
        lista.append(pagamentos[chave])
    return jsonify(lista)


app.run(host='0.0.0.0', port=5000)
