"""Extract data from downloads."""
import re
from argparse import ArgumentParser
from os.path import join
from os import listdir
from os.path import isfile
from typing import cast
from multiprocessing import Pool

from pandas import read_excel
from pandas import read_csv
from pandas import DataFrame
from pandas import Series
from pandas import merge
from pandas import concat
from numpy import mean

from _extraction_formats import get_supplement_filename  # pylint: disable=E0611
from _extraction_formats import get_extraction_method  # pylint: disable=E0611
from _extraction_formats import get_preservation_method  # pylint: disable=E0611
from _extraction_formats import get_storage_location  # pylint: disable=E0611
from _extraction_formats import form_assay_description  # pylint: disable=E0611
from _extraction_formats import form_intervention_description  # pylint: disable=E0611
from _extraction_formats import form_sample_id  # pylint: disable=E0611
from _extraction_formats import form_subject_id  # pylint: disable=E0611
from _extraction_formats import top_directory  # pylint: disable=E0611
from _extraction_formats import create_sparse_dataframe  # pylint: disable=E0611
from _cell_position_checking import check_cells_against_supplement_cells  # pylint: disable=E0611
from _cell_measurement_aggregation import create_cell_measurement_table  # pylint: disable=E0611
from _check_channel_references_in_phenotypes import check_channel_references  # pylint: disable=E0611

def parse_date(date_string: str, relative: bool=False, timepoint: int | None = None) -> str | None:
    match = re.search(r'^([\d]{4})([\d]{2})([\d]{2})$', str(date_string))
    if match:
        value = ''
        if relative:
            value = '-'.join(match.groups()) + ' relative to birth date'
        else:
            value = '-'.join(match.groups())
        if timepoint is not None:
            value = value + f', timepoint {timepoint}'
        return value
    raise ValueError('Cannot parse date from: {date_string}')

def retrieve_channels():
    channels = read_excel(get_supplement_filename(), sheet_name=2, header=2)
    channels = channels[channels['Metal-Tag'] != '']
    channels = channels[['Metal-Tag', 'Target Name', 'Clone']]
    def strip(string: str) -> str:
        return str(string).strip()
    channels['Clone'] = channels['Clone'].apply(strip)
    print(f'Channels: {" ".join(list(channels[0:3]["Target Name"]))} ... ({len(channels)} total).')
    return channels

def retrieve_antibody_info(supplement_channels, manual_channels):
    merged = get_merged_channels(supplement_channels, manual_channels)
    return merged['Clone']

def get_merged_channels(supplement_channels: DataFrame, manual_channels: DataFrame) -> DataFrame:
    df1 = supplement_channels.set_index('Target Name')
    df2 = manual_channels.set_index('Supplement fragment')
    df = merge(df2, df1, how='left', left_index=True, right_index=True)
    reindexed = df.set_index('Name')
    return reindexed

def write_elementary_phenotypes(supplement_channels: DataFrame, manual_channels: DataFrame):
    copyable = ['Name', 'Target structure class', 'Marking mechanism', 'Target full name']
    df = DataFrame({c: manual_channels[c] for c in copyable})
    df['Column header fragment prefix'] = df['Name']
    df['idx'] = df['Name']
    df.set_index('idx', inplace=True)
    df['Antibody'] = retrieve_antibody_info(supplement_channels, manual_channels)
    filename = join('generated_artifacts', 'elementary_phenotypes.csv')
    order = [
        'Name', 'Column header fragment prefix', 'Target structure class', 'Antibody',
        'Marking mechanism', 'Target full name',
    ]
    df = df[order]
    df.to_csv(filename, sep=',', index=False)

def get_metal_tag_suffix(channel_name: str, big_channels_df: DataFrame) -> str:
    metal_tag = big_channels_df['Metal-Tag'][channel_name]
    match = re.search(r'^([\d]{3})([a-zA-Z]{2})$', metal_tag)
    if match is None:
        raise ValueError(f'Could not parse metal tag: {metal_tag}')
    parts = match.groups()
    return f'{parts[1]}{parts[0]}'

def get_tiff_filename(
    sample_id: str,
    channel_name: str,
    big_channels_df: DataFrame,
    samples: DataFrame,
) -> str:
    suffix = get_metal_tag_suffix(channel_name, big_channels_df)
    filepath_fragment = samples['Filename base'][sample_id]
    directory = join(top_directory(), filepath_fragment)
    files = list(listdir(directory))
    matches = [
        file for file in files
        if re.search(f'_{suffix}.tiff$', file)
    ]
    if len(matches) > 1:
        raise ValueError(f'More than one file matches for {channel_name}: {matches}')
    if len(matches) == 0:
        raise ValueError(f'No file matches for {channel_name}.')
    return join(directory, matches[0])

