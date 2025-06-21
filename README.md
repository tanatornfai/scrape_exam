# Scrape TV data from Homepro and Powerbuy for price comparison

## Setup and Run Instructions

### 1. Build Airflow Image
```bash
docker build -t airflow-scraper .
```

### 2. Start Services
```bash
docker compose up -d
```

### 3. Run Pipeline
Access Airflow UI at http://localhost:8080 and trigger the scraping pipeline.

### 4. Check result
Open drive link{https://drive.google.com/drive/folders/1SaBmZ-jwPOhIl2uKvyShdE7k_cYOaZ6I?usp=sharing}
