# Architecture Documentation

## System Overview

This repository implements a **real-time streaming analytics system** using **Apache Spark Structured Streaming** and **Apache Kafka**. The system is designed to process advertising campaign events in real-time, perform windowed aggregations, and measure end-to-end latency performance.

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         ORCHESTRATION LAYER                         │
│                      (master_code_spark.py)                         │
└──────────────┬────────────────────────────────────┬─────────────────┘
               │                                    │
               │                                    │
    ┌──────────▼──────────┐            ┌──────────▼───────────┐
    │   DATA PRODUCERS    │            │   SPARK STREAMING    │
    │   (producer.py)     │            │   (SparkJob.py)      │
    │                     │            │                      │
    │  Multiple Processes │            │  Structured Stream   │
    │  Generate Events    │            │  Processing          │
    └──────────┬──────────┘            └──────────┬───────────┘
               │                                   │
               │                                   │
               ▼                                   ▼
    ┌──────────────────────────────────────────────────────┐
    │            APACHE KAFKA MESSAGE BROKER               │
    │                                                      │
    │  Topics:                                             │
    │  • events_spark    (input events)                   │
    │  • results_spark   (aggregated results)             │
    └──────────┬───────────────────────────────────────────┘
               │
               ▼
    ┌──────────────────────┐
    │  LATENCY CALCULATOR  │
    │ (latency_calculator.py)│
    │                      │
    │  Measures E2E        │
    │  Performance         │
    └──────────────────────┘
```

## Core Components

### 1. Configuration Management (`config.py`)
**Purpose**: Centralized configuration for the entire system.

**Key Parameters**:
- **Kafka Configuration**:
  - `BOOTSTRAP_SERVERS`: Kafka broker address (default: "localhost:9092")
  - `EVENTS_TOPIC`: Input topic for raw events ("events_spark")
  - `RESULT_TOPIC`: Output topic for aggregated results ("results_spark")
  - `PARTITIONS`: Number of Kafka partitions (2)
  
- **Campaign Configuration**:
  - `NUM_CAMPAIGNS`: Number of advertising campaigns (10)
  - `ADS_PER_CAMPAIGN`: Ads per campaign (100)
  - `TOTAL_ADS`: Total advertisements (1000)
  
- **Event Generation**:
  - `AD_TYPES`: ['image', 'video', 'carousel', 'text', 'story', 'shopping', 'collection']
  - `EVENT_TYPES`: ['view', 'click', 'purchase']
  - `DATA_GENERATOR`: Distribution type (documented: "poisson", "mmpp")
    - Note: "uniform" is also supported by producer.py but not documented in config.py
  
- **Performance Configuration**:
  - `NUM_PRODUCERS`: Parallel producers (2)
  - `EVENTS_PER_PRODUCER`: Events per producer (20,000)
  - `DURATION_SECONDS`: Test duration (60 seconds)
  - `WINDOW_SIZE_SEC`: Aggregation window (10 seconds)

### 2. Master Orchestrator (`master_code_spark.py`)
**Purpose**: Main entry point that orchestrates all system components.

**Responsibilities**:
1. **Setup Phase**:
   - Clears Kafka topics to ensure clean state
   - Creates ad-campaign mappings
   - Waits for Kafka metadata propagation

2. **Process Management**:
   - Spawns multiple producer processes
   - Launches Spark streaming job in subprocess
   - Starts latency calculator
   - Coordinates process lifecycle

3. **Execution Flow**:
   ```
   1. Clean Kafka topics
   2. Start Latency Calculator (async)
   3. Start Spark Job (async)
   4. Wait 30s for Spark initialization
   5. Start Producers (parallel)
   6. Wait for producers to complete
   7. Wait for Spark and latency calculator
   8. Report final metrics
   ```

### 3. Data Generation Layer

#### 3.1 Main Data Generator (`data_generation.py`)
**Purpose**: Core event generation logic.

**Functions**:
- `create_ad_campaign_mappings()`: Creates UUID-based ad-to-campaign mappings
- `generate_event_batch()`: Generates uniform distribution events

**Event Schema**:
```json
{
  "user_id": "UUID",
  "page_id": "UUID", 
  "ad_id": "UUID",
  "ad_type": "string",
  "event_type": "string",
  "event_time_ns": "nanoseconds timestamp",
  "window_id": "integer",
  "ip_address": "IP string",
  "campaign_id": "integer",
  "produce_time": "milliseconds timestamp"
}
```

#### 3.2 Poisson Distribution Generator (`data_generation_poisson_baseline.py`)
**Purpose**: Generates events following Poisson arrival process.

**Characteristics**:
- Uses exponential inter-arrival times
- More realistic traffic simulation
- Normalized within 1-second windows

#### 3.3 MMPP Generator (`data_generation_mmpp.py`)
**Purpose**: Markov-Modulated Poisson Process for bursty traffic.

**Features**:
- Two-state CTMC (Continuous-Time Markov Chain)
- Models traffic bursts and lulls
- Configurable state transition rates
- Stateful sampling with state persistence

**Parameters**:
- `rate_ratio`: High-to-low rate ratio (5.0)
- `q12`, `q21`: State transition rates (0.5)
- `avg_rate`: Target average throughput

### 4. Event Producer (`producer.py`)
**Purpose**: Multi-process Kafka producer for event ingestion.

**Features**:
- **Topic Management**: Creates Kafka topics if needed
- **Distribution Support**: Handles uniform, Poisson, and MMPP distributions
- **Parallel Production**: Multiple producers for high throughput
- **Batch Processing**: Generates events per logical second

**Producer Workflow**:
```
For each second in duration:
  1. Calculate logical timestamp
  2. Generate event batch based on selected distribution
  3. Send events to Kafka (events_topic)
  4. Continue to next second

