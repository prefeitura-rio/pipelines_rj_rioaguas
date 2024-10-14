# -*- coding: utf-8 -*-
# pylint: disable= line-too-long

"""
Schedules for the database dump pipeline
"""

from datetime import datetime, timedelta

import pytz
from prefect.schedules import Schedule
from prefect.schedules.clocks import IntervalClock

from pipelines.constants import constants

# from prefeitura_rio.pipelines_utils.io import untuple_clocks as untuple
# from prefeitura_rio.pipelines_utils.prefect import generate_dump_url_schedules

# gsheets_urls_nivel_reservatorio = {
#     "nivel_reservatorio": {
#         "dump_mode": "overwrite",
#         "url": "https://docs.google.com/spreadsheets/d/1zM0N_PonkALEK3YD2A4DF9W10Cm2n99_IiySm8zygqk/edit#gid=1343658906",  # noqa
#         "url_type": "google_sheet",
#         "gsheets_sheet_name": "Reservatórios",
#         "materialize_after_dump": True,
#         "materialization_mode": "prod",
#         "materialize_to_datario": False,
#         "dump_to_gcs": False,
#     },
# }


# gsheets_clocks_nivel_reservatorio = generate_dump_url_schedules(
#     interval=timedelta(hours=2),
#     start_date=datetime(2022, 11, 17, 12, 0, tzinfo=pytz.timezone("America/Sao_Paulo")),
#     labels=[
#         constants.RJ_RIOAGUAS_AGENT_LABEL.value,
#     ],
#     dataset_id="saneamento_drenagem",
#     table_parameters=gsheets_urls_nivel_reservatorio,
# )

# update_schedule_nivel_reservatorio = Schedule(clocks=untuple(gsheets_clocks_nivel_reservatorio))

update_schedule_nivel_reservatorio = Schedule(
    clocks=[
        IntervalClock(
            interval=timedelta(hours=2),
            start_date=datetime(2022, 11, 17, 12, 0, tzinfo=pytz.timezone("America/Sao_Paulo")),
            labels=[
                constants.RJ_RIOAGUAS_AGENT_LABEL.value,
            ],
            parameter_defaults={
                "dump_mode": "overwrite",
                "url": "https://docs.google.com/spreadsheets/d/1zM0N_PonkALEK3YD2A4DF9W10Cm2n99_IiySm8zygqk/edit#gid=1343658906",  # noqa
                "url_type": "google_sheet",
                "gsheets_sheet_name": "Reservatórios",
                "materialize_after_dump": True,
                "materialization_mode": "prod",
                "materialize_to_datario": False,
                "dump_to_gcs": False,
            },
        )
    ]
)
