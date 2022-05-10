select p.symbol as cell_phenotype, s.symbol as marker, c.polarity, c.study
from cell_phenotype_criterion c
left join cell_phenotype p on c.cell_phenotype = p.identifier 
left join chemical_species s on s.identifier = c.marker ;
