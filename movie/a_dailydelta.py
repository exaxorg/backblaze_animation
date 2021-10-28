from datetime import timedelta, date
from collections import defaultdict
from copy import deepcopy

description = "Store new and gone serial numbers per model for each consecutive date."

#options = dict(startdate=date(2013, 4, 10), stopdate=date(2021, 1, 1))
options = dict(startdate=date(2013, 4, 10), stopdate=date(2021, 1, 1))

datasets = ('source',)


def prepare(slices):
	# Create a list of startdates [startdate, ..., stopdate]
	# having slices + 1 entries.
	numdays = (options.stopdate - options.startdate).days
	delta = numdays / slices
	x = 0
	restartdates = [options.startdate, ]
	while x < numdays:
		x += delta
		restartdates.append(options.startdate + timedelta(days=round(x)))
	return restartdates, numdays


def analysis(sliceno, prepare_res):
	restartdates, numdays = prepare_res
	driveuid = defaultdict(dict)
	restore_active = defaultdict(dict)
	restore_failed = defaultdict(dict)
	restore_removed = defaultdict(set)
	lastseen = defaultdict(dict)
	current = defaultdict(set)
	aggregated_failed = defaultdict(set)
	delta_new = defaultdict(lambda: defaultdict(set))
	delta_failed = defaultdict(lambda: defaultdict(set))
	# we know that dataset is hash partitioned on "cleanmodel", so models
	# seen here in this slice are not seen anywhere else.  We also
	# know that the dataset is sorted by date in incremental order, so
	# when the date column is incremented, we have received all info
	# for the previous date.
	currentdt = None
	for dt, model, serial, failure in datasets.source.iterate_chain(
		sliceno,
		('date', 'cleanmodel', 'serial_number', 'failure'),
		hashlabel='cleanmodel',
		range={'date': (options.startdate, options.stopdate)},
	):
		if currentdt is None:
			currentdt = dt
		if dt != currentdt:
			if currentdt in restartdates:
				restore_active[currentdt] = deepcopy(current)
				restore_failed[currentdt] = deepcopy(aggregated_failed)
			currentdt = dt
		id = driveuid[model].get(serial)
		if id is None:
			# have not seen this drive before, assign unique (for this model) number to it.
			id = len(driveuid[model])
			driveuid[model][serial] = id
			delta_new[dt][model].add(id)
		lastseen[model][id] = dt
		current[model].add(id)
		if failure:
			delta_failed[dt][model].add(id)
			aggregated_failed[model].add(id)
			current[model].remove(id)
	restore_active[options.stopdate - timedelta(days=1)] = deepcopy(current)
	restore_failed[options.stopdate - timedelta(days=1)] = deepcopy(aggregated_failed)

	# find last occurrence of each drive
	delta_removed = defaultdict(lambda: defaultdict(set))
	for model, item in lastseen.items():
		for id, dt in item.items():
			delta_removed[dt + timedelta(days=1)][model].add(id)
	# create restartpoints for removed drives
	lasts = defaultdict(set)
	for ix in range(numdays):
		dt = options.startdate + timedelta(days=ix)
		for model, drives in delta_removed[dt].items():
			lasts[model].update(drives)
		if dt in restartdates:
			restore_removed[dt] = deepcopy(lasts)

	return dict(restore_active=restore_active, restore_failed=restore_failed, restore_removed=restore_removed, delta_new=dict(delta_new), delta_failed=dict(delta_failed), delta_removed=dict(delta_removed))


def synthesis(analysis_res, prepare_res):
	restartdates, numdays = prepare_res
	r = analysis_res.merge_auto()
	r['restartdates'] = restartdates
	r['numdays'] = numdays
	return r