def form_cells_mask_filename(base: str) -> str:
    return f'{base}_ilastik_s2_Probabilities_mask.tiff'

def retrieve_sample_subjects_stuff():
    samples = read_excel(get_supplement_filename(), sheet_name=1, header=1)
    samples = samples[samples['Cohort'] == 'ICI']
    samples['Sample ID'] = form_sample_id(samples['Sample_ID'])
    samples['Source subject'] = form_subject_id(samples['Sample_ID'])
    samples['Source site'] = samples['Tissue_Source_Simplified']
    age = 'Source subject age at specimen collection'
    samples[age] = samples['acquisition_date'].apply(lambda d: parse_date(d, relative=True))
    sex_codes = {'M': 'Male', 'F': 'Female'}
    samples['Sex'] = samples['Sex'].apply(lambda code: sex_codes[code])
    samples['Extraction method'] = get_extraction_method()
    def date1(d: str):
        return parse_date(d, timepoint=1)
    samples['Extraction date'] = samples['acquisition_date'].apply(date1)
    samples['Preservation method'] = get_preservation_method()
    samples['Storage location'] = get_storage_location()
    samples['Assay'] = samples['Treatment'].apply(form_assay_description)
    response_codes = {'Yes': 'Responder', 'No': 'Non-responder'}
    samples['Assessment'] = samples['Response'].apply(lambda code: response_codes[code])
    samples['Intervention'] = samples['Treatment'].apply(form_intervention_description)
    samples['Mask filename'] = samples['filename'].apply(form_cells_mask_filename)
    samples['Filename base'] = samples['filename']
    samples['idx'] = samples['Sample ID']
    samples.set_index('idx', inplace=True)
    columns = [
        'Sample ID',
        'Source subject',
        'Source site',
        age,
        'Sex',
        'Extraction method',
        'Extraction date',
        'Preservation method',
        'Storage location',
        'Assay',
        'Assessment',
        'Intervention',
        'Mask filename',
        'Filename base',
    ]
    samples = samples[columns]
    print(f'{samples.shape[0]} samples detected.')
    return samples

def get_cells_mask_filename(sample_row: Series, print_sample: bool=False) -> str:
    sample = re.sub('^Mold_sample_', '', sample_row["Sample ID"])
    if print_sample:
        print(f'{sample} ', end='', flush=True)
    return join(top_directory(), sample_row['Filename base'], sample_row['Mask filename'])

def centroid_aggregation(sparse_values: DataFrame) -> Series:
    return Series({
        'Row': cast(float, mean(sparse_values['Row'])),
        'Column': cast(float, mean(sparse_values['Column'])),
    })

def retrieve_cell_positions_one_sample(sample_info: Series) -> DataFrame:
    filename = get_cells_mask_filename(sample_info, print_sample=True)
    sparse_df = create_sparse_dataframe(filename)
    centroids = sparse_df.groupby('Value').apply(centroid_aggregation)  # type: ignore
    return centroids

def retrieve_cell_positions(samples: DataFrame) -> dict[str, DataFrame]:
    cells = {}
    print('Processing cell data from TIFF masks.')
    for sample_id, sample_info in samples.iterrows():
        cells[str(sample_id)] = retrieve_cell_positions_one_sample(sample_info)
        print(f'{len(cells[str(sample_id)])} cells. ', end='', flush=True)
    print('')
    sizes = [df.shape[0] for _, df in cells.items()]
    peek = ", ".join([str(s) for s in sizes[0:5]])
    print(f'{peek} ... cells found (across {len(cells)} samples).')
    print(f'{sum(sizes)} cells total.')
    return cells

def check_all_tiff_channel_files_available(channels: DataFrame, samples: DataFrame):
    try:
        for sample_id in samples.index:
            for channel in channels.index:
                filename = get_tiff_filename(sample_id, channel, channels, samples)
                if not isfile(filename):
                    raise ValueError(f'{sample_id} at {channel} not found. Tried {filename}.')
    except Exception as e:
        print('Some error searching for channel TIFF files.')
        raise e
    print('TIFF files found for all channel/sample combinations.')


class CellManifestWriter:
    """Write one sample's worth of cells to file."""
    def write_cell_file(self,
        index: int,
        sample_id: str,
        sample_info: Series,
        channels: DataFrame,
        samples: DataFrame,
    ):
        channel_files = {
            channel: get_tiff_filename(sample_id, channel, channels, samples)
            for channel in channels.index
        }
        mask_file = get_cells_mask_filename(sample_info)
        df = create_cell_measurement_table(channel_files, mask_file)
        base = f'{index}.csv'
        outfile = join('generated_artifacts', base)
        df.to_csv(outfile, sep=',', index=False)
        print(f'Done with {sample_id} (file {index}).')
        return (sample_id, base)


