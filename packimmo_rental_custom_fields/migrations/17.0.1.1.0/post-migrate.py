def migrate(cr, version):
    cr.execute(
        """
            UPDATE property_details
               SET floor_selection = CASE
                   WHEN type = 'land' THEN NULL
                   WHEN type = 'residential' AND total_floor = 0
                   THEN 'villa_basse'
                   ELSE floor::varchar
               END
        """
    )
