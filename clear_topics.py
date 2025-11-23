from config import *
import time
from kafka.admin import KafkaAdminClient, NewTopic


def clear_topic(topic = TOPIC_NAME, partitions=PARTITIONS, replication=REPLICATION_FACTOR):
    """Delete the topic and recreate it to ensure it is empty.

    Note: This requires the Kafka broker to have delete-topic enabled.
    """
    admin_client = KafkaAdminClient(bootstrap_servers=BOOTSTRAP_SERVERS)
    try:
        print(f"Deleting topic '{topic}' for cleanup...")
        admin_client.delete_topics([topic])
    except Exception as e:
        print(f"Warning: could not delete topic: {e}")
    finally:
        # Kafka deletes are async; give broker a moment
        time.sleep(2)
        admin_client.close()


    print(f"Topic '{topic}' cleared and recreated.")

if __name__ == "__main__":
    clear_topic(TOPIC_NAME, PARTITIONS, REPLICATION_FACTOR)
    clear_topic(WATERMARK_TOPIC, 1, REPLICATION_FACTOR)
    clear_topic(RESULT_TOPIC, 1, REPLICATION_FACTOR)