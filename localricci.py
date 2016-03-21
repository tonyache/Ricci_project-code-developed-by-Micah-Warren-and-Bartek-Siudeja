""" Coarse Ricci flow for a point cloud. """
import numpy as np
import numexpr as ne
from sklearn import cluster, datasets
from scipy.spatial.distance import cdist


# treat some numpy warnings as errors?
np.seterr(all="print")  # divide='raise', invalid='raise')

#
#   simulation parameters
#
runs = 100000  # how many iterations
show = 10  # how frequently we show the result
eta = 0.0075  # factor of Ricci that is added to distance squared
threshold = 0.15  # clustering threshold
upperthreshold = .65  # won't try to cluster if distances in ambiguity interva (threshold, upperthreshold)
# 'min' rescales the distance squared function so minimum is 1.
# 'L1' rescales it so the sum of distance squared stays the same
#   (perhaps this is a misgnomer and it should be 'L2' but whatever)
rescale = 'L1'
t = 0.1  # should not be integer to avaoid division problems
noise = 0.4  # noise coefficient
CLIP = 60  # value at which we clip distance function

np.set_printoptions(precision=2, suppress=True)

# import data
from tools import metricize, is_clustered
from Laplacian import Laplacian
from Ricci import coarseRicci, applyRicci


# sqdist = data.onedimensionpair(2, 3, noise)
# sqdist = data.cyclegraph(6, noise)
# sqdist = data.closefarsimplices(3, 0.1, 3)


# sqdist, pointset = data.twodimensionpair(35, 25, noise)
twodim = True

n_samples = 300
pointset, Zcolors = datasets.make_circles(n_samples=n_samples, factor=.5,
                                          noise=.01)
sqdist = cdist(pointset, pointset, 'sqeuclidean')
print pointset

metricize(sqdist)
L = Laplacian(sqdist, t)
Ricci = coarseRicci(L, sqdist)

print 'initial distance'
print sqdist
print 'initial Ricci'
print Ricci

applyRicci(sqdist, eta, Ricci, mode='sym')

initial_L1 = sqdist.sum()
# This will modify Ricci locally more than far away.
loosekernel = ne.evaluate('eta*exp(-sqdist)')

for i in range(runs + show + 3):
    L = Laplacian(sqdist, t)
    Ricci = coarseRicci(L, sqdist)
    applyRicci(sqdist, loosekernel, Ricci, mode='sym')

    # total_distance = sqdist.sum()
    # sqdist = (total_distance0/total_distance)*sqdist
    nonzero = sqdist[np.nonzero(sqdist)]
    mindist = np.amin(nonzero)
    s1 = mindist
    s2 = sqdist.sum()
    # print t
    # ne.evaluate("dist/s", out=dist)

    sqdist = np.clip(sqdist, 0, CLIP)
    if rescale == 'L1':
        ne.evaluate("initial_L1*sqdist/s2", out=sqdist)
    if rescale == 'min':
        ne.evaluate("sqdist/s1", out=sqdist)
    metricize(sqdist)
    if i % show == 2:
        print Ricci
        print "sqdist for ", i, "  time"
        print sqdist
        print 't = ', t
        # print Ricci
        # print Ricci/dist, '<- Ricc/dist'
        print '---------'
        if ((sqdist > threshold) & (sqdist < upperthreshold)).any():
            print 'values still in ambiguous interval'
            continue
        if is_clustered(sqdist, threshold):
            break


if twodim:
    np.savetxt('Zcolors.csv', Zcolors)
    import matplotlib.pyplot as plt
    plt.scatter(pointset[:, 0], pointset[:, 1])
    plt.axis('equal')
    plt.show()