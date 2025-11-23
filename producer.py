# producer.py
import time
import json
import sys
from kafka import KafkaProducer
from kafka.admin import KafkaAdminClient, NewTopic
from kafka.errors import TopicAlreadyExistsError
from multiprocessing import Process

from data_generation import create_ad_campaign_mappings, generate_event_batch
from data_generation_poisson_baseline import generate_poisson_event_batch
from data_generation_mmpp import return_throughputs
from config import *


def create_topic_if_not_exists(topic_name, partitions, replication_factor):
    admin_client = None
    try:
        admin_client = KafkaAdminClient(bootstrap_servers=BOOTSTRAP_SERVERS)

        topic = NewTopic(
            name=topic_name,
            num_partitions=partitions,
            replication_factor=replication_factor
        )

        admin_client.create_topics([topic])
        print(f"Topic '{topic_name}' created.")

    except TopicAlreadyExistsError:
        print(f"Topic '{topic_name}' already exists.")
    except Exception as e:
        print(f"Error creating topic {topic_name}: {e}")
    finally:
        if admin_client:
            admin_client.close()


def run_producer(producer_id, throughput, duration_sec, ad_campaign_map, base_event_time_sec):
    print(f"[{producer_id}] Starting... DATA_GENERATOR={DATA_GENERATOR}")

    producer = KafkaProducer(
        bootstrap_servers=BOOTSTRAP_SERVERS,
        value_serializer=lambda v: json.dumps(v).encode("utf-8")
    )

    # Precomputed throughput list for MMPP
    if DATA_GENERATOR == "mmpp":
        mmpp_list = return_throughputs(throughput, duration_sec)

    for second in range(duration_sec):

        logical_second = base_event_time_sec + second
        if DATA_GENERATOR == "uniform":
            event_batch = generate_event_batch(
                throughput,
                ad_campaign_map,
                logical_second,
                base_event_time_sec
            )

        elif DATA_GENERATOR == "poisson":
            event_batch = generate_poisson_event_batch(
                throughput,
                ad_campaign_map,
                logical_second,
                base_event_time_sec
            )

        elif DATA_GENERATOR == "mmpp":
            effective_tput = mmpp_list[second]
            event_batch = generate_event_batch(
                effective_tput,
                ad_campaign_map,
                logical_second,
                base_event_time_sec
            )

        else:
            raise ValueError(f"Invalid DATA_GENERATOR: {DATA_GENERATOR}")
        
        for event in event_batch:
            # print(event)
            # key_bytes = str(event["campaign_id"]).encode("utf-8")
            producer.send(EVENTS_TOPIC, value=event)
            # print(f"[{producer_id}] Sent event for ad_id: {event['ad_id']} with campaign_id: {event['campaign_id']}")
            # producer.flush()

    try:
        producer.flush(timeout=5)  
    except Exception as e:
        print("Flush failed:", e)
    finally:
        producer.close()
        print(f"[{producer_id}] Finished sending events.")



if __name__ == "__main__":
    print(f"Ensuring topic '{EVENTS_TOPIC}' exists with {PARTITIONS} partitions...")
    create_topic_if_not_exists(EVENTS_TOPIC, PARTITIONS, REPLICATION_FACTOR)
    print("Topic check complete.")

    # 2. Generate Mappings (Only once)
    ad_campaign_map = create_ad_campaign_mappings()

    # 3. Launch Producers
    processes = []
    base_event_time = 0 

    for i in range(NUM_PRODUCERS):
        producer_name = f"producer-{i+1}"
        
        # We use a shared duration and calculated throughput
        throughput = EVENTS_PER_PRODUCER 
        duration = DURATION_SECONDS

        print(f"Starting {producer_name} with throughput={throughput} events/sec and duration={duration} seconds...")

        # Create a new process for each producer
        p = Process(
            target=run_producer, 
            args=(producer_name, throughput, duration, ad_campaign_map, base_event_time)
        )
        processes.append(p)
        p.start()
        # Slight pause to stagger the start, helpful sometimes
        time.sleep(0.5) 

    # 4. Wait for all producers to finish
    print(f"\nWaiting for {NUM_PRODUCERS} producers to complete their {DURATION_SECONDS}s run...")
    for p in processes:
        p.join()

    print("\nAll producers have finished execution.")