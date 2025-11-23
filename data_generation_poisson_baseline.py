
import uuid 
import random
from config import *
import numpy as np
import time

def generate_poisson_event_batch(throughput, ad_campaign_map, logical_time_sec, base_event_time_sec):
    """
    Generates a batch of synthetic streaming events for a single logical second.
    Args:
        throughput (int): Fixed number of events to generate in this second.
        ad_campaign_map (dict): {ad_id_uuid: campaign_id_int}.
        logical_time_sec (int): The base timestamp (in seconds) for the batch.
        base_event_time_sec (int): Global starting reference time in seconds.
        dist_type (str): "uniform" (default) or "poisson".
    Returns:
        A list of event dictionaries.
    """
    ad_ids = list(ad_campaign_map.keys())
    events = []
    base_event_time_ns = int(base_event_time_sec * 1e9)

    # Generate exponential inter-arrival times
    inter_arrivals = np.random.exponential(scale=1.0, size=throughput)
    arrival_times = np.cumsum(inter_arrivals)
    # Normalize into [0,1)
    arrival_times = arrival_times / arrival_times[-1]
    offsets = arrival_times

    for offset in offsets:
        ad_id = random.choice(ad_ids)
        event_time_ns = int((logical_time_sec + offset) * 1e9)
        window_id = (event_time_ns - base_event_time_ns) // (10 * 1_000_000_000)
        event = {
            'user_id': str(uuid.uuid4()),
            'page_id': str(uuid.uuid4()),
            'ad_id': ad_id,
            'ad_type': random.choice(AD_TYPES),
            'event_type': random.choice(EVENT_TYPES),
            'event_time_ns': event_time_ns,
            'window_id': window_id,
            'ip_address': ".".join(str(random.randint(0, 255)) for _ in range(4)),
            'campaign_id': ad_campaign_map[ad_id],
            'produce_time': int(time.time_ns()/1e6)
        }
        events.append(event)

    return events

# if __name__ == "__main__":
#     # Test the data generation functions
#     ad_campaign_map = create_ad_campaign_mappings()
#     event_batch = generate_event_batch(100, ad_campaign_map, 1700000000, 1700000000)
#     print(f"Generated {len(event_batch)} events.")
#     for event in event_batch:
#         print(event['event_time_ns'])