select sc.source as subject, di.result as diagnosis, s.symbol as marker, q.quantity from expression_quantification q
left join chemical_species s on q.target = s.identifier
left join histological_structure hs on hs.identifier = q.histological_structure
left join histological_structure_identification i on i.histological_structure = hs.identifier
left join data_file df on df.sha256_hash = i.data_source
left join specimen_data_measurement_process sp on sp.identifier = df.source_generation_process
left join specimen_collection_process sc on sc.specimen = sp.specimen
left join subject su on su.identifier = sc.source
left join diagnosis di on di.subject = su.identifier
left join specimen_collection_study st on st.name = sc.study
where s.symbol='{{ marker_symbol }}' and st.name = '{{ specimen_collection_study_name }}' ;
