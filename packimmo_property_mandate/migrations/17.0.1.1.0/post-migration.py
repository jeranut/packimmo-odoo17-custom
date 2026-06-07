def migrate(cr, version):
    cr.execute(
        """
        UPDATE property_mandate AS mandate
           SET company_id = property.company_id
          FROM property_details AS property
         WHERE property.mandate_id = mandate.id
           AND property.company_id IS NOT NULL
           AND mandate.company_id IS DISTINCT FROM property.company_id
        """
    )
