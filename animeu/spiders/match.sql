SELECT DISTINCT
    group_concat(DISTINCT(umc.reference_id)) as reference_ids
FROM unmatched_character AS umc
INNER JOIN character_name AS cn
    ON cn.normalized_character_name = umc.normalized_character_name
INNER JOIN anime_name AS an
    ON an.anime_id = cn.anime_id
    AND an.normalized_anime_name = umc.normalized_anime_name
GROUP BY cn.character_name_id, an.anime_id
HAVING COUNT(DISTINCT(umc.reference_id)) > 1;
