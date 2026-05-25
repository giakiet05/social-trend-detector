# Social Trend Detector

Social Trend Detector is a multi-source trend detection system for social and news content. It collects content from TikTok, YouTube, Google Trends, and Vietnamese news RSS feeds, then groups related items into trends using embeddings, clustering, and LLM-based analysis.

The project is designed as a data pipeline rather than a single web application. Producers collect raw content, Kafka decouples ingestion from processing, a batch consumer detects trends, and Streamlit dashboards expose the processed results for users and administrators.

## System Overview

The system has three main layers:

1. Producer layer
   - Collects raw content from external sources.
   - Normalizes source-specific payloads into shared data models.
   - Publishes messages to Kafka topics for downstream processing.

2. Consumer and processing layer
   - Reads new Kafka messages in batch mode.
   - Converts raw source data into a unified content schema.
   - Cleans, filters, embeds, clusters, analyzes, deduplicates, and stores trends.

3. Dashboard layer
   - Provides user-facing views for browsing detected trends.
   - Provides admin views for managing trends, submitted keywords, extracted keywords, and active tracked keywords.

## Project Structure

```text
.
├── common/
│   ├── models.py                 # Shared source models, Kafka message wrapper, ContentItem, Trend
│   └── keyword_manager.py         # Keyword management shared by producer/dashboard flows
├── producer/
│   ├── orchestrator.py            # Runs TikTok, YouTube, and news producers concurrently
│   ├── scrapers/                  # Source-specific scraping/API clients
│   ├── producers/                 # Kafka producer wrappers for each source
│   └── config/                    # RSS feed and scraping keyword configuration
├── consumer/
│   ├── batch_consumer.py          # Batch Kafka consumer with Spark and checkpoint management
│   ├── processing/
│   │   ├── pipeline.py            # End-to-end trend detection pipeline orchestration
│   │   ├── clusterer.py           # HDBSCAN clustering wrapper
│   │   └── stages/                # Normalization, cleaning, filtering, embedding, clustering, analysis, deduplication, storage
│   ├── enrichment/                # OpenAI/Gemini clients for embeddings and LLM analysis
│   ├── storage/                   # MongoDB persistence layer
│   ├── models/                    # Spark schemas for Kafka message parsing
│   └── metrics/                   # Saved batch processing metrics
├── keyword_extractor/
│   ├── extractor.py               # LLM-based keyword extraction from news headlines
│   └── config/                    # RSS feed and extraction settings
├── dashboard/
│   ├── app.py                     # User dashboard
│   ├── admin.py                   # Admin dashboard
│   ├── components/                # Dashboard layout and chart components
│   └── storage/                   # Dashboard MongoDB access
├── docs/
│   └── report/                    # Project report, diagrams, and screenshots
├── docker-compose.yml             # Full application stack
├── docker-compose.infra.yml       # Infrastructure-only stack
├── Dockerfile.backend             # Producer/consumer runtime image
└── Dockerfile.dashboard           # Dashboard runtime image
```

## Data Sources

The producer layer supports multiple content sources:

- TikTok: collected through an external scraping/API provider and mapped into a video schema with text, hashtags, engagement metrics, author metadata, and URL fields.
- YouTube: collected through the YouTube Data API and mapped into a video schema with metadata and engagement statistics.
- Google Trends: collected as search trend signals and treated as an additional source for trend detection.
- News RSS: collected from Vietnamese news feeds and mapped into article data with title, summary, category, source, and publication time.

All source-specific data is wrapped in a Kafka message format before being published.

## Kafka Workflow

The producer layer publishes raw source data to Kafka topics. Each message contains:

- Source identifier
- Collection timestamp
- Source-specific payload
- Metadata needed by the consumer pipeline

The batch consumer reads all new messages since the last checkpoint. Offsets are saved locally after successful processing so the next batch can resume from the correct position.

This design keeps ingestion and processing independent:

- Producers can fail independently without breaking the consumer.
- The consumer can reprocess uncommitted batches after a failure.
- New sources can be added by implementing a scraper, a producer, and a normalization path.

## Trend Detection Pipeline

