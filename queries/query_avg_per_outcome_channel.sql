select di.result as diagnosis, s.symbol as channel, avg(q.quantity) as mean_expression from expression_quantification q
left join chemical_species s on q.target = s.identifier
left join histological_structure hs on hs.identifier = q.histological_structure
left join histological_structure_identification i on i.histological_structure = hs.identifier
left join data_file df on df.sha256_hash = i.data_source
left join specimen_data_measurement_process sp on sp.identifier = df.source_generation_process
left join specimen_collection_process sc on sc.specimen = sp.specimen
left join subject su on su.identifier = sc.source
left join diagnosis di on di.subject = su.identifier
group by di.result, s.symbol
order by s.symbol, di.result ;
