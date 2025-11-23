import json
from kafka import KafkaConsumer
from config import *
import numpy as np

def run_latency_calculator(results_queue):
    """
    Consumes results from the RESULT_TOPIC and calculates end-to-end latency:
    Latency = (Kafka Insert Timestamp) - (Max Produce Time)
    """
    print("[LatencyCalculator] Starting...")
    latency_measurements = []
    consumer = None

    try:
        consumer = KafkaConsumer(
            RESULT_TOPIC,
            bootstrap_servers=BOOTSTRAP_SERVERS,
            group_id="latency-calculator-group",
            auto_offset_reset='earliest',
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            consumer_timeout_ms=30000 
        )

        print(f"[LatencyCalculator] Listening on topic: {RESULT_TOPIC}...")

        for message in consumer:
            result_data = message.value

            # T_produce: Max produce time of event in the window (from Spark output)
            max_produce_ms = result_data.get('max_produce_time')
            
            # T_insert: The timestamp assigned by Kafka when the record was written (in ms)
            kafka_insert_ms = message.timestamp 
            window_start = result_data.get('window_start')

            if max_produce_ms is not None and kafka_insert_ms is not None:
                # Latency = T_insert - T_produce
                latency_ms = kafka_insert_ms - max_produce_ms
                
                latency_measurements.append(latency_ms)
                print(f"[LatencyCalculator] Window {window_start}: Latency = {latency_ms} ms (Kafka TS: {kafka_insert_ms}, Max Produce TS: {max_produce_ms})")
            else:
                 print(f"[LatencyCalculator] WARN: Missing timestamps in result for window {window_start}")

    except Exception as e:
        print(f"[LatencyCalculator] An error occurred: {e}")
    finally:
        if consumer:
            consumer.close()

        if latency_measurements:
            # Report summary statistics
            avg_latency = np.mean(latency_measurements)
            p90_latency = np.percentile(latency_measurements, 90)
            
            print(f"\n--- [LatencyCalculator] Summary ({len(latency_measurements)} windows) ---")
            print(f"Average End-to-End Latency: {avg_latency:.2f} ms")
            print(f"P90 Latency: {p90_latency:.2f} ms")
            
            results_queue.put({"avg_end_to_end": avg_latency, "p90_latency": p90_latency})
        else:
            print("\n[LatencyCalculator] No latency measurements were recorded.")
            results_queue.put({"avg_end_to_end": 0.0, "p90_latency": 0.0})

        print("[LatencyCalculator] Finished.")

if __name__ == "__main__":
    import queue
    q = queue.Queue()
    run_latency_calculator(q)