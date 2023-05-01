"""Create HTML page out of UMAP plots in database."""
import sys

from spatialprofilingtoolbox.db.database_connection import DatabaseConnectionMaker

html_template = '''
<!DOCTYPE html>
<html>
<body>
%s
</body>
</html>
'''
img_template = '''
<img width="500" src="data:image/svg+xml;base64,%s"><br>
<p>%s</p><br>
'''

def create_page_from_plots(plots_base64):
    imgs = '\n'.join([
        img_template % (plot_base64, channel)
        for channel, plot_base64 in plots_base64
    ])
    return (html_template % imgs).lstrip()

def create_page():
    study = sys.argv[1]
    database_config_file = sys.argv[2]
    with DatabaseConnectionMaker(database_config_file=database_config_file) as dcm:
        connection = dcm.get_connection()
        cursor=connection.cursor()
        cursor.execute('SELECT channel, svg_base64 FROM umap_plots WHERE study=%s', (study,))
        rows = cursor.fetchall()
        plots_base64 = sorted([(row[0], row[1]) for row in rows], key=lambda x: x[0])
    html = create_page_from_plots(plots_base64)
    print(html)

if __name__=='__main__':
    create_page()
