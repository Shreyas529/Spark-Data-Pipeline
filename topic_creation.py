from config import *
from producer import create_topic_if_not_exists, run_producer, create_ad_campaign_mappings

if __name__ == "__main__":
    # Create Kafka topic if it doesn't exist
    create_topic_if_not_exists(EVENTS_TOPIC, PARTITIONS, REPLICATION_FACTOR)
    create_topic_if_not_exists(RESULT_TOPIC, 1, REPLICATION_FACTOR)