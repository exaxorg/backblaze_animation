import subprocess

jobs = ('source',)

options = dict(framesname='frames/frame_%05d.jpg', framerate=60)

def synthesis(job):
	print(jobs.source.filename(options.framesname), int(options.framerate))
	subprocess.run(['ffmpeg',
					'-f', 'image2',
					'-framerate', str(options.framerate),
					'-i', jobs.source.filename(options.framesname),
					'-c:v', 'libx264',
					'-preset', 'veryfast',
					'-profile:v', 'high',
					'-cpu-used', '0',
					'out.mp4'])
	job.register_file('out.mp4')
