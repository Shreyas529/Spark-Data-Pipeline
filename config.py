AD_TYPES = ['image', 'video', 'carousel', 'text', 'story', 'shopping', 'collection']
EVENT_TYPES = ['view', 'click', 'purchase']

NUM_CAMPAIGNS = 10
ADS_PER_CAMPAIGN = 100
TOTAL_ADS = NUM_CAMPAIGNS * ADS_PER_CAMPAIGN

BOOTSTRAP_SERVERS = "localhost:9092"
TOPIC_NAME = 'events_spark'
PARTITIONS = 2
REPLICATION_FACTOR = 1

EVENTS_TOPIC = 'events_spark'
WATERMARK_TOPIC = 'local-watermarks'
CONSUMER_GROUP_ID = 'consumer-group_spark'

RESULT_TOPIC = 'results_spark'

DB_BATCH_SIZE = 1000

AGGREGATOR_GROUP_ID = 'aggregator-group_spark'

DATA_GENERATOR="poisson"  # Options: "poisson", "mmpp"

NUM_PRODUCERS = 2
NUM_CONSUMERS = 2
EVENTS_PER_PRODUCER = 20000
DURATION_SECONDS = 60

WINDOW_SIZE_SEC = 10

CHECKPOINT_DIR = "spark_checkpoints"

WATERMARK_LOG_FILE = "watermark_log.csv"