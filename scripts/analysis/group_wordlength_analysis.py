'''
Created on Nov 27, 2012

@author: teon
'''

import eelbrain.eellab as E
import basic.process as process
import os

root = os.path.join(os.path.expanduser('~'),'Dropbox', 'Experiments', 'NMG')
corrs_dir = os.path.join(root, 'results', 'meg', 'plots', 'corrs')
stats_dir = os.path.join(root, 'results', 'meg', 'stats')
logs_dir = os.path.join(root, 'results', 'logs')
saved_data = os.path.join(root, 'data', 'group_ds_corr.pickled')
roilabels = ['lh.fusiform', 'cuneus']

if os.path.lexists(saved_data):
    group_ds = pickle.load(open(saved_data))
else:
    e = process.NMG()
    
    datasets = []
    
    tstart = -0.1
    tstop = 0.6
    reject = 3e-12
    
    for _ in e.iter_vars(['subject']):
        e.logger('subject: ')
        meg_ds = e.load_events()
        index = meg_ds['target'].isany('prime', 'target')
        meg_ds = meg_ds[index]
    
        #add epochs to the dataset after excluding bad channels
        orig_N = meg_ds.N
        meg_ds = E.load.fiff.add_mne_epochs(meg_ds, tstart=tstart, tstop=tstop,
                                            #baseline=(tstart, 0), reject={'mag':reject}, preload=True)
                                            reject={'mag':reject}, preload=True)
        remainder = meg_ds.N*100/orig_N
        e.logger('epochs: %d' % remainder + r'% ' + 'of trials remain' )
        #do source transformation
        for roilabel in roilabels:
            meg_ds[roilabel] = e.make_stcs(meg_ds, labels=tuple(e.rois[roilabel]), 
                                           force_fixed=False)
    
            #collapsing across sources using a root-mean squared
            meg_ds[roilabel] = meg_ds[roilabel].summary('source',
                                name='stc')
    
            #baseline correct source estimates
            meg_ds[roilabel] -= meg_ds[roilabel].summary(time=(tstart, 0))
        del meg_ds['epochs']
    
    
    
        #Append to group level datasets
        datasets.append(meg_ds)
    
    #combines the datasets for group
    group_ds = E.combine(datasets)
    
    e.print_log(os.path.join(logs_dir, 'group_wordlength_log.txt'))
    E.save.pickle(group_ds, saved_data)


cstart = 0
cstop = None
ctp = .05
for roilabel in roilabels:
    title = 'Correlation of Word Length and Brain Activity in %s' % roilabel
    a = E.testnd.cluster_corr(Y=group_ds[roilabel], X=group_ds['word_length'],
                              norm=group_ds['subject'], tstart=cstart, 
                              tstop=cstop, tp=ctp)
    with open(os.path.join(stats_dir, 'group_wordlength_%s.txt' %roilabel) ,'w') as FILE:
        FILE.write(title + '\r\n'*2)
        FILE.write(str(a.as_table()))
    p = E.plot.uts.clusters(a, figtitle = title, axtitle = False, 
                            ls = 'dashed', tcolor = 'g')
    p.figure.savefig(os.path.join(corrs_dir,
        'group_wordlength_corr_%s.pdf' % roilabel))
    
#    idx = group_ds['target'] == 'target'
#    title = 'Word Length Correlation by Wordtype in %s' % roilabel
#    group = group_ds[idx]
#    group = group.compress(group['condition'] % group['wordtype'] %
#                              group['subject'], drop_bad = True)
#    a = E.testnd.cluster_anova(Y=group[roilabel], X=group['wordtype'], 
#                               tstart=cstart)
#    p = E.plot.uts.clusters(a, figtitle = title, ls = 'dashed', tcolor = 'g')
#    p.figure.savefig(os.path.join(corrs_dir, 'group_wordlength_wordtype_anova_%s.pdf' 
#                      % roilabel))