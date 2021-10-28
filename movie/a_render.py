from collections import defaultdict
from datetime import date, timedelta

from PIL import Image, ImageFont, ImageDraw
from os import mkdir
from os.path import dirname, join, exists

depend_extra = ('coords.txt',)

jobs = ('source', 'modelduration', 'sizes', 'totalsize')

options = dict(failframes=53)

missing_dates = set([date(2014, 11, 2), date(2015, 11, 1), date(2017, 1, 30)])

fonts = {size: ImageFont.truetype('DejaVuSerif', size) for size in (12, 14, 30, 300)}


def prepare(slices):
	mkdir('frames')
	startdate = jobs.source.params.options.startdate
	stopdate = jobs.source.params.options.stopdate

	# load total size per day
	totalsize = jobs.totalsize.load()
	# load coordinates of hard disk screen locations from file
	locationpermodel = {}
	with open(join(dirname(__file__), 'coords.txt'), 'rt') as fh:
		for line in fh:
			x, y, name = line.rstrip('\n').split(' ', 2)
			locationpermodel[name] = (int(x), int(y))
	# load dict with first date per MODEL
	modelfirstseen, _ = jobs.modelduration.load()
	# load all data to be plotted
	data = jobs.source.load()
	# load dict of drive size per model
	_, _, sizepermodel = jobs.sizes.load()
	# create dict of dates to frame numbers
	date2fnbr = {}
	days = data['numdays']
	for fnumber in range(days):
		date2fnbr[startdate + timedelta(days=fnumber)] = fnumber
	# Dict of start and stop dates per slice.
	# (The stop date is the next slice's start date.)
	daterangeperslice = dict()
	it = iter(data['restartdates'])
	prevdt = next(it)
	for sliceno, dt in enumerate(it):
		daterangeperslice[sliceno] = (prevdt, dt)
		prevdt = dt
	return modelfirstseen, data, locationpermodel, date2fnbr, daterangeperslice, sizepermodel, totalsize, startdate, stopdate


