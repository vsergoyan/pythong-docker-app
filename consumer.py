import pika
import os
import ast
import time

def connect_to_rabbitmq():
    while True:
        try:
            connection = pika.BlockingConnection(
                pika.ConnectionParameters(host=os.environ.get('RABBITMQ_HOST', 'rabbitmq'))
            )
            return connection
        except pika.exceptions.AMQPConnectionError:
            print("RabbitMQ not ready, retrying in 5 seconds...", flush=True)
            time.sleep(5)

def main():
    connection = connect_to_rabbitmq()
    channel = connection.channel()
    channel.queue_declare(queue='task_queue', durable=True)

    def callback(ch, method, properties, body):
        task = ast.literal_eval(body.decode())
        print(f" [x] Reminder: Task '{task['title']}' is scheduled for {task['due_date']}. Description: {task['description']}", flush=True)
        time.sleep(1)
        ch.basic_ack(delivery_tag=method.delivery_tag)

    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue='task_queue', on_message_callback=callback)
    print(' [*] Waiting for tasks. To exit press CTRL+C', flush=True)
    channel.start_consuming()

if __name__ == '__main__':
    main()
