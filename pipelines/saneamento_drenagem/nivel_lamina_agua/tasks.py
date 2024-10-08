# -*- coding: utf-8 -*-

"""
Tasks para pipeline de dados de nível de lâmina de água em via.
"""
# pylint: disable=C0327, E1120, W0108

from pathlib import Path
from typing import Union
import pandas as pd
import pendulum
import unidecode
from bs4 import BeautifulSoup
from prefect import task

from pipelines.constants import constants
from pipelines.utils import login, save_updated_rows_on_redis

from prefeitura_rio.pipelines_utils.pandas import (
    to_partitions,
    parse_date_columns,
)

from prefeitura_rio.pipelines_utils.infisical import get_secret
from prefeitura_rio.pipelines_utils.logging import log


@task
def download_file() -> pd.DataFrame:
    """
    Função para download de tabela com os dados.

    Args:
    download_url (str): URL onde a tabela está localizada.
    """
    infisical_url = constants.INFISICAL_URL.value

    url = get_secret(infisical_url, path="/nivel_lamina_agua")[infisical_url]

    session = login(url)

    page = session.get(url)

    # Faz o parse do htm e seleciona apenas dados que estão em tabela
    soup = BeautifulSoup(page.text, "html.parser")
    table = soup.find_all("table")

    # Converte dados para dataframe
    dados = pd.read_html(str(table), flavor="bs4")[0]

    return dados


@task
def tratar_dados(
    dados: pd.DataFrame, dataset_id: str, table_id: str, mode: str = "prod"
) -> pd.DataFrame:
    """Tratar dados para o padrão estabelecido e filtrar linhas para salvarmos apenas as medições
    que foram contratadas pela prefeitura.
    """

    # Cria id das estações
    estacao_2_id_estacao = {
        "Catete": "1",
        "Bangu - Rua da Feira": "2",
        "Bangu - Rua do Açudes": "3",
        "Rio Maracanã - Visc Itamarati": "4",
        "Itanhangá": "5",
        "Bangu - Av Santa Cruz": "6",
        "Lagoa": "7",
        "Rio Maracanã - R: Uruguai": "8",
    }

    dados["id_estacao"] = dados["Endereço"].map(estacao_2_id_estacao)

    rename_cols = {
        "Endereço": "endereco",
        "Último envio": "data_medicao",
        "Temperatura": "temperatura",
        "Umidade": "umidade",
        "Precipitação": "precipitacao",
        "Lâmina": "altura_agua",
    }

    # Substitui valores que aparecem nas linhas
    dados = dados.rename(rename_cols, axis=1).replace(
        {
            " ºC": "",
            " %": "",
            " mm": "",
            " cm": "",
            ",": ".",
            "R:": "rua",
        },
        regex=True,
    )

    dados["endereco"] = dados["endereco"].str.capitalize()
    dados["endereco"] = dados["endereco"].apply(lambda x: unidecode.unidecode(x))
    date_format = "%d/%m/%Y %H:%M"
    dados["data_medicao"] = pd.to_datetime(dados["data_medicao"], format=date_format)

    # Fixa ordem das colunas
    cols_order = [
        "data_medicao",
        "id_estacao",
        "endereco",
        "altura_agua",
        "precipitacao",
        "umidade",
        "temperatura",
    ]

    log(f"[DEBUG]: dados coletados\n{dados.head()}")

    dados = save_updated_rows_on_redis(
        dados,
        dataset_id,
        table_id,
        unique_id="id_estacao",
        date_column="data_medicao",
        date_format="%d/%m/%Y %H:%M",
        mode=mode,
    )
    log(f"[DEBUG]: dados que serão salvos\n{dados.head()}")

    return dados[cols_order]


@task
def salvar_dados(dados: pd.DataFrame) -> Union[str, Path]:
    """
    Salvar dados em csv.
    """
    save_cols = [
        "data_medicao",
        "id_estacao",
        "altura_agua",
    ]

    dataframe = dados[save_cols].copy()

    prepath = Path("/tmp/altura_agua/")
    prepath.mkdir(parents=True, exist_ok=True)

    partition_column = "data_medicao"
    dataframe, partitions = parse_date_columns(dataframe, partition_column)

    current_time = pendulum.now("America/Sao_Paulo").strftime("%Y%m%d%H%M")

    to_partitions(
        data=dataframe,
        partition_columns=partitions,
        savepath=prepath,
        data_type="csv",
        suffix=current_time,
    )
    log(f"[DEBUG] Files saved on {prepath}")

    return prepath
