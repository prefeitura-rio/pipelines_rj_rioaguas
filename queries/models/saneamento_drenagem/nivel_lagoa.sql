
SELECT
  DISTINCT
  CONCAT(id_estacao, '_', data_medicao) AS primary_key,
  id_estacao,
  nome_estacao,
  SAFE_CAST(lamina_nivel as FLOAT64) as lamina_nivel,
  SAFE_CAST(SAFE_CAST(data_medicao AS DATETIME) AS TIME) horario,
  SAFE_CAST(DATE_TRUNC(DATE(data_medicao), day) AS DATE) data_particao
FROM `rj-rioaguas.saneamento_drenagem_staging.nivel_lagoa`
