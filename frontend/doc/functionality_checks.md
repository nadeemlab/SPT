
# SPT application functionality checks

These checks are for whole-application testing, including backend datasets. Many of the checks can be done on a development or local instance of the application.

During the actions below, monitor the container logs. For actions that take place in the browser, also monitor the developer console for errors and warnings, and repeat these steps in different browsers.

1. **Landing page**. Check that the landing page basically loads, with styling. This includes the navigation bar and study selector presence.
2. **API service**. Check that the API service is live. Use `/study-names`, a cheap endpoint with no parameters.
3. **Study selector**. Check that the study selection dropdown menu is displaying without major placement problems, and with the expected names.
4. **Study selection**. Check that each study can be clicked with loading of summary info: publication title, number of samples, number of cells, sample cohort table, etc.
5. **Pre-computed fractions**. Check that the "phenotype fractions" page has a populated table.
6. **Phenotype definer**. Check that the correct number of channels are available for custom phenotype definition. Create custom phenotypes that exhaustively cover these, i.e. such that each channel is listed at least once in some custom-defined phenotype.
7. **Phenotype selector**. Check that each of the named phenotypes (plus the custom ones) can be clicked, with corresponding effect on the overlaps page heatmap (new entries). Delay should be less than about 10 seconds. To do this efficiently, click only a few at a time (say 3), then click these off before proceeding with the next ones. (All pairs of all selected phenotypes get queried, there is no need to do every possible combination just for testing).
8. **Heatmap entries**. Check that each heatmap tile, both in the flat list and the square/pairwise matrix, are clickable with instantaneous effect populating the per-sample table in the lower area.
9. **Per-sample features**. Check that the total cell counts appearing in the per-sample table are sensible (ideally, check that they match previous runs). Check that the phenotype-specific counts are also sensible.
10. **Cohort comparison verbalization**. Check that clicking a pair of cohort assignment values and then a feature/column name results in the appearance of the sentential summary. Check that the summary has numeric values (not NaN) for non-trivial features. Check that clicking a second feature results in the "fractional" statement variant (ratio of one feature's cell count to another).
