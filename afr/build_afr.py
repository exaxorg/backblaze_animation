def main(urd):
	imp = urd.peek('import_hash_cleanmodel_sort', '2021-06-30').joblist[-1]
	job = urd.build('afr', source=imp)

	dayspermodel, failspermodel, serialspermodel = job.load()

	afk = {}
	for model, days in dayspermodel.items():
		if serialspermodel[model] >= 60:
			afk[model] = 365 * failspermodel[model] / days

	print()
	print('AFR during Q2 2021')
	print("model                 #drives    #days   #fails       AFR")
	for model, val in sorted(afk.items(), key=lambda x: -x[1]):
		print("%-20s %8d %8d %8d %8.2f%%" % (model[:20], serialspermodel[model], dayspermodel[model], failspermodel[model], 100 * val))
