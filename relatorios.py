import pika
import json
import time

total = 0
quantidade = 0


def conectar():
    while True:
        try:
            conexao = pika.BlockingConnection(pika.ConnectionParameters(host='rabbitmq'))
            return conexao
        except:
            print("rabbitmq ainda nao subiu, tentando de novo...")
            time.sleep(3)


def receber(ch, method, properties, body):
  global total
  global quantidade
  evento = json.loads(body)
  valor = evento['pagamento']['valor']
  total = total + valor
  quantidade = quantidade + 1
  print("relatorio atualizado:", quantidade, "pagamentos, total de R$", total)
  ch.basic_ack(delivery_tag=method.delivery_tag)


conexao = conectar()
canal = conexao.channel()
canal.exchange_declare(exchange='eventos', exchange_type='fanout', durable=True)
canal.queue_declare(queue='relatorios', durable=True)
canal.queue_bind(exchange='eventos', queue='relatorios')

canal.basic_consume(queue='relatorios', on_message_callback=receber)
print("servico de relatorios esperando eventos...")
canal.start_consuming()
