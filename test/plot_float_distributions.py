"""Plot the distributions for each possible 8-bit floating point specification."""

from matplotlib import pyplot as plt
import matplotlib.pyplot as plt

from spatialprofilingtoolbox.standalone_utilities.float8 import float_format
from spatialprofilingtoolbox.standalone_utilities.float8 import generate_metadata_table


def create_comparison_plot():
    n_bins = 50
    _, axs = plt.subplots(4, 7, sharey=True, tight_layout=True)
    for J in reversed(range(4)):
        for I in range(7):
            f = float_format(I + 1, J)
            _, df = generate_metadata_table(f)
            values = df['decoded_value']
            axs[J, I].hist(values, bins=n_bins)

    for ax, J in zip(axs[:,0], reversed(range(4))):
        ax.set_ylabel(f'Exponent shift {J}', rotation=0)

    for ax, I in zip(axs[3,:], range(7)):
        ax.set_xlabel(f'Exponent bits {I + 1}\nFixed bits {8 - I - 1}', rotation=0)

    plt.show()


if __name__=='__main__':
    create_comparison_plot()
