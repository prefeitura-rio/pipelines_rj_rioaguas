# -*- coding: utf-8 -*-
"""
Utils Gerais da Rio-Águas.
"""

import pandas as pd
import requests
from prefeitura_rio.pipelines_utils.logging import log
from redis_pal import RedisPal


def login(url, user=None, password=None):
    """
    Função para fazer login no website.

    Args:
    url (str): URL da página inicial com os campos de usuário e senha.
    user (str): Usuário do login
    password (str): Senha de acesso.
    """

    client = requests.Session()

    # Retrieve the CSRF token first
    client.get(url)  # sets cookie
    if password:
        if "csrftoken" in client.cookies:
            # Django 1.6 and up
            csrftoken = client.cookies["csrftoken"]
        else:
            # older versions
            csrftoken = client.cookies["csrf"]

        payload = {
            "username": user,
            "password": password,
            "csrfmiddlewaretoken": csrftoken,
            "next": "/",
        }
    else:
        payload = {}

    client.post(url, data=payload, headers=dict(Referer=url))

    return client


def get_redis_client(
    host: str = "127.0.0.1",
    port: int = 6379,
    db: int = 0,  # pylint: disable=C0103
    password: str = None,
) -> RedisPal:
    """
    Returns a Redis client.
    """
    return RedisPal(
        host=host,
        port=port,
        db=db,
        password=password,
    )


# pylint: disable=W0106
def save_updated_rows_on_redis(  # pylint: disable=R0914
    dataframe: pd.DataFrame,
    dataset_id: str,
    table_id: str,
    unique_id: str = "id_estacao",
    date_column: str = "data_medicao",
    date_format: str = "%Y-%m-%d %H:%M:%S",
    mode: str = "prod",
) -> pd.DataFrame:
    """
    Acess redis to get the last time each unique_id was updated, return
    updated unique_id as a DataFrame and save new dates on redis
    """

    redis_client = get_redis_client(host="127.0.0.1")

    key = dataset_id + "." + table_id
    if mode == "dev":
        key = f"{mode}.{key}"

    # Access all data saved on redis with this key
    last_updates = redis_client.hgetall(key)

    if len(last_updates) == 0:
        last_updates = pd.DataFrame(dataframe[unique_id].unique(), columns=[unique_id])
        last_updates["last_update"] = "1900-01-01 00:00:00"
        log(f"Redis key: {key}\nCreating Redis fake values:\n {last_updates}")
    else:
        # Convert data in dictionary in format with unique_id in key and last updated time as value
        # Example > {"12": "2022-06-06 14:45:00"}
        last_updates = {k.decode("utf-8"): v.decode("utf-8") for k, v in last_updates.items()}

        # Convert dictionary to dataframe
        last_updates = pd.DataFrame(last_updates.items(), columns=[unique_id, "last_update"])

        log(f"Redis key: {key}\nRedis actual values:\n {last_updates}")

    # Garante that both are string
    dataframe[unique_id] = dataframe[unique_id].astype(str)
    last_updates[unique_id] = last_updates[unique_id].astype(str)

    # dataframe and last_updates need to have the same index, in our case unique_id
    missing_in_dfr = [
        i for i in last_updates[unique_id].unique() if i not in dataframe[unique_id].unique()
    ]
    missing_in_updates = [
        i for i in dataframe[unique_id].unique() if i not in last_updates[unique_id].unique()
    ]

    # If unique_id doesn't exists on updates we create a fake date for this station on updates
    if len(missing_in_updates) > 0:
        for i, _id in enumerate(missing_in_updates):
            last_updates.loc[-i] = [_id, "1900-01-01 00:00:00"]

    # If unique_id doesn't exists on dataframe we remove this stations from last_updates
    if len(missing_in_dfr) > 0:
        last_updates = last_updates[~last_updates[unique_id].isin(missing_in_dfr)]

    # Merge dfs using unique_id
    dataframe = dataframe.merge(last_updates, how="left", on=unique_id)
    log(f"Comparing times: {dataframe.sort_values(unique_id)}")

    # Keep on dataframe only the stations that has a time after the one that is saved on redis
    dataframe[date_column] = dataframe[date_column].apply(
        pd.to_datetime, format=date_format
    ) + pd.DateOffset(hours=0)

    dataframe["last_update"] = dataframe["last_update"].apply(
        pd.to_datetime, format="%Y-%m-%d %H:%M:%S"
    ) + pd.DateOffset(hours=0)

    dataframe = dataframe[dataframe[date_column] > dataframe["last_update"]].dropna(
        subset=[unique_id]
    )
    log(f"Dataframe after comparison: {dataframe.sort_values(unique_id)}")
    # Keep only the last date for each unique_id
    keep_cols = [unique_id, date_column]
    new_updates = dataframe[keep_cols].sort_values(keep_cols)
    new_updates = new_updates.groupby(unique_id, as_index=False).tail(1)
    new_updates[date_column] = new_updates[date_column].dt.strftime("%Y-%m-%d %H:%M:%S")
    log(f">>> Updated df: {new_updates.head(10)}")

    # Convert stations with the new updates dates in a dictionary
    new_updates = dict(zip(new_updates[unique_id], new_updates[date_column]))
    log(f">>> data to save in redis as a dict: {new_updates}")

    # Save this new information on redis
    [redis_client.hset(key, k, v) for k, v in new_updates.items()]

    return dataframe.reset_index()
