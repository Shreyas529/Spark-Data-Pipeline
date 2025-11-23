# master_code_spark.py
import multiprocessing
import time
import os
import subprocess
import sys

from producer import run_producer
from data_generation import create_ad_campaign_mappings
from latency_calculator import run_latency_calculator
from config import *
from clear_topics import clear_topic

def run_spark_job_in_process():
    """
    Submits the Spark job using the correct Python executable and environment.
    """
    print("[Master] Submitting Spark job...")
    
    # Get the path to the current Python executable (from envhome_py11)
    python_executable = sys.executable 
    script_path = os.path.abspath("SparkJob.py")
    
    if not os.path.exists(script_path):
        print(f"Error: Could not find SparkJob.py at {script_path}")
        return

    try:
        # Run the Spark job as a subprocess
        process = subprocess.run(
            [python_executable, script_path], 
            check=True, 
            text=True, 
            capture_output=True
        )
        print("[Master] Spark job finished successfully.")
        print(process.stdout)
    except subprocess.CalledProcessError as e:
        print(f"[Master] Spark job failed with error (Exit Code {e.returncode}):")
        print("--- Spark Job STDOUT ---")
        print(e.stdout)
        print("--- Spark Job STDERR ---")
        print(e.stderr)
        print("------------------------")
    except Exception as e:
        print(f"[Master] An unexpected error occurred while running Spark job: {e}")

def main():
    # 1. Setup Kafka topics
    print("🧹 Cleaning up resources...")
    clear_topic(EVENTS_TOPIC)
    clear_topic(RESULT_TOPIC)
    print("Cleanup complete.")

    print("[Master] Waiting 5s for Kafka metadata to propagate...")
    time.sleep(5)
    
    ad_campaign_map = create_ad_campaign_mappings()
    base_event_time = int(time.time())

    # 2. Create processes
    producer_processes = []
    for i in range(NUM_PRODUCERS):
        p = multiprocessing.Process(
            target=run_producer,
            args=(f"Producer-{i+1}", EVENTS_PER_PRODUCER, DURATION_SECONDS, ad_campaign_map, base_event_time)
        )
        producer_processes.append(p)

    latency_result_queue = multiprocessing.Queue()
    latency_process = multiprocessing.Process(
        target=run_latency_calculator,
        args=(latency_result_queue,)
    )
    
    spark_process = multiprocessing.Process(target=run_spark_job_in_process)

    print(f"🚀 Starting Spark pipeline with {NUM_PRODUCERS} producer(s)...")

    # 3. Start Latency Calculator and Spark Job first
    latency_process.start()
    spark_process.start()
    
    print("[Master] Waiting 15s for Spark job to initialize...")
    time.sleep(30) # Spark can take a bit longer to start up

    # 4. Start producers
    print("[Master] Starting producers...")
    for p in producer_processes:
        p.start()

    # 5. Wait for all processes to finish
    for p in producer_processes:
        p.join()
    print("[Master] All producers finished.")

    # Spark and Latency Calculator will finish on their own
    spark_process.join()
    latency_process.join()
    print("[Master] All processes finished.")

    # 6. Retrieve and display the final result
    try:
        # We can reuse the same latency calculator from the Flink patch
        final_latencies = latency_result_queue.get(timeout=10)
        
        # NOTE: Your patched latency calculator needs to read 'max_broker_log_time_ms'
        # (which it should already do from the Flink exercise)
        avg_e2e = final_latencies.get("avg_end_to_end", 0.0)
        
        print("\n--- FINAL RESULT ---")
        print(f"Overall Average End-to-End Latency: {avg_e2e:.2f} ms")
        print("--------------------")
    except Exception as e:
        print(f"\nCould not retrieve final latency result: {e}")

if __name__ == "__main__":
    main()