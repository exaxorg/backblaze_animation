from collections import Counter

description = "Total storage per day in bytes."

jobs = ('drivesizes',)

datasets = ('source',)


# We need to use our own computed drivesizes, because sometimes
# there are large fluctuations in the "capacity_bytes" column.

def prepare():
	return jobs.drivesizes.load()[0]


def analysis(sliceno, prepare_res):
	drivesizes = prepare_res
	s = Counter()
	for ts, model in datasets.source.iterate_chain(sliceno, ('date', 'cleanmodel')):
		s[ts] += drivesizes[model]
	return s


def synthesis(analysis_res):
	s = analysis_res.merge_auto()
	return s
