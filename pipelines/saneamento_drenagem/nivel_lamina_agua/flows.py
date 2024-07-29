# -*- coding: utf-8 -*-
"""
Flows para pipeline de dados de nível de lâmina de água em via.
"""
# pylint: disable=C0327, C0103

from datetime import timedelta

from prefect import case, Parameter
from prefect.run_configs import KubernetesRun
from prefect.storage import GCS
from prefect.tasks.prefect import create_flow_run, wait_for_flow_run

from pipelines.constants import constants
from pipelines.saneamento_drenagem.nivel_lamina_agua.tasks import (
    download_file,
    tratar_dados,
    salvar_dados,
)
from pipelines.saneamento_drenagem.nivel_lamina_agua.schedules import (
    MINUTE_SCHEDULE,
)

from prefeitura_rio.core import settings
from prefeitura_rio.pipelines_utils.custom import Flow
from prefeitura_rio.pipelines_utils.state_handlers import (
    handler_initialize_sentry,
    handler_inject_bd_credentials,
)
from prefeitura_rio.pipelines_utils.tasks import (
    create_table_and_upload_to_gcs,
    get_current_flow_project_name,
)
from prefeitura_rio.pipelines_utils.prefect import task_get_current_flow_run_labels

with Flow(
    "RIOAGUAS: Saneamento Drenagem - Lamina de água em via",
    state_handlers=[
        handler_initialize_sentry,
        handler_inject_bd_credentials,
    ],
    skip_if_running=False,
) as rj_rioaguas__saneamento_drenagem__lamina_agua__flow:

    # Parâmetros para a Materialização
    materialize_after_dump = Parameter("materialize_after_dump", default=False, required=False)
    materialize_to_datario = Parameter("materialize_to_datario", default=False, required=False)
    materialization_mode = Parameter("mode", default="dev", required=False)

    # Parâmetros para salvar dados no GCS
    dataset_id = Parameter("dataset_id", default="saneamento_drenagem", required=False)
    table_id = Parameter("table_id", default="nivel_lamina_agua_via", required=False)
    dump_mode = Parameter("dump_mode", default="append", required=False)

    # Dump to GCS after? Should only dump to GCS if materializing to datario
    dump_to_gcs = Parameter("dump_to_gcs", default=False, required=False)

    maximum_bytes_processed = Parameter(
        "maximum_bytes_processed",
        required=False,
        default=settings.GCS_DUMP_MAX_BYTES_PROCESSED_PER_TABLE,
    )

    # Tasks
    dados = download_file()
    dados_tratados = tratar_dados(dados, dataset_id, table_id)
    save_path = salvar_dados(dados_tratados)

    # Create table in BigQuery TODO
    upload_table = create_table_and_upload_to_gcs(
        data_path=save_path,
        dataset_id=dataset_id,
        table_id=table_id,
        dump_mode=dump_mode,
    )

    upload_table.set_upstream(save_path)

    # Trigger DBT flow run
    with case(materialize_after_dump, True):
        current_flow_labels = task_get_current_flow_run_labels()
        current_flow_project_name = get_current_flow_project_name()
        current_flow_project_name.set_upstream(current_flow_labels)
        materialization_flow = create_flow_run(
            flow_name=settings.FLOW_NAME_EXECUTE_DBT_MODEL,
            project_name=current_flow_project_name,
            parameters={
                "dataset_id": dataset_id,
                "table_id": table_id,
                "mode": materialization_mode,
                "materialize_to_datario": materialize_to_datario,
            },
            labels=current_flow_labels,
            run_name=f"Materialize {dataset_id}.{table_id}",
        )

        materialization_flow.set_upstream(upload_table)

        wait_for_materialization = wait_for_flow_run(
            materialization_flow,
            stream_states=True,
            stream_logs=True,
            raise_final_state=True,
        )

        wait_for_materialization.max_retries = settings.TASK_MAX_RETRIES_DEFAULT
        wait_for_materialization.retry_delay = timedelta(seconds=settings.TASK_RETRY_DELAY_DEFAULT)

        with case(dump_to_gcs, True):
            # Trigger Dump to GCS flow run with project id as datario
            dump_to_gcs_flow = create_flow_run(
                flow_name=settings.FLOW_NAME_DUMP_TO_GCS,
                project_name=current_flow_project_name,
                parameters={
                    "project_id": "datario",
                    "dataset_id": dataset_id,
                    "table_id": table_id,
                    "maximum_bytes_processed": maximum_bytes_processed,
                },
                labels=[
                    "datario",
                ],
                run_name=f"Dump to GCS {dataset_id}.{table_id}",
            )
            dump_to_gcs_flow.set_upstream(wait_for_materialization)

            wait_for_dump_to_gcs = wait_for_flow_run(
                dump_to_gcs_flow,
                stream_states=True,
                stream_logs=True,
                raise_final_state=True,
            )

rj_rioaguas__saneamento_drenagem__lamina_agua__flow.storage = GCS(constants.GCS_FLOWS_BUCKET.value)
rj_rioaguas__saneamento_drenagem__lamina_agua__flow.run_config = KubernetesRun(
    image=constants.DOCKER_IMAGE.value,
    labels=[
        constants.RJ_RIOAGUAS_AGENT_LABEL.value,
    ],
)
rj_rioaguas__saneamento_drenagem__lamina_agua__flow.schedule = MINUTE_SCHEDULE
