__init__.py: *.png __init__.py.gotmpl
	# http://github.com/NateScarlet/gotmpl v0.2.0
	ls *.png | jq -nR 'reduce inputs as $$item ([]; . + [$$item]) | { Files: . }' | gotmpl -i - -o $@ __init__.py.gotmpl
	python -m black $@


%.pos.png:
	magick convert $@ -depth 1 $@

	