def analysis(prepare_res, job, sliceno, slices):
	modelfirstseen, data, locationpermodel, date2fnbr, daterangeperslice, sizepermodel, totalsize, moviestartdate, moviestopdate = prepare_res

	background = (64, 64, 64)
	size = (1920, 1080)
	bg_image = Image.new('RGB', size, color=background)
	draw_on_bg = ImageDraw.Draw(bg_image)
	draw_on_bg.text((600, -100), 'exax.org', font=fonts[300], fill=(70,70,70))

	def square(drivenbr, origin):
		# return (x0, y0, x1, y1) of square size S at origin for drivenbr
		x0, y0 = origin
		S = 2
		s = drivenbr // (200 * 60)
		y = drivenbr % (200 * 60)
		x = y % 60
		y = y // 60
		return (
			x0 + S * (60 * s + x),
			y0 - S * y,
			x0 + S * (60 * s + x) + S - 1,
			y0 - S * y - S + 1
		)

	def drawdrive(n, origin, color=(255,255,255)):
		draw_on_bg.rectangle(square(n, origin), fill=color)

	def drawdrivenames(dt, init=False):
		for model in modelfirstseen:
			if (model in locationpermodel):
				if ((dt >= modelfirstseen[model]) and init) or ((dt == modelfirstseen[model]) and not init):
					x, y = locationpermodel[model]
					size = str(sizepermodel.get(model, 0)) + "TB"
					if model.startswith('ST'):
						model = 'Seagate_' + model
					model = model.replace('TOSHIBA', 'Toshiba')
					text = model.split('_')
					draw_on_bg.text((x, y + 3), text[1], font=fonts[12], fill=(255, 255, 255))
					sz = draw_on_bg.textsize(size + ' ', font=fonts[14])[0]
					draw_on_bg.text((x, y + 3 + 14), size, font=fonts[14], fill=(192, 255, 192))
					draw_on_bg.text((x + sz, y + 3 + 14), text[0], font=fonts[14], fill=(255, 255, 255))

	class SetFifo:
		def __init__(self, n):
			self.hist = [set() for x in range(n)]
			self.current = set()
			self.n = n

		def add(self, drive, origin):
			self.current.add(square(drive, origin)[:2])

		def update(self):
			self.hist = [self.current,] + self.hist[0:self.n - 1]
			self.current = set()

	if not daterangeperslice[sliceno]:
		return
	startdate, stopdate = daterangeperslice[sliceno]

	# draw current state
	for model, drives in data['restore_active'][startdate].items():
		if model in locationpermodel and drives:
			for drive in drives:
				drawdrive(drive, locationpermodel[model], color=(147, 147, 147))
	for model, drives in data['restore_removed'].get(startdate, {}).items():
		if model in locationpermodel and drives:
			for drive in drives:
				drawdrive(drive, locationpermodel[model], color=(0, 0, 0))
	for model, drives in data['restore_failed'].get(startdate, {}).items():
		if model in locationpermodel and drives:
			for drive in drives:
				drawdrive(drive, locationpermodel[model], color=(255, 47, 47))
	drawdrivenames(startdate, True)

	slack_days = max(13, options.failframes)
	fails = SetFifo(options.failframes)
	news = SetFifo(13)

	def feed_day(d):
		# Add new drives to animationfifo
		first = data['delta_new'].get(d, {})
		for model, drives in first.items():
			if model in locationpermodel and drives:
				for drive in drives:
					news.add(drive, locationpermodel[model])
		# Fill drives that go missing with black
		last = data['delta_removed'].get(d, {})
		for model, drives in last.items():
			if model in locationpermodel and drives:
				for drive in drives:
					drawdrive(drive, locationpermodel[model], color=(0, 0, 0))
		# Add failed drives to animationfifo
		failed = data['delta_failed'].get(d, {})
		for model, drives in failed.items():
			if model in locationpermodel and drives:
				for drive in drives:
					fails.add(drive, locationpermodel[model])
		drawdrivenames(d)
		feed_bg()

	def feed_bg():
		fails.update()
		news.update()
		for t, hist in enumerate(news.hist, 1):
			for x, y in hist:
				draw_on_bg.rectangle((x, y, x + 1, y - 1), fill=(255-8*t, 255-8*t, 255-8*t))
		for t, hist in enumerate(fails.hist, 1):
			for x, y in hist:
				draw_on_bg.rectangle((x, y, x + 1, y - 1), fill=(255, 255-5*t, 255-5*t))

	def animate_day(d, fnumber):
		frame_image = bg_image.copy()
		draw_on_frame = ImageDraw.Draw(frame_image, 'RGBA')
		for t, hist in enumerate(fails.hist, 1):
			for x, y in hist:
				draw_on_frame.ellipse((x - t, y - t, x + t, y + t), width=3 + (14 * t) // 48, outline=(255, 5*t, 5*t, 255-5*t))
		# Timestamp
		size = '{:,}TB'.format(round(totalsize[d]/1e12))
		sz = draw_on_frame.textsize(size, font=fonts[14])[0]
		draw_on_frame.text((1910-sz, 1020), size, font=fonts[14], fill=(255, 255, 255), stroke_fill=(0, 0, 0), stroke_width=1)
		draw_on_frame.text((1740, 1040), str(d), font=fonts[30], fill=(255, 255, 255), stroke_fill=(0, 0, 0), stroke_width=1)
		fn = 'frames/frame_%05d.jpg' % (fnumber,)
		assert not exists(fn), (fn, sliceno, d, fnumber)
		frame_image.save(fn)
		job.register_file(fn)

	if sliceno > 0:
		# we need to have the same data in the fifos and bg as we would
		# have had if starting from the beginning
		d = startdate - timedelta(days=slack_days)
		for _ in range(slack_days):
			feed_day(d)
			d += timedelta(days=1)

	d = startdate
	while d < stopdate:
		feed_day(d)
		animate_day(d, date2fnbr[d])
		d += timedelta(days=1)

	if sliceno == slices - 1:
		# final slice lets animation finish
		last_date = stopdate - timedelta(days=1)
		last_fnumber = date2fnbr[last_date]
		for fnumber in range(last_fnumber + 1, last_fnumber + slack_days + 3):
			feed_bg()
			animate_day(last_date, fnumber)