After duration completes:
  1. Flush producer buffer
  2. Close connection
```

### 5. Spark Streaming Job (`SparkJob.py`)
**Status**: ⚠️ **NOT INCLUDED IN REPOSITORY** - Referenced by master_code_spark.py but must be implemented separately.

**Purpose**: Real-time stream processing with Spark Structured Streaming.

**Required Functionality**:
- Must consume from `events_spark` topic
- Must perform windowed aggregations per campaign
- Must calculate metrics (count, max produce time)
- Must write results to `results_spark` topic
- Should use checkpointing for fault tolerance (checkpoint dir: `spark_checkpoints`)

### 6. Latency Calculator (`latency_calculator.py`)
**Purpose**: Measures end-to-end system latency.

**Methodology**:
- **Input**: Consumes from `results_spark` topic
- **Calculation**: `Latency = kafka_insert_timestamp - max_produce_time`
- **Metrics**:
  - Average end-to-end latency
  - P90 (90th percentile) latency
  - Per-window latency measurements

**Output**:
```
Window statistics with:
- Latency per window (ms)
- Average E2E latency
- P90 latency
```

### 7. Utility Scripts

#### 7.1 Topic Creation (`topic_creation.py`)
- Creates required Kafka topics
- Configures partitions and replication

#### 7.2 Topic Cleanup (`clear_topics.py`)
- Deletes and recreates topics
- Ensures clean state between runs

## Data Flow

### Event Lifecycle

1. **Generation Phase**:
   ```
   Data Generator → Event Batch (with timestamps)
   ```

2. **Production Phase**:
   ```
   Producer → Kafka (events_spark topic) [produce_time recorded]
   ```

3. **Processing Phase**:
   ```
   Spark Streaming:
     - Read from Kafka
     - Parse event_time_ns
     - Apply watermark
     - Window aggregation (10s windows)
     - Calculate campaign metrics
     - Record max_produce_time per window
   ```

4. **Output Phase**:
   ```
   Spark → Kafka (results_spark topic) [kafka_insert_time recorded]
   ```

5. **Measurement Phase**:
   ```
   Latency Calculator:
     - Read results
     - Calculate: E2E_latency = kafka_insert_time - max_produce_time
     - Report statistics
   ```

## Key Design Patterns

### 1. Multi-Process Architecture
- Uses Python `multiprocessing` for parallelism
- Independent producer processes for high throughput
- Separate process for latency calculation
- Spark job runs as subprocess

### 2. Configurable Distribution
- Supports multiple traffic patterns:
  - **Uniform**: Evenly distributed events
  - **Poisson**: Realistic random arrivals
  - **MMPP**: Bursty traffic simulation

### 3. Window-Based Aggregation
- Fixed 10-second tumbling windows
- Window ID calculated from base event time
- Allows deterministic windowing across system

### 4. Latency Tracking
- `produce_time`: When event enters Kafka
- `kafka_insert_time`: When result written to Kafka
- Enables end-to-end latency measurement

## System Requirements

### Dependencies
- **Apache Kafka**: Message broker (9092 port)
- **Apache Spark**: Structured Streaming engine
- **Python 3.x** with packages:
  - `kafka-python`: Kafka client
  - `numpy`: Numerical computations
  - `pyspark`: Spark Python API (for SparkJob)

### Infrastructure
- Kafka broker running on `localhost:9092`
- Sufficient memory for Spark driver/executors
- Write permissions for checkpoint directory

## Usage Patterns

### Standard Execution
```bash
python master_code_spark.py
```

### Component Testing

**Test Producer Only**:
```bash
python producer.py
```

**Test Data Generation**:
```bash
python -c "from data_generation import create_ad_campaign_mappings; print(len(create_ad_campaign_mappings()))"
```

**Test Topic Management**:
```bash
python topic_creation.py
python clear_topics.py
```

## Performance Characteristics

### Scalability Dimensions
1. **Producers**: Adjustable via `NUM_PRODUCERS`
2. **Throughput**: Configurable via `EVENTS_PER_PRODUCER`
3. **Duration**: Set via `DURATION_SECONDS`
4. **Partitions**: Kafka parallelism via `PARTITIONS`

### Latency Factors
- Producer batching and flush behavior
- Kafka broker performance
- Spark processing delay (micro-batching)
- Network latency
- Window size (affects aggregation delay)

## Configuration Tuning

### High Throughput
```python
NUM_PRODUCERS = 4
EVENTS_PER_PRODUCER = 50000
PARTITIONS = 4
```

### Low Latency
```python
WINDOW_SIZE_SEC = 5
PARTITIONS = 1
DB_BATCH_SIZE = 100
```

### Bursty Traffic Testing
```python
DATA_GENERATOR = "mmpp"
```

## Monitoring and Observability

### Built-in Metrics
- Per-window latency measurements
- Average end-to-end latency
- P90 latency
- Event counts per window

### Checkpointing
- Spark checkpoint directory: `spark_checkpoints`
- Enables recovery from failures
- Maintains processing state

## Limitations and Considerations

1. **⚠️ Critical: SparkJob.py Not Included**: The main Spark streaming job is referenced by master_code_spark.py (line 22) but is not present in the repository. This must be implemented before the system can run end-to-end. See section 5 above for required functionality.
2. **Single-node Deployment**: Configured for localhost (not production-ready distributed deployment)
3. **No Schema Registry**: Direct JSON serialization without schema validation
4. **Fixed Window Size**: 10-second windows hardcoded in data generation
5. **No Error Recovery**: Producers don't retry on failure

## Extension Points

### Adding New Metrics
1. Modify event schema in `data_generation.py`
2. Update Spark aggregation logic in `SparkJob.py`
3. Adjust result schema parsing in `latency_calculator.py`

### Custom Distribution
1. Create new generator in `data_generation_*.py`
2. Add option to `DATA_GENERATOR` in `config.py`
3. Update `producer.py` to handle new distribution

### Alternative Stream Processors
The architecture supports replacing Spark with:
- Apache Flink
- Kafka Streams
- Apache Storm

## Summary

This repository provides the **foundational components** for a production-grade streaming analytics pipeline with:
- ✅ Scalable multi-process producers
- ✅ Flexible traffic generation (uniform, Poisson, MMPP)
- ✅ Configurable system parameters
- ✅ End-to-end latency measurement framework
- ✅ Clean separation of concerns
- ⚠️ **Requires SparkJob.py implementation** for complete functionality

The architecture demonstrates best practices for streaming system design and is ideal for:
- Experimentation with streaming systems
- Performance benchmarking
- Understanding distributed stream processing patterns
- Educational purposes in streaming analytics

**Note**: To run the complete system, you must implement SparkJob.py to handle the Spark Structured Streaming logic (see section 5 for requirements).
