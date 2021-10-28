from datetime import date

description = "Create movie from Backblaze dataset."


def main(urd):
	imp = urd.peek('import_type', '2020-12-31').joblist[-1]
	sizes = urd.build('drivesizes', source=imp)
	tot = urd.build('totalsize', source=imp, drivesizes=sizes)

	imp = urd.peek('import_hash_cleanmodel_sort', '2020-12-31').joblist[-1]
	jmd = urd.build('modelduration', source=imp)
	jdd = urd.build(
		'dailydelta',
		source=imp,
		startdate=date(2013, 4, 10),
		stopdate=date(2021, 1, 1),
	)
	job = urd.build('render', source=jdd, modelduration=jmd, failframes=51, sizes=sizes, totalsize=tot)
	job = urd.build('ffmpeg', source=job, framerate=60)
	job.link_result('out.mp4')
