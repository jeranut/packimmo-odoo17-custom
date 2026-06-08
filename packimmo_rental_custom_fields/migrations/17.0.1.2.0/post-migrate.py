def migrate(cr, version):
    cr.execute(
        """
            UPDATE property_details
               SET floor_occupation = CASE
                   WHEN total_floor = 0 THEN 'plain_pied'
                   ELSE 'multiple_floors'
               END
        """
    )
