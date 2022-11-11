#!/bin/bash
spt db guess-channels-from-object-files \
../test_data/adi_preprocessed_tables/dataset1/lesion_0_1.csv \
../test_data/adi_preprocessed_tables/dataset1/lesion_0_2.csv \
../test_data/adi_preprocessed_tables/dataset1/lesion_0_3.csv \
../test_data/adi_preprocessed_tables/dataset1/lesion_6_1.csv \
../test_data/adi_preprocessed_tables/dataset1/lesion_6_2.csv \
../test_data/adi_preprocessed_tables/dataset1/lesion_6_3.csv \
../test_data/adi_preprocessed_tables/dataset1/lesion_6_4.csv \
 --output=elementary_phenotypes.csv >/dev/null 2>&1

channel_names=$(tail -n+2 elementary_phenotypes.csv | cut -f1 -d, | sort | tr '\n' ' ')
expected_channel_names="B2M B7H3 CD14 CD163 CD20 CD25 CD27 CD3 CD4 CD56 CD68 CD8 DAPI FOXP3 IDO1 KI67 LAG3 MHCI MHCII MRC1 PD1 PDL1 S100B SOX10 TGM2 TIM3 "
rm -f elementary_phenotypes.csv
if [[ "$channel_names" != "$expected_channel_names" ]];
then
    exit 1
else
    exit 0
fi
