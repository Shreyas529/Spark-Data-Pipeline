import psycopg2
import uuid
import random
import time
import statistics


from config import *

def create_ad_campaign_mappings():

    mappings = {}
    for campaign_int in range(1, NUM_CAMPAIGNS + 1):
        for _ in range(ADS_PER_CAMPAIGN):
            ad_id = str(uuid.uuid4())
            mappings[ad_id] = campaign_int
    return mappings


def generate_event_batch(throughput, ad_campaign_map, logical_time_sec, base_event_time_sec):

    ad_ids = list(ad_campaign_map.keys())
    events = []

    base_event_time_ns = int(base_event_time_sec * 1e9)
    for i in range(throughput):
        ad_id = random.choice(ad_ids)
        offset = i/throughput
        event_time_ns = int((logical_time_sec + offset) * 1e9)
        # Calculate window_id: every 10 seconds is one window
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
