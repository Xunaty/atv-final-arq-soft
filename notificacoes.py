import pika
import json
import time
import json

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
    pagamento = evento['pagamento']

    if id_evento in ja_processados:
        print("evento repetido, ignorando:", id_evento)
        ch.basic_ack(delivery_tag=method.delivery_tag)
        return

    if '@' not in pagamento['email']:
        print("email invalido, mandando pra DLQ:", pagamento['email'])
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
        return

    print("enviando email para", pagamento['email'], "...")
    time.sleep(3)
    print("email enviado! pagamento do curso", pagamento['curso'], "aprovado")

    ja_processados.append(id_evento)
    ch.basic_ack(delivery_tag=method.delivery_tag)


conexao = conectar()
canal = conexao.channel()
canal.exchange_declare(exchange='eventos', exchange_type='fanout', durable=True)

canal.exchange_declare(exchange='dlx', exchange_type='fanout', durable=True)
canal.queue_declare(queue='notificacoes_dlq', durable=True)
canal.queue_bind(exchange='dlx', queue='notificacoes_dlq')

canal.queue_declare(queue='notificacoes', durable=True, arguments={'x-dead-letter-exchange': 'dlx'})
canal.queue_bind(exchange='eventos', queue='notificacoes')

canal.basic_qos(prefetch_count=1)
canal.basic_consume(queue='notificacoes', on_message_callback=receber)
print("servico de notificacoes esperando eventos...")
canal.start_consuming()
