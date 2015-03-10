'''
Created on Nov 27, 2012
Analysis for Frontiers

@author: teon
'''

import eelbrain as E
import basic.process as process
import os
import numpy as np

redo = False

# raw data parameters
raw = 'calm_iir_hp1_lp40'
tmin = -0.1
tmax = 0.6
reject = {'mag':4e-12}
orient = 'free'
decim = 2
morph = True

# analysis paramaters
cstart = 0.3
cstop = None
pmin = .05

e = process.NMG(None, '{teon-backup_drive}')
e.set(raw=raw)
e.set(datatype='meg', orient=orient)

# l1 = mne.read_label(u'/Volumes/teon-backup/Experiments/MRI/fsaverage/label/lh.LATL.label')
l1 = e.read_label('lh.LATL')
# l2 = mne.read_label(u'/Volumes/teon-backup/Experiments/MRI/fsaverage/label/lh.LPTL.label')
l2 = e.read_label('lh.LPTL')

roi = l1 + l2

if os.path.lexists(e.get('group-file')) and not redo:
    group_ds = pickle.load(open(e.get('group-file')))
else:
    datasets = []
    for _ in e:
        print e.subject
        # Selection Criteria
        ds = e.load_events(edf=True, proj=False)
        idx = ds['target'] == 'prime'
        idy = ds['condition'] == 'identity'
        ds = ds[idx * idy]
        if 'raw' in ds.info:
            ds = e.make_epochs(ds, evoked=True, raw=raw, model='wordtype',
                               reject=reject, decim=decim)
        else:
            ds.info['use'] = False
        if ds.info['use']:
            ds = e.analyze_source(ds, evoked=True, orient=orient, tmin=tmin,
                                  morph=morph)
            # Append to group level datasets
            datasets.append(ds)
            del ds
    # combines the datasets for group
    group_ds = E.combine(datasets)
    del datasets
    E.save.pickle(group_ds, e.get('group-file', analysis=analysis))

n_sub = len(group_ds['subject'].cells)
e.logger.info('%d subjects entered into stats.\n %s'
              % (n_sub, group_ds['subject'].cells))

# Create a report
report = E.Report("Prime Analyses", author="Teon")
section = report.add_section("Info")
section.append('%d subjects entered into stats.\n\n %s\n\n'
              % (n_sub, group_ds['subject'].cells))
section = report.add_section("Planned Comparison of Word Type "
                             "Differences in Temporal Lobe.")
section.append('Rejection: %s. Cluster start: %s. Decim: %s' % (reject, cstart,
                                                                decim))

analyses = []
wtypes = list(group_ds['wordtype'].cells)
wtypes.remove('ortho')


for wtype in wtypes:
    idx = group_ds['wordtype'].isany('ortho', wtype)
    a = E.testnd.ttest_rel(Y=group_ds['stc'].sub(source=roi), X='wordtype',
                           c0='ortho', c1=wtype, match='subject', tstart=cstart,
                           tstop=cstop, pmin=pmin, ds=group_ds, sub=idx, tail=1,
                           samples=10000)
    analyses.append(a)
    title = 'TTest in Temporal Lobe'
    for i, cluster in enumerate(a.clusters[a.clusters['p'] < .15].itercases()):
        c_0 = cluster['cluster']
        p = cluster['p']
        c_tstart = cluster['tstart']
        c_tstop = cluster['tstop']
        section = report.add_section("Cluster %s, p=%s" % (i, p))
        report.add_section('Cluster start: %s, Cluster stop: %s' %(c_tstart,
                                                                   c_tstop))
        c_extent = c_0.sum('time')
        plt_extent = E.plot.brain.cluster(c_extent, surf='inflated',
                                          views=['frontal', 'lateral'])
        image = E.plot.brain.image(plt_extent, "cluster %s extent.png" % i,
                                   alt=None, close=True)
        image.save_image(e.get('plot-file', analysis=wtype+'_prime_brain'))
        section.add_image_figure(image, "Extent of the largest "
                                 "cluster, p=%s" % p)
        plt_extent.close()

        # extract and analyze the value in the cluster in each trial
        index = c_0 != 0
        c_value = group_ds['stc'].sum(index)

        index = c_extent != 0
        c_timecourse = group_ds['stc'].sub(source=roi).mean(index)
        color_maps = {wtype: 'green', 'ortho': 'blue'}
        plt_tc = E.plot.UTSStat(c_timecourse, X='wordtype', ds=group_ds,
                                sub=idx, axtitle=title, colors=color_maps,
                                ylabel='dSPM')
        # plot the cluster
        for ax in plt_tc._axes:
            ax.axvspan(c_tstart, c_tstop, color='r', alpha=0.15, zorder=-2)
        plt_tc.figure.savefig(e.get('plot-file', analysis=wtype+'_prime'))
        im = plt_tc.image()
        plt_tc.close()
        section.add_figure(caption='Difference Plots', content=im)
        

# save the report
report.save_html(e.get('report-file', analysis=analysis + '_temporal-prime-updated'))