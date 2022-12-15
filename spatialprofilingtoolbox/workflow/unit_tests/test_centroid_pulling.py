
from spatialprofilingtoolbox.workflow.common.structure_centroids_puller import \
    StructureCentroidsPuller

if __name__ == '__main__':
    with StructureCentroidsPuller(database_config_file='../db/.spt_db.config.container') as puller:
        puller.pull()
        structure_centroids = puller.get_structure_centroids()

    for study_name, study in structure_centroids.studies.items():
        if study.keys() != set(['lesion 0_1', 'lesion 0_2', 'lesion 0_3', 'lesion 6_1',
                                'lesion 6_2', 'lesion 6_3', 'lesion 6_4']):
            print('Wrong sample set: %s' % str(study.keys()))
            exit(1)
        for sample, points in study.items():
            if len(points) != 100:
                print('Wrong number of centroids: %s' % str(len(points)))
                exit(1)

            if sample == 'lesion 0_1':
                point_first = [4935.0, 12.0]
                point_last = [5330.0, 290.0]
                if point_first != points[0]:
                    print('Wrong first centroid: %s' % str(points[0]))
                    exit(1)
                if point_last != points[len(points)-1]:
                    print('Wrong last centroid: %s' %
                          str(points[len(points)-1]))
                    exit(1)
