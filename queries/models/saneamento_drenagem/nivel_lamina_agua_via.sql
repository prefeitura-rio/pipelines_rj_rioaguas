SELECT 
DISTINCT
CONCAT(id_estacao, '_', data_medicao) AS primary_key,
SAFE_CAST(altura_agua AS FLOAT64) altura_agua,
SAFE_CAST(SAFE_CAST(data_medicao AS DATETIME) AS TIME) horario,
SAFE_CAST(DATE_TRUNC(DATE(data_medicao), day) AS DATE) data_particao
FROM `rj-rioaguas.saneamento_drenagem_staging.nivel_lamina_agua_via`