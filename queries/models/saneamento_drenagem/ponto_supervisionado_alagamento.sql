SELECT 
DISTINCT
id_ponto_supervisionado,
classe,
SAFE_CAST(top_50 AS INT) top_50,
causa_alagamento,
medida_cor,
eliminado,
endereco_ponto_supervisionado,
bairro,
area_planejamento,
regiao_administrativa,
bacia_hidrografica,
sub_bacia_hidrografica,
SAFE_CAST(latitude AS FLOAT64) AS latitude,
SAFE_CAST(longitude AS FLOAT64) AS longitude,
SAFE_CAST(utm_x AS FLOAT64) AS utm_x,
SAFE_CAST(utm_y AS FLOAT64) AS utm_y,
ST_GEOGPOINT(SAFE_CAST(longitude AS FLOAT64), SAFE_CAST(latitude AS FLOAT64)) AS geometry,
projeto,
SAFE_CAST(data_atualizacao AS DATE) data_atualizacao,
SAFE_CAST(ano_vigencia AS INT) ano_vigencia
FROM `rj-rioaguas.saneamento_drenagem_staging.ponto_supervisionado_alagamento`
