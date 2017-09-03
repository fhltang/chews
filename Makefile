chews: genfiles
	protoc -I=proto --python_out=genfiles proto/config.proto

genfiles:
	mkdir genfiles
	touch genfiles/__init__.py
