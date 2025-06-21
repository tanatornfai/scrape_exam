import time
from pprint import pprint
import os
import pendulum

from airflow.providers.standard.operators.python import (
    PythonOperator,
)
from airflow.sdk import DAG
import duckdb
from helper import (
    HomeProProductScraping,
    PowerBuyProductScraping,
    upload_results_to_drive,
)
import pandas as pd

keyword = "TV Samsung"
current_dir = os.path.dirname(os.path.abspath(__file__))


def scrape_homepro(keyword):
    homepro = HomeProProductScraping(keyword)
    homepro.execute()


def scrape_powerbuy(keyword):
    powerbuy = PowerBuyProductScraping(keyword)
    powerbuy.execute()


def setup_databases():
    conn = duckdb.connect(os.path.join(current_dir, "products.db"))
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS products (
            website VARCHAR,
            keyword VARCHAR,
            name VARCHAR,
            price VARCHAR,
            product_id VARCHAR,
            monitor_size VARCHAR
        )
    """
    )


def compare_product_price():
    conn = duckdb.connect(os.path.join(current_dir, "products.db"))
    compare_df = pd.read_sql(
        """SELECT * FROM (PIVOT products 
            ON website 
            USING SUM(price)
            GROUP BY product_id, monitor_size) x
            """,
        con=conn,
    ).to_csv(os.path.join(current_dir, "tmp/compare_price.csv"), index=False)


with DAG(
    dag_id="product_price_comparison",
    schedule=None,
    start_date=pendulum.datetime(2025, 6, 20, tz="UTC"),
    catchup=False,
    tags=["exam"],
) as dag:

    setup_databases_task = PythonOperator(
        task_id="setup_databases",
        python_callable=setup_databases,
    )
    scrape_homepro_task = PythonOperator(
        task_id="scrape_homepro",
        python_callable=scrape_homepro,
        op_kwargs={"keyword": keyword},
    )
    scrape_powerbuy_task = PythonOperator(
        task_id="scrape_powerbuy",
        python_callable=scrape_powerbuy,
        op_kwargs={"keyword": keyword},
    )
    compare_product_price_task = PythonOperator(
        task_id="compare_product_price",
        python_callable=compare_product_price,
    )
    upload_results_to_drive_task = PythonOperator(
        task_id="upload_results_to_drive",
        python_callable=upload_results_to_drive,
        op_kwargs={
            "credentials_path": os.path.join(current_dir, "service_account.json"),
            "file_path": os.path.join(current_dir, "tmp/compare_price.csv"),
            "folder_id": "1SaBmZ-jwPOhIl2uKvyShdE7k_cYOaZ6I",
        },
    )
    (
        setup_databases_task
        >> [scrape_homepro_task, scrape_powerbuy_task]
        >> compare_product_price_task
        >> upload_results_to_drive_task
    )