def handle_cell_measurements(
    samples: DataFrame,
    channels: DataFrame,
    number_cores: int,
) -> list[tuple[str, str]]:
    print('Aggregating component TIFF files, for each sample, over cell segments.')
    writer = CellManifestWriter()
    samples_items = [
        (str(_sample_id), sample_row)
        for _sample_id, sample_row in samples.sort_values(by='Sample ID').iterrows()
    ]
    arguments = zip(
        range(samples.shape[0]),
        [item[0] for item in samples_items],
        [item[1] for item in samples_items],
        [channels for _ in range(samples.shape[0])],
        [samples for _ in range(samples.shape[0])],
    )
    print(f'Using {number_cores} cores.')
    with Pool(number_cores) as pool:
        cell_files_written = pool.starmap(writer.write_cell_file, arguments)
    return cell_files_written

def write_samples(samples: DataFrame):
    columns = [
        'Sample ID',
        'Source subject',
        'Source site',
        'Source subject age at specimen collection',
        'Extraction method',
        'Extraction date',
        'Preservation method',
        'Storage location',
        'Assay',
        'Assessment',
    ]
    df = samples[columns].sort_values(by='Sample ID')
    filename = join('generated_artifacts', 'samples.tsv')
    df.to_csv(filename, sep='\t', index=False)

def write_diagnosis(samples: DataFrame):
    columns = [
        'Source subject',
        'Assessment',
    ]
    df = samples[columns].rename(
        {
            'Source subject': 'Subject of diagnosis',
            'Assessment': 'Diagnosis',
        },
        axis=1,
    )
    df['Diagnosed condition'] = 'Response to immune checkpoint inhibitor therapy'
    df = df[['Subject of diagnosis', 'Diagnosed condition', 'Diagnosis']]
    df.sort_values(by='Subject of diagnosis', inplace=True)
    df['Date of diagnosis'] = 'timepoint 3'
    df['Last date of considered evidence'] = 'timepoint 3'
    filename = join('generated_artifacts', 'diagnosis.tsv')
    df.to_csv(filename, sep='\t', index=False)

def write_subjects(samples: DataFrame):
    columns = [
        'Source subject',
        'Sex',
    ]
    df = samples[columns].rename({'Source subject': 'Subject ID'}, axis=1)
    df.sort_values(by='Subject ID', inplace=True)
    filename = join('generated_artifacts', 'subjects.tsv')
    df.to_csv(filename, sep='\t', index=False)

def write_interventions(samples: DataFrame):
    columns = [
        'Source subject',
        'Intervention',
    ]
    df = samples[columns].rename({'Source subject': 'Subject of intervention'}, axis=1)
    df['Date of intervention'] = 'timepoint 2'
    df.sort_values(by='Subject of intervention', inplace=True)
    filename = join('generated_artifacts', 'interventions.tsv')
    df.to_csv(filename, sep='\t', index=False)

def write_file_manifest(cell_files_written: list[tuple[str, str]]):
    entries = [
        [
            'file_' + re.sub(r'\.csv$', '', filename),
            filename,
            sample,
            'Tabular cell manifest',
        ]
        for sample, filename in cell_files_written
    ]
    columns = ['File ID', 'File name', 'Sample ID', 'Data type']
    cells = DataFrame(entries, columns=columns)
    specials = read_csv(join('manually_created', 'file_manifest_specials.tsv'), sep='\t')
    specials['Sample ID'] = ''
    df = concat([cells, specials])
    df['Project ID'] = 'Melanoma CyTOF ICI'
    filename = join('generated_artifacts', 'file_manifest.tsv')
    df.to_csv(filename, sep='\t', index=False)

def extract(number_cores: int):
    supplement_channels = retrieve_channels()
    manual_channels = read_csv(join('manually_created', 'channels.tsv'), sep='\t')
    write_elementary_phenotypes(supplement_channels, manual_channels)
    check_channel_references()
    channels = get_merged_channels(supplement_channels, manual_channels)
    samples = retrieve_sample_subjects_stuff()
    write_samples(samples)
    write_subjects(samples)
    write_diagnosis(samples)
    write_interventions(samples)
    cell_files_written = handle_cell_measurements(samples, channels, number_cores)
    write_file_manifest(cell_files_written)
    check_all_tiff_channel_files_available(channels, samples)
    cell_positions = retrieve_cell_positions(samples)
    check_cells_against_supplement_cells(cell_positions)


if __name__=='__main__':
    parser = ArgumentParser(
        prog='extract',
    )
    parser.add_argument(
        '--cores',
        dest='cores',
        type=int,
        required=False,
        default=1,
        help='Number of cores for parallelization.'
    )
    args = parser.parse_args()
    extract(args.cores)
