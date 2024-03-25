
# Data preparation instructions

Start in spt-data.

1. Set up temporary local database. Consider setting the data directory to be in a large-storage area.
    ```sh
    sudo systemctl start postgresql
    ```

2. Set up schema.
    ```sh
    spt db create-schema --database-config-file=~/.spt_db.config.local --force
    ```

3. Drop constraints.
    ```sh
    spt db modify-constraints --database-config-file=~/.spt_db.config.local --drop
    ```

4. Import one small-ish dataset. In `spt-data`:
    ```sh
    bash convenience_scripts/configure_all_imports.sh
    source convenience_scripts/import_functions.sh
    import_dataset "melanoma_intralesional_il2" $PWD
    ```

5. Recreate constraints.
    ```sh
    spt db modify-constraints --database-config-file=~/.spt_db.config.local --recreate
    ```

6. Refresh views.
    ```sh
    spt db create-schema --refresh-views-only --database-config-file=~/.spt_db.config.local
    ```

7. Create the special index.
    ```sh
    spt db index-expressions-table --database-config-file=~/.spt_db.config.local
    ```

8. Run UMAPs workflow.
    ```sh
    mkdir umap_runs
    cd umap_runs
    mkdir mel_il2
    cd mel_il2
    spt workflow configure --workflow="reduction visual" --study-name="Melanoma intralesional IL2" --local --database-config-file=~/.spt_db.config.local
    ./run.sh
    ```

9. Dump the database to dump file.
    ```sh
    pg_dump -Fc scstudies > mel_il2.jun_13_2023.sqldump
    ```

10. Create the expression and location cache files.
    ```sh
    mkdir cachefiles
    cd cachefiles
    spt ondemand cache-expressions-data-array --database-config-file=~/.spt_db.config.local
    ```

11. Restore the database into the AWS prod db.
    ```sh
    pg_restore -h spt.cneqeknwkgdc.us-east-1.rds.amazonaws.com -U apireader -d scstudies2 mel_il2.jun_13_2023.sqldump
    ```

12. Grant permissions, if necessary.
    ```sh
    psql -h spt.cneqeknwkgdc.us-east-1.rds.amazonaws.com -U apireader scstudies2

    GRANT SELECT ON ALL TABLES IN SCHEMA public TO apireader;
    GRANT SELECT ON ALL SEQUENCES IN SCHEMA public TO apireader;
    GRANT TEMPORARY ON DATABASE scstudies2 TO apireader;
    ```

13. Upload the expression and location cache files.
    ```sh
    aws s3 cp ./cachefiles s3://spt-prod-fast-counts
    ```

14. Restart services.

15. Test the frontend. Browser at:
    https://oncopathtk.spt.aws.mskcc.org

## June 13 run times
- #4 (29 min)
- #6 (18 min)
- #7 (7 hours)
- #8 (2 min)
- #9 (2 min)
- #10 (5 min)
- #11 (1.5 hours)
- extra views refresh (>25 mins)

## Unexplained errors in #11
```
pg_restore: while PROCESSING TOC:
pg_restore: from TOC entry 3395; 0 38757 MATERIALIZED VIEW DATA computed_feature_3_specifiers_study_specimen postgres
pg_restore: error: could not execute query: ERROR:  relation "feature_specifier" does not exist
LINE 1: ...feature_specification, ordinality, specifier from feature_sp...
                                                             ^
QUERY:  select feature_specification, ordinality, specifier from feature_specifier order by 1,2
Command was: REFRESH MATERIALIZED VIEW public.computed_feature_3_specifiers_study_specimen;


pg_restore: from TOC entry 3396; 0 38765 MATERIALIZED VIEW DATA computed_feature_3_specifiers_generalized_cases postgres
pg_restore: error: could not execute query: ERROR:  materialized view "computed_feature_3_specifiers_study_specimen" has not been populated
HINT:  Use the REFRESH MATERIALIZED VIEW command.
Command was: REFRESH MATERIALIZED VIEW public.computed_feature_3_specifiers_generalized_cases;


pg_restore: from TOC entry 3398; 0 38780 MATERIALIZED VIEW DATA computed_feature_3_specifiers_maxima postgres
pg_restore: error: could not execute query: ERROR:  materialized view "computed_feature_3_specifiers_generalized_cases" has not been populated
HINT:  Use the REFRESH MATERIALIZED VIEW command.
Command was: REFRESH MATERIALIZED VIEW public.computed_feature_3_specifiers_maxima;


pg_restore: from TOC entry 3399; 0 38788 MATERIALIZED VIEW DATA computed_feature_3_specifiers_minima postgres
pg_restore: error: could not execute query: ERROR:  materialized view "computed_feature_3_specifiers_generalized_cases" has not been populated
HINT:  Use the REFRESH MATERIALIZED VIEW command.
Command was: REFRESH MATERIALIZED VIEW public.computed_feature_3_specifiers_minima;


pg_restore: from TOC entry 3397; 0 38773 MATERIALIZED VIEW DATA computed_feature_3_specifiers_moments_generalized_cases postgres
pg_restore: error: could not execute query: ERROR:  materialized view "computed_feature_3_specifiers_generalized_cases" has not been populated
HINT:  Use the REFRESH MATERIALIZED VIEW command.
Command was: REFRESH MATERIALIZED VIEW public.computed_feature_3_specifiers_moments_generalized_cases;


pg_restore: from TOC entry 3400; 0 38796 MATERIALIZED VIEW DATA computed_feature_3_specifiers_stats postgres
pg_restore: error: could not execute query: ERROR:  materialized view "computed_feature_3_specifiers_maxima" has not been populated
HINT:  Use the REFRESH MATERIALIZED VIEW command.
Command was: REFRESH MATERIALIZED VIEW public.computed_feature_3_specifiers_stats;


pg_restore: warning: errors ignored on restore: 6
```
Possibly needs some `public` schema name to be inserted somewhere.

