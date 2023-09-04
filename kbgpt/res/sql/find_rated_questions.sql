WITH
    latest_rating AS (
        -- find all latest rating for the question and node id
        WITH ranked_groups AS (
                SELECT
                    *,
                    ROW_NUMBER () OVER (
                        PARTITION BY question_id,
                        node_id
                        ORDER BY
                            `timestamp` DESC
                    ) AS rn
                FROM
                    rating_human_rating
                WHERE
                    rater = '{rater}'
            )
        SELECT *
        FROM ranked_groups
        WHERE rn = 1
    )
SELECT {columns}
FROM log_qa_record q
WHERE
    -- filter the ones that not in partially rated
    q.id NOT IN (
        -- this is the not rated or partially rated
        SELECT q.id
        FROM log_qa_record q
            JOIN log_jinja_engine_record j ON q.invoke_id = j.invoke_id
            LEFT JOIN latest_rating lr ON q.invoke_id = lr.invoke_id
        WHERE
            lr.rating IS NULL
    )
