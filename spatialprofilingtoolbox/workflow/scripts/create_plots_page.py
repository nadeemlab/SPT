"""Create HTML page out of UMAP plots in database."""
import sys
import argparse
from os.path import expanduser

from spatialprofilingtoolbox.workflow.common.cli_arguments import add_argument
from spatialprofilingtoolbox.db.database_connection import DBCursor

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<body>
%s
</body>
</html>
'''
IMG_TEMPLATE = '''
<img width="350" src="data:image/png;base64,%s"><br>
<p>%s</p><br>
'''

def create_page_from_plots(plots_base64):
    imgs = '\n'.join([
        IMG_TEMPLATE % (plot_base64, channel)
        for channel, plot_base64 in plots_base64
    ])
    return (HTML_TEMPLATE % imgs).lstrip()

def create_page_and_print(study, database_config_file):
    with DBCursor(database_config_file=database_config_file, study=study) as cursor:
        cursor.execute('SELECT channel, png_base64 FROM umap_plots WHERE study=%s', (study,))
        rows = cursor.fetchall()
        plots_base64 = sorted([(row[0], row[1]) for row in rows], key=lambda x: x[0])
    html = create_page_from_plots(plots_base64)
    print(html)

if __name__=='__main__':
    parser = argparse.ArgumentParser(
        prog='spt workflow create-plots-page',
        description='Pull out UMAP plots for a given study into an HTML page.'
    )
    add_argument(parser, 'database config')
    add_argument(parser, 'study name')
    args = parser.parse_args()

    if args.database_config_file:
        config_file = expanduser(args.database_config_file)
    else:
        sys.exit()

    create_page_and_print(args.study_name, config_file)
