# -*- coding: utf-8 -*-
# pylint: disable= line-too-long

"""
Database dumping flows for nivel_reservatorio project
"""

from copy import deepcopy

from prefect.run_configs import KubernetesRun
from prefect.storage import GCS
from prefeitura_rio.pipelines_templates.dump_url.flows import dump_url_flow
from prefeitura_rio.pipelines_utils.prefect import set_default_parameters
from prefeitura_rio.pipelines_utils.state_handlers import (
    handler_initialize_sentry,
    handler_inject_bd_credentials,
)

from pipelines.constants import constants
from pipelines.saneamento_drenagem.nivel_reservatorio.schedules import (
    update_schedule_nivel_reservatorio,
)

nivel_gsheets_flow = deepcopy(dump_url_flow)
nivel_gsheets_flow.state_handlers = [handler_inject_bd_credentials, handler_initialize_sentry]
nivel_gsheets_flow.name = "RIOAGUAS: Saneamento Drenagem - Nivel dos reservatorios"
nivel_gsheets_flow.storage = GCS(constants.GCS_FLOWS_BUCKET.value)
nivel_gsheets_flow.run_config = KubernetesRun(
    image=constants.DOCKER_IMAGE.value,
    labels=[
        constants.RJ_RIOAGUAS_AGENT_LABEL.value,
    ],
)

nivel_gsheets_flow_parameters = {
    "dataset_id": "saneamento_drenagem",
    "dump_mode": "overwrite",
    "url": "https://docs.google.com/spreadsheets/d/1zM0N_PonkALEK3YD2A4DF9W10Cm2n99_IiySm8zygqk/edit#gid=1343658906",  # noqa
    "url_type": "google_sheet",
    "gsheets_sheet_name": "Reservatórios",
    "table_id": "nivel_reservatorio",
}

nivel_gsheets_flow = set_default_parameters(
    nivel_gsheets_flow, default_parameters=nivel_gsheets_flow_parameters
)

nivel_gsheets_flow.schedule = update_schedule_nivel_reservatorio
