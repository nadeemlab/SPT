
import spatialprofilingtoolbox
from spatialprofilingtoolbox.db.feature_matrix import FeatureMatrixExtractor

if __name__=='__main__':
	m = FeatureMatrixExtractor.extract('../db/.spt_db.config.container')
	print(m)
