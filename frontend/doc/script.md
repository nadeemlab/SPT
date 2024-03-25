
Testing session October 31 2023.

- URL: http://k8s-ingressn-ingressn-957844105a-df35bc90d7a2ee62.elb.us-east-1.amazonaws.com

Scenario 1
==========
*This study found both indicators highly predictive of complete response and indicators highly predictive of resistance to immunotherapy. The presence of proliferating CD8+ T cells displaying the exhausted state and the presence of aggregations of B cells both predicted complete response to subsequent treatment, while loss of MHCI on tumor cells predicted resistance to subsequent treatment.*

1. Select study => **Melanoma intralesional IL2**.
2. Create custom phenotype **KI67+ PD1+ LAG3+ TIM3+**, then **Add to selection**.
3. Select from phenotype list: **CD8+ T cell** and **KI67+ PD1+ LAG3+ TIM3+** and **B cell**.
4. **Next**.
5. Click tile with row/column: **CD8+ T cell** and **KI67+ PD1+ LAG3+ TIM3+**.
6. Click cohort **1** and click cohort **3**.
7. Click the numerical table column heading **CD8+ T cell, KI67+ PD1+ LAG3+ TIM3+**.
8. Note verbalization. (*25 ratio*)
9. Click the isolated column tile **CD8+ T cell**.
10. Click the numerical table column heading **CD8+ T cell**.
11. Note verbalization. (*6 ratio*)
12. Click the isolated column tile **B cell**.
13. Click the expander button **>** beside numerical table column header **B cell**.
14. Select **cell proximity** from drop-down.
15. After some time, if verbalization not updated, click cohort **1** or **3** again. (*3.58 ratio*)

Scenario 2
==========
*This study uncovered markers predictive of favorable response to ICI (Immune Checkpoint Inhibition) therapy, specifically anti-PDL1 and anti-CTLA4 therapies, by analysis of cell population structure and spatial proximity in pre-treatment melanoma samples, as measured by multiplexed imaging mass cytometry (time-of-flight) images. Proximity of antigen-experienced cytotoxic T cells (CD8+ CD45RO+) to melanoma cells was associated with favorable response. The overall presence of the proliferative such cells was also associated with favorable response.*

1. Select study => **Melanoma CyTOF ICI**.
2. Create custom phenotype **CD8A+ CD3+ CD45RO+**, then **Add to selection**.
3. Create custom phenotype **KI67+**, then **Add to selection**.
4. Select from phenotype list: **CD8A+ CD3+ CD45RO+** and **Melanoma** and **KI67+**.
5. **Next**.
6. Click tile with row/column: **Melanoma** and **CD8A+ CD3+ CD45RO+**.
7. Click expander button **>** beside numerical table column header **CD8A+ CD3+ CD45RO+**, **Melanoma**.
8. Select **neighborhood enrichment** from drop-down.
9. Wait for some values in the column to populate.
10. Click cohort **1** and **2**.
11. Note verbalization. Click cohort **1** or **2** again to refresh. (*1.24 ratio*)
12. Select **co-occurrence** from drop-down.
13. Wait for some values to populate.
14. Note verbalization. Click cohort **1** or **2** to refresh. (*1.06 ratio*)
15. Click tile with row/column: **CD8A+ CD3+ CD45RO+** and **KI67**.
16. Click numerical table column header **CD8A+ CD3+ CD45RO+, KI67**.
17. Note verbalization. (*1.41 ratio*)

Scenario 3
==========
*In this study, cell-intrinsic heterogeneity was found to be indicative of poor disease outcomes, and spatial localization of respective tumor subtypes within a single tumor to respective regions was found to be both common and associated with better prognosis than the heterogeneous alternative.*

1. Select study => **Breast cancer IMC**.
2. Create custom phenotype **CK+ KRT14+**, then **Add to selection**.
3. Create custom phenotype **CK+ KRT7+**, then **Add to selection**.
4. Create custom phenotype **CK+ KRT5+**, then **Add to selection**.
4. Create custom phenotype **CK+ KRT19+**, then **Add to selection**.
5. Create custom phenotype **CK+**, then **Add to selection**.
6. Select phenotypes from list: **CK+ KRT14+** and **CK+ KRT7+** and **CK+ KRT5+**.
7. Select tile with row/column: **CK+ KRT14+** and **CK+ KRT7+**.
8. Click expander button **>** beside numerical table column header **CK+ KRT14+, CK+ KRT7+**.
9. Select **cell proximity** from drop-down.
10. Wait for values to populate.
11. Click cohort **2** and cohort **1**.
12. Note verbalization. (*1.69 ratio*)
13. Repeat steps 7-12 for pair **CK+ KRT14+** and **CK+ KRT5+**, comparing cohorts **2** and **3**. (*1.53 ratio*)
14. Click isolated column tile **CK+ KRT14** and **CK+ KRT19+**.
15. Click numerical table column header **CK+ KRT14** then header **CK+ KRT19+**.
16. Click cohort **2** and cohort **1**.
17. Note verbalization. (*11.48 ratio*)
18. Click cohort **2** and cohort **3**.
19. Note verbalization. (*112.7 ratio*)