The consumer pipeline is implemented as a sequence of processing stages.

### 1. Normalization

Source-specific records are converted into a unified `ContentItem` representation. This gives later stages a consistent structure for text, author information, engagement metrics, source name, timestamp, URL, and metadata.

### 2. Cleaning

The pipeline removes invalid or low-value text data, including missing text fields, overly short content, URLs, mentions, HTML fragments, and unnecessary whitespace.

### 3. Filtering

Content is filtered using quality signals such as engagement rate, follower count when available, text length, and hashtag count. The goal is to reduce spam, bot-like content, and weak signals before embedding and clustering.

### 4. Embedding

Cleaned text is converted into vector embeddings through a configurable embedding provider. The code supports OpenAI and Gemini clients behind a shared interface, allowing the pipeline to switch providers through configuration.

### 5. Clustering

Embeddings are grouped with HDBSCAN. The clustering stage uses an adaptive minimum cluster size based on batch size, then performs a second pass to assign some noise items to the nearest valid cluster when the cosine distance is below a threshold.

This step converts individual posts, videos, articles, and search signals into candidate trend groups.

### 6. LLM Analysis

Each cluster is analyzed by an LLM. The analysis stage ranks items by engagement, selects representative samples, and asks the model to return structured JSON with:

- Topic
- Summary
- Sentiment
- Keywords
- Content type
- Risk level
- Marketing guidance
- Social management guidance

The output is used directly by the dashboard layer and stored as part of the trend document.

### 7. Deduplication

New trends are compared with recent trends already stored in MongoDB. Deduplication uses a multi-factor score based on:

- Topic embedding similarity
- Keyword overlap
- Time decay
- Source overlap

If a new trend matches an existing trend, the pipeline merges samples, counters, keywords, and timestamps instead of inserting a duplicate record.

### 8. Storage

Final trends are inserted or updated in MongoDB. Old trends are cleaned up after a retention window so the dashboard focuses on recent activity.

## Keyword Extraction Workflow

The keyword extractor is a separate workflow for discovering new tracked keywords from news headlines.

It works as follows:

1. Collect headlines from selected Vietnamese RSS feeds.
2. Send the batch of headlines to an LLM.
3. Extract candidate trending keywords with category and reason fields.
4. Store extracted keywords in MongoDB with a pending status.
5. Let an admin approve or reject candidates from the dashboard.

Approved keywords can be added to the active keyword set used by producers in later collection cycles.

## Dashboard Workflow

The dashboard layer reads processed data from MongoDB.

User dashboard:

- Lists detected trends sorted by engagement.
- Shows topic, summary, sentiment, risk level, content type, keywords, source distribution, and sample items.
- Supports search and filtering by sentiment, risk level, and content type.
- Allows users to submit suggested keywords for review.

Admin dashboard:

- Reviews and manages detected trends.
- Approves or rejects user-submitted keywords.
- Reviews LLM-extracted keyword candidates.
- Adds, edits, and removes active tracked keywords.
- Records keyword management history for auditing.

## Main Data Models

The shared models in `common/models.py` define the contract between producers and consumers.

Important model groups:

- Source models: `TikTokVideo`, `YouTubeVideo`, `NewsArticle`, and trend-related source payloads.
- Kafka wrapper: a message envelope used when publishing source records to Kafka.
- Unified model: `ContentItem`, used by the processing pipeline after normalization.
- Output model: `Trend`, used for analyzed and stored trends.

The `Trend` model contains both content-level analysis and operational metadata, including topic, summary, sentiment, keywords, sample items, source counts, engagement statistics, risk level, and guidance fields.

## Design Notes

- Kafka is used as the boundary between collection and processing.
- PySpark is used for batch-oriented Kafka reads and schema-based parsing.
- HDBSCAN is used because the number of trends is not known in advance.
- LLM analysis is applied after clustering, not per item, to reduce cost and produce trend-level summaries.
- Deduplication is performed across batches to keep long-running trends updated instead of creating repeated records.
- MongoDB stores trends, active keywords, submitted keywords, extracted keywords, and keyword history.
- Streamlit is used for fast dashboard development and direct inspection of processed trend data.
