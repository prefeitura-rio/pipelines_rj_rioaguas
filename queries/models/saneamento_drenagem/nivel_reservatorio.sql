{{
    config(
        partition_by={
            "field": "data_particao",
            "data_type": "date",
            "granularity": "month",
        }    
    )
}}

WITH VARNHAGEN AS (
SELECT
  CONCAT('3_',REPLACE(SAFE_CAST(SAFE.PARSE_TIMESTAMP('%d/%m/%Y %H:%M:%S', _) AS STRING), ' ','_')) as primary_key,
  '3' AS id_reservatorio,
  SAFE_CAST('Varnhagen' AS STRING) AS nome_reservatorio,
  SAFE_CAST(SAFE.PARSE_TIMESTAMP('%d/%m/%Y %H:%M:%S', _) AS DATE) as data_particao,
  SAFE_CAST(SAFE.PARSE_TIMESTAMP('%d/%m/%Y %H:%M:%S', _) AS TIME) as horario,
  SAFE_CAST(REPLACE(nivel_na_varnhagen, ",", ".") as FLOAT64) as altura_agua,
FROM `rj-rioaguas.saneamento_drenagem_staging.nivel_reservatorio`
WHERE nivel_na_varnhagen != 'nan' AND nivel_na_varnhagen IS NOT NULL AND nivel_na_varnhagen != '' AND nivel_na_varnhagen != 'null'),

NITEROI AS (
SELECT
  CONCAT('2_',REPLACE(SAFE_CAST(SAFE.PARSE_TIMESTAMP('%d/%m/%Y %H:%M:%S', _) AS STRING), ' ','_')) as primary_key,
  '2' AS id_reservatorio,
  SAFE_CAST('Niteroi' AS STRING) AS nome_reservatorio,
  SAFE_CAST(SAFE.PARSE_TIMESTAMP('%d/%m/%Y %H:%M:%S', _) AS DATE) as data_particao,
  SAFE_CAST(SAFE.PARSE_TIMESTAMP('%d/%m/%Y %H:%M:%S', _) AS TIME) as horario,
  SAFE_CAST(REPLACE(nivel_na_niteroi, ",", ".") as FLOAT64) as altura_agua
FROM `rj-rioaguas.saneamento_drenagem_staging.nivel_reservatorio`
WHERE nivel_na_niteroi != 'nan' AND nivel_na_niteroi IS NOT NULL AND nivel_na_niteroi != '' AND nivel_na_niteroi != 'null'),


BANDEIRA AS (
SELECT
  CONCAT('1_',REPLACE(SAFE_CAST(SAFE.PARSE_TIMESTAMP('%d/%m/%Y %H:%M:%S', _) AS STRING), ' ','_')) as primary_key  ,
  '1' AS id_reservatorio,
  SAFE_CAST('Bandeira' AS STRING) AS nome_reservatorio,
  SAFE_CAST(SAFE.PARSE_TIMESTAMP('%d/%m/%Y %H:%M:%S', _) AS DATE) as data_particao,
  SAFE_CAST(SAFE.PARSE_TIMESTAMP('%d/%m/%Y %H:%M:%S', _) AS TIME) as horario,    
  SAFE_CAST(REPLACE(nivel_bandeira, ",", ".") as FLOAT64) as altura_agua
FROM `rj-rioaguas.saneamento_drenagem_staging.nivel_reservatorio`
WHERE nivel_bandeira != 'nan' AND nivel_bandeira IS NOT NULL AND nivel_bandeira != '' AND nivel_bandeira != 'null')

SELECT DISTINCT * FROM VARNHAGEN
UNION ALL

SELECT DISTINCT * FROM NITEROI

UNION ALL

SELECT DISTINCT * FROM BANDEIRA  