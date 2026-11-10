import pika
import json
import time

matriculas = {}
ja_processados = []


def conectar():
    while True:
        try:
            conexao = pika.BlockingConnection(pika.ConnectionParameters(host='rabbitmq'))
            return conexao
        except:
            print("rabbitmq ainda nao subiu, tentando de novo...")
            time.sleep(3)


def receber(ch, method, properties, body):
    evento = json.loads(body)
    id_evento = evento['id_evento']

    if id_evento in ja_processados:
        print("evento repetido, ignorando:", id_evento)
        ch.basic_ack(delivery_tag=method.delivery_tag)
        return

    pagameto = evento['pagamento']
    matriculas[pagameto['chave']] = {
        'aluno': pagameto['aluno'],
        'curso': pagameto['curso'],
        'situacao': 'confirmada'
    }
    print("matricula confirmda:", pagameto['aluno'], "no curso", pagameto['curso'])
    print("total de matriculas confirmadas:", len(matriculas))

    ja_processados.append(id_evento)
    ch.basic_ack(delivery_tag=method.delivery_tag)


conexao = conectar()
canal = conexao.channel()
canal.exchange_declare(exchange='eventos', exchange_type='fanout', durable=True)
canal.queue_declare(queue='matriculas', durable=True)
canal.queue_bind(exchange='eventos', queue='matriculas')

canal.basic_qos(prefetch_count=1)
canal.basic_consume(queue='matriculas', on_message_callback=receber)
print("servico de matriculas esperando eventos...")
canal.start_consuming()
