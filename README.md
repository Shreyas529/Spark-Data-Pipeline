# SDS Assignment 4 - Apache Spark Streaming Analytics

A real-time streaming analytics system for processing advertising campaign events using **Apache Spark Structured Streaming** and **Apache Kafka**.

## Quick Start

⚠️ **Important**: This repository contains the foundational components. You must implement `SparkJob.py` before running the complete system. See [ARCHITECTURE.md](ARCHITECTURE.md) section 5 for requirements.

### Prerequisites
- Apache Kafka (running on localhost:9092)
- Apache Spark with PySpark
- Python 3.x with dependencies:
  - kafka-python
  - numpy

### Running the System

1. **Start Kafka** (ensure broker is running on localhost:9092)

2. **Implement SparkJob.py** (see architecture documentation for requirements)

3. **Run the master orchestrator**:
   ```bash
   python master_code_spark.py
   ```

This will:
- Clean Kafka topics
- Start multiple producers generating events
- Launch Spark streaming job
- Calculate end-to-end latency metrics

## Repository Structure

```
├── config.py                           # Centralized configuration
├── master_code_spark.py               # Main orchestrator
├── producer.py                         # Kafka event producers
├── data_generation.py                  # Core data generation (uniform dist.)
├── data_generation_poisson_baseline.py # Poisson distribution generator
├── data_generation_mmpp.py            # MMPP (bursty) generator
├── latency_calculator.py              # E2E latency measurement
├── topic_creation.py                  # Kafka topic setup
├── clear_topics.py                    # Kafka topic cleanup
└── ARCHITECTURE.md                    # Detailed architecture documentation
```

## Key Features

- ✅ **Multi-Process Producers**: Parallel event generation for high throughput
- ✅ **Flexible Traffic Patterns**: Supports uniform, Poisson, and MMPP distributions
- ✅ **Windowed Aggregations**: 10-second tumbling windows for real-time metrics
- ✅ **Latency Measurement**: End-to-end performance tracking
- ✅ **Configurable System**: Easy parameter tuning via config.py

## Configuration

Edit `config.py` to customize:

```python
# Traffic generation
NUM_PRODUCERS = 2
EVENTS_PER_PRODUCER = 20000
DURATION_SECONDS = 60
DATA_GENERATOR = "poisson"  # Documented: "poisson" or "mmpp" (see config.py)

# Kafka configuration
BOOTSTRAP_SERVERS = "localhost:9092"
EVENTS_TOPIC = 'events_spark'
RESULT_TOPIC = 'results_spark'
PARTITIONS = 2

# Window configuration
WINDOW_SIZE_SEC = 10
```

## Architecture

For detailed architecture documentation including:
- System overview with diagrams
- Component descriptions
- Data flow and event lifecycle
- Design patterns
- Performance tuning
- Extension points

Please see **[ARCHITECTURE.md](ARCHITECTURE.md)**

## Testing Individual Components

### Test Producers Only
```bash
python producer.py
```

### Create/Clear Kafka Topics
```bash
python topic_creation.py
python clear_topics.py
```

### Test Data Generation
```python
from data_generation import create_ad_campaign_mappings
mappings = create_ad_campaign_mappings()
print(f"Created {len(mappings)} ad mappings")
```

## Traffic Patterns

The system supports three traffic generation patterns:

### Poisson Distribution (Recommended)
Realistic random arrivals with exponential inter-arrival times:
```python
DATA_GENERATOR = "poisson"
```

### MMPP (Markov-Modulated Poisson Process)
Simulates bursty traffic with high/low states:
```python
DATA_GENERATOR = "mmpp"
```

### Uniform Distribution
Evenly distributed events (works but not documented in config.py):
```python
DATA_GENERATOR = "uniform"
```

Note: Only "poisson" and "mmpp" are officially documented in config.py. The "uniform" option is supported by producer.py but not listed in the configuration file.

## Event Schema

```json
{
  "user_id": "UUID",
  "page_id": "UUID",
  "ad_id": "UUID",
  "ad_type": "image|video|carousel|text|story|shopping|collection",
  "event_type": "view|click|purchase",
  "event_time_ns": 1700000000123456789,
  "window_id": 42,
  "ip_address": "192.168.1.1",
  "campaign_id": 5,
  "produce_time": 1700000000123
}
```

## Metrics

The system calculates:
- **End-to-End Latency**: Time from event production to result insertion
- **P90 Latency**: 90th percentile latency
- **Per-Window Statistics**: Latency measurements for each 10-second window

## Known Limitations

1. **⚠️ SparkJob.py Not Included**: Must be implemented separately
2. **Single-Node Setup**: Configured for localhost only
3. **No Error Recovery**: Producers don't implement retry logic
4. **Fixed Window Size**: 10-second windows are hardcoded

## Use Cases

- 📊 Streaming system experimentation
- ⚡ Performance benchmarking
- 📚 Educational purposes in stream processing
- 🔬 Understanding distributed data pipelines

## License

See repository license file.

## Contributing

This is an educational/assignment repository. For detailed architecture and extension points, see [ARCHITECTURE.md](ARCHITECTURE.md).
