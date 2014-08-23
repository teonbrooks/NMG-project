'''
Created on Nov 27, 2012

@author: teon
'''

import eelbrain.eellab as E
import basic.process as process
import os
import cPickle as pickle
import numpy as np

redo = True

# raw data parameters
raw = 'calm_fft_hp1_lp40'
tmin = -0.1
tmax = 0.6
reject = 4e-12
decim = 2
analysis = 'wl'
orient = 'fixed'
avg = True


# analysis paramaters
cstart = 0
cstop = None
pmin = .1

# roilabels = ['fusiform', 'cuneus']
# rois = ['lh.fusiform', 'lh.cuneus']

e = process.NMG()
e.set(raw=raw)
e.set(datatype='meg')
e.set(analysis=analysis, orient=orient)

if os.path.lexists(e.get('group-file')) and not redo:
    group_ds = pickle.load(open(e.get('group-file')))
else:
    datasets = []
    for _ in e:
        # Selection Criteria
        ds = e.load_events()
        ds = ds[ds['target'].isany('prime', 'target')]

        ds = e.make_epochs(ds, evoked=False, raw=raw, decim=decim)

        if ds.info['use']:
            design_matrix = np.ones([ds.n_cases, 2])
            design_matrix[:, 1] = ds['st'].x
            names = ['intercept', 'st']
            ols_fit = mne.stats.regression.ols_epochs(ds['epochs'],
                                                      design_matrix, names)
            ds = ds.aggregate('subject', drop_bad=True)
            ds['epochs'] = [ols_fit['t']['st']]

        if ds.info['use']:
            ds = e.analyze_source(ds, rois=rois, roilabels=roilabels,
                                  tmin=tmin, avg=avg)
            # Append to group level datasets
            datasets.append(ds)
            del ds
    # combines the datasets for group
    group_ds = E.combine(datasets)
    del datasets
    E.save.pickle(group_ds, e.get('group-file'))

sub = len(group_ds['subject'].cells)
e.logger.info('%d subjects entered into stats.\n %s'
              % (sub, group_ds['subject'].cells))

analyses = []
for roilabel in roilabels:
    title = 'Correlation of Word Length in %s' % roilabel
    a = E.testnd.corr(Y=group_ds[roilabel], X='word_length', norm='subject',
                      tstart=cstart, tstop=cstop, pmin=pmin, ds=group_ds,
                      samples=1000, tmin=.01, match='subject')
    p = E.plot.UTSClusters(a, title=None, axtitle=title, w=10)
    e.set(analysis='%s_%s' % (analysis, roilabel))
    p.figure.savefig(e.get('plot-file'))
    analyses.append(a)

