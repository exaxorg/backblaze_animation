description = "Find first and last date seen for each model."

datasets = ('source',)


def analysis(sliceno):
	seen = set()
	low = {}
	high = {}
	for ts, model in datasets.source.iterate_chain(sliceno, ('date', 'cleanmodel'), hashlabel='cleanmodel'):
		if model not in seen:
			seen.add(model)
			low[model] = ts
			high[model] = ts
		else:
			if ts < low[model]:
				low[model] = ts
			elif ts > high[model]:
				high[model] = ts
	return (low, high)


def synthesis(analysis_res):
	low, high = analysis_res.merge_auto()
	return (low, high)
