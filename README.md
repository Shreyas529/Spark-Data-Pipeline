# Spark Data Pipeline

A real-time data streaming pipeline for processing advertising events using Apache Kafka and Apache Spark. This project simulates ad event generation with configurable traffic patterns and measures end-to-end processing latency.

## Overview

This pipeline processes advertising events (views, clicks, purchases) in real-time by:

1. **Generating synthetic events** using different traffic models (Uniform, Poisson, MMPP)
2. **Streaming events** through Apache Kafka
3. **Processing events** with Apache Spark Structured Streaming
4. **Measuring latency** to evaluate pipeline performance

## Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Producer  │────▶│    Kafka    │────▶│  Spark Job  │────▶│   Results   │
│  (Events)   │     │   Topics    │     │ (Processing)│     │   Topic     │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
                                                                   │
                                                                   ▼
                                                          ┌─────────────┐
                                                          │  Latency    │
                                                          │ Calculator  │
                                                          └─────────────┘
```

## Prerequisites

- Python 3.x
- Apache Kafka (running on `localhost:9092`)
- Apache Spark
- Required Python packages:
  - `kafka-python`
  - `numpy`
  - `pyspark`

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/Shreyas529/Spark-Data-Pipeline.git
   cd Spark-Data-Pipeline
   ```

2. Install Python dependencies:
   ```bash
   pip install kafka-python numpy pyspark
   ```

3. Ensure Kafka is running on `localhost:9092`

## Configuration

All configuration options are defined in `config.py`:

| Parameter | Default | Description |
|-----------|---------|-------------|
| `NUM_CAMPAIGNS` | 10 | Number of ad campaigns |
| `ADS_PER_CAMPAIGN` | 100 | Ads per campaign |
| `BOOTSTRAP_SERVERS` | `localhost:9092` | Kafka broker address |
| `EVENTS_TOPIC` | `events_spark` | Kafka topic for events |
| `RESULT_TOPIC` | `results_spark` | Kafka topic for results |
| `NUM_PRODUCERS` | 2 | Number of producer processes |
| `EVENTS_PER_PRODUCER` | 20000 | Events per producer per second |
| `DURATION_SECONDS` | 60 | Duration of event generation |
| `WINDOW_SIZE_SEC` | 10 | Aggregation window size |
| `DATA_GENERATOR` | `poisson` | Traffic pattern: `uniform`, `poisson`, or `mmpp` |

## Usage

### Running the Complete Pipeline

Run the master script to start the entire pipeline:

```bash
python master_code_spark.py
```

This will:
1. Clear existing Kafka topics
2. Start the Spark processing job
3. Start event producers
4. Calculate and report latency metrics

### Running Individual Components

**Create Kafka Topics:**
```bash
python topic_creation.py
```

**Start Producers Only:**
```bash
python producer.py
```

**Clear Topics:**
```bash
python clear_topics.py
```

## File Descriptions

| File | Description |
|------|-------------|
| `master_code_spark.py` | Main orchestration script that coordinates all components |
| `producer.py` | Kafka producer that sends generated events to topics |
| `config.py` | Configuration parameters for the pipeline |
| `data_generation.py` | Uniform event generation with ad-campaign mappings |
| `data_generation_poisson_baseline.py` | Poisson-distributed event generation |
| `data_generation_mmpp.py` | Markov-Modulated Poisson Process (MMPP) event generation |
| `latency_calculator.py` | Consumes results and calculates end-to-end latency |
| `topic_creation.py` | Creates required Kafka topics |
| `clear_topics.py` | Clears Kafka topics for fresh runs |

## Event Schema

Each generated event contains:

```json
{
  "user_id": "uuid",
  "page_id": "uuid",
  "ad_id": "uuid",
  "ad_type": "image|video|carousel|text|story|shopping|collection",
  "event_type": "view|click|purchase",
  "event_time_ns": "timestamp in nanoseconds",
  "window_id": "aggregation window identifier",
  "ip_address": "simulated IP",
  "campaign_id": "integer campaign ID",
  "produce_time": "producer timestamp in milliseconds"
}
```

## Traffic Generation Models

- **Uniform**: Events distributed evenly across each second
- **Poisson**: Events follow a Poisson arrival process (exponential inter-arrival times)
- **MMPP**: Markov-Modulated Poisson Process for bursty, correlated traffic patterns

## Output

The pipeline outputs:
- **Per-window latency**: Processing latency for each aggregation window
- **Average End-to-End Latency**: Mean latency across all windows
- **P90 Latency**: 90th percentile latency
