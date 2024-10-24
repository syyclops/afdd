import pandas as pd
import datetime
import psycopg
from psycopg import Connection
import os
import asyncio
import logging

from neo4j import GraphDatabase
from dotenv import load_dotenv
from datetime import timedelta
from typing import List

from afdd.logger import logger
from afdd.models import Rule
from afdd.utils import round_time, create_anomaly
from afdd.db import (
    load_timeseries,
    append_anomalies,
    load_rules,
    get_rules,
    load_graph_data,
)


def analyze_data(
    graph: pd.DataFrame, timeseries_data: pd.DataFrame, rule: Rule, start_time: str
) -> List[tuple]:
    duration = rule.condition.duration
    resample_size = int(
        duration * 0.25
    )  # increment size of the rolling average (how far it's going to roll each time)
    rounded_start = round_time(
        time=start_time, resample_size=resample_size
    )  # start time rounded to the nearest normalized time
    throwaway_at_start = rounded_start + timedelta(
        seconds=int(duration)
    )  # gets rid of the first few values of our table that aren't full windows
    logger.info(f"throwaway time: {throwaway_at_start}")
    # normalizes timestamps to intervals of resample size and compute the rolling mean
    resampled = (
        timeseries_data.groupby(level=0).resample(f"{resample_size}s", level=1).mean()
    )
    logger.info(f"resampled data:\n {resampled}")

    rolling_mean = resampled.groupby(level=0).rolling(window=5, min_periods=1).mean()
    rolling_mean = rolling_mean.droplevel(level=0)
    logger.info(f"df after rolling:\n{rolling_mean}")

    # filter out rows where timestamp is before cutoff_time
    rolling_mean = rolling_mean.loc[
        rolling_mean.index.get_level_values("ts") >= throwaway_at_start
    ]
    logger.info(f"df after throwing away:\n{rolling_mean}")

    # Evaluate the equation
    rolling_mean["results"] = rolling_mean.eval(rule.condition.equation)
    logger.info(f"new_df with results column:\n{rolling_mean}")

    # Put Trues in anomaly_df
    anomaly_df = rolling_mean.loc[rolling_mean["results"] == True]
    anomaly_df = anomaly_df.drop(columns=["results"])

    anomaly_df.reset_index(level="ts", inplace=True)  # to make the index 'ts' a column
    anomaly_df.rename(columns={"ts": "end_time"}, inplace=True)

    anomaly_df["start_time"] = anomaly_df["end_time"] - timedelta(seconds=duration)
    anomaly_df["start_time"] = pd.to_datetime(anomaly_df["start_time"])
    logger.info(f"anomaly_df after adding start_time:\n {anomaly_df}")

    anomaly_list = []
    for component, new_df in anomaly_df.groupby(level=0):
        # new_df = new_df[throwaway::]
        logger.info(f"component: {component}")
        logger.info(f"component df:\n {new_df}")
        combine_mask = new_df["start_time"] <= new_df["end_time"].shift(1)

        group_key = (~combine_mask).cumsum()
        grouped = (
            new_df.groupby(group_key)
            .agg({"start_time": "min", "end_time": "max"})
            .reset_index(drop=True)
        )
        logger.info(f"new_df after combining:\n {grouped}")

        device = graph.loc[graph["componentURI"] == component, "deviceURI"].values[0]
        points = graph.loc[
            (graph["componentURI"] == component)
            & (graph["class"].isin(rule.sensor_types)),
            "point",
        ].values
        grouped["anomaly"] = grouped.apply(
            lambda row: create_anomaly(
                row=row,
                component=component,
                device=device,
                rule_id=rule.rule_id,
                points=points,
            ),
            axis=1,
        )
        logger.info(f"new_df after adding anomaly column:\n {grouped}")
        anomaly_list.extend(grouped["anomaly"].tolist())

    return anomaly_list


async def start_rule(conn: Connection, graphInfoDF: pd.DataFrame, rule: Rule):
    """Evaluates a rule against its threshold"""
    while True:
        logger.info(
            "---------------------------------------------------------------------------------------------------------------------------------------------------------"
        )
        logger.info(f"*** STARTING ANALYSIS OF RULE {rule.rule_id} ***")

        resample_size = int(rule.condition.duration * 0.25)
        overlap = (
            rule.condition.duration / resample_size - 1
        ) * resample_size  # accounts for rolling averages from end of last iteration of loop
        start_time = (
            datetime.datetime.now()
            - datetime.timedelta(seconds=rule.condition.sleep_time)
            - datetime.timedelta(seconds=overlap)
        )
        end_time = datetime.datetime.now()
        sensors = rule.sensor_types
        logger.info(f"start_time: {start_time}, end_time: {end_time}")

        logger.info(f"*** LOADING TIMESERIES DATA FOR RULE {rule.rule_id} ***")
        timeseries_df = load_timeseries(
            conn=conn,
            graph=graphInfoDF,
            start_time=start_time,
            end_time=end_time,
            brick_list=sensors,
        )

        logger.info(f"*** ANALYZING DATA FOR RULE {rule.rule_id} ***")
        anomaly_list = analyze_data(
            graph=graphInfoDF,
            timeseries_data=timeseries_df,
            rule=rule,
            start_time=start_time,
        )

        logger.info(f"*** APPENDING AND UPDATING ANOMALIES FOR RULE {rule.rule_id} ***")
        append_anomalies(conn=conn, anomaly_list=anomaly_list)

        logger.info(f"*** SLEEPING RULE {rule.rule_id} ***")
        await asyncio.sleep(rule.condition.sleep_time)


async def start(conn: Connection, graphInfoDF: pd.DataFrame, rules_list: List[Rule]):
    """Creates a start_rule() coroutine object for each rule in the rules_list"""
    coro_list = []

    for rule in rules_list:
        coro_list.append(start_rule(conn=conn, graphInfoDF=graphInfoDF, rule=rule))

    await asyncio.gather(*coro_list)


def main():
    logging.info("")  # makes logs show up in docker?
    load_dotenv(override=True)
    logger.info(
        "+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++"
    )

    postgres_conn_string = os.environ["POSTGRES_CONNECTION_STRING"]
    conn = psycopg.connect(postgres_conn_string)

    neo4j_driver = GraphDatabase.driver(
        os.environ["NEO4J_URI"],
        auth=(os.environ["NEO4J_USER"], os.environ["NEO4J_PASSWORD"]),
        max_connection_lifetime=200,
    )
    neo4j_driver.verify_connectivity()

    # Loads rules.json into postgres then gets rules from postgres
    load_rules(conn=conn, rules_json="rules.json")
    rules_list = get_rules(conn=conn)
    logger.info(f"rules_list: {rules_list}")

    # Load graph data from neo4j
    graph_df = load_graph_data(driver=neo4j_driver, rules_list=rules_list)
    logger.info(f"graph_df: {graph_df}")

    neo4j_driver.close()

    # running anomaly detect in sleep time cycle
    asyncio.run(start(conn=conn, graphInfoDF=graph_df, rules_list=rules_list))


if __name__ == "__main__":
    main()
