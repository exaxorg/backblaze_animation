from collections import Counter, defaultdict

datasets = ('source',)

description = "Find drive sizes for all drive models."

"""
  Return dict {model: size, ...}.
  In a few cases, sizes are reported as -1, so we return
  the most common value and hope for the best.
"""


def analysis(sliceno):
	c = defaultdict(Counter)
	for m, size in datasets.source.iterate_chain(sliceno, ('cleanmodel', 'capacity_bytes')):
		if size > 0:
			c[m][size] += 1
	return c

def synthesis(analysis_res):
	res = Counter()
	tbres = {}
	c = analysis_res.merge_auto()
	for model, data in c.items():
		size = data.most_common()[0][0]
		res[model] = size
		# TBs as a string
		size = "%3.1f" % (size / 1e12)
		if size.endswith('.0'):
			size = size[:-2]
		tbres[model] = size
	return res, c, tbres
